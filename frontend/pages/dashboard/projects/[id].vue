<template>
  <div class="space-y-6">
    <Breadcrumb
      :items="[
        { label: 'Dashboard', to: '/dashboard' },
        { label: 'Prosjekter', to: '/dashboard/projects' },
        { label: project?.name || '…' },
      ]"
    />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white truncate">
            {{ project?.name || 'Prosjekt' }}
          </h1>
          <UBadge v-if="project" color="neutral" variant="subtle" class="font-mono shrink-0">
            {{ project.identifier }}
          </UBadge>
          <UBadge v-if="project?.is_archived" color="warning" variant="subtle" class="shrink-0">
            Arkivert
          </UBadge>
        </div>
        <p v-if="project?.description" class="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
          {{ project.description }}
        </p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <!-- View toggle -->
        <div class="flex rounded-lg border border-gray-200 dark:border-gray-700 p-0.5">
          <UButton
            :color="viewMode === 'board' ? 'primary' : 'neutral'"
            :variant="viewMode === 'board' ? 'soft' : 'ghost'"
            size="sm"
            icon="i-heroicons-view-columns"
            @click="setView('board')"
          >
            Tavle
          </UButton>
          <UButton
            :color="viewMode === 'list' ? 'primary' : 'neutral'"
            :variant="viewMode === 'list' ? 'soft' : 'ghost'"
            size="sm"
            icon="i-heroicons-list-bullet"
            @click="setView('list')"
          >
            Liste
          </UButton>
        </div>
        <UButton v-if="canEdit" color="primary" icon="i-heroicons-plus" @click="openCreateItem()">
          Ny sak
        </UButton>
        <UDropdownMenu v-if="projectMenuItems.length" :items="projectMenuItems">
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-heroicons-ellipsis-vertical"
            aria-label="Prosjektmeny"
          />
        </UDropdownMenu>
      </div>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <UInput
          v-model="search"
          icon="i-heroicons-magnifying-glass"
          placeholder="Søk i saker…"
          class="w-full"
        />
        <USelectMenu
          v-model="selectedStateFilter"
          :items="stateFilterOptions"
          placeholder="Alle statuser"
          @update:model-value="onFilterChange"
        />
        <USelectMenu
          v-model="selectedPriority"
          :items="priorityFilterOptions"
          placeholder="Alle prioriteter"
          @update:model-value="onFilterChange"
        />
        <USelectMenu
          v-model="selectedLabel"
          :items="labelFilterOptions"
          placeholder="Alle etiketter"
          @update:model-value="onFilterChange"
        />
        <USelectMenu
          v-model="selectedCycle"
          :items="cycleFilterOptions"
          placeholder="Alle sykluser"
          @update:model-value="onFilterChange"
        />
        <USelectMenu
          v-model="selectedModule"
          :items="moduleFilterOptions"
          placeholder="Alle moduler"
          @update:model-value="onFilterChange"
        />
        <USelectMenu
          v-model="selectedAssignee"
          :items="assigneeFilterOptions"
          placeholder="Alle ansvarlige"
          @update:model-value="onFilterChange"
        />
      </div>
    </UCard>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <!-- Board mode -->
    <div v-else-if="viewMode === 'board'" class="flex gap-4 overflow-x-auto pb-4">
      <div
        v-for="col in visibleColumns"
        :key="col.state.id"
        class="w-72 shrink-0 rounded-lg bg-gray-50 dark:bg-gray-800/50 p-2"
      >
        <div class="flex items-center gap-2 px-1 py-2">
          <span
            class="w-2.5 h-2.5 rounded-full shrink-0"
            :style="{ backgroundColor: col.state.color || '#9CA3AF' }"
          />
          <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
            {{ col.state.name }}
          </span>
          <UBadge color="neutral" variant="subtle" size="sm">{{ col.total }}</UBadge>
          <UButton
            v-if="canEdit"
            color="neutral"
            variant="ghost"
            size="xs"
            icon="i-heroicons-plus"
            class="ml-auto"
            aria-label="Ny sak i denne statusen"
            @click="openCreateItem(col.state.id)"
          />
        </div>
        <div class="space-y-2">
          <WorkItemCard
            v-for="it in col.items"
            :key="it.id"
            :item="it"
            :project="project"
            @open="openItem"
            @change-state="moveItem"
          />
          <p v-if="!col.items.length" class="px-1 py-3 text-xs text-gray-400 dark:text-gray-500">
            Ingen saker
          </p>
        </div>
      </div>
    </div>

    <!-- List mode -->
    <template v-else>
      <UCard v-if="items.length === 0" class="text-center py-12">
        <UIcon name="i-heroicons-rectangle-stack" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p class="text-gray-500">Ingen saker funnet.</p>
      </UCard>
      <UCard v-else :ui="{ body: 'p-0 sm:p-0' }">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="text-left py-3 px-4 font-medium text-gray-500">ID</th>
                <th class="text-left py-3 px-4 font-medium text-gray-500">Navn</th>
                <th class="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                <th class="text-left py-3 px-4 font-medium text-gray-500">Prioritet</th>
                <th class="text-left py-3 px-4 font-medium text-gray-500">Frist</th>
                <th class="text-left py-3 px-4 font-medium text-gray-500">Ansvarlig</th>
                <th class="text-right py-3 px-4 font-medium text-gray-500">Underoppgaver</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="it in items"
                :key="it.id"
                class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer"
                @click="openItem(it)"
              >
                <td class="py-3 px-4 font-mono text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  {{ it.identifier }}
                </td>
                <td class="py-3 px-4 text-gray-900 dark:text-white">
                  <span v-if="it.parent_identifier" class="text-gray-400 mr-1">↳</span>
                  {{ it.name }}
                </td>
                <td class="py-3 px-4 whitespace-nowrap">
                  <span class="inline-flex items-center gap-1.5">
                    <span
                      class="w-2 h-2 rounded-full"
                      :style="{ backgroundColor: it.state?.color || '#9CA3AF' }"
                    />
                    <span class="text-gray-700 dark:text-gray-300">{{ it.state?.name || '—' }}</span>
                  </span>
                </td>
                <td class="py-3 px-4 whitespace-nowrap">
                  <UBadge
                    v-if="it.priority && it.priority !== 'none'"
                    :color="priorityMeta(it.priority).color"
                    :icon="priorityMeta(it.priority).icon"
                    variant="subtle"
                    size="sm"
                  >
                    {{ priorityMeta(it.priority).label }}
                  </UBadge>
                </td>
                <td
                  class="py-3 px-4 whitespace-nowrap"
                  :class="isOverdue(it) ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-gray-400'"
                >
                  {{ it.target_date ? formatDate(it.target_date) : '' }}
                </td>
                <td class="py-3 px-4">
                  <span v-if="it.assignees?.length" class="flex -space-x-1">
                    <UAvatar
                      v-for="a in it.assignees.slice(0, 3)"
                      :key="a.id"
                      :alt="a.display_name"
                      size="2xs"
                      :title="a.display_name"
                    />
                    <span
                      v-if="it.assignees.length > 3"
                      class="flex items-center justify-center w-5 h-5 rounded-full bg-gray-200 dark:bg-gray-700 text-[10px]"
                    >
                      +{{ it.assignees.length - 3 }}
                    </span>
                  </span>
                </td>
                <td class="py-3 px-4 text-right text-gray-500 dark:text-gray-400">
                  {{ it.sub_item_count || '' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>
      <div v-if="total > limit" class="flex justify-center">
        <UPagination
          v-model="page"
          :total="total"
          :items-per-page="limit"
          @update:model-value="loadData()"
        />
      </div>
    </template>

    <!-- Work item detail -->
    <WorkItemDetailSlideover
      v-model:open="detailOpen"
      :item-id="selectedItemId"
      :project="project"
      @updated="onItemMutated"
      @deleted="onItemMutated"
    />

    <!-- Create work item modal -->
    <UModal v-model:open="createItemOpen" :ui="{ content: 'max-w-xl' }">
      <template #content>
        <div class="p-6 space-y-4 max-h-[85vh] overflow-y-auto">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">Ny sak</h2>

          <UFormField label="Navn" required>
            <UInput
              v-model="itemForm.name"
              placeholder="Hva skal gjøres?"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </UFormField>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField label="Status">
              <USelectMenu v-model="itemForm.state" :items="stateOptions" class="w-full" />
            </UFormField>
            <UFormField label="Prioritet">
              <USelectMenu v-model="itemForm.priority" :items="PRIORITY_OPTIONS" class="w-full" />
            </UFormField>
            <UFormField label="Startdato">
              <UInput v-model="itemForm.startDate" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Frist">
              <UInput v-model="itemForm.targetDate" type="date" class="w-full" />
            </UFormField>
          </div>

          <UFormField label="Overordnet sak">
            <USelectMenu
              v-model="itemForm.parent"
              :items="parentOptions"
              placeholder="Ingen"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Etiketter">
            <USelectMenu
              v-model="itemForm.labels"
              :items="labelOptions"
              multiple
              placeholder="Ingen etiketter"
              class="w-full"
            />
          </UFormField>

          <div v-if="itemFormError" class="text-sm text-red-600 dark:text-red-400">
            {{ itemFormError }}
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <UButton color="neutral" variant="ghost" @click="createItemOpen = false">Avbryt</UButton>
            <UButton color="primary" :loading="savingItem" @click="saveItem">Lagre</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Edit project modal -->
    <UModal v-model:open="editProjectOpen" :ui="{ content: 'max-w-xl' }">
      <template #content>
        <div class="p-6 space-y-4 max-h-[85vh] overflow-y-auto">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">Rediger prosjekt</h2>

          <UFormField label="Navn" required>
            <UInput v-model="projectForm.name" class="w-full" :ui="{ base: 'w-full' }" />
          </UFormField>

          <UFormField label="Beskrivelse">
            <UTextarea
              v-model="projectForm.description"
              :rows="3"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </UFormField>

          <UCheckbox v-model="projectForm.is_archived" label="Arkivert" />

          <div v-if="projectFormError" class="text-sm text-red-600 dark:text-red-400">
            {{ projectFormError }}
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <UButton color="neutral" variant="ghost" @click="editProjectOpen = false">Avbryt</UButton>
            <UButton color="primary" :loading="savingProject" @click="saveProject">Lagre</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import WorkItemCard from '~/components/projects/WorkItemCard.vue'
import WorkItemDetailSlideover from '~/components/projects/WorkItemDetailSlideover.vue'

definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const route = useRoute()
const { canEdit, isAdmin } = usePermissions()

const projectId = computed(() => parseInt(route.params.id as string))

const project = ref<any | null>(null)
const loading = ref(true)
const viewMode = ref<'board' | 'list'>('board')

// Board data
const columns = ref<any[]>([])
// List data
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const limit = 20

// Filters
const search = ref('')
const selectedStateFilter = ref<any>(null)
const selectedPriority = ref<any>(null)
const selectedLabel = ref<any>(null)
const selectedCycle = ref<any>(null)
const selectedModule = ref<any>(null)
const selectedAssignee = ref<any>(null)
// Distinct assignee names accumulated across loads (so an active assignee
// filter doesn't shrink its own option list).
const assigneeNames = ref<Set<string>>(new Set())

// Detail slideover
const detailOpen = ref(false)
const selectedItemId = ref<number | null>(null)

// Create item modal
const createItemOpen = ref(false)
const savingItem = ref(false)
const itemFormError = ref('')
const itemForm = ref<any>({
  name: '',
  state: null,
  priority: null,
  parent: null,
  startDate: '',
  targetDate: '',
  labels: [],
})

// Edit project modal
const editProjectOpen = ref(false)
const savingProject = ref(false)
const projectFormError = ref('')
const projectForm = ref({ name: '', description: '', is_archived: false })

// ---- options ---------------------------------------------------------------

const stateOptions = computed(() =>
  (project.value?.states || []).map((s: any) => ({ label: s.name, value: s.id }))
)
const labelOptions = computed(() =>
  (project.value?.labels || []).map((l: any) => ({ label: l.name, value: l.id }))
)
const stateFilterOptions = computed(() => [
  { label: 'Alle statuser', value: '' },
  ...stateOptions.value,
])
const priorityFilterOptions = [{ label: 'Alle prioriteter', value: '' }, ...PRIORITY_OPTIONS]
const labelFilterOptions = computed(() => [
  { label: 'Alle etiketter', value: '' },
  ...labelOptions.value,
])
const cycleFilterOptions = computed(() => [
  { label: 'Alle sykluser', value: '' },
  ...(project.value?.cycles || []).map((c: any) => ({ label: c.name, value: c.id })),
])
const moduleFilterOptions = computed(() => [
  { label: 'Alle moduler', value: '' },
  ...(project.value?.modules || []).map((m: any) => ({ label: m.name, value: m.id })),
])
const assigneeFilterOptions = computed(() => [
  { label: 'Alle ansvarlige', value: '' },
  ...[...assigneeNames.value].sort((a, b) => a.localeCompare(b, 'nb')).map((n) => ({
    label: n,
    value: n,
  })),
])

const allLoadedItems = computed(() =>
  viewMode.value === 'board' ? columns.value.flatMap((c: any) => c.items || []) : items.value
)

const parentOptions = computed(() => [
  { label: 'Ingen', value: '' },
  ...allLoadedItems.value
    .filter((it: any) => !it.parent_id)
    .map((it: any) => ({ label: `${it.identifier} ${it.name}`, value: it.id })),
])

// In board mode the state filter narrows which columns are shown (the board
// endpoint is already grouped by state, so this is purely client-side).
const visibleColumns = computed(() => {
  if (!selectedStateFilter.value?.value) return columns.value
  return columns.value.filter((c: any) => c.state.id === selectedStateFilter.value.value)
})

const projectMenuItems = computed(() => {
  const menu: any[] = []
  if (canEdit.value) {
    menu.push({ label: 'Rediger prosjekt', icon: 'i-heroicons-pencil-square', onSelect: openEditProject })
  }
  if (isAdmin.value) {
    menu.push({ label: 'Slett prosjekt', icon: 'i-heroicons-trash', color: 'error', onSelect: removeProject })
  }
  return menu
})

// ---- loading -----------------------------------------------------------------

const buildFilterParams = () => {
  const params: Record<string, any> = {}
  if (search.value.trim()) params.search = search.value.trim()
  if (selectedPriority.value?.value) params.priority = selectedPriority.value.value
  if (selectedLabel.value?.value) params.label_id = String(selectedLabel.value.value)
  if (selectedCycle.value?.value) params.cycle_id = String(selectedCycle.value.value)
  if (selectedModule.value?.value) params.module_id = String(selectedModule.value.value)
  if (selectedAssignee.value?.value) params.assignee = selectedAssignee.value.value
  return params
}

const collectAssigneeNames = () => {
  for (const it of allLoadedItems.value) {
    for (const a of it.assignees || []) {
      if (a.display_name) assigneeNames.value.add(a.display_name)
    }
  }
  // Reassign to trigger reactivity on the Set
  assigneeNames.value = new Set(assigneeNames.value)
}

const loadProject = async () => {
  try {
    project.value = await api.getProject(projectId.value)
  } catch (err) {
    console.error('Failed to load project:', err)
    toast.add({ title: 'Prosjektet ble ikke funnet', color: 'error' })
    navigateTo('/dashboard/projects')
  }
}

const loadData = async (soft = false) => {
  if (!soft) loading.value = true
  try {
    if (viewMode.value === 'board') {
      const data: any = await api.getProjectBoard(projectId.value, buildFilterParams())
      columns.value = data.columns || []
    } else {
      const params = {
        ...buildFilterParams(),
        skip: String((page.value - 1) * limit),
        limit: String(limit),
      }
      if (selectedStateFilter.value?.value) params.state_id = String(selectedStateFilter.value.value)
      const data: any = await api.getProjectWorkItems(projectId.value, params)
      items.value = data.items || []
      total.value = data.total || 0
    }
    collectAssigneeNames()
  } catch (err) {
    console.error('Failed to load work items:', err)
  } finally {
    loading.value = false
  }
}

const setView = (mode: 'board' | 'list') => {
  if (viewMode.value === mode) return
  viewMode.value = mode
  page.value = 1
  loadData()
}

const onFilterChange = () => {
  page.value = 1
  loadData()
}

// Debounced search (250 ms)
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadData()
  }, 250)
})

