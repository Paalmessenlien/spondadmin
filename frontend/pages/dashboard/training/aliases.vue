<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Training plan', to: '/dashboard/training' },
      { label: 'Aliases' }
    ]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Training aliases</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Map vaktliste initials to members. Unresolved shifts will be fixed once an alias is set.
        </p>
      </div>
      <UButton v-if="canEdit" icon="i-heroicons-plus" @click="openCreateAlias">
        New alias
      </UButton>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-gray-700">
      <nav class="flex gap-4 -mb-px">
        <button
          type="button"
          :class="tabClasses('aliases')"
          @click="activeTab = 'aliases'"
        >
          Aliases
          <UBadge color="neutral" variant="subtle" size="sm" class="ml-1">{{ aliases.length }}</UBadge>
        </button>
        <button
          type="button"
          :class="tabClasses('unresolved')"
          @click="activeTab = 'unresolved'"
        >
          Unresolved
          <UBadge
            :color="unresolvedGroups.length > 0 ? 'warning' : 'neutral'"
            variant="subtle"
            size="sm"
            class="ml-1"
          >
            {{ unresolvedGroups.length }}
          </UBadge>
        </button>
      </nav>
    </div>

    <!-- Aliases tab -->
    <UCard v-if="activeTab === 'aliases'">
      <div v-if="loadingAliases" class="flex justify-center py-12">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>
      <div v-else-if="aliases.length === 0" class="text-center py-12 text-gray-500">
        No aliases yet. Import a vaktliste or add one manually.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-3 px-4 font-medium text-gray-500">Initials</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Member</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Source</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Created</th>
              <th class="text-right py-3 px-4 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="alias in aliases"
              :key="alias.id"
              class="border-b border-gray-100 dark:border-gray-800"
            >
              <td class="py-3 px-4 font-mono font-medium">{{ alias.initials }}</td>
              <td class="py-3 px-4">
                <template v-if="alias.member">
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ alias.member.first_name }} {{ alias.member.last_name }}
                  </div>
                  <div class="text-xs text-gray-500 font-mono">{{ alias.member.spond_id }}</div>
                </template>
                <span v-else class="text-gray-400">—</span>
              </td>
              <td class="py-3 px-4">
                <UBadge :color="sourceColor(alias.source)" variant="subtle" size="sm">
                  {{ alias.source }}
                </UBadge>
              </td>
              <td class="py-3 px-4 text-gray-500 text-xs">{{ formatDate(alias.created_at) }}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex justify-end gap-1">
                  <UButton
                    v-if="canEdit"
                    color="neutral"
                    variant="ghost"
                    icon="i-heroicons-pencil-square"
                    size="xs"
                    aria-label="Edit alias"
                    @click="openEditAlias(alias)"
                  />
                  <UButton
                    v-if="canEdit"
                    color="red"
                    variant="ghost"
                    icon="i-heroicons-trash"
                    size="xs"
                    aria-label="Delete alias"
                    @click="confirmDelete(alias)"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <!-- Unresolved tab -->
    <UCard v-else>
      <div v-if="loadingUnresolved" class="flex justify-center py-12">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>
      <div v-else-if="unresolvedGroups.length === 0" class="text-center py-12">
        <UIcon name="i-heroicons-check-circle" class="w-12 h-12 mx-auto mb-3 text-green-500" />
        <p class="text-gray-700 dark:text-gray-300 font-medium">All initials resolved</p>
        <p class="text-sm text-gray-500 mt-1">No draft shifts have unmapped initials.</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-3 px-4 font-medium text-gray-500">Initials</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Shifts affected</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Sample dates</th>
              <th class="text-right py-3 px-4 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="grp in unresolvedGroups"
              :key="grp.initials"
              class="border-b border-gray-100 dark:border-gray-800"
            >
              <td class="py-3 px-4 font-mono font-medium text-amber-700">{{ grp.initials }}</td>
              <td class="py-3 px-4">{{ grp.shifts.length }}</td>
              <td class="py-3 px-4 text-xs text-gray-500">
                {{ grp.shifts.slice(0, 3).map((s: any) => s.date).join(', ') }}
                <span v-if="grp.shifts.length > 3">… +{{ grp.shifts.length - 3 }}</span>
              </td>
              <td class="py-3 px-4 text-right">
                <UButton
                  v-if="canEdit"
                  size="xs"
                  icon="i-heroicons-user-plus"
                  @click="openAssignFromUnresolved(grp)"
                >
                  Assign member
                </UButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <!-- Create/Edit alias modal -->
    <UModal v-model:open="aliasModalOpen">
      <template #content>
        <div class="p-6 space-y-4">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ editingAlias ? 'Edit alias' : 'New alias' }}
          </h2>

          <form class="space-y-4" @submit.prevent="handleSaveAlias">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Initials</label>
              <UInput
                v-model="aliasForm.initials"
                placeholder="e.g. PM"
                :disabled="lockInitials"
                required
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Member</label>
              <UInput
                v-model="memberSearch"
                placeholder="Search members…"
                icon="i-heroicons-magnifying-glass"
                @input="debouncedSearchMembers"
              />
              <div class="mt-2 max-h-48 overflow-y-auto rounded border border-gray-200 dark:border-gray-700">
                <button
                  v-for="m in memberResults"
                  :key="m.id"
                  type="button"
                  :class="[
                    'w-full text-left px-3 py-2 text-sm border-b border-gray-100 dark:border-gray-800 last:border-b-0',
                    aliasForm.member_id === m.id
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800',
                  ]"
                  @click="aliasForm.member_id = m.id; selectedMemberLabel = `${m.first_name} ${m.last_name}`"
                >
                  {{ m.first_name }} {{ m.last_name }}
                </button>
                <div v-if="memberResults.length === 0" class="text-xs text-gray-500 px-3 py-2">
                  Type to search members…
                </div>
              </div>
              <div v-if="selectedMemberLabel" class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Selected: <strong>{{ selectedMemberLabel }}</strong>
              </div>
            </div>

            <div v-if="aliasFormError" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-3">
              {{ aliasFormError }}
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <UButton color="neutral" variant="outline" @click="aliasModalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="savingAlias" icon="i-heroicons-check">
                {{ assigningFromUnresolved ? 'Assign & resolve shifts' : (editingAlias ? 'Save' : 'Create alias') }}
              </UButton>
            </div>
          </form>
        </div>
      </template>
    </UModal>

    <!-- Delete confirm -->
    <UModal v-model:open="deleteModalOpen">
      <template #content>
        <div class="p-6 space-y-4">
          <h2 class="text-lg font-bold text-red-600">Delete alias?</h2>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            This won't change any existing shifts. Future imports will treat
            <strong class="font-mono">{{ deletingAlias?.initials }}</strong> as unresolved again.
          </p>
          <div class="flex justify-end gap-2">
            <UButton color="neutral" variant="outline" @click="deleteModalOpen = false">Cancel</UButton>
            <UButton color="red" :loading="deletingInProgress" @click="handleDelete">Delete</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const toast = useToast()
