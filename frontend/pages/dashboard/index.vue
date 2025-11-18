<template>
  <div class="space-y-6">
        <!-- Header -->
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Overview of your Spond data
          </p>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Events Stats -->
          <UCard>
            <template #header>
              <div class="flex items-center space-x-2">
                <UIcon name="i-heroicons-calendar" class="h-5 w-5 text-blue-500" />
                <h3 class="text-lg font-semibold">Events</h3>
              </div>
            </template>

            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Total Events</span>
                <span class="font-semibold">{{ eventStats?.total_events || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Upcoming</span>
                <span class="font-semibold text-green-600">{{ eventStats?.upcoming_events || 0 }}</span>
              </div>
            </div>

            <template #footer>
              <UButton to="/dashboard/events" block variant="soft">
                View Events
              </UButton>
            </template>
          </UCard>

          <!-- Groups Stats -->
          <UCard>
            <template #header>
              <div class="flex items-center space-x-2">
                <UIcon name="i-heroicons-user-group" class="h-5 w-5 text-purple-500" />
                <h3 class="text-lg font-semibold">Groups</h3>
              </div>
            </template>

            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Total Groups</span>
                <span class="font-semibold">{{ groupStats?.total_groups || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Subgroups</span>
                <span class="font-semibold text-purple-600">{{ groupStats?.total_subgroups || 0 }}</span>
              </div>
            </div>

            <template #footer>
              <UButton to="/dashboard/groups" block variant="soft">
                View Groups
              </UButton>
            </template>
          </UCard>

          <!-- Members Stats -->
          <UCard>
            <template #header>
              <div class="flex items-center space-x-2">
                <UIcon name="i-heroicons-users" class="h-5 w-5 text-orange-500" />
                <h3 class="text-lg font-semibold">Members</h3>
              </div>
            </template>

            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Total Members</span>
                <span class="font-semibold">{{ memberStats?.total_members || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">With Email</span>
                <span class="font-semibold text-orange-600">{{ memberStats?.members_with_email || 0 }}</span>
              </div>
            </div>

            <template #footer>
              <UButton to="/dashboard/members" block variant="soft">
                View Members
              </UButton>
            </template>
          </UCard>
        </div>

        <!-- Quick Actions -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">Quick Actions</h3>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UButton
              icon="i-heroicons-arrow-path"
              size="lg"
              color="blue"
              variant="soft"
              block
              :loading="syncing.events"
              @click="syncEvents"
            >
              Sync Events
            </UButton>

            <UButton
              icon="i-heroicons-arrow-path"
              size="lg"
              color="purple"
              variant="soft"
              block
              :loading="syncing.groups"
              @click="syncGroups"
            >
              Sync Groups
            </UButton>

            <UButton
              icon="i-heroicons-arrow-path"
              size="lg"
              color="orange"
              variant="soft"
              block
              :loading="syncing.members"
              @click="syncMembers"
            >
              Sync Members
            </UButton>
          </div>
        </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const api = useApi()
const toast = useToast()
const config = useRuntimeConfig()
const authStore = useAuthStore()

const syncing = reactive({
  events: false,
  groups: false,
  members: false,
})

// Create headers with auth token
const headers = computed(() => ({
  Authorization: authStore.token ? `Bearer ${authStore.token}` : ''
}))

// Fetch stats using useFetch
const { data: eventStats, refresh: refreshEventStats } = await useFetch('/events/stats', {
  baseURL: config.public.apiBase,
  headers: headers.value,
  lazy: true,
  key: 'event-stats',
})

const { data: groupStats, refresh: refreshGroupStats } = await useFetch('/groups/stats', {
  baseURL: config.public.apiBase,
  headers: headers.value,
  lazy: true,
  key: 'group-stats',
})

const { data: memberStats, refresh: refreshMemberStats } = await useFetch('/members/stats', {
  baseURL: config.public.apiBase,
  headers: headers.value,
  lazy: true,
  key: 'member-stats',
})

const syncEvents = async () => {
  if (!authStore.selectedGroupId) {
    toast.add({ title: 'Error', description: 'Please select a group first', color: 'red' })
    return
  }

  syncing.events = true
  try {
    await api.syncEvents({ group_id: authStore.selectedGroupId, include_hidden: true })
    toast.add({ title: 'Success', description: 'Events synced successfully', color: 'green' })
    await refreshEventStats()
  } catch (error) {
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
    await refreshGroupStats()
  } catch (error) {
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
    await refreshMemberStats()
  } catch (error) {
    toast.add({ title: 'Error', description: 'Failed to sync members', color: 'red' })
  } finally {
    syncing.members = false
  }
}
</script>
