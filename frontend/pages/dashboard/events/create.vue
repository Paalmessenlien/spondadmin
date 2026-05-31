<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '#ui/types'

definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const api = useApi()
const toast = useToast()
const router = useRouter()
const authStore = useAuthStore()

// Form schema
const schema = z.object({
  heading: z.string().min(3, 'Heading must be at least 3 characters'),
  description: z.string().optional(),
  event_type: z.enum(['EVENT', 'RECURRING', 'AVAILABILITY']),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string().min(1, 'End time is required'),
  location_address: z.string().optional(),
  location_latitude: z.number().optional(),
  location_longitude: z.number().optional(),
  max_accepted: z.number().min(0).default(0),
  cancelled: z.boolean().default(false),
  hidden: z.boolean().default(false),
  sync_to_spond: z.boolean().default(false)
})

type Schema = z.output<typeof schema>

// Form state
const loading = ref(false)
const state = reactive<Schema>({
  heading: '',
  description: '',
  event_type: 'EVENT',
  start_time: '',
  end_time: '',
  location_address: '',
  max_accepted: 0,
  cancelled: false,
  hidden: false,
  sync_to_spond: false
})

// --- Audience controls -------------------------------------------------
// The Spond-group binding drives subgroup filtering. Default to the
// header-selected group; admin can override per-event.
interface GroupOption {
  id: number
  spond_id: string
  name: string
  subgroups: { uid: string; name: string }[]
  member_count?: number
}
const groupOptions = ref<GroupOption[]>([])
const selectedGroupSpondId = ref<string | null>(authStore.selectedGroupId || null)

// inherit/subgroup/members — mirrors TrainingShiftEditor semantics minus
// the "inherit" option (there's no session type to inherit from here).
type AudienceMode = 'all' | 'subgroup' | 'members'
const audienceMode = ref<AudienceMode>('all')
const invitedMemberIds = ref<string[]>([])    // Spond member ids (strings)
const invitedSubgroupUids = ref<string[]>([]) // Spond subgroup uids
const ownerIds = ref<string[]>([])

const activeGroup = computed<GroupOption | null>(() => {
  if (!selectedGroupSpondId.value) return null
  return groupOptions.value.find(g => g.spond_id === selectedGroupSpondId.value) ?? null
})
const subgroupOptions = computed(() => activeGroup.value?.subgroups ?? [])

const toggleSubgroup = (uid: string, checked: boolean) => {
  if (checked) {
    if (!invitedSubgroupUids.value.includes(uid)) {
      invitedSubgroupUids.value = [...invitedSubgroupUids.value, uid]
    }
  } else {
    invitedSubgroupUids.value = invitedSubgroupUids.value.filter(u => u !== uid)
  }
}

// --- Invite scheduling -------------------------------------------------
const inviteLeadDays = ref<number | null>(null)
const inviteSendTime = ref<string>('')  // 'HH:MM' or ''

const inviteScheduleSummary = computed(() => {
  const lead = inviteLeadDays.value
  const sendTime = (inviteSendTime.value || '').slice(0, 5)
  if (lead === null || lead === undefined || !sendTime) {
    return 'Sends immediately when synced to Spond'
  }
  if (!state.start_time) return `${lead} day(s) before, ${sendTime}`
  try {
    const dt = new Date(state.start_time)
    dt.setDate(dt.getDate() - lead)
    const y = dt.getFullYear()
    const m = String(dt.getMonth() + 1).padStart(2, '0')
    const d = String(dt.getDate()).padStart(2, '0')
    return `Sends on ${y}-${m}-${d} ${sendTime} (Europe/Oslo)`
  } catch {
    return `${lead} day(s) before, ${sendTime}`
  }
})

// --- Event type options ------------------------------------------------
const eventTypeOptions = [
  { value: 'EVENT', label: 'Event' },
  { value: 'RECURRING', label: 'Recurring' },
  { value: 'AVAILABILITY', label: 'Availability' }
]

// --- Lifecycle ---------------------------------------------------------
const loadGroups = async () => {
  try {
    const resp: any = await api.getGroups()
    const list: any[] = Array.isArray(resp) ? resp : (resp?.groups || [])
    const detailed = await Promise.all(
      list.map(g => api.getGroup(g.id).catch(() => null))
    )
    groupOptions.value = list
      .map((g, idx) => {
        const full: any = detailed[idx] ?? g
        return {
          id: g.id,
          spond_id: g.spond_id || full?.spond_id,
          name: g.name || full?.name,
          subgroups: (full?.subgroups || []).map((sg: any) => ({
            uid: sg.spond_id || sg.uid || sg.id,
            name: sg.name,
          })),
          member_count: g.member_count,
        } as GroupOption
      })
      .sort((a, b) => a.name.localeCompare(b.name))

    if (!selectedGroupSpondId.value && groupOptions.value.length > 0) {
      selectedGroupSpondId.value = groupOptions.value[0].spond_id
    }
  } catch (err) {
    console.warn('Could not load groups:', err)
  }
}

