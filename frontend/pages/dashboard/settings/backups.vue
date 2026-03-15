<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Database Backups' }
    ]" />

    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Database Backups</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Create, restore, and manage database backups
        </p>
      </div>
      <UButton
        icon="i-heroicons-plus"
        label="Create Backup"
        :loading="creating"
        @click="createBackup"
      />
    </div>

    <UCard v-if="error">
      <div class="text-red-600 dark:text-red-400">{{ error }}</div>
    </UCard>

    <UCard>
      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-gray-400" />
      </div>

      <div v-else-if="backups.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        No backups yet. Create your first backup to get started.
      </div>

      <div v-else class="divide-y divide-gray-200 dark:divide-gray-700">
        <div
          v-for="backup in backups"
          :key="backup.id"
          class="py-4 flex items-center justify-between"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ backup.filename }}
              </p>
              <UBadge
                :color="statusColor(backup.status)"
                :label="backup.status"
                size="xs"
              />
              <UBadge
                v-if="backup.cdn_url"
                color="info"
                label="CDN"
                size="xs"
              />
            </div>
            <div class="mt-1 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span>{{ formatDate(backup.created_at) }}</span>
              <span v-if="backup.size_bytes">{{ formatSize(backup.size_bytes) }}</span>
              <span>{{ backup.backup_type }}</span>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-4">
            <UButton
              v-if="!backup.cdn_url && backup.status === 'completed'"
              icon="i-heroicons-cloud-arrow-up"
              size="xs"
              variant="soft"
              label="Upload CDN"
              :loading="uploadingId === backup.id"
              @click="uploadToCdn(backup.id)"
            />
            <UButton
              v-if="backup.status === 'completed'"
              icon="i-heroicons-arrow-path"
              size="xs"
              variant="soft"
              color="warning"
              label="Restore"
              @click="confirmRestore(backup)"
            />
            <UButton
              icon="i-heroicons-trash"
              size="xs"
              variant="soft"
              color="error"
              @click="confirmDelete(backup)"
            />
          </div>
        </div>
      </div>
    </UCard>

    <!-- Restore confirmation modal -->
    <UModal v-model:open="showRestoreModal">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Confirm Restore</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            This will replace all current data with the backup from
            <strong>{{ restoreTarget?.filename }}</strong>.
            This action cannot be undone.
          </p>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" label="Cancel" @click="showRestoreModal = false" />
            <UButton
              color="warning"
              label="Restore"
              :loading="restoring"
              @click="restoreBackup"
            />
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete confirmation modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Confirm Delete</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Delete backup <strong>{{ deleteTarget?.filename }}</strong>?
            This will remove the local file and CDN copy.
          </p>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" label="Cancel" @click="showDeleteModal = false" />
            <UButton
              color="error"
              label="Delete"
              :loading="deleting"
              @click="deleteBackup"
            />
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

const backups = ref<any[]>([])
const loading = ref(true)
const creating = ref(false)
const restoring = ref(false)
const deleting = ref(false)
const uploadingId = ref<number | null>(null)
const error = ref('')

const showRestoreModal = ref(false)
const restoreTarget = ref<any>(null)
const showDeleteModal = ref(false)
const deleteTarget = ref<any>(null)

const fetchBackups = async () => {
  loading.value = true
  error.value = ''
  try {
    const data = await api.getBackups()
    backups.value = (data as any).backups || []
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to load backups'
  } finally {
    loading.value = false
  }
}

const createBackup = async () => {
  creating.value = true
  try {
    await api.createBackup()
    toast.add({ title: 'Backup created successfully', color: 'success' })
    await fetchBackups()
  } catch (e: any) {
    toast.add({ title: 'Backup failed', description: e.data?.detail || String(e), color: 'error' })
  } finally {
    creating.value = false
  }
}

const uploadToCdn = async (id: number) => {
  uploadingId.value = id
  try {
    await api.uploadBackupToCdn(id)
    toast.add({ title: 'Uploaded to CDN', color: 'success' })
    await fetchBackups()
  } catch (e: any) {
    toast.add({ title: 'CDN upload failed', description: e.data?.detail || String(e), color: 'error' })
  } finally {
    uploadingId.value = null
  }
}

const confirmRestore = (backup: any) => {
  restoreTarget.value = backup
  showRestoreModal.value = true
}

const restoreBackup = async () => {
  if (!restoreTarget.value) return
  restoring.value = true
  try {
    await api.restoreBackup(restoreTarget.value.id)
    toast.add({ title: 'Database restored', color: 'success' })
    showRestoreModal.value = false
  } catch (e: any) {
    toast.add({ title: 'Restore failed', description: e.data?.detail || String(e), color: 'error' })
  } finally {
    restoring.value = false
  }
}

const confirmDelete = (backup: any) => {
  deleteTarget.value = backup
  showDeleteModal.value = true
}

const deleteBackup = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.deleteBackup(deleteTarget.value.id)
    toast.add({ title: 'Backup deleted', color: 'success' })
    showDeleteModal.value = false
    await fetchBackups()
  } catch (e: any) {
    toast.add({ title: 'Delete failed', description: e.data?.detail || String(e), color: 'error' })
  } finally {
    deleting.value = false
  }
}

const statusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'in_progress': return 'warning'
    case 'failed': return 'error'
    default: return 'neutral'
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(fetchBackups)
</script>
