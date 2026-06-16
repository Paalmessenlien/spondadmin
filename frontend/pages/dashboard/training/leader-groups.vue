<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Training plan', to: '/dashboard/training' },
      { label: 'Leader groups' }
    ]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Leader groups</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Named pools of members who can lead training shifts. Bind a group to a session type to
          narrow the leader picker.
        </p>
      </div>
      <UButton v-if="isAdmin" icon="i-heroicons-plus" @click="openNewGroup">
        New leader group
      </UButton>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <UCard v-else-if="leaderGroups.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-user-group" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-700 dark:text-gray-300 font-medium">No leader groups yet</p>
      <p class="text-sm text-gray-500 mt-1">
        Create one to bundle members who can lead training shifts.
      </p>
      <div v-if="isAdmin" class="mt-4">
        <UButton icon="i-heroicons-plus" @click="openNewGroup">New leader group</UButton>
      </div>
    </UCard>

    <div v-else class="space-y-4">
      <UCard
        v-for="g in leaderGroups"
        :key="g.id"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ g.name }}</h2>
            <p v-if="g.description" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {{ g.description }}
            </p>
            <p class="text-xs text-gray-500 mt-1">
              {{ g.members.length }} member{{ g.members.length === 1 ? '' : 's' }}
            </p>
          </div>
          <div v-if="isAdmin" class="flex gap-2 shrink-0">
            <UButton
              size="sm"
              color="neutral"
              variant="soft"
              icon="i-heroicons-pencil-square"
              @click="openEditGroup(g)"
            >
              Edit
            </UButton>
            <UButton
              size="sm"
              color="red"
              variant="soft"
              icon="i-heroicons-trash"
              @click="confirmDelete(g)"
            >
              Delete
            </UButton>
          </div>
        </div>

        <!-- Member pills -->
        <div v-if="g.members.length > 0" class="mt-4 flex flex-wrap gap-1.5">
          <span
            v-for="m in g.members"
            :key="m.id"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs"
          >
            {{ m.first_name }} {{ m.last_name }}
            <button
              v-if="isAdmin"
              type="button"
              class="ml-1 text-blue-500 hover:text-blue-700"
              aria-label="Remove member"
              @click="removeMember(g, m.id)"
            >
              ×
            </button>
          </span>
        </div>

        <!-- Add member -->
        <div v-if="isAdmin" class="mt-3 max-w-md">
          <UInput
            v-model="g._search"
            placeholder="Add member…"
            icon="i-heroicons-magnifying-glass"
            size="sm"
            class="w-full"
            :ui="{ base: 'w-full' }"
            @input="onSearchInput(g)"
          />
          <!-- Results rendered inline so they push the card content down
               instead of overflowing UCard's rounded corner clip. -->
          <div
            v-if="g._search?.trim() && g._results && g._results.length > 0"
            class="mt-1 max-h-56 overflow-y-auto rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm"
          >
            <button
              v-for="m in g._results"
              :key="m.id"
              type="button"
              class="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="addMember(g, m)"
            >
              {{ m.first_name }} {{ m.last_name }}
            </button>
          </div>
          <p
            v-else-if="g._search?.trim() && g._results && g._results.length === 0"
            class="mt-1 text-xs text-gray-500"
          >
            No matches.
          </p>
        </div>
      </UCard>
    </div>

    <!-- New / edit leader group modal -->
    <UModal v-model:open="editorOpen" :ui="{ content: 'max-w-xl' }">
      <template #content>
        <div v-if="draft" class="p-6 space-y-4 max-h-[85vh] overflow-y-auto">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ draft.id ? 'Edit leader group' : 'New leader group' }}
          </h2>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <UInput
              v-model="draft.name"
              placeholder="e.g. Wednesday leaders"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
            <UTextarea
              v-model="draft.description"
              :rows="3"
              placeholder="Optional notes about this pool of leaders."
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <div class="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <UButton color="neutral" variant="outline" @click="editorOpen = false">
              Cancel
            </UButton>
            <UButton
              icon="i-heroicons-check"
              :loading="saving"
              :disabled="!draft.name?.trim()"
              @click="saveDraft"
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
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const { isAdmin } = usePermissions()

interface MemberRow {
  id: number
  first_name: string
  last_name: string
}

