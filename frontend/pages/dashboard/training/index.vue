<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Training plan' }
    ]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Training plan</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Monthly schedule for training shifts, with one-click publish to Spond.
        </p>
      </div>
      <div class="flex flex-wrap items-end gap-2">
        <!-- Plan switcher. The active plan drives which session types +
             shifts are loaded. Persisted in auth.selectedPlanId via
             localStorage so reload remembers the choice. -->
        <div class="min-w-[220px]">
          <label class="block text-xs font-medium text-gray-500 mb-1">Active plan</label>
          <select
            v-model.number="activePlanIdModel"
            class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            @change="onPlanChange"
          >
            <option v-if="plans.length === 0" :value="null">
              — no plans —
            </option>
            <option v-for="p in plans" :key="p.id" :value="p.id">
              {{ p.name }}
            </option>
          </select>
        </div>

        <UButton
          color="neutral"
          variant="outline"
          icon="i-heroicons-cog-6-tooth"
          to="/dashboard/training/plans"
        >
          Manage plans
        </UButton>
        <UButton
          v-if="canEdit"
          color="primary"
          icon="i-heroicons-plus"
          :disabled="!authStore.hasSelectedPlan"
          @click="openNewShift"
        >
          New shift
        </UButton>
        <UButton
          v-if="isAdmin"
          color="neutral"
          variant="outline"
          icon="i-heroicons-user-group"
          to="/dashboard/training/leader-groups"
        >
          Leader groups
        </UButton>
        <UButton
          v-if="isAdmin"
          color="neutral"
          variant="outline"
          icon="i-heroicons-arrow-up-tray"
          :disabled="!authStore.hasSelectedPlan"
          :title="authStore.hasSelectedPlan ? '' : 'Pick or create a plan first'"
          @click="importModalOpen = true"
        >
          Import xlsx
        </UButton>
      </div>
    </div>

    <!-- Month selector -->
    <UCard>
      <div class="flex items-center justify-between gap-4">
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-heroicons-chevron-left"
          aria-label="Previous month"
          @click="shiftMonth(-1)"
        />
        <div class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ monthLabel }}
        </div>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-heroicons-chevron-right"
          aria-label="Next month"
          @click="shiftMonth(1)"
        />
      </div>
    </UCard>

    <!-- Manage session types (collapsible, admin) -->
    <UCard v-if="isAdmin">
      <button
        type="button"
        class="w-full flex items-center justify-between text-left"
        @click="manageOpen = !manageOpen"
      >
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-adjustments-horizontal" class="w-5 h-5 text-gray-500" />
          <span class="font-medium text-gray-900 dark:text-white">Manage session types</span>
          <UBadge color="neutral" variant="subtle" size="sm">{{ sessionTypes.length }}</UBadge>
        </div>
        <UIcon
          :name="manageOpen ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
          class="w-5 h-5 text-gray-400"
        />
      </button>

      <div v-if="manageOpen" class="mt-4 space-y-3">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="text-left py-2 px-2 font-medium text-gray-500">Name</th>
                <th class="text-left py-2 px-2 font-medium text-gray-500">Time</th>
                <th class="text-left py-2 px-2 font-medium text-gray-500">Location</th>
                <th class="text-left py-2 px-2 font-medium text-gray-500">Spond group</th>
                <th class="text-left py-2 px-2 font-medium text-gray-500">Spond subgroup</th>
                <th class="text-right py-2 px-2 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="st in sessionTypes"
                :key="st.id"
                class="border-b border-gray-100 dark:border-gray-800"
              >
                <td class="py-2 px-2 font-medium text-gray-900 dark:text-white">
                  {{ st.name }}
                </td>
                <td class="py-2 px-2 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                  {{ formatTime(st.default_start_time) }}–{{ formatTime(st.default_end_time) }}
                </td>
                <td class="py-2 px-2 text-gray-700 dark:text-gray-300">
                  {{ st.location || '—' }}
                </td>
                <td class="py-2 px-2 text-gray-700 dark:text-gray-300">
                  <span v-if="st.group">{{ st.group.name }}</span>
                  <span v-else class="text-amber-600">— not linked —</span>
                </td>
                <td class="py-2 px-2 text-gray-700 dark:text-gray-300">
                  {{ subgroupNameForSessionType(st) }}
                </td>
                <td class="py-2 px-2 text-right">
                  <UButton
                    size="xs"
                    color="neutral"
                    variant="soft"
                    icon="i-heroicons-pencil-square"
                    @click="openEditSessionType(st)"
                  >
                    Edit
                  </UButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="border-t border-gray-200 dark:border-gray-700 pt-3 flex justify-end">
          <UButton
            size="sm"
            icon="i-heroicons-plus"
            @click="openNewSessionType"
          >
            New session type
          </UButton>
        </div>
      </div>
    </UCard>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <!-- Empty state -->
    <UCard v-else-if="sessionTypes.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-clipboard-document-list" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-700 dark:text-gray-300 font-medium">No session types yet</p>
      <p class="text-sm text-gray-500 mt-1">
        Import a vaktliste .xlsx to create session types automatically, or add them manually above.
      </p>
      <div v-if="isAdmin" class="mt-4">
        <UButton icon="i-heroicons-arrow-up-tray" @click="importModalOpen = true">Import xlsx</UButton>
      </div>
    </UCard>

    <UCard v-else-if="shifts.length === 0 && !loading" class="text-center py-12">
      <UIcon name="i-heroicons-calendar" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-700 dark:text-gray-300 font-medium">No shifts this month</p>
      <p class="text-sm text-gray-500 mt-1">
        Click any cell below to create a shift, or import a vaktliste .xlsx.
      </p>
      <CalendarGrid
        class="mt-6"
        :session-types="sessionTypes"
        :days="daysInMonth"
        :shifts-by-key="shiftsByKey"
        :can-edit="canEdit"
        :can-create="canEdit"
        @cell-click="onCellClick"
      />
    </UCard>

    <!-- Calendar grid -->
    <UCard v-else>
      <CalendarGrid
        :session-types="sessionTypes"
        :days="daysInMonth"
        :shifts-by-key="shiftsByKey"
        :can-edit="canEdit"
        :can-create="canEdit"
        @cell-click="onCellClick"
      />

      <template #footer>
        <div class="flex flex-wrap items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
          <span class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded bg-blue-100 border border-blue-400" /> Draft
          </span>
          <span class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded bg-green-100 border border-green-500" /> Published
          </span>
          <span class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded bg-amber-100 border border-amber-400" /> Unresolved initials
          </span>
          <span class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded bg-gray-200 border border-gray-400" /> Cancelled
          </span>
        </div>
      </template>
    </UCard>

    <!-- Shift editor -->
    <TrainingShiftEditor
      v-model:open="editorOpen"
      :shift="editorShift"
      :session-types="sessionTypes"
      :groups="groupOptions"
      :leader-groups="leaderGroupOptions"
      @saved="loadMonth"
      @deleted="loadMonth"
    />

    <!-- Import modal -->
    <UModal v-model:open="importModalOpen" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="p-6 space-y-4">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">Import vaktliste (.xlsx)</h2>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Existing draft shifts will be overwritten. Published shifts are never overwritten.
          </p>

          <input
            ref="fileInput"
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            class="block w-full text-sm text-gray-700 dark:text-gray-300 file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900/30 dark:file:text-blue-300"
            @change="onFilePicked"
          />

          <div v-if="importReport" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4 space-y-3 text-sm">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <div class="text-xs text-gray-500">Created</div>
                <div class="text-lg font-semibold text-green-600">{{ importReport.created }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Updated</div>
                <div class="text-lg font-semibold text-blue-600">{{ importReport.updated }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Skipped (published)</div>
                <div class="text-lg font-semibold text-gray-700 dark:text-gray-300">{{ importReport.skipped_published }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Skipped (unknown)</div>
                <div class="text-lg font-semibold text-amber-600">{{ importReport.skipped_unknown }}</div>
              </div>
            </div>

            <div v-if="importReport.created_session_types?.length" class="text-xs text-gray-600 dark:text-gray-400">
              New session types: {{ importReport.created_session_types.join(', ') }}
            </div>
            <div v-if="importReport.created_aliases" class="text-xs text-gray-600 dark:text-gray-400">
              New aliases created: {{ importReport.created_aliases }}
            </div>

            <div v-if="importReport.unresolved_initials?.length">
              <div class="flex items-center justify-between mb-1">
                <div class="text-sm font-medium text-amber-700 dark:text-amber-400">
                  Unresolved initials ({{ importReport.unresolved_initials.length }})
                </div>
                <NuxtLink
                  to="/dashboard/training/aliases?showUnresolved=1"
                  class="text-xs text-blue-600 hover:underline"
                  @click="importModalOpen = false"
                >
                  Review unresolved →
                </NuxtLink>
              </div>
              <ul class="text-xs space-y-1 max-h-40 overflow-y-auto">
                <li
                  v-for="(u, idx) in importReport.unresolved_initials.slice(0, 20)"
                  :key="idx"
                  class="text-gray-600 dark:text-gray-400"
                >
                  <span class="font-mono text-amber-700">{{ u.initials }}</span>
                  ({{ u.name }}) — {{ u.session_type_name }} on {{ u.date }}
                </li>
              </ul>
            </div>

            <div v-if="importReport.errors?.length" class="text-xs text-red-600">
              <div class="font-medium">Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(e, idx) in importReport.errors" :key="idx">{{ e }}</li>
              </ul>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <UButton color="neutral" variant="outline" @click="importModalOpen = false">
              {{ importReport ? 'Close' : 'Cancel' }}
            </UButton>
            <UButton
              v-if="!importReport"
              :loading="importing"
              :disabled="!importFile"
              icon="i-heroicons-arrow-up-tray"
              @click="handleImport"
            >
              Upload
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Edit / new session type modal -->
    <UModal v-model:open="editSessionTypeOpen" :ui="{ content: 'max-w-3xl' }">
      <template #content>
        <div v-if="editingSessionType" class="p-6 space-y-4">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ editingSessionType.id ? 'Edit session type' : 'New session type' }}
          </h2>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <UInput
              v-model="editingSessionType._editName"
              :placeholder="editingSessionType.name || 'e.g. Tuesday training'"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start</label>
              <TimeInputHHMM v-model="editingSessionType._editStart" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End</label>
              <TimeInputHHMM v-model="editingSessionType._editEnd" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Location</label>
            <UInput
              v-model="editingSessionType._editLocation"
              placeholder="—"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Spond group</label>
            <select
              v-model.number="editingSessionType._editGroup"
              class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
              @change="onGroupChanged(editingSessionType)"
            >
              <option :value="null">— not linked —</option>
              <option v-for="g in groupOptions" :key="g.id" :value="g.id">
                {{ g.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Spond subgroups
              <span class="ml-1 text-xs font-normal text-gray-400">
                — leave all unchecked to invite the whole group.
              </span>
            </label>
            <div
              v-if="!editingSessionType._editGroup"
              class="text-xs text-gray-500 italic"
            >
              Pick a Spond group first.
            </div>
            <div
              v-else-if="subgroupsForGroup(editingSessionType._editGroup).length === 0"
              class="text-xs text-gray-500 italic"
            >
              This group has no subgroups.
            </div>
            <div
              v-else
              class="grid grid-cols-2 gap-x-4 gap-y-1.5 max-h-48 overflow-y-auto rounded-md border border-gray-200 dark:border-gray-700 p-2"
            >
              <label
                v-for="sg in subgroupsForGroup(editingSessionType._editGroup)"
                :key="sg.uid"
                class="inline-flex items-center gap-1.5 text-sm cursor-pointer"
              >
                <input
                  type="checkbox"
                  :value="sg.uid"
                  :checked="editingSessionType._editSubgroupUids?.includes(sg.uid)"
                  class="rounded border-gray-300 dark:border-gray-600"
                  @change="toggleSessionTypeSubgroup(editingSessionType, sg.uid, ($event.target as HTMLInputElement).checked)"
                />
                <span>{{ sg.name }}</span>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Leader group
              <span class="ml-1 text-xs font-normal text-gray-400">
                — pool of members who can lead this session.
                <NuxtLink
                  to="/dashboard/training/leader-groups"
                  class="text-blue-600 hover:underline"
                  @click="editSessionTypeOpen = false"
                >
                  Manage →
                </NuxtLink>
              </span>
            </label>
            <select
              v-model.number="editingSessionType._editLeaderGroup"
              class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option :value="null">— any member —</option>
              <option v-for="lg in leaderGroupOptions" :key="lg.id" :value="lg.id">
                {{ lg.name }} ({{ lg.members?.length ?? 0 }})
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Send Spond invitation
              <span class="ml-1 text-xs font-normal text-gray-400">
                — leave blank to send immediately on publish.
              </span>
            </label>
            <div class="flex flex-wrap items-center gap-2 text-sm">
              <UInput
                v-model.number="editingSessionType._editInviteLeadDays"
                type="number"
                min="0"
                max="365"
                placeholder="—"
                class="w-24"
                :ui="{ base: 'w-24' }"
              />
              <span class="text-gray-600 dark:text-gray-400">days before, at</span>
              <TimeInputHHMM v-model="editingSessionType._editInviteSendTime" />
              <span class="text-gray-500 dark:text-gray-400 text-xs">(Europe/Oslo)</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
              <span class="ml-1 text-xs font-normal text-gray-400">
                — base Spond event description when shifts are published.
              </span>
            </label>
            <UTextarea
              v-model="editingSessionType._editDescription"
              :rows="4"
              placeholder="e.g. Tren med oss på Birkebeineren. Husk å ta med drikkeflaske."
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <div class="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <UButton color="neutral" variant="outline" @click="editSessionTypeOpen = false">
              Cancel
            </UButton>
            <UButton
              icon="i-heroicons-check"
              :loading="!!editingSessionType._saving"
              @click="saveEditedSessionType"
            >
              Save
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import CalendarGrid from '~/components/training/CalendarGrid.vue'
import TrainingShiftEditor from '~/components/training/TrainingShiftEditor.vue'

definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const authStore = useAuthStore()
const { canEdit, isAdmin } = usePermissions()

interface PlanRow {
  id: number
  name: string
  period_start: string
  period_end: string
}
const plans = ref<PlanRow[]>([])

// Two-way binding for the plan <select>. Reads from auth store; writes
// go through setSelectedPlan so localStorage stays in sync.
const activePlanIdModel = computed<number | null>({
  get: () => authStore.selectedPlanId,
  set: (v) => authStore.setSelectedPlan(v),
})

interface SessionType {
  id: number
  name: string
  default_start_time: string
  default_end_time: string
  location: string | null
  description: string | null
  group_id: number | null
  spond_subgroup_uids: string[] | null
  leader_group_id: number | null
  invite_lead_days: number | null
  invite_send_time: string | null
  group: { id: number; spond_id: string; name: string } | null
  leader_group: { id: number; name: string } | null
  _editName?: string
  _editStart?: string
  _editEnd?: string
  _editLocation?: string
  _editDescription?: string
  _editGroup?: number | null
  _editSubgroupUids?: string[]
  _editLeaderGroup?: number | null
  _editInviteLeadDays?: number | null
  _editInviteSendTime?: string
  _saving?: boolean
}

interface LeaderGroupOption {
  id: number
  name: string
  description: string | null
  members: { id: number; first_name: string; last_name: string }[]
}

interface GroupOption {
  id: number
  spond_id: string
  name: string
  subgroups: { uid: string; name: string }[]
}

interface Shift {
  id: number
  session_type_id: number
  session_type: SessionType
  date: string
  leader_member_id: number | null
  leader: { id: number; first_name: string; last_name: string } | null
  raw_initials: string | null
  start_time_override: string | null
  end_time_override: string | null
  notes: string | null
  status: 'draft' | 'published' | 'cancelled'
  spond_event_id: string | null
}

const today = new Date()
const currentMonth = ref<{ year: number; month: number }>({
  year: today.getFullYear(),
  month: today.getMonth() + 1,
})

const sessionTypes = ref<SessionType[]>([])
const shifts = ref<Shift[]>([])
const loading = ref(true)
const manageOpen = ref(false)

const editorOpen = ref(false)
const editorShift = ref<any>(null)

const importModalOpen = ref(false)
const importing = ref(false)
const importFile = ref<File | null>(null)
const importReport = ref<any>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const groupOptions = ref<GroupOption[]>([])
const leaderGroupOptions = ref<LeaderGroupOption[]>([])

const editSessionTypeOpen = ref(false)
const editingSessionType = ref<SessionType | null>(null)

const subgroupsForGroup = (groupId: number | null | undefined) => {
  if (!groupId) return []
  return groupOptions.value.find(g => g.id === groupId)?.subgroups ?? []
}

const onGroupChanged = (st: SessionType | null) => {
  // Clear the subgroup selection when the group changes — uids only make
  // sense within a specific parent group.
  if (st) st._editSubgroupUids = []
}

const toggleSessionTypeSubgroup = (st: SessionType, uid: string, checked: boolean) => {
  const current = st._editSubgroupUids ?? []
  if (checked) {
    if (!current.includes(uid)) st._editSubgroupUids = [...current, uid]
  } else {
    st._editSubgroupUids = current.filter(u => u !== uid)
  }
}

const formatTime = (t: string | null | undefined) => (t ? t.slice(0, 5) : '')

const subgroupNameForSessionType = (st: SessionType): string => {
  const uids = st.spond_subgroup_uids ?? []
  if (uids.length === 0) return '— whole group —'
  const group = groupOptions.value.find(g => g.id === st.group_id)
  if (!group) return `${uids.length} subgroup${uids.length === 1 ? '' : 's'}`
  const names = uids
    .map(uid => group.subgroups.find(sg => sg.uid === uid)?.name ?? uid)
  if (names.length <= 2) return names.join(', ')
  return `${names.slice(0, 2).join(', ')} +${names.length - 2}`
}

const openEditSessionType = (st: SessionType) => {
  // Rehydrate the _edit* working copies from the canonical values so the
  // modal starts from the last saved state, not whatever was typed before.
  st._editName = st.name
  st._editStart = formatTime(st.default_start_time)
  st._editEnd = formatTime(st.default_end_time)
  st._editLocation = st.location || ''
  st._editDescription = st.description || ''
  st._editGroup = st.group_id ?? null
  st._editSubgroupUids = [...(st.spond_subgroup_uids ?? [])]
  st._editLeaderGroup = st.leader_group_id ?? null
  st._editInviteLeadDays = st.invite_lead_days ?? null
  st._editInviteSendTime = (st.invite_send_time || '').slice(0, 5)
  editingSessionType.value = st
  editSessionTypeOpen.value = true
}

const openNewSessionType = () => {
  // A "draft" session type that lives only in the modal until the user clicks
  // Save. id stays unset so saveEditedSessionType knows to POST instead of PATCH.
  editingSessionType.value = {
    id: 0,
    name: '',
    default_start_time: '17:00:00',
    default_end_time: '19:00:00',
    location: null,
    description: null,
    group_id: null,
    spond_subgroup_uids: null,
    leader_group_id: null,
    invite_lead_days: null,
    invite_send_time: null,
    group: null,
    leader_group: null,
    _editName: '',
    _editStart: '17:00',
    _editEnd: '19:00',
    _editLocation: '',
    _editDescription: '',
    _editGroup: null,
    _editSubgroupUids: [],
    _editLeaderGroup: null,
    _editInviteLeadDays: null,
    _editInviteSendTime: '',
  } as SessionType
  // We use a sentinel id of 0 because the template renders on `editingSessionType`
  // and we want all the fields wired. The save handler treats id===0 as "create".
  ;(editingSessionType.value as any).id = 0
  editSessionTypeOpen.value = true
}

const saveEditedSessionType = async () => {
  const st = editingSessionType.value
  if (!st) return
  const isNew = !st.id
  const ok = isNew
    ? await createSessionTypeFromModal(st)
    : await saveSessionType(st)
  if (ok) editSessionTypeOpen.value = false
}

const createSessionTypeFromModal = async (st: SessionType): Promise<boolean> => {
  if (!st._editName?.trim()) {
    toast.add({
      title: 'Name required',
      description: 'Give the session type a name first.',
      color: 'warning',
    })
    return false
  }
  st._saving = true
  const planId = authStore.selectedPlanId
  if (planId === null) {
    toast.add({
      title: 'No active plan',
      description: 'Pick or create a training plan first.',
      color: 'amber',
    })
    return false
  }
  try {
    const startRaw = st._editStart || '17:00'
    const endRaw = st._editEnd || '19:00'
    const sendTimeRaw = st._editInviteSendTime?.trim() || ''
    const body: Record<string, any> = {
      name: st._editName.trim(),
      plan_id: planId,
      default_start_time: startRaw.length === 5 ? `${startRaw}:00` : startRaw,
      default_end_time: endRaw.length === 5 ? `${endRaw}:00` : endRaw,
      location: st._editLocation?.trim() ? st._editLocation.trim() : null,
      description: st._editDescription?.trim() ? st._editDescription : null,
      group_id: st._editGroup ?? null,
      spond_subgroup_uids: (st._editSubgroupUids ?? []).length > 0
        ? [...(st._editSubgroupUids ?? [])]
        : null,
      leader_group_id: st._editLeaderGroup ?? null,
      invite_lead_days:
        st._editInviteLeadDays !== null && st._editInviteLeadDays !== undefined && Number.isFinite(Number(st._editInviteLeadDays))
          ? Number(st._editInviteLeadDays)
          : null,
      invite_send_time: sendTimeRaw
        ? (sendTimeRaw.length === 5 ? `${sendTimeRaw}:00` : sendTimeRaw)
        : null,
    }
    await api.createTrainingSessionType(body)
    await loadSessionTypes()
    toast.add({
      title: 'Created',
      description: `${body.name} added`,
      color: 'success',
    })
    return true
  } catch (err: any) {
    toast.add({
      title: 'Create failed',
      description: err?.data?.detail || 'Could not create session type',
      color: 'error',
    })
    return false
  } finally {
    st._saving = false
  }
}

const monthLabel = computed(() => {
  const d = new Date(currentMonth.value.year, currentMonth.value.month - 1, 1)
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const monthString = computed(() =>
  `${currentMonth.value.year}-${String(currentMonth.value.month).padStart(2, '0')}`
)

const daysInMonth = computed(() => {
  const { year, month } = currentMonth.value
  const lastDay = new Date(year, month, 0).getDate()
  const days: { date: string; day: number; weekday: string; isWeekend: boolean }[] = []
  for (let d = 1; d <= lastDay; d++) {
    const dateObj = new Date(year, month - 1, d)
    const iso = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const wd = dateObj.getDay()
    days.push({
      date: iso,
      day: d,
      weekday: dateObj.toLocaleDateString('en-US', { weekday: 'short' }).charAt(0),
      isWeekend: wd === 0 || wd === 6,
    })
  }
  return days
})

const shiftsByKey = computed(() => {
  const map: Record<string, Shift> = {}
  for (const s of shifts.value) {
    map[`${s.session_type_id}|${s.date}`] = s
  }
  return map
})

const shiftMonth = (delta: number) => {
  let { year, month } = currentMonth.value
  month += delta
  while (month < 1) {
    month += 12
    year -= 1
  }
  while (month > 12) {
    month -= 12
    year += 1
  }
  currentMonth.value = { year, month }
  loadMonth()
}

const hydrateSessionType = (st: any): SessionType => ({
  ...st,
  _editName: st.name,
  _editStart: (st.default_start_time || '').slice(0, 5),
  _editEnd: (st.default_end_time || '').slice(0, 5),
  _editLocation: st.location || '',
  _editDescription: st.description || '',
  _editGroup: st.group_id ?? null,
  _editSubgroupUids: [...(st.spond_subgroup_uids ?? [])],
  _editLeaderGroup: st.leader_group_id ?? null,
  _editInviteLeadDays: st.invite_lead_days ?? null,
  _editInviteSendTime: (st.invite_send_time || '').slice(0, 5),
})

const loadSessionTypes = async () => {
  const planId = authStore.selectedPlanId
  if (planId === null) {
    sessionTypes.value = []
    return
  }
  try {
    const data = await api.getTrainingSessionTypesForPlan(planId)
    sessionTypes.value = (data.items || []).map(hydrateSessionType)
  } catch (err) {
    console.error('Failed to load session types:', err)
  }
}

const loadMonth = async () => {
  const planId = authStore.selectedPlanId
  if (planId === null) {
    sessionTypes.value = []
    shifts.value = []
    loading.value = false
    return
  }
  loading.value = true
  try {
    const [stResp, shResp] = await Promise.all([
      sessionTypes.value.length === 0
        ? api.getTrainingSessionTypesForPlan(planId)
        : Promise.resolve({ items: sessionTypes.value }),
      api.getTrainingShifts({
        month: monthString.value,
        limit: 500,
        plan_id: planId,
      }),
    ])
    if (sessionTypes.value.length === 0) {
      sessionTypes.value = ((stResp as any).items || []).map(hydrateSessionType)
    }
    shifts.value = (shResp as any).items || []
  } catch (err: any) {
    console.error('Failed to load training data:', err)
    toast.add({
      title: 'Load failed',
      description: err?.data?.detail || 'Could not load training plan',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

const loadPlans = async () => {
  try {
    const resp: any = await api.getTrainingPlans()
    plans.value = (resp.items || []).map((p: any) => ({
      id: p.id,
      name: p.name,
      period_start: p.period_start,
      period_end: p.period_end,
    }))
    // First-time visit: snap to the newest plan so the calendar isn't empty.
    if (
      authStore.selectedPlanId === null &&
      plans.value.length > 0
    ) {
      authStore.setSelectedPlan(plans.value[0].id)
    }
  } catch (err) {
    console.warn('Could not load training plans:', err)
  }
}

const onPlanChange = async () => {
  // Wipe loaded data so the calendar doesn't flash stale shifts.
  sessionTypes.value = []
  shifts.value = []
  // Jump to the plan's start month one-shot — admin can navigate away after.
  const planId = authStore.selectedPlanId
  if (planId !== null) {
    const p = plans.value.find(pp => pp.id === planId)
    if (p?.period_start) {
      const [y, m] = p.period_start.split('-').map(Number)
      if (Number.isFinite(y) && Number.isFinite(m)) {
        currentMonth.value = { year: y, month: m }
      }
    }
  }
  await loadMonth()
}

const loadGroups = async () => {
  try {
    const resp: any = await api.getGroups()
    const list: any[] = Array.isArray(resp) ? resp : (resp?.groups || [])
    // Load each group's full record (with subgroups) in parallel. The list
    // endpoint typically only carries metadata; the detail endpoint embeds
    // the subgroup array.
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
        } as GroupOption
      })
      .sort((a, b) => a.name.localeCompare(b.name))
  } catch (err) {
    console.warn('Could not load groups:', err)
  }
}

const onCellClick = (sessionTypeId: number, date: string, existing: Shift | null) => {
  if (existing) {
    editorShift.value = { ...existing }
  } else {
    if (!canEdit.value) return
    editorShift.value = {
      session_type_id: sessionTypeId,
      date,
      leader_member_id: null,
      raw_initials: null,
      start_time_override: null,
      end_time_override: null,
      notes: '',
      status: 'draft',
    }
  }
  editorOpen.value = true
}

const openNewShift = () => {
  editorShift.value = {
    session_type_id: sessionTypes.value[0]?.id ?? null,
    date: `${monthString.value}-01`,
    leader_member_id: null,
    raw_initials: null,
    start_time_override: null,
    end_time_override: null,
    notes: '',
    status: 'draft',
  }
  editorOpen.value = true
}

const onFilePicked = (e: Event) => {
  const target = e.target as HTMLInputElement
  importFile.value = target.files?.[0] ?? null
  importReport.value = null
}

const handleImport = async () => {
  if (!importFile.value) return
  const planId = authStore.selectedPlanId
  if (planId === null) {
    toast.add({
      title: 'No active plan',
      description: 'Pick or create a training plan first.',
      color: 'amber',
    })
    return
  }
  importing.value = true
  importReport.value = null
  try {
    const report: any = await api.importTrainingXlsx(planId, importFile.value)
    importReport.value = report
    toast.add({
      title: 'Import complete',
      description: `${report.created} created, ${report.updated} updated, ${report.skipped_published} kept published`,
      color: 'success',
    })
    // Refresh data
    await Promise.all([loadSessionTypes(), loadMonth()])
  } catch (err: any) {
    toast.add({
      title: 'Import failed',
      description: err?.data?.detail || err?.message || 'Could not import file',
      color: 'error',
    })
  } finally {
    importing.value = false
  }
}

const saveSessionType = async (st: SessionType): Promise<boolean> => {
  st._saving = true
  try {
    const body: Record<string, any> = {}
    if (st._editName !== undefined && st._editName !== st.name) body.name = st._editName
    if (st._editStart) body.default_start_time = st._editStart.length === 5 ? `${st._editStart}:00` : st._editStart
    if (st._editEnd) body.default_end_time = st._editEnd.length === 5 ? `${st._editEnd}:00` : st._editEnd
    body.location = st._editLocation?.trim() ? st._editLocation.trim() : null
    body.description = st._editDescription?.trim() ? st._editDescription : null
    body.group_id = st._editGroup ?? null
    body.spond_subgroup_uids = (st._editSubgroupUids ?? []).length > 0
      ? [...(st._editSubgroupUids ?? [])]
      : null
    body.leader_group_id = st._editLeaderGroup ?? null
    body.invite_lead_days =
      st._editInviteLeadDays !== null && st._editInviteLeadDays !== undefined && Number.isFinite(Number(st._editInviteLeadDays))
        ? Number(st._editInviteLeadDays)
        : null
    const sendTimeRaw = st._editInviteSendTime?.trim() || ''
    body.invite_send_time = sendTimeRaw
      ? (sendTimeRaw.length === 5 ? `${sendTimeRaw}:00` : sendTimeRaw)
      : null
    const updated: any = await api.updateTrainingSessionType(st.id, body)
    Object.assign(st, updated)
    st._editName = updated.name
    st._editStart = (updated.default_start_time || '').slice(0, 5)
    st._editEnd = (updated.default_end_time || '').slice(0, 5)
    st._editLocation = updated.location || ''
    st._editDescription = updated.description || ''
    st._editGroup = updated.group_id ?? null
    st._editSubgroupUids = [...(updated.spond_subgroup_uids ?? [])]
    st._editLeaderGroup = updated.leader_group_id ?? null
    st._editInviteLeadDays = updated.invite_lead_days ?? null
    st._editInviteSendTime = (updated.invite_send_time || '').slice(0, 5)
    toast.add({ title: 'Saved', description: `${updated.name} updated`, color: 'success' })
    return true
  } catch (err: any) {
    toast.add({
      title: 'Save failed',
      description: err?.data?.detail || 'Could not save session type',
      color: 'error',
    })
    return false
  } finally {
    st._saving = false
  }
}

const loadLeaderGroups = async () => {
  try {
    const resp: any = await api.getLeaderGroups()
    leaderGroupOptions.value = (resp.items || []).map((lg: any) => ({
      id: lg.id,
      name: lg.name,
      description: lg.description || null,
      members: lg.members || [],
    }))
  } catch (err) {
    console.warn('Could not load leader groups:', err)
  }
}

onMounted(async () => {
  // Plans must load before the calendar so we know which plan is active.
  // Once selectedPlanId is set, loadMonth uses it.
  await loadPlans()
  await Promise.all([loadMonth(), loadGroups(), loadLeaderGroups()])
})
</script>
