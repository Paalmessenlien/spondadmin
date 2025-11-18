<template>
  <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Events</h1>
            <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Manage your Spond events
            </p>
          </div>

          <div class="flex gap-3">
            <UButton
              icon="i-heroicons-plus"
              color="primary"
              to="/dashboard/events/create"
            >
              Create Event
            </UButton>

            <UButton
              icon="i-heroicons-arrow-path"
              color="gray"
              variant="soft"
              :loading="syncing"
              @click="handleSync"
            >
              Sync from Spond
            </UButton>
          </div>
        </div>

        <!-- Filters -->
        <UCard>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <UInput
              v-model="filters.search"
              placeholder="Search events..."
              icon="i-heroicons-magnifying-glass"
            />

            <USelectMenu
              v-model="filters.include_hidden"
              :options="[
                { label: 'All Events', value: 'both' },
                { label: 'Visible Only', value: 'false' },
                { label: 'Hidden Only', value: 'true' },
              ]"
              value-attribute="value"
              option-attribute="label"
              placeholder="Filter by visibility"
            />

            <USelectMenu
              v-model="filters.include_archived"
              :options="[
                { label: 'Active & Upcoming', value: 'false' },
                { label: 'All Events', value: 'both' },
                { label: 'Archived Only', value: 'true' },
              ]"
              value-attribute="value"
              option-attribute="label"
              placeholder="Filter by status"
            />

            <UButton
              variant="soft"
              @click="loadEvents"
            >
              Apply Filters
            </UButton>
          </div>
        </UCard>

        <!-- Events Table -->
        <UCard>
          <template v-if="loading">
            <div class="flex justify-center py-12">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
            </div>
          </template>

          <template v-else-if="events.length === 0">
            <div class="text-center py-12">
              <UIcon name="i-heroicons-calendar" class="h-12 w-12 mx-auto text-gray-400" />
              <h3 class="mt-2 text-sm font-semibold text-gray-900 dark:text-white">No events</h3>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Sync events from Spond to get started.
              </p>
            </div>
          </template>

          <template v-else>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Event
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Sync
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Responses
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  <tr
                    v-for="event in events"
                    :key="`event-${event.id}`"
                    class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                    @click="navigateTo(`/dashboard/events/${event.id}`)"
                  >
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
                        {{ event.heading }}
                      </div>
                      <div v-if="event.description" class="text-sm text-gray-500 dark:text-gray-400 truncate max-w-md">
                        {{ event.description }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {{ formatDate(event.start_time) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <UBadge :color="event.event_type === 'RECURRING' ? 'blue' : 'gray'">
                        {{ event.event_type }}
                      </UBadge>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <UBadge v-if="event.cancelled" color="red">Cancelled</UBadge>
                      <UBadge v-else-if="event.hidden" color="orange">Hidden</UBadge>
                      <UBadge v-else color="green">Active</UBadge>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <SyncStatusBadge
                        :status="event.sync_status"
                        :error="event.sync_error"
                      />
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div class="flex space-x-2">
                        <span class="text-green-600">✓ {{ event.responses?.accepted_uids?.length || 0 }}</span>
                        <span class="text-red-600">✗ {{ event.responses?.declined_uids?.length || 0 }}</span>
                        <span class="text-gray-600">? {{ event.responses?.unanswered_uids?.length || 0 }}</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pagination -->
            <div class="flex justify-between items-center mt-4 px-4">
              <div class="text-sm text-gray-700 dark:text-gray-300">
                Showing {{ events.length }} of {{ total }} events
              </div>
              <div class="flex space-x-2">
                <UButton
                  size="sm"
                  variant="soft"
                  :disabled="filters.skip === 0"
                  @click="previousPage"
                >
                  Previous
                </UButton>
                <UButton
                  size="sm"
                  variant="soft"
                  :disabled="filters.skip + filters.limit >= total"
                  @click="nextPage"
                >
                  Next
                </UButton>
              </div>
            </div>
          </template>
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

const events = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const syncing = ref(false)

const filters = reactive({
  search: '',
  include_hidden: 'true',
  include_archived: 'false',  // Default to showing only active and upcoming events
  skip: 0,
  limit: 20,
})

onMounted(() => {
  loadEvents()
})

const loadEvents = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: filters.skip,
      limit: filters.limit,
      include_hidden: filters.include_hidden,
      include_archived: filters.include_archived,
    }

    if (filters.search) {
      params.search = filters.search
    }

    const response = await api.getEvents(params)
    events.value = response.events || []
    total.value = response.total || 0
  } catch (error) {
    console.error('Failed to load events:', error)
    toast.add({ title: 'Error', description: 'Failed to load events', color: 'red' })
  } finally {
    loading.value = false
  }
}

const handleSync = async () => {
  const authStore = useAuthStore()

  if (!authStore.selectedGroupId) {
    toast.add({ title: 'Error', description: 'Please select a group first', color: 'red' })
    return
  }

  syncing.value = true
  try {
    await api.syncEvents({ group_id: authStore.selectedGroupId, include_hidden: true })
    toast.add({ title: 'Success', description: 'Events synced successfully', color: 'green' })
    await loadEvents()
  } catch (error) {
    toast.add({ title: 'Error', description: 'Failed to sync events', color: 'red' })
  } finally {
    syncing.value = false
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const nextPage = () => {
  filters.skip += filters.limit
  loadEvents()
}

const previousPage = () => {
  filters.skip = Math.max(0, filters.skip - filters.limit)
  loadEvents()
}
</script>