interface LeaderGroupRow {
  id: number
  name: string
  description: string | null
  members: MemberRow[]
  _search?: string
  _results?: MemberRow[]
  _searchTimer?: ReturnType<typeof setTimeout> | null
}

const leaderGroups = ref<LeaderGroupRow[]>([])
const loading = ref(true)

const editorOpen = ref(false)
const draft = ref<{ id: number | null; name: string; description: string | null } | null>(null)
const saving = ref(false)

const load = async () => {
  loading.value = true
  try {
    const resp: any = await api.getLeaderGroups()
    leaderGroups.value = (resp.items || []).map((lg: any) => ({
      id: lg.id,
      name: lg.name,
      description: lg.description || null,
      members: lg.members || [],
      _search: '',
      _results: [],
      _searchTimer: null,
    }))
  } catch (err: any) {
    toast.add({
      title: 'Load failed',
      description: err?.data?.detail || 'Could not load leader groups',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

const openNewGroup = () => {
  draft.value = { id: null, name: '', description: '' }
  editorOpen.value = true
}

const openEditGroup = (g: LeaderGroupRow) => {
  draft.value = { id: g.id, name: g.name, description: g.description || '' }
  editorOpen.value = true
}

const saveDraft = async () => {
  if (!draft.value) return
  const d = draft.value
  if (!d.name.trim()) return
  saving.value = true
  try {
    if (d.id) {
      await api.updateLeaderGroup(d.id, {
        name: d.name.trim(),
        description: d.description?.trim() ? d.description : null,
      })
      toast.add({ title: 'Saved', description: `${d.name} updated`, color: 'success' })
    } else {
      await api.createLeaderGroup({
        name: d.name.trim(),
        description: d.description?.trim() ? d.description : null,
      })
      toast.add({ title: 'Created', description: `${d.name} added`, color: 'success' })
    }
    editorOpen.value = false
    await load()
  } catch (err: any) {
    toast.add({
      title: 'Save failed',
      description: err?.data?.detail || 'Could not save leader group',
      color: 'error',
    })
  } finally {
    saving.value = false
  }
}

const confirmDelete = async (g: LeaderGroupRow) => {
  if (!confirm(`Delete leader group "${g.name}"? Session types referencing it will fall back to allowing any member.`)) return
  try {
    await api.deleteLeaderGroup(g.id)
    toast.add({ title: 'Deleted', description: `${g.name} removed`, color: 'success' })
    await load()
  } catch (err: any) {
    toast.add({
      title: 'Delete failed',
      description: err?.data?.detail || 'Could not delete leader group',
      color: 'error',
    })
  }
}

const onSearchInput = (g: LeaderGroupRow) => {
  if (g._searchTimer) clearTimeout(g._searchTimer)
  g._searchTimer = setTimeout(() => runMemberSearch(g), 250)
}

const runMemberSearch = async (g: LeaderGroupRow) => {
  const q = g._search?.trim() ?? ''
  if (!q) {
    g._results = []
    return
  }
  try {
    const resp: any = await api.getMembers({ search: q, limit: 20 })
    const existing = new Set(g.members.map(m => m.id))
    g._results = (resp.members || [])
      .filter((m: any) => !existing.has(m.id))
      .map((m: any) => ({ id: m.id, first_name: m.first_name, last_name: m.last_name }))
  } catch (err) {
    console.error('Member search failed:', err)
  }
}

const addMember = async (g: LeaderGroupRow, m: MemberRow) => {
  const newIds = [...g.members.map(x => x.id), m.id]
  try {
    const updated: any = await api.setLeaderGroupMembers(g.id, newIds)
    g.members = updated.members || []
    g._search = ''
    g._results = []
  } catch (err: any) {
    toast.add({
      title: 'Add failed',
      description: err?.data?.detail || 'Could not add member',
      color: 'error',
    })
  }
}

const removeMember = async (g: LeaderGroupRow, memberId: number) => {
  const newIds = g.members.filter(m => m.id !== memberId).map(m => m.id)
  try {
    const updated: any = await api.setLeaderGroupMembers(g.id, newIds)
    g.members = updated.members || []
  } catch (err: any) {
    toast.add({
      title: 'Remove failed',
      description: err?.data?.detail || 'Could not remove member',
      color: 'error',
    })
  }
}

onMounted(load)
</script>
