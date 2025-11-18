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
          <div class="space-y-4">
            <!-- Filter Controls -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
              <UInput
                v-model="filters.search"
                placeholder="Search events..."
                icon="i-heroicons-magnifying-glass"
                class="lg:col-span-2"
              >
                <template #trailing>
                  <UButton
                    v-if="filters.search"
                    color="gray"
                    variant="link"
                    icon="i-heroicons-x-mark"
                    :padded="false"
                    @click="filters.search = ''"
                  />
                </template>
              </UInput>

              <USelectMenu
                v-model="filters.event_type"
                :options="eventTypeOptions"
                value-attribute="value"
                option-attribute="label"
                placeholder="All Types"
              />

              <USelectMenu
                v-model="filters.include_hidden"
                :options="visibilityOptions"
                value-attribute="value"
                option-attribute="label"
                placeholder="Visibility"
              />

              <USelectMenu
                v-model="filters.include_archived"
                :options="archivedOptions"
                value-attribute="value"
                option-attribute="label"
                placeholder="Status"
              />

              <UButton
                v-if="hasActiveFilters"
                color="gray"
                variant="soft"
                icon="i-heroicons-x-circle"
                @click="clearFilters"
              >
                Clear Filters
              </UButton>
            </div>

            <!-- Date Range Filters -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <UInput
                v-model="filters.start_date"
                type="date"
                label="From Date"
                placeholder="Filter from date"
              />
              <UInput
                v-model="filters.end_date"
                type="date"
                label="To Date"
                placeholder="Filter to date"
              />
            </div>

            <!-- Active Filter Chips -->
            <div v-if="activeFilterChips.length > 0" class="flex flex-wrap gap-2">
              <UBadge
                v-for="chip in activeFilterChips"
                :key="chip.key"
                color="primary"
                variant="subtle"
                class="gap-1"
              >
                {{ chip.label }}
                <UButton
                  color="primary"
                  variant="link"
                  icon="i-heroicons-x-mark"
                  :padded="false"
                  size="2xs"
                  @click="removeFilter(chip.key)"
                />
              </UBadge>
            </div>
          </div>
        </UCard>

        <!-- View Tabs and Content -->
        <UCard>
          <!-- Tabs -->
          <UTabs
            v-model="selectedView"
            :items="viewTabs"
            class="mb-6"
          />

          <!-- List View -->
          <div v-if="selectedView === 'list'">
            <template v-if="loading">
              <div class="flex justify-center py-12">
                <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
              </div>
            </template>

            <template v-else-if="events.length === 0">
              <div class="text-center py-12">
                <UIcon name="i-heroicons-calendar" class="h-12 w-12 mx-auto text-gray-400" />
                <h3 class="mt-2 text-sm font-semibold text-gray-900 dark:text-white">
                  {{ filters.search ? 'No events found' : 'No events' }}
                </h3>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {{ filters.search ? `No results for "${filters.search}"` : 'Sync events from Spond to get started.' }}
                </p>
              </div>
            </template>

            <template v-else>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
                  <tr>
                    <th
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      @click="toggleSort('heading')"
                    >
                      <div class="flex items-center gap-1">
                        <span>Event</span>
                        <UIcon
                          v-if="filters.order_by === 'heading'"
                          :name="filters.order_desc ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-up'"
                          class="w-4 h-4"
                        />
                      </div>
                    </th>
                    <th
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      @click="toggleSort('start_time')"
                    >
                      <div class="flex items-center gap-1">
                        <span>Date</span>
                        <UIcon
                          v-if="filters.order_by === 'start_time'"
                          :name="filters.order_desc ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-up'"
                          class="w-4 h-4"
                        />
                      </div>
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
                    class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                    @click="navigateTo(`/dashboard/events/${event.id}`)"
                  >
                    <td class="px-6 py-4">
                      <div class="text-sm font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
                        {{ event.heading }}
                      </div>
                      <div
                        v-if="event.description"
                        class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 max-w-md"
                        :title="event.description"
                      >
                        {{ event.description }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {{ formatDate(event.start_time) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <UBadge :color="getEventTypeColor(event.event_type)">
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
                      <div
                        class="flex space-x-2"
                        :title="getResponsesTooltip(event.responses)"
                      >
                        <span class="text-green-600">✓ {{ event.responses?.accepted_uids?.length || 0 }}</span>
                        <span class="text-red-600">✗ {{ event.responses?.declined_uids?.length || 0 }}</span>
                        <span class="text-gray-600">? {{ event.responses?.unanswered_uids?.length || 0 }}</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Enhanced Pagination -->
            <div class="flex flex-col sm:flex-row justify-between items-center gap-4 mt-4 px-4 py-3 border-t border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-4">
                <div class="text-sm text-gray-700 dark:text-gray-300">
                  Showing {{ startItem }} - {{ endItem }} of {{ total }} events
                </div>
                <USelectMenu
                  v-model="filters.limit"
                  :options="pageSizeOptions"
                  value-attribute="value"
                  option-attribute="label"
                  size="sm"
                  class="w-32"
                />
              </div>

              <div class="flex items-center gap-2">
                <UButton
                  size="sm"
                  variant="soft"
                  icon="i-heroicons-chevron-double-left"
                  :disabled="currentPage === 1"
                  @click="goToFirstPage"
                />
                <UButton
                  size="sm"
                  variant="soft"
                  icon="i-heroicons-chevron-left"
                  :disabled="currentPage === 1"
                  @click="previousPage"
                />
                <div class="text-sm text-gray-700 dark:text-gray-300 px-3">
                  Page {{ currentPage }} of {{ totalPages }}
                </div>
                <UButton
                  size="sm"
                  variant="soft"
                  icon="i-heroicons-chevron-right"
                  :disabled="currentPage === totalPages"
                  @click="nextPage"
                />
                <UButton
                  size="sm"
                  variant="soft"
                  icon="i-heroicons-chevron-double-right"
                  :disabled="currentPage === totalPages"
                  @click="goToLastPage"
                />
              </div>
            </div>
            </template>
          </div>

          <!-- Calendar View -->
          <div v-else-if="selectedView === 'calendar'">
            <EventsFullCalendarView
              :events="events"
              :filters="filters"
              :loading="loading"
              @update:dates="handleCalendarDatesChange"
              @update:calendar-view="handleCalendarViewChange"
            />
          </div>

          <!-- Upcoming View -->
          <div v-else-if="selectedView === 'upcoming'">
            <EventsUpcomingView
              :events="events"
              :loading="loading"
            />
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

const events = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const syncing = ref(false)

// View management with localStorage persistence
const selectedView = ref(
  process.client ? (localStorage.getItem('events-view-preference') || 'list') : 'list'
)

const viewTabs = [
  {
    value: 'list',
    label: 'List',
    icon: 'i-heroicons-list-bullet',
  },
  {
    value: 'calendar',
    label: 'Calendar',
    icon: 'i-heroicons-calendar-days',
  },
  {
    value: 'upcoming',
    label: 'Upcoming',
    icon: 'i-heroicons-clock',
  },
]

// Watch for view changes and save to localStorage
watch(selectedView, (newView) => {
  if (process.client) {
    localStorage.setItem('events-view-preference', newView)
  }
})

const filters = reactive({
  search: '',
  event_type: '',
  include_hidden: 'true',
  include_archived: 'false',
  start_date: '',
  end_date: '',
  skip: 0,
  limit: 20,
  order_by: 'start_time',
  order_desc: true,
})

// Filter options
const eventTypeOptions = [
  { label: 'All Types', value: '' },
  { label: 'Regular Events', value: 'EVENT' },
  { label: 'Recurring Events', value: 'RECURRING' },
  { label: 'Availability', value: 'AVAILABILITY' },
]

const visibilityOptions = [
  { label: 'All Events', value: 'both' },
  { label: 'Visible Only', value: 'false' },
  { label: 'Hidden Only', value: 'true' },
]

const archivedOptions = [
  { label: 'Active & Upcoming', value: 'false' },
  { label: 'All Events', value: 'both' },
  { label: 'Archived Only', value: 'true' },
]

const pageSizeOptions = [
  { label: '10 per page', value: 10 },
  { label: '20 per page', value: 20 },
  { label: '50 per page', value: 50 },
  { label: '100 per page', value: 100 },
]

// Computed properties
const currentPage = computed(() => Math.floor(filters.skip / filters.limit) + 1)
const totalPages = computed(() => Math.ceil(total.value / filters.limit))
const startItem = computed(() => Math.min(filters.skip + 1, total.value))
const endItem = computed(() => Math.min(filters.skip + filters.limit, total.value))

const hasActiveFilters = computed(() => {
  return filters.search ||
         filters.event_type ||
         filters.include_hidden !== 'true' ||
         filters.include_archived !== 'false' ||
         filters.start_date ||
         filters.end_date
})

const activeFilterChips = computed(() => {
  const chips = []

  if (filters.search) {
    chips.push({ key: 'search', label: `Search: "${filters.search}"` })
  }

  if (filters.event_type) {
    const typeOption = eventTypeOptions.find(opt => opt.value === filters.event_type)
    chips.push({ key: 'event_type', label: `Type: ${typeOption?.label}` })
  }

  if (filters.include_hidden !== 'true') {
    const visOption = visibilityOptions.find(opt => opt.value === filters.include_hidden)
    chips.push({ key: 'include_hidden', label: `Visibility: ${visOption?.label}` })
  }

  if (filters.include_archived !== 'false') {
    const archOption = archivedOptions.find(opt => opt.value === filters.include_archived)
    chips.push({ key: 'include_archived', label: `Status: ${archOption?.label}` })
  }

  if (filters.start_date) {
    chips.push({ key: 'start_date', label: `From: ${filters.start_date}` })
  }

  if (filters.end_date) {
    chips.push({ key: 'end_date', label: `To: ${filters.end_date}` })
  }

  return chips
})

// Watch for filter changes and auto-apply
let searchTimeout: NodeJS.Timeout | null = null

watch(() => filters.search, (newValue) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    filters.skip = 0 // Reset to first page on search
    loadEvents()
  }, 300) // 300ms debounce
})

