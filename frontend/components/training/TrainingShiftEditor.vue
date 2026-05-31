<template>
  <UModal v-model:open="isOpen" :ui="{ content: 'max-w-xl' }">
    <template #content>
      <div class="p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ isEditing ? 'Edit shift' : 'New shift' }}
          </h2>
          <UBadge :color="statusColor" variant="subtle" size="sm">
            {{ form.status }}
          </UBadge>
        </div>

        <div v-if="form.spond_event_id" class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="flex items-center gap-1">
              <UIcon name="i-heroicons-check-badge" class="w-4 h-4 text-green-600" />
              Spond event id:
              <code class="font-mono text-[11px]">{{ form.spond_event_id }}</code>
            </span>
            <UButton
              v-if="props.shift?.linked_event_id"
              :to="`/dashboard/events/${props.shift.linked_event_id}`"
              size="xs"
              color="primary"
              variant="soft"
              icon="i-heroicons-arrow-top-right-on-square"
            >
              View Spond event
            </UButton>
          </div>
          <div v-if="reverseSyncedLabel" class="flex items-center gap-1 text-[11px] text-gray-400">
            <UIcon name="i-heroicons-arrow-path" class="w-3.5 h-3.5" />
            Updated from Spond {{ reverseSyncedLabel }}
          </div>
        </div>

        <form class="space-y-4" @submit.prevent="handleSave">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Session type</label>
            <select
              v-model="form.session_type_id"
              :disabled="isEditing"
              class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option :value="null" disabled>Select session type…</option>
              <option v-for="st in sessionTypes" :key="st.id" :value="st.id">
                {{ st.name }} ({{ formatTime(st.default_start_time) }}–{{ formatTime(st.default_end_time) }})
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date</label>
            <UInput type="date" class="w-full" v-model="form.date" :disabled="isEditing" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Leader
              <span v-if="form.raw_initials && !form.leader_member_id" class="ml-1 text-amber-600">
                (unresolved: {{ form.raw_initials }})
              </span>
              <span
                v-if="activeLeaderGroup"
                class="ml-1 text-xs font-normal text-gray-500"
              >
                — from <strong>{{ activeLeaderGroup.name }}</strong>
                ({{ activeLeaderGroup.members.length }} members)
              </span>
            </label>
            <!-- When a leader is already placed, show the pill on its own.
                 Click the X to clear → search input reappears. -->
            <div v-if="form.leader_member_id" class="flex items-center gap-2 text-sm">
              <NuxtLink
                :to="`/dashboard/members/${form.leader_member_id}`"
                class="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50"
                title="View member profile"
              >
                {{ selectedLeaderLabel }}
                <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-3.5 h-3.5 opacity-70" />
              </NuxtLink>
              <UButton
                size="xs"
                color="neutral"
                variant="ghost"
                icon="i-heroicons-x-mark"
                aria-label="Clear leader"
                @click="clearLeader"
              />
            </div>
            <div v-else class="relative">
              <UInput
                v-model="memberSearch"
                :placeholder="activeLeaderGroup ? 'Pick a leader from the pool…' : 'Search members…'"
                icon="i-heroicons-magnifying-glass"
                @input="debouncedSearch"
              />
              <div
                v-if="(memberSearch.trim() || activeLeaderGroup) && filteredMembers.length > 0"
                class="absolute z-10 mt-1 w-full max-h-64 overflow-y-auto rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg"
              >
                <button
                  v-for="member in filteredMembers"
                  :key="member.id"
                  type="button"
                  class="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                  @click="selectLeader(member)"
                >
                  {{ member.first_name }} {{ member.last_name }}
                </button>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start time</label>
              <UInput type="time" class="w-full" v-model="form.start_time_override" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End time</label>
              <UInput type="time" class="w-full" v-model="form.end_time_override" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
            <UTextarea v-model="form.notes" :rows="3" placeholder="Optional notes…" />
          </div>

          <!-- Audience: who gets invited when this shift is published. -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Invited
              </label>
              <span class="text-xs text-gray-500">{{ inheritedSummary }}</span>
            </div>

            <div class="flex flex-wrap gap-3 text-sm">
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="invite-mode"
                  value="inherit"
                  :checked="inviteMode === 'inherit'"
                  @change="onInviteModeChange('inherit')"
                />
                <span>Inherit</span>
              </label>
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="invite-mode"
                  value="subgroup"
                  :checked="inviteMode === 'subgroup'"
                  :disabled="subgroupOptionsForShift.length === 0"
                  @change="onInviteModeChange('subgroup')"
                />
                <span :class="subgroupOptionsForShift.length === 0 ? 'text-gray-400' : ''">
                  Subgroup
                </span>
              </label>
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="invite-mode"
                  value="members"
                  :checked="inviteMode === 'members'"
                  :disabled="!audienceGroup"
                  @change="onInviteModeChange('members')"
                />
                <span :class="!audienceGroup ? 'text-gray-400' : ''">
                  Specific members
                </span>
              </label>
            </div>

            <!-- Subgroup picker (multi-select) -->
            <div v-if="inviteMode === 'subgroup'" class="space-y-1.5">
              <div
                v-if="subgroupOptionsForShift.length === 0"
                class="text-xs text-gray-500 italic"
              >
                No subgroups available on this Spond group.
              </div>
              <div
                v-else
                class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 max-h-44 overflow-y-auto rounded-md border border-gray-200 dark:border-gray-700 p-2"
              >
                <label
                  v-for="sg in subgroupOptionsForShift"
                  :key="sg.uid"
                  class="inline-flex items-center gap-1.5 text-sm cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :value="sg.uid"
                    :checked="(form.invited_subgroup_uids ?? []).includes(sg.uid)"
                    class="rounded border-gray-300 dark:border-gray-600"
                    @change="toggleShiftSubgroup(sg.uid, ($event.target as HTMLInputElement).checked)"
                  />
                  <span>{{ sg.name }}</span>
                </label>
              </div>
              <p class="text-xs text-gray-500">
                Members of any checked subgroup will be invited.
              </p>
            </div>

            <!-- Member picker -->
            <div v-if="inviteMode === 'members'" class="space-y-2">
              <div v-if="invitedMembers.length > 0" class="flex flex-wrap gap-1.5">
                <span
                  v-for="m in invitedMembers"
                  :key="m.id"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs"
                >
                  {{ m.first_name }} {{ m.last_name }}
                  <button
                    type="button"
                    class="ml-1 text-blue-500 hover:text-blue-700"
                    aria-label="Remove invitee"
                    @click="removeInvitee(m.id)"
                  >
                    ×
                  </button>
                </span>
              </div>

              <div class="relative">
                <UInput
                  v-model="inviteeSearch"
                  placeholder="Add member…"
                  icon="i-heroicons-magnifying-glass"
                  @input="onInviteeSearchInput"
                />
                <div
                  v-if="inviteeSearch.trim() && inviteeResults.length > 0"
                  class="absolute z-10 mt-1 w-full max-h-56 overflow-y-auto rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg"
                >
                  <button
                    v-for="m in inviteeResults"
                    :key="m.id"
                    type="button"
                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                    @click="addInvitee(m)"
                  >
                    {{ m.first_name }} {{ m.last_name }}
                  </button>
                </div>
              </div>

              <p v-if="invitedMembers.length === 0" class="text-xs text-gray-500">
                Search and click members to add them. At least one is required to save in this mode.
              </p>
            </div>
          </div>

          <!-- Invite scheduling: when Spond should actually send out the invitation. -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Send invitation
              </label>
              <span class="text-xs text-gray-500">{{ inviteScheduleSummary }}</span>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-sm">
              <UInput
                v-model.number="form.invite_lead_days"
                type="number"
                min="0"
                max="365"
                :placeholder="inheritedLeadDaysPlaceholder"
                class="w-24"
                :ui="{ base: 'w-24' }"
              />
              <span class="text-gray-600 dark:text-gray-400">days before, at</span>
              <UInput type="time" class="w-full" v-model="form.invite_send_time" />
              <span class="text-gray-500 text-xs">(Europe/Oslo)</span>
              <UButton
                v-if="inviteScheduleDiffersFromDefault"
                size="xs"
                color="neutral"
                variant="ghost"
                @click="clearInviteSchedule"
              >
                Reset to session default
              </UButton>
            </div>
            <p class="text-xs text-gray-500">
              Leave blank to inherit from the session type, or to send immediately on publish.
            </p>
          </div>

          <div v-if="formError" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-3">
            {{ formError }}
          </div>

          <div class="flex flex-wrap justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <UButton color="neutral" variant="outline" @click="close">Cancel</UButton>

            <!-- Draft: Save, Delete (admin), Publish (admin) -->
            <template v-if="form.status === 'draft'">
              <UButton
                v-if="isEditing && isAdmin"
                color="red"
                variant="soft"
                icon="i-heroicons-trash"
                :loading="deleting"
                @click="handleDelete"
              >
                Delete
              </UButton>
              <UButton
                v-if="canEdit"
                type="submit"
                :loading="saving"
                icon="i-heroicons-check"
              >
                Save
              </UButton>
              <!--
                Manual, per-shift publish. Opens a confirm modal that summarizes
                the audience and send-at before any Spond call is made.
                There is intentionally no "publish many" / bulk button.
              -->
              <UButton
                v-if="isEditing && isAdmin"
                color="success"
                icon="i-heroicons-paper-airplane"
                :loading="publishing"
                @click="askPublish"
              >
                Publish to Spond
              </UButton>
            </template>

            <!-- Published: Save notes, Cancel shift (admin) -->
            <template v-else-if="form.status === 'published'">
              <UButton
                v-if="isAdmin"
                color="warning"
                variant="soft"
                icon="i-heroicons-x-circle"
                @click="askCancel"
              >
                Cancel shift
              </UButton>
              <UButton
                v-if="canEdit"
                type="submit"
                :loading="saving"
                icon="i-heroicons-check"
              >
                Save notes
              </UButton>
            </template>

            <!-- Cancelled: Save notes, Reactivate (admin) -->
            <template v-else-if="form.status === 'cancelled'">
              <UButton
                v-if="isAdmin"
                color="primary"
                variant="soft"
                icon="i-heroicons-arrow-uturn-left"
                @click="handleReactivate"
              >
                Reactivate
              </UButton>
              <UButton
                v-if="canEdit"
                type="submit"
                :loading="saving"
                icon="i-heroicons-check"
              >
                Save notes
              </UButton>
            </template>
          </div>
        </form>
      </div>
    </template>
  </UModal>

  <!-- Publish confirm -->
  <UModal v-model:open="publishConfirmOpen" :ui="{ content: 'max-w-lg' }">
    <template #content>
      <div class="p-6 space-y-4">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">Publish to Spond?</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          This will create a real Spond event in
          <strong>{{ publishSummary.group }}</strong>.
          Review carefully — there is no undo from this app.
        </p>

        <dl class="text-sm rounded-md bg-gray-50 dark:bg-gray-800 p-3 space-y-1.5">
          <div class="flex justify-between gap-3">
            <dt class="text-gray-500 dark:text-gray-400">Session</dt>
            <dd class="text-gray-900 dark:text-white text-right">{{ publishSummary.session }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-gray-500 dark:text-gray-400">Date</dt>
            <dd class="text-gray-900 dark:text-white text-right">{{ publishSummary.date }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-gray-500 dark:text-gray-400">Leader</dt>
            <dd class="text-gray-900 dark:text-white text-right">{{ publishSummary.leader }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-gray-500 dark:text-gray-400">Audience</dt>
            <dd class="text-gray-900 dark:text-white text-right">{{ publishSummary.audience }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-gray-500 dark:text-gray-400">Send</dt>
            <dd class="text-gray-900 dark:text-white text-right">{{ publishSummary.sendAt }}</dd>
          </div>
        </dl>

        <p
          v-if="hasUnsavedChanges"
          class="text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded p-2"
        >
          You have unsaved changes — Spond will use the last saved values, not what's shown in the editor. Save first if you want changes to take effect.
        </p>

        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="publishConfirmOpen = false">Cancel</UButton>
          <UButton color="success" :loading="publishing" icon="i-heroicons-paper-airplane" @click="handlePublish">
            Publish now
          </UButton>
        </div>
      </div>
    </template>
  </UModal>

  <!-- Cancel-shift confirm -->
  <UModal v-model:open="cancelConfirmOpen">
    <template #content>
      <div class="p-6 space-y-4">
        <h2 class="text-lg font-bold text-amber-600">Cancel this shift?</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          The shift status will be set to <strong>cancelled</strong>. The Spond event reference is kept for the record but no API call is made to Spond.
        </p>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="cancelConfirmOpen = false">Back</UButton>
          <UButton color="warning" :loading="cancelling" icon="i-heroicons-x-circle" @click="handleCancelShift">
            Cancel shift
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
interface SessionType {
  id: number
  name: string
  default_start_time: string
  default_end_time: string
  location: string | null
  group_id: number | null
  spond_subgroup_uids: string[] | null
  leader_group_id?: number | null
  invite_lead_days?: number | null
  invite_send_time?: string | null
  group?: { id: number; spond_id: string; name: string } | null
  leader_group?: { id: number; name: string } | null
}

interface LeaderSummary {
  id: number
  spond_id: string
  first_name: string
  last_name: string
}

interface ShiftLike {
  id?: number
  session_type_id: number | null
  session_type?: SessionType | null
  date: string
  leader_member_id: number | null
  leader?: LeaderSummary | null
  raw_initials?: string | null
  start_time_override?: string | null
  end_time_override?: string | null
  notes?: string | null
  invited_subgroup_uids?: string[] | null
  invited_member_ids?: number[] | null
  invite_lead_days?: number | null
  invite_send_time?: string | null
  status?: 'draft' | 'published' | 'cancelled'
  spond_event_id?: string | null
  linked_event_id?: number | null
  last_reverse_synced_at?: string | null
}

interface GroupSummary {
  id: number
  spond_id: string
  name: string
  subgroups: { uid: string; name: string }[]
}

interface InvitedMember {
  id: number
  first_name: string
  last_name: string
}

interface LeaderGroupOption {
  id: number
  name: string
  members: { id: number; first_name: string; last_name: string }[]
}

const props = withDefaults(
  defineProps<{
    open: boolean
    shift: ShiftLike | null
    sessionTypes: SessionType[]
    groups?: GroupSummary[]
    leaderGroups?: LeaderGroupOption[]
  }>(),
  { groups: () => [], leaderGroups: () => [] }
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'saved'): void
  (e: 'deleted'): void
}>()

const api = useApi()
const toast = useToast()
const { canEdit, isAdmin } = usePermissions()

const isOpen = computed({
  get: () => props.open,
  set: (v: boolean) => emit('update:open', v),
})

const isEditing = computed(() => !!(props.shift && props.shift.id))

const form = ref<ShiftLike & { status: 'draft' | 'published' | 'cancelled' }>({
  session_type_id: null,
  date: '',
  leader_member_id: null,
  raw_initials: null,
  start_time_override: null,
  end_time_override: null,
  notes: '',
  invited_subgroup_uids: null,
  invited_member_ids: null,
  invite_lead_days: null,
  invite_send_time: null,
  status: 'draft',
  spond_event_id: null,
})

// Audience mode for the per-shift invite override. Persisted to the backend
// as (invited_subgroup_uids, invited_member_ids); both null → 'inherit'.
const inviteMode = ref<'inherit' | 'subgroup' | 'members'>('inherit')
const invitedMembers = ref<InvitedMember[]>([])
const inviteeSearch = ref('')
const inviteeResults = ref<InvitedMember[]>([])

const saving = ref(false)
const deleting = ref(false)
const publishing = ref(false)
const cancelling = ref(false)
const formError = ref('')

const publishConfirmOpen = ref(false)
const cancelConfirmOpen = ref(false)

const memberSearch = ref('')
const members = ref<any[]>([])
const selectedLeaderLabel = ref('')

const statusColor = computed(() => {
  switch (form.value.status) {
    case 'published': return 'success'
    case 'cancelled': return 'neutral'
    default: return 'info'
  }
})

const selectedSessionTypeName = computed(() => {
  const st = props.sessionTypes.find(s => s.id === form.value.session_type_id)
  return st?.name || 'this session'
})

// Human-readable "updated from Spond" timestamp for the reverse-sync badge.
const reverseSyncedLabel = computed(() => {
  const ts = props.shift?.last_reverse_synced_at
  if (!ts) return ''
  const d = new Date(ts.endsWith('Z') ? ts : `${ts}Z`)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('nb-NO', { dateStyle: 'short', timeStyle: 'short' })
})

const normalizeTime = (t: string | null | undefined): string => (t ? t.slice(0, 5) : '')

const sessionTypeFor = (id: number | null | undefined) =>
  id == null ? null : props.sessionTypes.find(s => s.id === id) ?? null

watch(
  () => props.shift,
  (s) => {
    if (!s) {
      form.value = {
        session_type_id: null,
        date: '',
        leader_member_id: null,
        raw_initials: null,
        start_time_override: null,
        end_time_override: null,
        notes: '',
        status: 'draft',
        spond_event_id: null,
      }
      selectedLeaderLabel.value = ''
      memberSearch.value = ''
      formError.value = ''
      return
    }
    // Pre-fill the time inputs with the effective time (override if set,
    // otherwise the session type's default). On save we'll only persist the
    // override if it differs from the default.
    const st = sessionTypeFor(s.session_type_id)
    const effectiveStart =
      normalizeTime(s.start_time_override) || normalizeTime(st?.default_start_time)
    const effectiveEnd =
      normalizeTime(s.end_time_override) || normalizeTime(st?.default_end_time)
    form.value = {
      id: s.id,
      session_type_id: s.session_type_id,
      date: s.date,
      leader_member_id: s.leader_member_id,
      raw_initials: s.raw_initials ?? null,
      start_time_override: effectiveStart || null,
      end_time_override: effectiveEnd || null,
      notes: s.notes ?? '',
      invited_subgroup_uids: s.invited_subgroup_uids ? [...s.invited_subgroup_uids] : null,
      invited_member_ids: s.invited_member_ids ?? null,
      // Pre-fill the schedule fields with the *effective* values (shift
      // override if set, otherwise the session type's default) so the admin
      // can see what will be used. We only persist as an override on save if
      // the value differs from the session type's default.
      invite_lead_days:
        s.invite_lead_days != null ? s.invite_lead_days : (st?.invite_lead_days ?? null),
      invite_send_time:
        (s.invite_send_time || st?.invite_send_time || '').slice(0, 5) || null,
      status: s.status ?? 'draft',
      spond_event_id: s.spond_event_id ?? null,
    }
    if (s.leader) {
      selectedLeaderLabel.value = `${s.leader.first_name} ${s.leader.last_name}`
    } else {
      selectedLeaderLabel.value = ''
    }
    memberSearch.value = ''
    formError.value = ''

    // Hydrate the audience controls from the loaded shift.
    if (s.invited_member_ids && s.invited_member_ids.length > 0) {
      inviteMode.value = 'members'
      loadInvitedMembers(s.invited_member_ids)
    } else if (s.invited_subgroup_uids && s.invited_subgroup_uids.length > 0) {
      inviteMode.value = 'subgroup'
      invitedMembers.value = []
    } else {
      inviteMode.value = 'inherit'
      invitedMembers.value = []
    }
    inviteeSearch.value = ''
    inviteeResults.value = []
  },
  { immediate: true }
)

// When the session type changes (only possible for new shifts — the select is
// disabled in edit mode) snap the time fields back to that session type's
// defaults so the user sees the right times without having to type them.
watch(
  () => form.value.session_type_id,
  (newId, oldId) => {
    if (newId == null || newId === oldId) return
    if (isEditing.value) return
    const st = sessionTypeFor(newId)
    if (!st) return
    form.value.start_time_override = normalizeTime(st.default_start_time) || null
    form.value.end_time_override = normalizeTime(st.default_end_time) || null
    form.value.invite_lead_days = st.invite_lead_days ?? null
    form.value.invite_send_time = (st.invite_send_time || '').slice(0, 5) || null
  }
)

const activeLeaderGroup = computed<LeaderGroupOption | null>(() => {
  const st = sessionTypeFor(form.value.session_type_id)
  if (!st?.leader_group_id) return null
  return props.leaderGroups.find(lg => lg.id === st.leader_group_id) ?? null
})

const filteredMembers = computed(() => {
  // If the session type has a leader-group binding, restrict the picker to
  // that pool (and do client-side substring matching, no API call needed).
  if (activeLeaderGroup.value) {
    const q = memberSearch.value.trim().toLowerCase()
    const pool = activeLeaderGroup.value.members
    if (!q) return pool.slice(0, 15)
    return pool
      .filter(m => `${m.first_name} ${m.last_name}`.toLowerCase().includes(q))
      .slice(0, 15)
  }
  return members.value.slice(0, 15)
})

// --- Audience: subgroup options come from the session type's bound group ---

const audienceGroup = computed<GroupSummary | null>(() => {
  const st = sessionTypeFor(form.value.session_type_id)
  if (!st || st.group_id == null) return null
  return props.groups.find(g => g.id === st.group_id) ?? null
})

const subgroupOptionsForShift = computed(() => audienceGroup.value?.subgroups ?? [])

const inheritedSummary = computed(() => {
  const st = sessionTypeFor(form.value.session_type_id)
  const grpName = audienceGroup.value?.name
  const uids = st?.spond_subgroup_uids ?? []
  if (uids.length > 0 && audienceGroup.value) {
    const names = uids
      .map(uid => audienceGroup.value!.subgroups.find(s => s.uid === uid)?.name ?? uid)
    const list = names.length <= 2 ? names.join(', ') : `${names.slice(0, 2).join(', ')} +${names.length - 2}`
    return `Inherit: ${list} (of ${grpName})`
  }
  if (grpName) return `Inherit: whole group (${grpName})`
  return 'Inherit: session type defaults'
})

const toggleShiftSubgroup = (uid: string, checked: boolean) => {
  const current = form.value.invited_subgroup_uids ?? []
  if (checked) {
    if (!current.includes(uid)) form.value.invited_subgroup_uids = [...current, uid]
  } else {
    const next = current.filter(u => u !== uid)
    form.value.invited_subgroup_uids = next.length > 0 ? next : null
  }
}

// --- Invite scheduling helpers ---

const inheritedLeadDaysPlaceholder = computed(() => {
  const st = sessionTypeFor(form.value.session_type_id)
  return st?.invite_lead_days != null ? String(st.invite_lead_days) : '—'
})

const inviteScheduleSummary = computed(() => {
  const lead =
    form.value.invite_lead_days !== null && form.value.invite_lead_days !== undefined
      ? Number(form.value.invite_lead_days)
      : null
  const sendTime = (form.value.invite_send_time || '').slice(0, 5) || null

  if (lead === null || !sendTime) {
    return 'Sends immediately on publish'
  }
  const baseDate = form.value.date
  if (!baseDate) return `${lead} day(s) before, ${sendTime}`
  try {
    const [y, m, d] = baseDate.split('-').map(Number)
    const dt = new Date(y, (m || 1) - 1, d || 1)
    dt.setDate(dt.getDate() - lead)
    const iso = `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
    const source = inviteScheduleDiffersFromDefault.value ? 'shift override' : 'session-type default'
    return `Sends on ${iso} ${sendTime} (${source})`
  } catch {
    return `${lead} day(s) before, ${sendTime}`
  }
})

const inviteScheduleDiffersFromDefault = computed(() => {
  const st = sessionTypeFor(form.value.session_type_id)
  const defLead = st?.invite_lead_days ?? null
  const defTime = (st?.invite_send_time || '').slice(0, 5) || null
  const curLead =
    form.value.invite_lead_days !== null && form.value.invite_lead_days !== undefined
      ? Number(form.value.invite_lead_days)
      : null
  const curTime = (form.value.invite_send_time || '').slice(0, 5) || null
  return curLead !== defLead || curTime !== defTime
})

const clearInviteSchedule = () => {
  // Reset the visible inputs to the session type's defaults (which is what
  // they'd inherit if the shift's override columns are NULL). On save,
  // `buildInviteScheduleFields` will see equality with the default and
  // persist NULL — keeping the inherit-from-session-type semantic.
  const st = sessionTypeFor(form.value.session_type_id)
  form.value.invite_lead_days = st?.invite_lead_days ?? null
  form.value.invite_send_time = (st?.invite_send_time || '').slice(0, 5) || null
}

// --- Publish confirm summary ---

const publishSummary = computed(() => {
  const st = sessionTypeFor(form.value.session_type_id)
  const grpName = audienceGroup.value?.name ?? '(unbound group)'
  const session = st?.name ?? '(unknown)'

  const start = (form.value.start_time_override || st?.default_start_time || '').slice(0, 5)
  const end = (form.value.end_time_override || st?.default_end_time || '').slice(0, 5)
  const date = form.value.date
    ? `${form.value.date} · ${start}–${end}`
    : '(no date)'

  const leader = selectedLeaderLabel.value
    || (form.value.raw_initials ? `(unresolved: ${form.value.raw_initials})` : '(none)')

  const nameFor = (uid: string) =>
    audienceGroup.value?.subgroups.find(s => s.uid === uid)?.name ?? uid
  const summarizeUids = (uids: string[]): string => {
    const names = uids.map(nameFor)
    return names.length <= 2 ? names.join(', ') : `${names.slice(0, 2).join(', ')} +${names.length - 2}`
  }

  let audience: string
  if (form.value.invited_member_ids && form.value.invited_member_ids.length > 0) {
    audience = `${form.value.invited_member_ids.length} specific member(s)`
  } else if (form.value.invited_subgroup_uids && form.value.invited_subgroup_uids.length > 0) {
    audience = `Subgroups: ${summarizeUids(form.value.invited_subgroup_uids)}`
  } else if (st?.spond_subgroup_uids && st.spond_subgroup_uids.length > 0) {
    audience = `Subgroups: ${summarizeUids(st.spond_subgroup_uids)} (session default)`
  } else {
    audience = 'Whole group'
  }

  let sendAt: string
  const effLead =
    form.value.invite_lead_days !== null && form.value.invite_lead_days !== undefined
      ? form.value.invite_lead_days
      : st?.invite_lead_days ?? null
  const effSendTime = (
    form.value.invite_send_time || st?.invite_send_time || ''
  ).slice(0, 5)
  if (effLead === null || !effSendTime || !form.value.date) {
    sendAt = 'Immediately'
  } else {
    try {
      const [y, m, d] = form.value.date.split('-').map(Number)
      const dt = new Date(y, (m || 1) - 1, d || 1)
      dt.setDate(dt.getDate() - effLead)
      const iso = `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
      sendAt = `${iso} ${effSendTime} (Europe/Oslo)`
    } catch {
      sendAt = `${effLead} days before · ${effSendTime}`
    }
  }

  return { group: grpName, session, date, leader, audience, sendAt }
})

// Best-effort dirty check: compare key fields to whatever was on props.shift.
// Used to warn the admin that publish acts on saved state, not the edited form.
const hasUnsavedChanges = computed(() => {
  const s = props.shift
  if (!s) return false
  const same = (a: any, b: any) => (a ?? null) === (b ?? null)
  return !(
    same(s.leader_member_id, form.value.leader_member_id) &&
    same(s.raw_initials, form.value.raw_initials) &&
    same(s.notes, form.value.notes ?? null) &&
    same((s.start_time_override || '').slice(0, 5) || null,
         (form.value.start_time_override || '').slice(0, 5) || null) &&
    same((s.end_time_override || '').slice(0, 5) || null,
         (form.value.end_time_override || '').slice(0, 5) || null) &&
    JSON.stringify(s.invited_subgroup_uids ?? null) === JSON.stringify(form.value.invited_subgroup_uids ?? null) &&
    JSON.stringify(s.invited_member_ids ?? null) === JSON.stringify(form.value.invited_member_ids ?? null) &&
    same(s.invite_lead_days, form.value.invite_lead_days) &&
    same((s.invite_send_time || '').slice(0, 5) || null,
         (form.value.invite_send_time || '').slice(0, 5) || null)
  )
})

const onInviteModeChange = (mode: 'inherit' | 'subgroup' | 'members') => {
  inviteMode.value = mode
  if (mode === 'inherit') {
    form.value.invited_subgroup_uids = null
    form.value.invited_member_ids = null
    invitedMembers.value = []
  } else if (mode === 'subgroup') {
    form.value.invited_member_ids = null
    invitedMembers.value = []
    // Seed with the session type's defaults so the user starts from "what
    // would be invited anyway" and can deviate from there.
    if (!form.value.invited_subgroup_uids || form.value.invited_subgroup_uids.length === 0) {
      const st = sessionTypeFor(form.value.session_type_id)
      const defaults = st?.spond_subgroup_uids ?? []
      form.value.invited_subgroup_uids = defaults.length > 0 ? [...defaults] : []
    }
  } else {
    form.value.invited_subgroup_uids = null
  }
}

const loadInvitedMembers = async (ids: number[]) => {
  if (!ids.length) {
    invitedMembers.value = []
    return
  }
  try {
    // The /members/ list endpoint doesn't filter by id, so fetch enough rows
    // to find them. With ~150 club members one page is fine.
    const resp: any = await api.getMembers({ limit: 1000 })
    const lookup: Record<number, InvitedMember> = {}
    for (const m of (resp.members || [])) {
      lookup[m.id] = { id: m.id, first_name: m.first_name, last_name: m.last_name }
    }
    invitedMembers.value = ids.map(id => lookup[id]).filter(Boolean) as InvitedMember[]
  } catch (err) {
    console.error('Failed to resolve invited members:', err)
  }
}

let inviteeSearchTimer: ReturnType<typeof setTimeout> | null = null
const onInviteeSearchInput = () => {
  if (inviteeSearchTimer) clearTimeout(inviteeSearchTimer)
  inviteeSearchTimer = setTimeout(runInviteeSearch, 250)
}

const runInviteeSearch = async () => {
  const q = inviteeSearch.value.trim()
  if (!q) {
    inviteeResults.value = []
    return
  }
  try {
    const params: Record<string, any> = { search: q, limit: 20 }
    // Scope the search to the audience group when one is bound, so admins
    // don't accidentally invite members of an unrelated group.
    if (audienceGroup.value) params.group_id = audienceGroup.value.spond_id
    const resp: any = await api.getMembers(params)
    const taken = new Set(invitedMembers.value.map(m => m.id))
    inviteeResults.value = (resp.members || [])
      .filter((m: any) => !taken.has(m.id))
      .map((m: any) => ({ id: m.id, first_name: m.first_name, last_name: m.last_name }))
  } catch (err) {
    console.error('Failed to search members:', err)
  }
}

const addInvitee = (m: InvitedMember) => {
  if (invitedMembers.value.some(x => x.id === m.id)) return
  invitedMembers.value.push(m)
  form.value.invited_member_ids = invitedMembers.value.map(x => x.id)
  inviteeSearch.value = ''
  inviteeResults.value = []
}

const removeInvitee = (id: number) => {
  invitedMembers.value = invitedMembers.value.filter(m => m.id !== id)
  form.value.invited_member_ids = invitedMembers.value.length
    ? invitedMembers.value.map(m => m.id)
    : null
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
const debouncedSearch = () => {
  // When the session type has a leader-group binding the picker filters its
  // local pool client-side; no API call needed.
  if (activeLeaderGroup.value) return
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(loadMembers, 250)
}

const loadMembers = async () => {
  if (activeLeaderGroup.value) return
  try {
    const params: Record<string, any> = { limit: 50 }
    if (memberSearch.value.trim()) params.search = memberSearch.value.trim()
    const response: any = await api.getMembers(params)
    members.value = response.members || []
  } catch (err) {
    console.error('Failed to load members:', err)
  }
}

const selectLeader = (m: any) => {
  form.value.leader_member_id = m.id
  selectedLeaderLabel.value = `${m.first_name} ${m.last_name}`
  memberSearch.value = ''
}

const clearLeader = () => {
  form.value.leader_member_id = null
  selectedLeaderLabel.value = ''
}

const close = () => {
  isOpen.value = false
}

const overrideOrNull = (value: string | null, defaultValue: string): string | null => {
  const v = normalizeTime(value)
  const def = normalizeTime(defaultValue)
  if (!v) return null
  return v === def ? null : v
}

const buildInviteFields = () => {
  // Encode the (radio) inviteMode back to the (subgroup, members) pair the
  // backend understands.
  if (inviteMode.value === 'subgroup') {
    const uids = form.value.invited_subgroup_uids ?? []
    return {
      invited_subgroup_uids: uids.length > 0 ? [...uids] : null,
      invited_member_ids: null,
    }
  }
  if (inviteMode.value === 'members') {
    return {
      invited_subgroup_uids: null,
      invited_member_ids:
        form.value.invited_member_ids && form.value.invited_member_ids.length > 0
          ? form.value.invited_member_ids
          : null,
    }
  }
  return { invited_subgroup_uids: null, invited_member_ids: null }
}

const buildInviteScheduleFields = () => {
  // Persist as an override only when the value differs from the session
  // type's default. That keeps the shift "following" the session type when
  // the admin doesn't intentionally diverge.
  const st = sessionTypeFor(form.value.session_type_id)

  let lead: number | null = null
  if (
    form.value.invite_lead_days !== null
    && form.value.invite_lead_days !== undefined
    && Number.isFinite(Number(form.value.invite_lead_days))
  ) {
    const n = Number(form.value.invite_lead_days)
    lead = n === (st?.invite_lead_days ?? null) ? null : n
  }

  let sendTime: string | null = null
  const raw = (form.value.invite_send_time || '').trim()
  if (raw) {
    const hhmm = raw.length === 5 ? raw : raw.slice(0, 5)
    const defaultHHMM = (st?.invite_send_time || '').slice(0, 5)
    sendTime = hhmm === defaultHHMM
      ? null
      : (raw.length === 5 ? `${raw}:00` : raw)
  }

  return { invite_lead_days: lead, invite_send_time: sendTime }
}

const buildPatchBody = () => {
  // For published shifts, only allow notes/status/spond_event_id
  if (form.value.status === 'published') {
    return { notes: form.value.notes ?? null }
  }
  const st = sessionTypeFor(form.value.session_type_id)
  return {
    session_type_id: form.value.session_type_id,
    date: form.value.date,
    leader_member_id: form.value.leader_member_id,
    raw_initials: form.value.leader_member_id ? null : form.value.raw_initials,
    start_time_override: overrideOrNull(form.value.start_time_override, st?.default_start_time ?? ''),
    end_time_override: overrideOrNull(form.value.end_time_override, st?.default_end_time ?? ''),
    notes: form.value.notes ?? null,
    status: form.value.status,
    ...buildInviteFields(),
    ...buildInviteScheduleFields(),
  }
}

const handleSave = async () => {
  if (!form.value.session_type_id || !form.value.date) {
    formError.value = 'Session type and date are required'
    return
  }
  if (inviteMode.value === 'members' && invitedMembers.value.length === 0) {
    formError.value = 'Add at least one member, or switch to Inherit / Subgroup.'
    return
  }
  if (
    inviteMode.value === 'subgroup' &&
    (!form.value.invited_subgroup_uids || form.value.invited_subgroup_uids.length === 0) &&
    subgroupOptionsForShift.value.length > 0
  ) {
    formError.value = 'Pick at least one subgroup.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    if (isEditing.value && form.value.id) {
      await api.updateTrainingShift(form.value.id, buildPatchBody())
      toast.add({ title: 'Saved', description: 'Shift updated', color: 'success' })
    } else {
      const st = sessionTypeFor(form.value.session_type_id)
      await api.createTrainingShift({
        session_type_id: form.value.session_type_id,
        date: form.value.date,
        leader_member_id: form.value.leader_member_id,
        raw_initials: form.value.leader_member_id ? null : form.value.raw_initials,
        start_time_override: overrideOrNull(form.value.start_time_override, st?.default_start_time ?? ''),
        end_time_override: overrideOrNull(form.value.end_time_override, st?.default_end_time ?? ''),
        notes: form.value.notes || null,
        ...buildInviteFields(),
        ...buildInviteScheduleFields(),
      })
      toast.add({ title: 'Created', description: 'Shift added', color: 'success' })
    }
    emit('saved')
    close()
  } catch (err: any) {
    formError.value = err?.data?.detail || err?.message || 'Failed to save shift'
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!form.value.id) return
  if (!confirm('Delete this draft shift?')) return
  deleting.value = true
  try {
    await api.deleteTrainingShift(form.value.id)
    toast.add({ title: 'Deleted', description: 'Shift removed', color: 'success' })
    emit('deleted')
    close()
  } catch (err: any) {
    toast.add({
      title: 'Delete failed',
      description: err?.data?.detail || 'Could not delete shift',
      color: 'error',
    })
  } finally {
    deleting.value = false
  }
}

const askPublish = () => {
  publishConfirmOpen.value = true
}

const handlePublish = async () => {
  if (!form.value.id) return
  publishing.value = true
  try {
    await api.publishTrainingShift(form.value.id)
    toast.add({ title: 'Published', description: 'Spond event created', color: 'success' })
    publishConfirmOpen.value = false
    emit('saved')
    close()
  } catch (err: any) {
    const detail = err?.data?.detail || err?.message || 'Publish failed'
    toast.add({ title: 'Publish failed', description: detail, color: 'error' })
  } finally {
    publishing.value = false
  }
}

const askCancel = () => {
  cancelConfirmOpen.value = true
}

const handleCancelShift = async () => {
  if (!form.value.id) return
  cancelling.value = true
  try {
    await api.updateTrainingShift(form.value.id, { status: 'cancelled', notes: form.value.notes ?? null })
    toast.add({ title: 'Cancelled', description: 'Shift marked cancelled', color: 'success' })
    cancelConfirmOpen.value = false
    emit('saved')
    close()
  } catch (err: any) {
    toast.add({
      title: 'Cancel failed',
      description: err?.data?.detail || 'Could not cancel shift',
      color: 'error',
    })
  } finally {
    cancelling.value = false
  }
}

const handleReactivate = async () => {
  if (!form.value.id) return
  try {
    await api.updateTrainingShift(form.value.id, { status: 'draft', notes: form.value.notes ?? null })
    toast.add({ title: 'Reactivated', description: 'Shift set to draft', color: 'success' })
    emit('saved')
    close()
  } catch (err: any) {
    toast.add({
      title: 'Reactivate failed',
      description: err?.data?.detail || 'Could not reactivate',
      color: 'error',
    })
  }
}

const formatTime = (t: string) => (t ? t.slice(0, 5) : '')

onMounted(() => {
  loadMembers()
})
</script>