// ---- board: optimistic state move ----------------------------------------------

const moveItem = async (it: any, stateId: number) => {
  if (it.state?.id === stateId) return
  const from = columns.value.find((c: any) => c.items.some((i: any) => i.id === it.id))
  const to = columns.value.find((c: any) => c.state.id === stateId)
  if (!from || !to) return
  const idx = from.items.findIndex((i: any) => i.id === it.id)
  const [moved] = from.items.splice(idx, 1)
  from.total--
  const prevState = moved.state
  moved.state = to.state
  to.items.push(moved)
  to.total++
  try {
    await api.updateWorkItem(it.id, { state_id: stateId })
  } catch (err) {
    // Roll the card back to its original column
    const backIdx = to.items.findIndex((i: any) => i.id === it.id)
    if (backIdx !== -1) to.items.splice(backIdx, 1)
    to.total--
    moved.state = prevState
    from.items.splice(idx, 0, moved)
    from.total++
    toast.add({ title: 'Kunne ikke flytte saken', color: 'error' })
  }
}

// ---- detail slideover -------------------------------------------------------------

const openItem = (it: any) => {
  selectedItemId.value = it.id
  detailOpen.value = true
}

const onItemMutated = () => {
  loadData(true)
  loadProject()
}

// ---- create work item ---------------------------------------------------------------

