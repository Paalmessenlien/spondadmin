<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Club overview and quick stats
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
          <UButton to="/dashboard/events" block color="neutral" variant="outline">
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
          <UButton to="/dashboard/groups" block color="neutral" variant="outline">
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
          <UButton to="/dashboard/members" block color="neutral" variant="outline">
            View Members
          </UButton>
        </template>
      </UCard>
    </div>

    <!-- Coming Soon Features -->
    <div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Coming Soon</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UCard v-for="feature in comingSoonFeatures" :key="feature.title">
          <div class="flex items-start space-x-3">
            <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
              <UIcon :name="feature.icon" class="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ feature.title }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ feature.description }}</p>
            </div>
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const config = useRuntimeConfig()
const authStore = useAuthStore()
const { headers } = useAuthHeaders()

const statsQuery = computed(() => {
  if (authStore.selectedGroupId) {
    return { group_id: authStore.selectedGroupId }
  }
  return {}
})

const { data: eventStats } = await useFetch('/events/stats', {
  baseURL: config.public.apiBase,
  headers: headers,
  query: statsQuery,
  lazy: true,
  key: 'event-stats',
  watch: [() => authStore.selectedGroupId],
})

const { data: groupStats } = await useFetch('/groups/stats', {
  baseURL: config.public.apiBase,
  headers: headers,
  lazy: true,
  key: 'group-stats',
})

const { data: memberStats } = await useFetch('/members/stats', {
  baseURL: config.public.apiBase,
  headers: headers,
  query: statsQuery,
  lazy: true,
  key: 'member-stats',
  watch: [() => authStore.selectedGroupId],
})

const comingSoonFeatures = [
  {
    title: 'Scores & Records',
    description: 'Track scores, personal bests, handicaps, and classifications.',
    icon: 'i-heroicons-viewfinder-circle',
  },
  {
    title: 'Competitions',
    description: 'Manage tournaments, match scheduling, and results.',
    icon: 'i-heroicons-trophy',
  },
  {
    title: 'Equipment',
    description: 'Club equipment inventory and loan tracking.',
    icon: 'i-heroicons-cube',
  },
]
</script>
