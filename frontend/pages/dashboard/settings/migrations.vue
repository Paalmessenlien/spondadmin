<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Migrations' }
    ]" />

    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Database Migrations</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          View migration status and apply pending migrations
        </p>
      </div>
      <UButton
        v-if="status && !status.is_up_to_date"
        icon="i-heroicons-play"
        label="Run Migrations"
        :loading="running"
        @click="runMigrations"
      />
    </div>

    <!-- Status Card -->
    <UCard>
      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-gray-400" />
      </div>

      <div v-else-if="status" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <p class="text-sm text-gray-500 dark:text-gray-400">Status</p>
            <UBadge
              :color="status.is_up_to_date ? 'success' : 'warning'"
              :label="status.is_up_to_date ? 'Up to date' : 'Pending migrations'"
              class="mt-1"
            />
          </div>
          <div class="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <p class="text-sm text-gray-500 dark:text-gray-400">Current Revision</p>
            <p class="text-sm font-mono font-semibold text-gray-900 dark:text-white mt-1">
              {{ status.current_revision || 'None' }}
            </p>
          </div>
          <div class="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <p class="text-sm text-gray-500 dark:text-gray-400">Head Revision</p>
            <p class="text-sm font-mono font-semibold text-gray-900 dark:text-white mt-1">
              {{ status.head_revision || 'None' }}
            </p>
          </div>
        </div>

        <div class="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
          <span>Applied: <strong>{{ status.applied_count }}</strong></span>
          <span>Pending: <strong>{{ status.pending_count }}</strong></span>
        </div>
      </div>

      <div v-else-if="error" class="text-red-600 dark:text-red-400">{{ error }}</div>
    </UCard>

    <!-- Migration History -->
    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Migration History</h3>
      </template>

      <div v-if="loadingHistory" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-gray-400" />
      </div>

      <div v-else-if="history.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        No migrations found.
      </div>

      <div v-else class="divide-y divide-gray-200 dark:divide-gray-700">
        <div
          v-for="migration in history"
          :key="migration.revision"
          class="py-3 flex items-center justify-between"
        >
          <div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-mono text-gray-700 dark:text-gray-300">
                {{ migration.revision }}
              </span>
              <UBadge
                :color="migration.applied ? 'success' : 'warning'"
                :label="migration.applied ? 'Applied' : 'Pending'"
                size="xs"
              />
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ migration.description }}
            </p>
          </div>
          <span class="text-xs text-gray-400">{{ migration.filename }}</span>
        </div>
      </div>
    </UCard>

    <!-- Run Result -->
    <UCard v-if="runResult">
      <template #header>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Migration Result</h3>
      </template>
      <div class="space-y-2 text-sm">
        <p>Status: <UBadge :color="runResult.status === 'completed' ? 'success' : 'info'" :label="runResult.status" /></p>
        <p v-if="runResult.migrations_applied !== undefined">
          Migrations applied: <strong>{{ runResult.migrations_applied }}</strong>
        </p>
        <pre v-if="runResult.output" class="text-xs bg-gray-50 dark:bg-gray-800 p-3 rounded overflow-x-auto">{{ runResult.output }}</pre>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const { canManageSystem } = usePermissions()
if (!canManageSystem.value) navigateTo('/dashboard')

const api = useApi()
const toast = useToast()

const status = ref<any>(null)
const history = ref<any[]>([])
const loading = ref(true)
const loadingHistory = ref(true)
const running = ref(false)
const error = ref('')
const runResult = ref<any>(null)

const fetchStatus = async () => {
  loading.value = true
  try {
    status.value = await api.getMigrationStatus()
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to load migration status'
  } finally {
    loading.value = false
  }
}

const fetchHistory = async () => {
  loadingHistory.value = true
  try {
    history.value = await api.getMigrationHistory() as any[]
  } catch {
    // Status card already shows errors
  } finally {
    loadingHistory.value = false
  }
}

const runMigrations = async () => {
  running.value = true
  runResult.value = null
  try {
    runResult.value = await api.runMigrations()
    toast.add({ title: 'Migrations completed', color: 'success' })
    await fetchStatus()
    await fetchHistory()
  } catch (e: any) {
    toast.add({ title: 'Migration failed', description: e.data?.detail || String(e), color: 'error' })
  } finally {
    running.value = false
  }
}

onMounted(() => {
  fetchStatus()
  fetchHistory()
})
</script>
