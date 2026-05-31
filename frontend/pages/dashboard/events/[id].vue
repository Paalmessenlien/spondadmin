<template>
  <div class="space-y-6">
        <!-- Breadcrumb -->
        <Breadcrumb
          :items="[
            { label: 'Dashboard', to: '/dashboard' },
            { label: 'Events', to: '/dashboard/events' },
            { label: event?.heading || 'Event Details' }
          ]"
        />

        <!-- Banner when this event originated from a training shift.
             linked_shift_id is computed at query time on the backend, so
             this banner appears automatically once the synced event lands. -->
        <div
          v-if="event && event.linked_shift_id"
          class="rounded-md bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-4 py-3 flex items-start gap-3"
        >
          <UIcon name="i-heroicons-academic-cap" class="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
          <div class="flex-1 text-sm">
            <p class="text-amber-800 dark:text-amber-300 font-medium">
              Published from a training shift
            </p>
            <p class="text-amber-700 dark:text-amber-400 mt-0.5">
              This event was created via the training-plan publish flow.
              <NuxtLink
                :to="`/dashboard/training?shift=${event.linked_shift_id}`"
                class="underline hover:no-underline"
              >
                Open in the training calendar →
              </NuxtLink>
            </p>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center py-12">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
        </div>

        <!-- Error State -->
        <UCard v-else-if="error">
          <div class="text-center py-8">
            <UIcon name="i-heroicons-exclamation-triangle" class="h-12 w-12 mx-auto text-red-500 mb-4" />
            <h3 class="text-lg font-semibold text-red-600 mb-2">Error Loading Event</h3>
            <p class="text-gray-600 dark:text-gray-400">{{ error }}</p>
          </div>
        </UCard>

        <!-- Event Details -->
        <template v-else-if="event">
          <!-- Header Card -->
          <UCard>
            <div class="space-y-4">
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    {{ event.heading }}
                  </h1>
                  <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                    <div class="flex items-center space-x-1">
                      <UIcon name="i-heroicons-calendar" />
                      <span>{{ formatDate(event.start_time) }}</span>
                    </div>
                    <div class="flex items-center space-x-1">
                      <UIcon name="i-heroicons-clock" />
                      <span>{{ formatTime(event.start_time) }} - {{ formatTime(event.end_time) }}</span>
                    </div>
                    <UBadge :color="getEventTypeColor(event.event_type)">
                      {{ event.event_type || 'Event' }}
                    </UBadge>
                    <CategoryBadge v-if="event.category_id" :category-id="event.category_id" size="sm" />
                    <SyncStatusBadge :status="event.sync_status" :error="event.sync_error" />
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-2">
                  <!-- Push to Spond - works for local_only, pending, or error status events -->
                  <UButton
                    v-if="event.sync_status === 'local_only' || event.sync_status === 'pending' || event.sync_status === 'error'"
                    icon="i-heroicons-arrow-up-tray"
                    color="primary"
                    :loading="pushing"
                    @click="handlePushToSpond"
                  >
                    {{ event.sync_status === 'local_only' ? 'Push to Spond' : 'Sync to Spond' }}
                  </UButton>
                  <UButton
                    icon="i-heroicons-pencil-square"
                    color="neutral"
                    variant="outline"
                    @click="openEditModal"
                  >
                    Edit
                  </UButton>
                </div>
              </div>

              <!-- Description -->
              <div v-if="event.description" class="prose dark:prose-invert max-w-none">
                <p class="text-gray-700 dark:text-gray-300">{{ event.description }}</p>
              </div>

              <!-- Location -->
              <div v-if="event.location_address || event.location" class="flex items-start space-x-2">
                <UIcon name="i-heroicons-map-pin" class="mt-1 text-gray-500" />
                <div>
                  <div class="font-semibold">Location</div>
                  <div class="text-sm text-gray-600 dark:text-gray-400">
                    {{ event.location_address || event.location?.feature || event.location?.address }}
                  </div>
                </div>
              </div>

              <!-- Max Participants -->
              <div v-if="event.max_accepted > 0" class="flex items-start space-x-2">
                <UIcon name="i-heroicons-users" class="mt-1 text-gray-500" />
                <div>
                  <div class="font-semibold">Maximum Participants</div>
                  <div class="text-sm text-gray-600 dark:text-gray-400">
                    {{ event.max_accepted }} people
                  </div>
                </div>
              </div>

              <!-- Status Badges -->
              <div class="flex items-center gap-2">
                <UBadge v-if="event.cancelled" color="red">Cancelled</UBadge>
                <UBadge v-if="event.hidden" color="orange">Hidden</UBadge>
              </div>
            </div>
          </UCard>

          <!-- Statistics Cards -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600">{{ responseStats.accepted }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Accepted</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-red-600">{{ responseStats.declined }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Declined</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-gray-600">{{ responseStats.unanswered }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Unanswered</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-blue-600">{{ responseStats.total }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Total Invited</div>
              </div>
            </UCard>
          </div>

          <!-- Attendees List -->
          <UCard>
            <template #header>
              <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                <h2 class="text-xl font-bold">Attendees</h2>
                <UInput
                  v-model="searchQuery"
                  placeholder="Search attendees..."
                  icon="i-heroicons-magnifying-glass"
                  class="w-full sm:w-64"
                />
              </div>
            </template>

            <!-- Tabs for response types -->
            <UTabs
              :items="tabs"
              v-model="selectedTab"
            >
              <template #content="{ item }">
                <div class="space-y-2 mt-4">
                  <div v-if="filteredAttendees(item.value).length === 0" class="text-center py-8 text-gray-500">
                    No attendees in this category
                  </div>

                  <div
                    v-for="attendee in filteredAttendees(item.value)"
                    :key="attendee.profile?.id"
                    class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div class="flex items-center space-x-3">
                      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold">
                        {{ getInitials(attendee.profile) }}
                      </div>
                      <div>
                        <NuxtLink
                          v-if="attendee.profile?.member_id"
                          :to="`/dashboard/members/${attendee.profile.member_id}`"
                          class="font-medium text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                          title="View member profile"
                        >
                          {{ attendee.profile?.firstName }} {{ attendee.profile?.lastName }}
                          <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-3.5 h-3.5 opacity-70" />
                        </NuxtLink>
                        <div v-else class="font-medium">
                          {{ attendee.profile?.firstName }} {{ attendee.profile?.lastName }}
                        </div>
                        <div v-if="attendee.profile?.email" class="text-sm text-gray-600 dark:text-gray-400">
                          {{ attendee.profile.email }}
                        </div>
                      </div>
                    </div>
                    <UBadge :color="getResponseColor(attendee.answer)">
                      {{ formatAnswer(attendee.answer) }}
                    </UBadge>
                  </div>
                </div>
              </template>
            </UTabs>
          </UCard>
        </template>

        <!-- Edit Modal — opens only via the Edit button. The default
             detail page is read-only. -->
        <UModal v-model:open="isEditModalOpen" :ui="{ content: 'max-w-2xl' }">
          <template #content>
          <div class="p-6">
            <div class="flex justify-between items-center mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold">Edit Event</h3>
              <UButton
                color="neutral"
                variant="ghost"
                icon="i-heroicons-x-mark"
                @click="isEditModalOpen = false"
              />
            </div>

            <UForm :schema="editSchema" :state="editState" @submit="handleEditSubmit" class="space-y-4">
              <!-- Basic Information -->
              <UFormField label="Event Title" name="heading" required>
                <UInput
                  v-model="editState.heading"
                  placeholder="e.g. Training Session"
                  :disabled="editLoading"
                />
              </UFormField>

              <UFormField label="Description" name="description">
                <UTextarea
                  v-model="editState.description"
                  placeholder="Event description..."
                  :rows="3"
                  :disabled="editLoading"
                />
              </UFormField>

              <!-- Date and Time -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UFormField label="Start Time" name="start_time" required>
                  <UInput
                    v-model="editState.start_time"
                    type="datetime-local"
                    :disabled="editLoading"
                  />
                </UFormField>

                <UFormField label="End Time" name="end_time" required>
                  <UInput
                    v-model="editState.end_time"
                    type="datetime-local"
                    :disabled="editLoading"
                  />
                </UFormField>
              </div>

              <!-- Location -->
              <UFormField label="Address" name="location_address">
                <UInput
                  v-model="editState.location_address"
                  placeholder="e.g. Main Stadium, 123 Street"
                  :disabled="editLoading"
                />
              </UFormField>

              <!-- Settings -->
              <UFormField label="Maximum Participants" name="max_accepted">
                <UInput
                  v-model.number="editState.max_accepted"
                  type="number"
                  min="0"
                  placeholder="0 = unlimited"
                  :disabled="editLoading"
                />
              </UFormField>

              <UFormField name="cancelled">
                <UCheckbox
                  v-model="editState.cancelled"
                  label="Mark as cancelled"
                  :disabled="editLoading"
                />
              </UFormField>

              <UFormField name="hidden">
                <UCheckbox
                  v-model="editState.hidden"
                  label="Hide event"
                  :disabled="editLoading"
                />
              </UFormField>

              <!-- Audience (only when event has a group) -->
              <div v-if="eventGroupId" class="space-y-3 border-t pt-4">
                <h4 class="font-semibold text-gray-900 dark:text-white">
                  Audience
                </h4>

                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Who is invited?
                  </label>
                  <div class="flex flex-wrap gap-3 text-sm">
                    <label class="inline-flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        v-model="editAudienceMode"
                        value="all"
                        :disabled="editLoading"
                      />
                      <span>Whole group</span>
                    </label>
                    <label class="inline-flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        v-model="editAudienceMode"
                        value="subgroup"
                        :disabled="editLoading || editSubgroupOptions.length === 0"
                      />
                      <span :class="editSubgroupOptions.length === 0 ? 'text-gray-400' : ''">
                        Specific subgroups
                      </span>
                    </label>
                    <label class="inline-flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        v-model="editAudienceMode"
                        value="members"
                        :disabled="editLoading"
                      />
                      <span>Specific members</span>
                    </label>
                  </div>
                </div>

                <div v-if="editAudienceMode === 'subgroup'">
                  <div
                    v-if="editSubgroupOptions.length === 0"
                    class="text-xs text-gray-500 italic"
                  >
                    This group has no subgroups.
                  </div>
                  <div
                    v-else
                    class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 max-h-44 overflow-y-auto rounded-md border border-gray-200 dark:border-gray-700 p-2"
                  >
                    <label
                      v-for="sg in editSubgroupOptions"
                      :key="sg.uid"
                      class="inline-flex items-center gap-1.5 text-sm cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        :value="sg.uid"
                        :checked="editInvitedSubgroupUids.includes(sg.uid)"
                        class="rounded border-gray-300 dark:border-gray-600"
                        :disabled="editLoading"
                        @change="toggleEditSubgroup(sg.uid, ($event.target as HTMLInputElement).checked)"
                      />
                      <span>{{ sg.name }}</span>
                    </label>
                  </div>
                </div>

                <UFormField
                  v-if="editAudienceMode === 'members'"
                  label="Invited members"
                  name="invited_member_ids"
                >
                  <MemberSelect
                    v-model="editInvitedMemberIds"
                    :group-id="eventGroupId"
                    placeholder="Select members to invite..."
                    :disabled="editLoading"
                  />
                </UFormField>

                <UFormField label="Responsible persons" name="owner_ids">
                  <MemberSelect
                    v-model="editOwnerIds"
                    :group-id="eventGroupId"
                    :use-profile-id="true"
                    placeholder="Select responsible persons..."
                    :disabled="editLoading"
                  />
                </UFormField>
              </div>

              <!-- Invite scheduling -->
              <div class="space-y-2 border-t pt-4">
                <h4 class="font-semibold text-gray-900 dark:text-white">
                  Send invitation
                </h4>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Leave blank to send immediately on push to Spond.
                </p>
                <div class="flex flex-wrap items-center gap-2 text-sm">
                  <UInput
                    v-model.number="editInviteLeadDays"
                    type="number"
                    min="0"
                    max="365"
                    placeholder="—"
                    class="w-24"
                    :ui="{ base: 'w-24' }"
                    :disabled="editLoading"
                  />
                  <span class="text-gray-600 dark:text-gray-400">days before, at</span>
                  <UInput type="time" class="w-full" v-model="editInviteSendTime" :disabled="editLoading" />
                  <span class="text-gray-500 text-xs">(Europe/Oslo)</span>
                </div>
                <p class="text-xs text-gray-500">{{ editInviteScheduleSummary }}</p>
              </div>

              <UFormField name="sync_to_spond">
                <UCheckbox
                  v-model="editState.sync_to_spond"
                  label="Sync changes to Spond immediately"
                  :disabled="editLoading"
                />
                <template #help>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    If unchecked, changes will be saved locally. You can sync them to Spond later.
                    <span v-if="eventGroupId" class="block mt-1 text-amber-600 dark:text-amber-400">
                      Note: Attendee and owner changes are only synced when this is checked.
                    </span>
                  </p>
                </template>
              </UFormField>

              <!-- Actions -->
              <div class="flex justify-end gap-3 pt-4">
                <UButton
                  color="neutral"
                  variant="outline"
                  :disabled="editLoading"
                  @click="isEditModalOpen = false"
                >
                  Cancel
                </UButton>
                <UButton
                  type="submit"
                  color="primary"
                  :loading="editLoading"
                  :disabled="editLoading"
                >
                  Save Changes
                </UButton>
              </div>
            </UForm>
          </div>
          </template>
        </UModal>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '#ui/types'

definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const route = useRoute()
const api = useApi()
const toast = useToast()

const eventId = computed(() => parseInt(route.params.id as string))

const event = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const searchQuery = ref('')
const selectedTab = ref(0)
const pushing = ref(false)
const isEditModalOpen = ref(false)
const editLoading = ref(false)

// Edit form schema
const editSchema = z.object({
  heading: z.string().min(3, 'Heading must be at least 3 characters').optional(),
  description: z.string().optional(),
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  location_address: z.string().optional(),
  max_accepted: z.number().min(0).optional(),
  cancelled: z.boolean().optional(),
  hidden: z.boolean().optional(),
  sync_to_spond: z.boolean().optional()
})

type EditSchema = z.output<typeof editSchema>

// Edit form state
const editState = reactive<EditSchema>({
  heading: '',
  description: '',
  start_time: '',
  end_time: '',
  location_address: '',
  max_accepted: 0,
  cancelled: false,
  hidden: false,
  sync_to_spond: false
})

// --- Audience controls for the edit modal ------------------------------
interface GroupOption {
  id: number
  spond_id: string
  name: string
  subgroups: { uid: string; name: string }[]
}
const groupOptions = ref<GroupOption[]>([])
type EditAudienceMode = 'all' | 'subgroup' | 'members'
const editAudienceMode = ref<EditAudienceMode>('all')
const editInvitedMemberIds = ref<string[]>([])
const editInvitedSubgroupUids = ref<string[]>([])
const editOwnerIds = ref<string[]>([])
const editInviteLeadDays = ref<number | null>(null)
const editInviteSendTime = ref<string>('')

// Get group_id from event (prefer direct group_id, fallback to raw_data)
const eventGroupId = computed(() => {
  // First try the direct group_id field
  if (event.value?.group_id) return event.value.group_id
  // Fallback to raw_data.recipients.group.id for backward compatibility
  if (event.value?.raw_data?.recipients?.group?.id) return event.value.raw_data.recipients.group.id
  return null
})

const editActiveGroup = computed<GroupOption | null>(() => {
  if (!eventGroupId.value) return null
  return groupOptions.value.find(g => g.spond_id === eventGroupId.value) ?? null
})
const editSubgroupOptions = computed(() => editActiveGroup.value?.subgroups ?? [])

const toggleEditSubgroup = (uid: string, checked: boolean) => {
  if (checked) {
    if (!editInvitedSubgroupUids.value.includes(uid)) {
      editInvitedSubgroupUids.value = [...editInvitedSubgroupUids.value, uid]
    }
  } else {
    editInvitedSubgroupUids.value = editInvitedSubgroupUids.value.filter(u => u !== uid)
  }
}

const editInviteScheduleSummary = computed(() => {
  const lead = editInviteLeadDays.value
  const sendTime = (editInviteSendTime.value || '').slice(0, 5)
  if (lead === null || lead === undefined || !sendTime) {
    return 'Sends immediately when pushed to Spond'
  }
  if (!editState.start_time) return `${lead} day(s) before, ${sendTime}`
  try {
    const dt = new Date(editState.start_time)
    dt.setDate(dt.getDate() - lead)
    const y = dt.getFullYear()
    const m = String(dt.getMonth() + 1).padStart(2, '0')
    const d = String(dt.getDate()).padStart(2, '0')
    return `Sends on ${y}-${m}-${d} ${sendTime} (Europe/Oslo)`
  } catch {
    return `${lead} day(s) before, ${sendTime}`
  }
})

const loadEditGroups = async () => {
  try {
    const resp: any = await api.getGroups()
    const list: any[] = Array.isArray(resp) ? resp : (resp?.groups || [])
    const detailed = await Promise.all(
      list.map(g => api.getGroup(g.id).catch(() => null))
    )
    groupOptions.value = list.map((g, idx) => {
      const full: any = detailed[idx] ?? g
      return {
        id: g.id,
        spond_id: g.spond_id || full?.spond_id,
        name: g.name || full?.name,
        subgroups: (full?.subgroups || []).map((sg: any) => ({
          uid: sg.spond_id || sg.uid || sg.id,
          name: sg.name,
        })),
      } as GroupOption
    })
  } catch (err) {
    console.warn('Could not load groups for edit:', err)
  }
}

const tabs = [
  { label: 'All', value: 'all' },
  { label: 'Accepted', value: 'accepted' },
  { label: 'Declined', value: 'declined' },
  { label: 'Unanswered', value: 'unanswered' }
]

onMounted(async () => {
  await Promise.all([loadEvent(), loadEditGroups()])
})

const loadEvent = async () => {
  loading.value = true
  error.value = null
  try {
    event.value = await api.getEvent(eventId.value)
  } catch (err: any) {
    console.error('Failed to load event:', err)
    error.value = err?.data?.detail || 'Failed to load event details'
    toast.add({ title: 'Error', description: error.value, color: 'red' })
  } finally {
    loading.value = false
  }
}

const openEditModal = () => {
  // Populate edit form with current event data
  editState.heading = event.value.heading
  editState.description = event.value.description || ''
  editState.start_time = event.value.start_time ? new Date(event.value.start_time).toISOString().slice(0, 16) : ''
  editState.end_time = event.value.end_time ? new Date(event.value.end_time).toISOString().slice(0, 16) : ''
  editState.location_address = event.value.location_address || ''
  editState.max_accepted = event.value.max_accepted || 0
  editState.cancelled = event.value.cancelled || false
  editState.hidden = event.value.hidden || false
  editState.sync_to_spond = false

  // Hydrate the audience controls. Precedence:
  //   • stored invited_subgroup_uids → "subgroup" mode
  //   • else stored/raw_data invited_member_ids → "members" mode
  //   • else "all" (whole group)
  const rawData = event.value.raw_data
  const storedSubgroupUids: string[] | null = event.value.invited_subgroup_uids ?? null
  const storedMemberIds: string[] | null = rawData?.recipients?.groupMembers ?? null

  if (storedSubgroupUids && storedSubgroupUids.length > 0) {
    editAudienceMode.value = 'subgroup'
    editInvitedSubgroupUids.value = [...storedSubgroupUids]
    editInvitedMemberIds.value = []
  } else if (storedMemberIds && storedMemberIds.length > 0) {
    editAudienceMode.value = 'members'
    editInvitedSubgroupUids.value = []
    editInvitedMemberIds.value = [...storedMemberIds]
  } else {
    editAudienceMode.value = 'all'
    editInvitedSubgroupUids.value = []
    editInvitedMemberIds.value = []
  }

  // Owners from raw_data
  if (rawData?.owners && Array.isArray(rawData.owners)) {
    editOwnerIds.value = rawData.owners.map((o: any) => o.id).filter((id: any) => id)
  } else {
    editOwnerIds.value = []
  }

  // Invite scheduling fields from the event row
  editInviteLeadDays.value = event.value.invite_lead_days ?? null
  editInviteSendTime.value = (event.value.invite_send_time || '').slice(0, 5) || ''

  isEditModalOpen.value = true
}

const handleEditSubmit = async (submitEvent: FormSubmitEvent<EditSchema>) => {
  // Audience validation up-front (parallel to create.vue).
  if (editAudienceMode.value === 'subgroup' && editInvitedSubgroupUids.value.length === 0) {
    toast.add({
      title: 'Pick at least one subgroup',
      description: 'Subgroup audience requires at least one selection. Switch to "Whole group" to invite everyone.',
      color: 'amber',
    })
    return
  }
  if (editAudienceMode.value === 'members' && editInvitedMemberIds.value.length === 0) {
    toast.add({
      title: 'Pick at least one member',
      description: 'Specific-members audience requires at least one selection. Switch to "Whole group" to invite everyone.',
      color: 'amber',
    })
    return
  }

  editLoading.value = true
  try {
    // Prepare update data
    const updateData: any = {}

    if (submitEvent.data.heading) updateData.heading = submitEvent.data.heading
    if (submitEvent.data.description !== undefined) updateData.description = submitEvent.data.description
    if (submitEvent.data.start_time) updateData.start_time = new Date(submitEvent.data.start_time).toISOString()
    if (submitEvent.data.end_time) updateData.end_time = new Date(submitEvent.data.end_time).toISOString()
    if (submitEvent.data.location_address !== undefined) updateData.location_address = submitEvent.data.location_address
    if (submitEvent.data.max_accepted !== undefined) updateData.max_accepted = submitEvent.data.max_accepted
    if (submitEvent.data.cancelled !== undefined) updateData.cancelled = submitEvent.data.cancelled
    if (submitEvent.data.hidden !== undefined) updateData.hidden = submitEvent.data.hidden
    if (submitEvent.data.sync_to_spond !== undefined) updateData.sync_to_spond = submitEvent.data.sync_to_spond

    // Audience — always send so explicit clears (e.g. removing all subgroups
    // by switching to "whole group") propagate to the DB.
    if (editAudienceMode.value === 'subgroup') {
      updateData.invited_subgroup_uids = [...editInvitedSubgroupUids.value]
      updateData.invited_member_ids = null
    } else if (editAudienceMode.value === 'members') {
      updateData.invited_subgroup_uids = null
      updateData.invited_member_ids = [...editInvitedMemberIds.value]
    } else {
      updateData.invited_subgroup_uids = null
      updateData.invited_member_ids = null
    }

    if (submitEvent.data.sync_to_spond && editOwnerIds.value.length > 0) {
      updateData.owner_ids = editOwnerIds.value
    }

    // Invite scheduling — always send so blanking the inputs clears the
    // stored intent.
    const sendTimeRaw = (editInviteSendTime.value || '').trim()
    updateData.invite_lead_days =
      editInviteLeadDays.value !== null && editInviteLeadDays.value !== undefined && Number.isFinite(Number(editInviteLeadDays.value))
        ? Number(editInviteLeadDays.value)
        : null
    updateData.invite_send_time = sendTimeRaw
      ? (sendTimeRaw.length === 5 ? `${sendTimeRaw}:00` : sendTimeRaw)
      : null

    await api.updateEvent(Number(eventId.value), updateData)

    toast.add({
      title: 'Success',
      description: submitEvent.data.sync_to_spond
        ? 'Event updated and synced to Spond'
        : 'Event updated locally',
      color: 'green'
    })

    isEditModalOpen.value = false
    await loadEvent()
  } catch (err: any) {
    toast.add({
      title: 'Error',
      description: err.data?.detail || 'Failed to update event',
      color: 'red'
    })
  } finally {
    editLoading.value = false
  }
}

const handlePushToSpond = async () => {
  pushing.value = true
  try {
    await api.pushEventToSpond(Number(eventId.value))

    toast.add({
      title: 'Success',
      description: 'Event pushed to Spond successfully',
      color: 'green'
    })

    await loadEvent()
  } catch (err: any) {
    toast.add({
      title: 'Error',
      description: err.data?.detail || 'Failed to push event to Spond',
      color: 'red'
    })
  } finally {
    pushing.value = false
  }
}

const responseStats = computed(() => {
  if (!event.value?.responses?.responses) {
    return { accepted: 0, declined: 0, unanswered: 0, total: 0 }
  }

  const responses = event.value.responses.responses
  return {
    accepted: responses.filter((r: any) => r.answer?.toLowerCase() === 'accepted').length,
    declined: responses.filter((r: any) => r.answer?.toLowerCase() === 'declined').length,
    unanswered: responses.filter((r: any) =>
      !r.answer || r.answer.toLowerCase() === 'unanswered'
    ).length,
    total: responses.length
  }
})

const filteredAttendees = (type: string) => {
  if (!event.value?.responses?.responses) return []

  let attendees = event.value.responses.responses

  // Filter by response type
  if (type !== 'all') {
    attendees = attendees.filter((r: any) => {
      const answer = r.answer?.toLowerCase() || 'unanswered'
      if (type === 'unanswered') {
        return !r.answer || answer === 'unanswered'
      }
      return answer === type
    })
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    attendees = attendees.filter((r: any) => {
      const name = `${r.profile?.firstName || ''} ${r.profile?.lastName || ''}`.toLowerCase()
      const email = r.profile?.email?.toLowerCase() || ''
      return name.includes(query) || email.includes(query)
    })
  }

  return attendees
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getInitials = (profile: any) => {
  if (!profile) return '?'
  const first = profile.firstName?.[0] || ''
  const last = profile.lastName?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const formatAnswer = (answer: string) => {
  if (!answer) return 'Unanswered'
  return answer.charAt(0).toUpperCase() + answer.slice(1).toLowerCase()
}

const getResponseColor = (answer: string) => {
  const ans = answer?.toLowerCase() || 'unanswered'
  if (ans === 'accepted') return 'green'
  if (ans === 'declined') return 'red'
  return 'gray'
}

const getEventTypeColor = (type: string) => {
  const typeMap: Record<string, string> = {
    'TRAINING': 'blue',
    'EVENT': 'purple',
    'MATCH': 'orange',
    'MEETING': 'cyan'
  }
  return typeMap[type?.toUpperCase()] || 'gray'
}
</script>
