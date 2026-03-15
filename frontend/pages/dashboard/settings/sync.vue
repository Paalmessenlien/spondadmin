<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Spond Sync' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Spond Sync</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Manage data synchronization with Spond
      </p>
    </div>

    <!-- Manual Sync -->
    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Manual Sync</h3>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UButton
          icon="i-heroicons-arrow-path"
          size="lg"
          color="primary"
          block
          :loading="syncing.events"
          @click="syncEvents"
        >
          Sync Events
        </UButton>

        <UButton
          icon="i-heroicons-arrow-path"
          size="lg"
          color="primary"
          block
          :loading="syncing.groups"
          @click="syncGroups"
        >
          Sync Groups
        </UButton>

        <UButton
          icon="i-heroicons-arrow-path"
          size="lg"
          color="primary"
          block
          :loading="syncing.members"
          @click="syncMembers"
        >
          Sync Members
        </UButton>
      </div>
    </UCard>

    <!-- Scheduler Status -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">Background Scheduler</h3>
          <UBadge :color="schedulerStatus?.running ? 'green' : 'gray'" size="sm">
            {{ schedulerStatus?.running ? 'Running' : 'Stopped' }}
          </UBadge>
        </div>
      </template>

      <div v-if="schedulerLoading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-6 w-6 text-gray-400" />
      </div>

      <div v-else-if="schedulerStatus?.jobs?.length" class="space-y-3">
        <div
          v-for="job in schedulerStatus.jobs"
          :key="job.id"
          class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
        >
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ job.name }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Next run: {{ job.next_run ? formatDate(job.next_run) : 'Not scheduled' }}
            </p>
          </div>
          <UButton
            icon="i-heroicons-play"
            size="xs"
            variant="soft"
            :loading="triggeringJob === job.id"
            @click="triggerJob(job.id)"
          >
            Run Now
          </UButton>
        </div>
      </div>

      <div v-else class="text-center py-8 text-sm text-gray-500">
        No scheduled jobs found. Check your backend configuration.
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
const config = useRuntimeConfig()
const authStore = useAuthStore()

const syncing = reactive({
  events: false,
  groups: false,
  members: false,
})

const schedulerLoading = ref(true)
const schedulerStatus = ref<any>(null)
const triggeringJob = ref<string | null>(null)

const headers = computed(() => ({
  Authorization: authStore.token ? `Bearer ${authStore.token}` : ''
}))

// Fetch scheduler status
onMounted(async () => {
  try {
    schedulerStatus.value = await $fetch('/scheduler/status', {
      baseURL: config.public.apiBase,
      headers: headers.value,
    })
  } catch {
    // Scheduler might not be running
  } finally {
    schedulerLoading.value = false
  }
})

const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleString()
  } catch {
    return dateStr
  }
}

const triggerJob = async (jobId: string) => {
  triggeringJob.value = jobId
  try {
    await $fetch(`/scheduler/jobs/${jobId}/trigger`, {
      baseURL: config.public.apiBase,
      method: 'POST',
      headers: headers.value,
    })
    toast.add({ title: 'Success', description: `Job "${jobId}" triggered`, color: 'green' })
  } catch {
    toast.add({ title: 'Error', description: 'Failed to trigger job', color: 'red' })
  } finally {
    triggeringJob.value = null
  }
}

const syncEvents = async () => {
  if (!authStore.selectedGroupId) {
    toast.add({ title: 'Error', description: 'Please select a group first', color: 'red' })
    return
  }
  syncing.events = true
  try {
    await api.syncEvents({ group_id: authStore.selectedGroupId, include_hidden: true })
    toast.add({ title: 'Success', description: 'Events synced successfully', color: 'green' })
  } catch {
    toast.add({ title: 'Error', description: 'Failed to sync events', color: 'red' })
  } finally {
    syncing.events = false
  }
}

const syncGroups = async () => {
  syncing.groups = true
  try {
    await api.syncGroups()
    toast.add({ title: 'Success', description: 'Groups synced successfully', color: 'green' })
  } catch {
    toast.add({ title: 'Error', description: 'Failed to sync groups', color: 'red' })
  } finally {
    syncing.groups = false
  }
}

const syncMembers = async () => {
  syncing.members = true
  try {
    await api.syncMembers()
    toast.add({ title: 'Success', description: 'Members synced successfully', color: 'green' })
  } catch {
    toast.add({ title: 'Error', description: 'Failed to sync members', color: 'red' })
  } finally {
    syncing.members = false
  }
}
</script>
