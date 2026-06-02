<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Admin Users' }
    ]" />

    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Admin Users</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Invite administrators and manage their roles. Authentication is handled by Clerk.
        </p>
      </div>
      <UButton icon="i-heroicons-envelope" @click="openInviteModal">
        Invite User
      </UButton>
    </div>

    <UCard>
      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>

      <div v-else-if="admins.length === 0" class="text-center py-12 text-gray-500">
        No admin users found.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-3 px-4 font-medium text-gray-500">User</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Email</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Role</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Status</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Clerk</th>
              <th class="text-left py-3 px-4 font-medium text-gray-500">Created</th>
              <th class="text-right py-3 px-4 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="admin in admins"
              :key="admin.id"
              class="border-b border-gray-100 dark:border-gray-800"
            >
              <td class="py-3 px-4">
                <div class="flex items-center space-x-3">
                  <div
                    class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                    :class="admin.id === currentUser?.id ? 'bg-blue-600' : 'bg-gray-400'"
                  >
                    {{ getInitials(admin.full_name || admin.username) }}
                  </div>
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white">
                      {{ admin.full_name || admin.username }}
                      <span v-if="admin.id === currentUser?.id" class="ml-1 text-xs text-blue-600 dark:text-blue-400">(you)</span>
                    </div>
                    <div class="text-xs text-gray-500">@{{ admin.username }}</div>
                  </div>
                </div>
              </td>
              <td class="py-3 px-4 text-gray-600 dark:text-gray-400">{{ admin.email }}</td>
              <td class="py-3 px-4">
                <UBadge :color="roleColor(admin.role)" variant="subtle" size="sm">
                  {{ admin.role }}
                </UBadge>
              </td>
              <td class="py-3 px-4">
                <UBadge :color="admin.is_active ? 'green' : 'red'" variant="subtle" size="sm">
                  {{ admin.is_active ? 'Active' : 'Inactive' }}
                </UBadge>
              </td>
              <td class="py-3 px-4">
                <UBadge
                  :color="admin.clerk_user_id ? 'green' : 'yellow'"
                  variant="subtle"
                  size="sm"
                >
                  {{ admin.clerk_user_id ? 'Linked' : 'Pending sign-in' }}
                </UBadge>
              </td>
              <td class="py-3 px-4 text-gray-600 dark:text-gray-400 text-xs">
                {{ formatDate(admin.created_at) }}
              </td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end space-x-1">
                  <UButton
                    color="neutral"
                    variant="ghost"
                    icon="i-heroicons-pencil-square"
                    size="xs"
                    @click="openEditModal(admin)"
                  />
                  <UButton
                    v-if="admin.id !== currentUser?.id"
                    color="red"
                    variant="ghost"
                    icon="i-heroicons-trash"
                    size="xs"
                    @click="confirmDelete(admin)"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Role Permissions</h3>
      </template>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div>
          <div class="flex items-center space-x-2 mb-1">
            <UBadge color="red" variant="subtle" size="sm">admin</UBadge>
          </div>
          <p class="text-gray-600 dark:text-gray-400">Full access. Manage users, settings, sync, scraper, and all data.</p>
        </div>
        <div>
          <div class="flex items-center space-x-2 mb-1">
            <UBadge color="blue" variant="subtle" size="sm">editor</UBadge>
          </div>
          <p class="text-gray-600 dark:text-gray-400">View everything + modify data (categories, reports). Cannot manage users or system settings.</p>
        </div>
        <div>
          <div class="flex items-center space-x-2 mb-1">
            <UBadge color="neutral" variant="subtle" size="sm">viewer</UBadge>
          </div>
          <p class="text-gray-600 dark:text-gray-400">Read-only. Can browse all dashboards but cannot create, edit, or delete anything.</p>
        </div>
      </div>
    </UCard>

    <!-- Invite Modal -->
    <UModal v-model:open="inviteModalOpen">
      <template #content>
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">Invite Admin User</h2>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Clerk will send a sign-in invitation to this email. The user becomes active automatically on their first sign-in.
          </p>

          <form @submit.prevent="handleInvite" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
              <UInput
                v-model="inviteForm.email"
                type="email"
                placeholder="user@example.com"
                required
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
              <UInput
                v-model="inviteForm.full_name"
                placeholder="Full Name (optional)"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
              <select
                v-model="inviteForm.role"
                class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="admin">Admin - Full access</option>
                <option value="editor">Editor - View + modify data</option>
                <option value="kasserer">Kasserer - Review expenses (utlegg)</option>
                <option value="viewer">Viewer - Read-only</option>
              </select>
            </div>

            <div v-if="formError" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-3">
              {{ formError }}
            </div>

            <div class="flex justify-end space-x-3 pt-2">
              <UButton color="neutral" variant="outline" @click="inviteModalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="submitting" icon="i-heroicons-envelope">Send Invitation</UButton>
            </div>
          </form>
        </div>
      </template>
    </UModal>

    <!-- Edit Modal -->
    <UModal v-model:open="editModalOpen">
      <template #content>
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">Edit User</h2>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Email and password are managed by Clerk. Here you can change the local role and active flag.
          </p>

          <form @submit.prevent="handleEdit" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
              <UInput :model-value="editingAdmin?.username || ''" disabled />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
              <UInput :model-value="editingAdmin?.email || ''" disabled />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
              <UInput v-model="editForm.full_name" placeholder="Full Name" />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
              <select
                v-model="editForm.role"
                class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="admin">Admin - Full access</option>
                <option value="editor">Editor - View + modify data</option>
                <option value="kasserer">Kasserer - Review expenses (utlegg)</option>
                <option value="viewer">Viewer - Read-only</option>
              </select>
            </div>

            <div class="flex items-center space-x-2">
              <input
                id="is_active"
                v-model="editForm.is_active"
                type="checkbox"
                class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              />
              <label for="is_active" class="text-sm text-gray-700 dark:text-gray-300">Active</label>
            </div>

            <div v-if="formError" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-3">
              {{ formError }}
            </div>

            <div class="flex justify-end space-x-3 pt-2">
              <UButton color="neutral" variant="outline" @click="editModalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="submitting">Save Changes</UButton>
            </div>
          </form>
        </div>
      </template>
    </UModal>

    <UModal v-model:open="deleteModalOpen">
      <template #content>
        <div class="p-6">
          <h2 class="text-lg font-bold text-red-600 mb-2">Delete User</h2>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            Are you sure you want to delete <strong>{{ deletingAdmin?.full_name || deletingAdmin?.username }}</strong>?
            This removes both the local admin row and the Clerk user. This action cannot be undone.
          </p>
          <div class="flex justify-end space-x-3">
            <UButton color="neutral" variant="outline" @click="deleteModalOpen = false">Cancel</UButton>
            <UButton color="red" :loading="submitting" @click="handleDelete">Delete</UButton>
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
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