const openCreateItem = (stateId?: number) => {
  const defaultState =
    (stateId != null && stateOptions.value.find((o: any) => o.value === stateId)) ||
    stateOptions.value.find((o: any) => {
      const s = (project.value?.states || []).find((st: any) => st.id === o.value)
      return s?.is_default
    }) ||
    stateOptions.value[0] ||
    null
  itemForm.value = {
    name: '',
    state: defaultState,
    priority: PRIORITY_OPTIONS.find((o) => o.value === 'none') || null,
    parent: null,
    startDate: '',
    targetDate: '',
    labels: [],
  }
  itemFormError.value = ''
  createItemOpen.value = true
}

const saveItem = async () => {
  itemFormError.value = ''
  if (!itemForm.value.name.trim()) {
    itemFormError.value = 'Navn er påkrevd'
    return
  }
  savingItem.value = true
  try {
    await api.createWorkItem(projectId.value, {
      name: itemForm.value.name.trim(),
      state_id: itemForm.value.state?.value || null,
      priority: itemForm.value.priority?.value || 'none',
      parent_id: itemForm.value.parent?.value || null,
      start_date: itemForm.value.startDate || null,
      target_date: itemForm.value.targetDate || null,
      label_ids: itemForm.value.labels.map((o: any) => o.value),
    })
    toast.add({ title: 'Sak opprettet', color: 'success' })
    createItemOpen.value = false
    await loadData(true)
    loadProject()
  } catch (err: any) {
    itemFormError.value = err?.data?.detail || 'Kunne ikke opprette saken'
  } finally {
    savingItem.value = false
  }
}