watch(() => [
  filters.event_type,
  filters.include_hidden,
  filters.include_archived,
  filters.start_date,
  filters.end_date,
  filters.limit,
  filters.order_by,
  filters.order_desc,
], () => {
  filters.skip = 0 // Reset to first page when filters change
  loadEvents()
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
      order_by: filters.order_by,
      order_desc: filters.order_desc,
    }

    if (filters.search) {
      params.search = filters.search
    }

    if (filters.event_type) {
      params.event_type = filters.event_type
    }

    if (filters.start_date) {
      params.start_date = new Date(filters.start_date).toISOString()
    }

    if (filters.end_date) {
      params.end_date = new Date(filters.end_date).toISOString()
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

const toggleSort = (field: string) => {
  if (filters.order_by === field) {
    filters.order_desc = !filters.order_desc
  } else {
    filters.order_by = field
    filters.order_desc = true
  }
}

const clearFilters = () => {
  filters.search = ''
  filters.event_type = ''
  filters.include_hidden = 'true'
  filters.include_archived = 'false'
  filters.start_date = ''
  filters.end_date = ''
}

const removeFilter = (key: string) => {
  switch (key) {
    case 'search':
      filters.search = ''
      break
    case 'event_type':
      filters.event_type = ''
      break
    case 'include_hidden':
      filters.include_hidden = 'true'
      break
    case 'include_archived':
      filters.include_archived = 'false'
      break
    case 'start_date':
      filters.start_date = ''
      break
    case 'end_date':
      filters.end_date = ''
      break
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

const getEventTypeColor = (type: string) => {
  switch (type) {
    case 'RECURRING':
      return 'blue'
    case 'AVAILABILITY':
      return 'purple'
    default:
      return 'gray'
  }
}

const getResponsesTooltip = (responses: any) => {
  if (!responses) return 'No responses yet'

  const accepted = responses.accepted_uids?.length || 0
  const declined = responses.declined_uids?.length || 0
  const unanswered = responses.unanswered_uids?.length || 0

  return `${accepted} accepted, ${declined} declined, ${unanswered} unanswered`
}

// Pagination functions
const goToFirstPage = () => {
  filters.skip = 0
  loadEvents()
}

const goToLastPage = () => {
  filters.skip = (totalPages.value - 1) * filters.limit
  loadEvents()
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    filters.skip += filters.limit
    loadEvents()
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    filters.skip = Math.max(0, filters.skip - filters.limit)
    loadEvents()
  }
}

// Calendar view handlers
const handleCalendarDatesChange = (dateRange: { start: string, end: string }) => {
  // When calendar navigation changes, update filters to match
  // This ensures events are fetched for the visible calendar range
  // Note: We don't auto-apply this to avoid unexpected filter changes
  // Users can still use the date filter inputs if they want specific date ranges
}

const handleCalendarViewChange = (viewType: string) => {
  // This is already saved in the FullCalendar component
  // Just a placeholder for any additional logic if needed
}
</script>