interface AdminUser {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  role: string
  clerk_user_id?: string | null
  created_at: string
  updated_at: string
}

const admins = ref<AdminUser[]>([])
const loading = ref(true)
const inviteModalOpen = ref(false)
const editModalOpen = ref(false)
const deleteModalOpen = ref(false)
const editingAdmin = ref<AdminUser | null>(null)
const deletingAdmin = ref<AdminUser | null>(null)
const submitting = ref(false)
const formError = ref('')

const inviteForm = ref({
  email: '',
  full_name: '',
  role: 'viewer',
})

const editForm = ref({
  full_name: '',
  role: 'viewer',
  is_active: true,
})

const loadAdmins = async () => {
  loading.value = true
  try {
    admins.value = await api.getAdmins()
  } catch {
    toast.add({ title: 'Error', description: 'Failed to load users', color: 'red' })
  } finally {
    loading.value = false
  }
}

onMounted(loadAdmins)

const openInviteModal = () => {
  inviteForm.value = { email: '', full_name: '', role: 'viewer' }
  formError.value = ''
  inviteModalOpen.value = true
}

const openEditModal = (admin: AdminUser) => {
  editingAdmin.value = admin
  editForm.value = {
    full_name: admin.full_name || '',
    role: admin.role,
    is_active: admin.is_active,
  }
  formError.value = ''
  editModalOpen.value = true
}

const confirmDelete = (admin: AdminUser) => {
  deletingAdmin.value = admin
  deleteModalOpen.value = true
}

const handleInvite = async () => {
  submitting.value = true
  formError.value = ''
  try {
    await api.inviteAdmin({
      email: inviteForm.value.email,
      full_name: inviteForm.value.full_name || undefined,
      role: inviteForm.value.role,
    })
    toast.add({ title: 'Invitation sent', description: `Email sent to ${inviteForm.value.email}`, color: 'green' })
    inviteModalOpen.value = false
    await loadAdmins()
  } catch (err: any) {
    const detail = err?.data?.detail
    formError.value = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : (detail || err.message || 'Invitation failed')
  } finally {
    submitting.value = false
  }
}

const handleEdit = async () => {
  if (!editingAdmin.value) return
  submitting.value = true
  formError.value = ''
  try {
    await api.updateAdmin(editingAdmin.value.id, {
      full_name: editForm.value.full_name || null,
      role: editForm.value.role,
      is_active: editForm.value.is_active,
      is_superuser: editForm.value.role === 'admin',
    })
    toast.add({ title: 'Saved', description: 'User updated', color: 'green' })
    editModalOpen.value = false
    await loadAdmins()
    if (editingAdmin.value.id === currentUser.value?.id) {
      await authStore.fetchUser()
    }
  } catch (err: any) {
    const detail = err?.data?.detail
    formError.value = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : (detail || err.message || 'Update failed')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async () => {
  if (!deletingAdmin.value) return
  submitting.value = true
  try {
    await api.deleteAdmin(deletingAdmin.value.id)
    toast.add({ title: 'Deleted', description: 'User removed', color: 'green' })
    deleteModalOpen.value = false
    await loadAdmins()
  } catch (err: any) {
    toast.add({
      title: 'Error',
      description: err?.data?.detail || 'Failed to delete user',
      color: 'red',
    })
  } finally {
    submitting.value = false
  }
}

const roleColor = (role: string) => {
  switch (role) {
    case 'admin': return 'red'
    case 'editor': return 'blue'
    case 'kasserer': return 'green'
    default: return 'neutral'
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const getInitials = (name: string) => {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return name.substring(0, 2).toUpperCase()
}
</script>
