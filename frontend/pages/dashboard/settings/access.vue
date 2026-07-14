<template>
  <div class="space-y-8">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Roles & Access Groups' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Roles &amp; Access Groups</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        A <strong>role</strong> sets how much a user can do (view vs edit); its default modules apply
        to users on that role who aren't in a group. An <strong>access group</strong> bundles a role +
        a module set you can assign to many users at once.
      </p>
    </div>

    <!-- ============ ROLES ============ -->
    <section class="space-y-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Role default modules</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Which modules each role can reach by default. Admins always get every module.
        </p>
      </div>

      <div v-if="loadingRoles" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-6 w-6" />
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Admin: read-only -->
        <UCard>
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <UBadge color="red" variant="subtle" size="sm">admin</UBadge>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Full access</span>
            </div>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            <UIcon name="i-heroicons-shield-check" class="w-4 h-4 inline-block mr-1 align-text-bottom" />
            Admins have access to all modules — not configurable.
          </p>
        </UCard>

        <!-- Editable roles -->
        <UCard v-for="role in editableRoles" :key="role">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <UBadge :color="roleColor(role)" variant="subtle" size="sm">{{ role }}</UBadge>
              <span class="text-xs text-gray-500">{{ (roleModules[role] || []).length }} modules</span>
            </div>
            <UButton
              size="xs"
              :loading="savingRole === role"
              :disabled="!roleDirty(role)"
              @click="saveRole(role)"
            >
              {{ roleDirty(role) ? 'Save' : 'Saved' }}
            </UButton>
          </div>
          <ModuleCheckboxGrid
            :groups="moduleGroups"
            :selected="roleModules[role] || []"
            @toggle="key => toggleIn(roleModules[role], key)"
          />
        </UCard>
      </div>
    </section>

    <!-- ============ ACCESS GROUPS ============ -->
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Access groups</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Reusable presets. Assign a user to a group from the Admin Users page.
          </p>
        </div>
        <UButton icon="i-heroicons-plus" @click="openGroupModal()">New group</UButton>
      </div>

      <UCard>
        <div v-if="loadingGroups" class="flex justify-center py-8">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-6 w-6" />
        </div>
        <div v-else-if="groups.length === 0" class="text-center py-10 text-gray-500">
          No access groups yet. Create one to bundle a role + modules for easy assignment.
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="g in groups"
            :key="g.id"
            class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-gray-200 dark:border-gray-700 p-3"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-medium text-gray-900 dark:text-white">{{ g.name }}</span>
                <UBadge :color="roleColor(g.role)" variant="subtle" size="sm">{{ g.role }}</UBadge>
                <UBadge color="neutral" variant="subtle" size="sm">{{ g.member_count }} member{{ g.member_count === 1 ? '' : 's' }}</UBadge>
              </div>
              <p v-if="g.description" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{{ g.description }}</p>
              <div class="flex flex-wrap gap-1 mt-1.5">
                <UBadge v-for="key in g.modules" :key="key" color="neutral" variant="soft" size="sm">
                  {{ moduleLabel(key) }}
                </UBadge>
              </div>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <UButton color="neutral" variant="ghost" icon="i-heroicons-pencil-square" size="xs" @click="openGroupModal(g)" />
              <UButton color="red" variant="ghost" icon="i-heroicons-trash" size="xs" @click="confirmDeleteGroup(g)" />
            </div>
          </div>
        </div>
      </UCard>
    </section>

    <!-- Group create/edit modal -->
    <UModal v-model:open="groupModalOpen">
      <template #content>
        <div class="p-6 max-h-[85vh] overflow-y-auto">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
            {{ editingGroup ? 'Edit access group' : 'New access group' }}
          </h2>
          <form class="space-y-4" @submit.prevent="saveGroup">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
              <UInput v-model="groupForm.name" placeholder="e.g. Board, Coaches, Treasurers" required />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
              <UInput v-model="groupForm.description" placeholder="Optional" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
              <select
                v-model="groupForm.role"
                class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="admin">Admin - Full access</option>
                <option value="editor">Editor - View + modify data</option>
                <option value="kasserer">Kasserer - Review expenses (utlegg)</option>
                <option value="viewer">Viewer - Read-only</option>
              </select>
              <p class="text-xs text-gray-500 mt-1">Members inherit this role. Editing it later updates every member.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Modules</label>
              <p v-if="groupForm.role === 'admin'" class="text-sm text-gray-500 bg-blue-50 dark:bg-blue-900/20 rounded p-3">
                Admin groups grant all modules regardless of selection.
              </p>
              <ModuleCheckboxGrid
                v-else
                :groups="moduleGroups"
                :selected="groupForm.modules"
                @toggle="key => toggleIn(groupForm.modules, key)"
              />
            </div>

            <div v-if="groupError" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-3">
              {{ groupError }}
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <UButton color="neutral" variant="outline" @click="groupModalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="savingGroup">{{ editingGroup ? 'Save' : 'Create' }}</UButton>
            </div>
          </form>
        </div>
      </template>
    </UModal>

    <!-- Delete confirm -->
    <UModal v-model:open="deleteModalOpen">
      <template #content>
        <div class="p-6">
          <h2 class="text-lg font-bold text-red-600 mb-2">Delete access group</h2>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            Delete <strong>{{ deletingGroup?.name }}</strong>?
            Its {{ deletingGroup?.member_count || 0 }} member(s) will fall back to their role defaults.
          </p>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" @click="deleteModalOpen = false">Cancel</UButton>
            <UButton color="red" :loading="savingGroup" @click="doDeleteGroup">Delete</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const { canManageSystem } = usePermissions()