const { canEdit } = usePermissions()

interface MemberSummary {
  id: number
  spond_id: string
  first_name: string
  last_name: string
}

interface Alias {
  id: number
  member_id: number
  initials: string
  source: string
  member: MemberSummary | null
  created_at: string
  updated_at: string
}

interface UnresolvedShift {
  id: number
  date: string
  raw_initials: string
  session_type_id: number
}

interface UnresolvedGroup {
  initials: string
  shifts: UnresolvedShift[]
}

const activeTab = ref<'aliases' | 'unresolved'>(
  route.query.showUnresolved === '1' ? 'unresolved' : 'aliases'
)

const aliases = ref<Alias[]>([])
const unresolvedGroups = ref<UnresolvedGroup[]>([])
const loadingAliases = ref(true)
const loadingUnresolved = ref(true)

const aliasModalOpen = ref(false)
const deleteModalOpen = ref(false)
const editingAlias = ref<Alias | null>(null)
const deletingAlias = ref<Alias | null>(null)
const savingAlias = ref(false)
const deletingInProgress = ref(false)
const aliasFormError = ref('')
const lockInitials = ref(false)
const assigningFromUnresolved = ref<UnresolvedGroup | null>(null)

const aliasForm = ref<{ initials: string; member_id: number | null }>({
  initials: '',
  member_id: null,
})

const memberSearch = ref('')
const memberResults = ref<MemberSummary[]>([])
const selectedMemberLabel = ref('')

const tabClasses = (tab: string) =>
  activeTab.value === tab
    ? 'px-3 py-2 text-sm font-medium border-b-2 border-blue-600 text-blue-600 dark:text-blue-400 flex items-center'
    : 'px-3 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center'

const sourceColor = (s: string) => {
  switch (s) {
    case 'vaktliste': return 'info'
    case 'manual': return 'success'
    case 'auto': return 'warning'
    default: return 'neutral'
  }
}