// ---- edit / delete project -------------------------------------------------------------

const openEditProject = () => {
  projectForm.value = {
    name: project.value?.name || '',
    description: project.value?.description || '',
    is_archived: Boolean(project.value?.is_archived),
  }
  projectFormError.value = ''
  editProjectOpen.value = true
}

const saveProject = async () => {
  projectFormError.value = ''
  if (!projectForm.value.name.trim()) {
    projectFormError.value = 'Navn er påkrevd'
    return
  }
  savingProject.value = true
  try {
    project.value = await api.updateProject(projectId.value, {
      name: projectForm.value.name.trim(),
      description: projectForm.value.description.trim() || null,
      is_archived: projectForm.value.is_archived,
    })
    toast.add({ title: 'Prosjekt oppdatert', color: 'success' })
    editProjectOpen.value = false
  } catch (err: any) {
    projectFormError.value = err?.data?.detail || 'Kunne ikke oppdatere prosjektet'
  } finally {
    savingProject.value = false
  }
}

const removeProject = async () => {
  if (!project.value) return
  if (
    !confirm(`Slette prosjektet «${project.value.name}» og alle saker? Dette kan ikke angres.`)
  ) {
    return
  }
  try {
    await api.deleteProject(projectId.value)
    toast.add({ title: 'Prosjekt slettet', color: 'success' })
    navigateTo('/dashboard/projects')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke slette prosjektet',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

// ---- formatting ---------------------------------------------------------------------------

const formatDate = (d: string) => new Date(d).toLocaleDateString('nb-NO')

const isOverdue = (it: any) => {
  if (!it.target_date || it.state?.group === 'completed') return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return new Date(it.target_date) < today
}

onMounted(async () => {
  await loadProject()
  await loadData()
})
</script>