if (!canManageSystem.value) navigateTo('/dashboard')

const api = useApi()
const toast = useToast()

interface ModuleDef { key: string; label: string; group: string }

const moduleRegistry = ref<ModuleDef[]>([])
const editableRoles = ['editor', 'viewer', 'kasserer']

// Role editing state: live-editable copy + pristine baseline for dirty checks.
const roleModules = reactive<Record<string, string[]>>({})
const rolePristine = reactive<Record<string, string>>({})
const savingRole = ref<string | null>(null)
const loadingRoles = ref(true)

// Groups
const groups = ref<any[]>([])
const loadingGroups = ref(true)
const groupModalOpen = ref(false)
const editingGroup = ref<any | null>(null)
const savingGroup = ref(false)
const groupError = ref('')
const groupForm = ref<{ name: string; description: string; role: string; modules: string[] }>({
  name: '', description: '', role: 'viewer', modules: [],
})
const deleteModalOpen = ref(false)
const deletingGroup = ref<any | null>(null)

const moduleGroups = computed(() => {
  const out: { group: string; modules: ModuleDef[] }[] = []
  for (const m of moduleRegistry.value) {
    let g = out.find(x => x.group === m.group)
    if (!g) { g = { group: m.group, modules: [] }; out.push(g) }
    g.modules.push(m)
  }
  return out
})

const moduleLabel = (key: string) => moduleRegistry.value.find(m => m.key === key)?.label ?? key

const roleColor = (role: string) => ({ admin: 'red', editor: 'blue', kasserer: 'amber', viewer: 'green' }[role] ?? 'neutral')

// Toggle a key inside a reactive array in place (used by both editors).
const toggleIn = (arr: string[], key: string) => {
  const i = arr.indexOf(key)
  if (i === -1) arr.push(key)
  else arr.splice(i, 1)
}

const roleDirty = (role: string) => JSON.stringify([...(roleModules[role] || [])].sort()) !== rolePristine[role]

const loadModules = async () => {
  const data = await api.getModules()
  moduleRegistry.value = data.modules
}

const loadRoles = async () => {
  loadingRoles.value = true
  try {
    const rows = await api.getRoleDefaults()
    for (const r of rows) {
      roleModules[r.role] = [...r.modules]
      rolePristine[r.role] = JSON.stringify([...r.modules].sort())
    }
  } catch {
    toast.add({ title: 'Error', description: 'Failed to load role defaults', color: 'red' })
  } finally {
    loadingRoles.value = false
  }
}

const saveRole = async (role: string) => {
  savingRole.value = role
  try {
    const updated = await api.updateRoleDefault(role, roleModules[role] || [])
    roleModules[role] = [...updated.modules]
    rolePristine[role] = JSON.stringify([...updated.modules].sort())
    toast.add({ title: 'Saved', description: `Updated ${role} default modules`, color: 'green' })
  } catch (err: any) {
    toast.add({ title: 'Error', description: err?.data?.detail || 'Failed to save', color: 'red' })
  } finally {
    savingRole.value = null
  }
}

const loadGroups = async () => {
  loadingGroups.value = true
  try {
    groups.value = await api.getAccessGroups()
  } catch {
    toast.add({ title: 'Error', description: 'Failed to load access groups', color: 'red' })
  } finally {
    loadingGroups.value = false
  }
}

const openGroupModal = (g?: any) => {
  editingGroup.value = g || null
  groupError.value = ''
  groupForm.value = g
    ? { name: g.name, description: g.description || '', role: g.role, modules: [...g.modules] }
    : { name: '', description: '', role: 'viewer', modules: [] }
  groupModalOpen.value = true
}

const saveGroup = async () => {
  savingGroup.value = true
  groupError.value = ''
  try {
    const payload = {
      name: groupForm.value.name,
      description: groupForm.value.description || null,
      role: groupForm.value.role,
      modules: groupForm.value.modules,
    }
    if (editingGroup.value) {
      await api.updateAccessGroup(editingGroup.value.id, payload)
      toast.add({ title: 'Saved', description: 'Access group updated', color: 'green' })
    } else {
      await api.createAccessGroup(payload)
      toast.add({ title: 'Created', description: 'Access group created', color: 'green' })
    }
    groupModalOpen.value = false
    await loadGroups()
  } catch (err: any) {
    const detail = err?.data?.detail
    groupError.value = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : (detail || 'Save failed')
  } finally {
    savingGroup.value = false
  }
}

const confirmDeleteGroup = (g: any) => {
  deletingGroup.value = g
  deleteModalOpen.value = true
}

const doDeleteGroup = async () => {
  if (!deletingGroup.value) return
  savingGroup.value = true
  try {
    await api.deleteAccessGroup(deletingGroup.value.id)
    toast.add({ title: 'Deleted', description: 'Access group removed', color: 'green' })
    deleteModalOpen.value = false
    await loadGroups()
  } catch (err: any) {
    toast.add({ title: 'Error', description: err?.data?.detail || 'Failed to delete', color: 'red' })
  } finally {
    savingGroup.value = false
  }
}

onMounted(async () => {
  await loadModules()
  await Promise.all([loadRoles(), loadGroups()])
})
</script>