const formatDate = (s: string) => {
  if (!s) return '—'
  return new Date(s).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

const loadAliases = async () => {
  loadingAliases.value = true
  try {
    const resp = await api.getTrainingAliases()
    aliases.value = resp.items || []
  } catch (err: any) {
    console.error('Failed to load aliases:', err)
  } finally {
    loadingAliases.value = false
  }
}

const loadUnresolved = async () => {
  loadingUnresolved.value = true
  try {
    const resp = await api.getTrainingShifts({ status: 'draft', limit: 1000 })
    const items: any[] = resp.items || []
    const grouped: Record<string, UnresolvedShift[]> = {}
    for (const s of items) {
      if (s.raw_initials && !s.leader_member_id) {
        if (!grouped[s.raw_initials]) grouped[s.raw_initials] = []
        grouped[s.raw_initials].push({
          id: s.id,
          date: s.date,
          raw_initials: s.raw_initials,
          session_type_id: s.session_type_id,
        })
      }
    }
    unresolvedGroups.value = Object.entries(grouped)
      .map(([initials, shifts]) => ({ initials, shifts }))
      .sort((a, b) => a.initials.localeCompare(b.initials))
  } catch (err: any) {
    console.error('Failed to load unresolved:', err)
  } finally {
    loadingUnresolved.value = false
  }
}

let memberSearchTimer: ReturnType<typeof setTimeout> | null = null
const debouncedSearchMembers = () => {
  if (memberSearchTimer) clearTimeout(memberSearchTimer)
  memberSearchTimer = setTimeout(searchMembers, 250)
}

const searchMembers = async () => {
  try {
    const params: Record<string, any> = { limit: 30 }
    if (memberSearch.value.trim()) params.search = memberSearch.value.trim()
    const response: any = await api.getMembers(params)
    memberResults.value = response.members || []
  } catch (err) {
    console.error('Member search failed:', err)
  }
}

const openCreateAlias = () => {
  editingAlias.value = null
  assigningFromUnresolved.value = null
  lockInitials.value = false
  aliasForm.value = { initials: '', member_id: null }
  selectedMemberLabel.value = ''
  aliasFormError.value = ''
  memberResults.value = []
  memberSearch.value = ''
  aliasModalOpen.value = true
}

const openEditAlias = (alias: Alias) => {
  editingAlias.value = alias
  assigningFromUnresolved.value = null
  lockInitials.value = true
  aliasForm.value = { initials: alias.initials, member_id: alias.member_id }
  selectedMemberLabel.value = alias.member
    ? `${alias.member.first_name} ${alias.member.last_name}`
    : ''
  aliasFormError.value = ''
  memberResults.value = alias.member ? [alias.member as any] : []
  memberSearch.value = ''
  aliasModalOpen.value = true
}

const openAssignFromUnresolved = (grp: UnresolvedGroup) => {
  editingAlias.value = null
  assigningFromUnresolved.value = grp
  lockInitials.value = true
  aliasForm.value = { initials: grp.initials, member_id: null }
  selectedMemberLabel.value = ''
  aliasFormError.value = ''
  memberResults.value = []
  memberSearch.value = ''
  aliasModalOpen.value = true
}

const confirmDelete = (alias: Alias) => {
  deletingAlias.value = alias
  deleteModalOpen.value = true
}

const handleSaveAlias = async () => {
  if (!aliasForm.value.initials.trim() || !aliasForm.value.member_id) {
    aliasFormError.value = 'Initials and member are required'
    return
  }
  savingAlias.value = true
  aliasFormError.value = ''
  try {
    if (editingAlias.value) {
      await api.updateTrainingAlias(editingAlias.value.id, {
        member_id: aliasForm.value.member_id,
      })
    } else {
      await api.createTrainingAlias({
        initials: aliasForm.value.initials.trim(),
        member_id: aliasForm.value.member_id,
        source: 'manual',
      })
    }

    // If assigning from unresolved, also patch the affected shifts
    if (assigningFromUnresolved.value) {
      const grp = assigningFromUnresolved.value
      const memberId = aliasForm.value.member_id
      const failures: string[] = []
      for (const sh of grp.shifts) {
        try {
          await api.updateTrainingShift(sh.id, {
            leader_member_id: memberId,
            raw_initials: null,
          })
        } catch (e: any) {
          failures.push(`#${sh.id}`)
        }
      }
      const resolved = grp.shifts.length - failures.length
      toast.add({
        title: 'Alias assigned',
        description: failures.length
          ? `${resolved}/${grp.shifts.length} shifts updated. Failed: ${failures.join(', ')}`
          : `${resolved} shifts updated`,
        color: failures.length ? 'warning' : 'success',
      })
    } else {
      toast.add({ title: 'Saved', description: 'Alias saved', color: 'success' })
    }

    aliasModalOpen.value = false
    await Promise.all([loadAliases(), loadUnresolved()])
  } catch (err: any) {
    aliasFormError.value = err?.data?.detail || err?.message || 'Failed to save alias'
  } finally {
    savingAlias.value = false
  }
}

const handleDelete = async () => {
  if (!deletingAlias.value) return
  deletingInProgress.value = true
  try {
    await api.deleteTrainingAlias(deletingAlias.value.id)
    toast.add({ title: 'Deleted', description: 'Alias removed', color: 'success' })
    deleteModalOpen.value = false
    await loadAliases()
  } catch (err: any) {
    toast.add({
      title: 'Delete failed',
      description: err?.data?.detail || 'Could not delete alias',
      color: 'error',
    })
  } finally {
    deletingInProgress.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadAliases(), loadUnresolved()])
})
</script>