const onGroupChanged = () => {
  // Subgroup uids only make sense within their parent group.
  invitedSubgroupUids.value = []
  invitedMemberIds.value = []
}

onMounted(async () => {
  loadGroups()
})

// Set default date/time (tomorrow at 10:00). Run on mount so SSR/hydration
// don't differ.
onMounted(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(10, 0, 0, 0)

  const tomorrowEnd = new Date(tomorrow)
  tomorrowEnd.setHours(12, 0, 0, 0)

  state.start_time = tomorrow.toISOString().slice(0, 16)
  state.end_time = tomorrowEnd.toISOString().slice(0, 16)
})

async function onSubmit(event: FormSubmitEvent<Schema>) {
  // Validate audience before kicking off the API call.
  if (audienceMode.value === 'subgroup' && invitedSubgroupUids.value.length === 0) {
    toast.add({
      title: 'Pick at least one subgroup',
      description: 'Subgroup audience requires at least one selection. Switch to "Whole group" instead to invite everyone.',
      color: 'amber',
    })
    return
  }
  if (audienceMode.value === 'members' && invitedMemberIds.value.length === 0) {
    toast.add({
      title: 'Pick at least one member',
      description: 'Specific-members audience requires at least one selection. Switch to "Whole group" to invite everyone.',
      color: 'amber',
    })
    return
  }

  loading.value = true

  try {
    const sendTimeRaw = (inviteSendTime.value || '').trim()
    const payload: any = {
      ...event.data,
      start_time: new Date(event.data.start_time).toISOString(),
      end_time: new Date(event.data.end_time).toISOString(),
      group_id: selectedGroupSpondId.value || undefined,
      invite_lead_days:
        inviteLeadDays.value !== null && inviteLeadDays.value !== undefined && Number.isFinite(Number(inviteLeadDays.value))
          ? Number(inviteLeadDays.value)
          : null,
      invite_send_time: sendTimeRaw
        ? (sendTimeRaw.length === 5 ? `${sendTimeRaw}:00` : sendTimeRaw)
        : null,
    }

    if (audienceMode.value === 'subgroup') {
      payload.invited_subgroup_uids = [...invitedSubgroupUids.value]
      payload.invited_member_ids = null
    } else if (audienceMode.value === 'members') {
      payload.invited_member_ids = [...invitedMemberIds.value]
      payload.invited_subgroup_uids = null
    } else {
      payload.invited_subgroup_uids = null
      payload.invited_member_ids = null
    }

    if (ownerIds.value.length > 0) {
      payload.owner_ids = ownerIds.value
    }

    const response = await api.createEvent(payload)

    toast.add({
      title: 'Event created',
      description: event.data.sync_to_spond
        ? 'Event created and synced to Spond'
        : 'Event created locally',
      color: 'green'
    })

    router.push(`/dashboard/events/${response.id}`)
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.data?.detail || 'Failed to create event',
      color: 'red'
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
        <NuxtLink to="/dashboard/events" class="hover:text-gray-700 dark:hover:text-gray-200">
          Events
        </NuxtLink>
        <UIcon name="i-heroicons-chevron-right" class="w-4 h-4" />
        <span>Create Event</span>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Create New Event
      </h1>
    </div>

    <!-- Form -->
    <UCard>
      <UForm :schema="schema" :state="state" @submit="onSubmit" class="space-y-6">
        <!-- Basic Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Basic Information
          </h3>

          <UFormField label="Event Title" name="heading" required>
            <UInput
              v-model="state.heading"
              placeholder="e.g. Training Session"
              :disabled="loading"
            />
          </UFormField>

          <UFormField label="Description" name="description">
            <UTextarea
              v-model="state.description"
              placeholder="Event description..."
              :rows="3"
              :disabled="loading"
            />
          </UFormField>

          <UFormField label="Event Type" name="event_type" required>
            <USelectMenu
              v-model="state.event_type"
              :options="eventTypeOptions"
              value-attribute="value"
              option-attribute="label"
              :disabled="loading"
            />
          </UFormField>
        </div>

        <!-- Date and Time -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Date & Time
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <UFormField label="Start Time" name="start_time" required>
              <UInput
                v-model="state.start_time"
                type="datetime-local"
                :disabled="loading"
              />
            </UFormField>

            <UFormField label="End Time" name="end_time" required>
              <UInput
                v-model="state.end_time"
                type="datetime-local"
                :disabled="loading"
              />
            </UFormField>
          </div>
        </div>

        <!-- Location -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Location
          </h3>

          <UFormField label="Address" name="location_address">
            <UInput
              v-model="state.location_address"
              placeholder="e.g. Main Stadium, 123 Street"
              :disabled="loading"
            />
          </UFormField>
        </div>

        <!-- Audience -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Audience
          </h3>

          <UFormField label="Spond group" name="group_id">
            <select
              v-model="selectedGroupSpondId"
              class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
              :disabled="loading"
              @change="onGroupChanged"
            >
              <option :value="null">— pick a group —</option>
              <option v-for="g in groupOptions" :key="g.id" :value="g.spond_id">
                {{ g.name }}
              </option>
            </select>
          </UFormField>

          <div v-if="selectedGroupSpondId">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Who is invited?
            </label>
            <div class="flex flex-wrap gap-3 text-sm">
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  v-model="audienceMode"
                  value="all"
                  :disabled="loading"
                />
                <span>Whole group</span>
              </label>
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  v-model="audienceMode"
                  value="subgroup"
                  :disabled="loading || subgroupOptions.length === 0"
                />
                <span :class="subgroupOptions.length === 0 ? 'text-gray-400' : ''">
                  Specific subgroups
                </span>
              </label>
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  v-model="audienceMode"
                  value="members"
                  :disabled="loading"
                />
                <span>Specific members</span>
              </label>
            </div>
          </div>

          <!-- Subgroup checkbox grid -->
          <div v-if="audienceMode === 'subgroup' && selectedGroupSpondId">
            <div
              v-if="subgroupOptions.length === 0"
              class="text-xs text-gray-500 italic"
            >
              This group has no subgroups.
            </div>
            <div
              v-else
              class="grid grid-cols-2 gap-x-4 gap-y-1.5 max-h-44 overflow-y-auto rounded-md border border-gray-200 dark:border-gray-700 p-2"
            >
              <label
                v-for="sg in subgroupOptions"
                :key="sg.uid"
                class="inline-flex items-center gap-1.5 text-sm cursor-pointer"
              >
                <input
                  type="checkbox"
                  :value="sg.uid"
                  :checked="invitedSubgroupUids.includes(sg.uid)"
                  class="rounded border-gray-300 dark:border-gray-600"
                  :disabled="loading"
                  @change="toggleSubgroup(sg.uid, ($event.target as HTMLInputElement).checked)"
                />
                <span>{{ sg.name }}</span>
              </label>
            </div>
            <p class="mt-2 text-xs text-gray-500">
              Members of any checked subgroup will be invited.
            </p>
          </div>

          <!-- Member picker -->
          <UFormField
            v-if="audienceMode === 'members' && selectedGroupSpondId"
            label="Invited members"
            name="invited_member_ids"
          >
            <MemberSelect
              v-model="invitedMemberIds"
              :group-id="selectedGroupSpondId"
              placeholder="Select members to invite..."
              :disabled="loading"
            />
          </UFormField>

          <UFormField label="Responsible persons" name="owner_ids">
            <MemberSelect
              v-model="ownerIds"
              :group-id="selectedGroupSpondId || undefined"
              :use-profile-id="true"
              placeholder="Select responsible persons..."
              :disabled="loading || !selectedGroupSpondId"
            />
            <template #help>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Select members who will be responsible for this event.
              </p>
            </template>
          </UFormField>
        </div>

        <!-- Invite scheduling -->
        <div class="space-y-3">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Send invitation
          </h3>
          <p class="text-xs text-gray-500 dark:text-gray-400 -mt-2">
            Leave blank to send immediately when synced to Spond.
          </p>
          <div class="flex flex-wrap items-center gap-2 text-sm">
            <UInput
              v-model.number="inviteLeadDays"
              type="number"
              min="0"
              max="365"
              placeholder="—"
              class="w-24"
              :ui="{ base: 'w-24' }"
              :disabled="loading"
            />
            <span class="text-gray-600 dark:text-gray-400">days before, at</span>
            <UInput type="time" class="w-full" v-model="inviteSendTime" :disabled="loading" />
            <span class="text-gray-500 text-xs">(Europe/Oslo)</span>
          </div>
          <p class="text-xs text-gray-500">{{ inviteScheduleSummary }}</p>
        </div>

        <!-- Settings -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Settings
          </h3>

          <UFormField label="Maximum Participants" name="max_accepted">
            <UInput
              v-model.number="state.max_accepted"
              type="number"
              min="0"
              placeholder="0 = unlimited"
              :disabled="loading"
            />
          </UFormField>

          <UFormField name="cancelled">
            <UCheckbox
              v-model="state.cancelled"
              label="Mark as cancelled"
              :disabled="loading"
            />
          </UFormField>

          <UFormField name="hidden">
            <UCheckbox
              v-model="state.hidden"
              label="Hide event"
              :disabled="loading"
            />
          </UFormField>

          <UFormField name="sync_to_spond">
            <UCheckbox
              v-model="state.sync_to_spond"
              label="Sync to Spond immediately"
              :disabled="loading"
            />
            <template #help>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                If unchecked, event will be created locally only. You can sync it to Spond later.
              </p>
            </template>
          </UFormField>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-4">
          <UButton
            type="submit"
            color="primary"
            :loading="loading"
            :disabled="loading"
          >
            <UIcon name="i-heroicons-plus" class="w-4 h-4 mr-2" />
            Create Event
          </UButton>

          <UButton
            color="neutral"
            variant="outline"
            :to="'/dashboard/events'"
            :disabled="loading"
          >
            Cancel
          </UButton>
        </div>
      </UForm>
    </UCard>
  </div>
</template>
