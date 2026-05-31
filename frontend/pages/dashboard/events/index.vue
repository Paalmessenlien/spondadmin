<template>
  <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Events</h1>
            <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Manage your Spond events
            </p>
          </div>

          <div class="flex flex-wrap gap-3">
            <UButton
              icon="i-heroicons-plus"
              color="primary"
              to="/dashboard/events/create"
            >
              Create Event
            </UButton>

            <UButton
              icon="i-heroicons-arrow-path"
              color="neutral"
              variant="outline"
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
            <!-- Row 1: Search + Type + Date range -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3 items-end">
              <div class="lg:col-span-5">
                <label class="block text-xs font-medium text-gray-500 mb-1">Search</label>
                <UInput
                  v-model="filters.search"
                  placeholder="Heading, description…"
                  icon="i-heroicons-magnifying-glass"
                  class="w-full"
                  :ui="{ base: 'w-full' }"
                >
                  <template #trailing>
                    <UButton
                      v-if="filters.search"
                      color="neutral"
                      variant="link"
                      icon="i-heroicons-x-mark"
                      :padded="false"
                      @click="filters.search = ''"
                    />
                  </template>
                </UInput>
              </div>

              <div class="lg:col-span-3">
                <label class="block text-xs font-medium text-gray-500 mb-1">Type</label>
                <select
                  v-model="filters.event_type"
                  class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
                >
                  <option
                    v-for="opt in eventTypeOptions"
                    :key="opt.value || 'all'"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </option>
                </select>
              </div>

              <div class="lg:col-span-2">
                <label class="block text-xs font-medium text-gray-500 mb-1">From</label>
                <UInput type="date" class="w-full" v-model="filters.start_date" />
              </div>

              <div class="lg:col-span-2">
                <label class="block text-xs font-medium text-gray-500 mb-1">To</label>
                <UInput type="date" class="w-full" v-model="filters.end_date" />
              </div>
            </div>

            <!-- Row 2: Toggles + Clear -->
            <div class="flex flex-wrap items-center justify-between gap-3 text-sm">
              <div class="flex flex-wrap gap-4">
                <label class="inline-flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="filters.include_hidden"
                    class="rounded border-gray-300 dark:border-gray-600"
                  />
                  <span class="text-gray-700 dark:text-gray-300">Include hidden</span>
                </label>
                <label class="inline-flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="filters.include_archived"
                    class="rounded border-gray-300 dark:border-gray-600"
                  />
                  <span class="text-gray-700 dark:text-gray-300">Include archived</span>
                </label>
              </div>

              <UButton
                v-if="hasActiveFilters"
                color="neutral"
                variant="outline"
                size="sm"
                icon="i-heroicons-x-circle"
                @click="clearFilters"
              >
                Clear filters
              </UButton>
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
                <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {{ filters.search ? `No results for "${filters.search}"` : 'Sync events from Spond to get started.' }}
                </p>
              </div>
            </template>

            <template v-else>
            <ResponsiveTable
              :columns="eventCols"
              :rows="events"
              row-key="id"
              :sort-field="filters.order_by"
              :sort-desc="filters.order_desc"
              empty-text="No events."
              @sort="toggleSort"
            >
              <template #cell-heading="{ row }">
                <div class="flex items-center gap-1.5 flex-wrap justify-end md:justify-start">
                  <NuxtLink :to="`/dashboard/events/${row.id}`" class="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline">
                    {{ row.heading }}
                  </NuxtLink>
                  <UBadge
                    v-if="row.linked_shift_id"
                    color="amber"
                    variant="subtle"
                    size="xs"
                    class="gap-1 shrink-0"
                    :title="`Published from training shift #${row.linked_shift_id}`"
                  >
                    <UIcon name="i-heroicons-academic-cap" class="w-3 h-3" />
                    Vakt
                  </UBadge>
                </div>
                <div v-if="row.description" class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 md:max-w-md" :title="row.description">
                  {{ row.description }}
                </div>
                <div v-if="row.category_id" class="mt-1">
                  <CategoryBadge :category-id="row.category_id" size="xs" />
                </div>
              </template>
              <template #cell-start_time="{ row }">
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.start_time) }}</span>
              </template>
              <template #cell-event_type="{ row }">
                <UBadge :color="getEventTypeColor(row.event_type)">{{ row.event_type }}</UBadge>
              </template>
              <template #cell-status="{ row }">
                <UBadge v-if="row.cancelled" color="red">Cancelled</UBadge>
                <UBadge v-else-if="row.hidden" color="orange">Hidden</UBadge>
                <UBadge v-else color="green">Active</UBadge>
              </template>
              <template #cell-sync="{ row }">
                <SyncStatusBadge :status="row.sync_status" :error="row.sync_error" />
              </template>
              <template #cell-responses="{ row }">
                <div class="flex gap-2 justify-end md:justify-start" :title="getResponsesTooltip(row.responses)">
                  <span class="text-green-600">✓ {{ row.responses?.acceptedIds?.length || 0 }}</span>
                  <span class="text-red-600">✗ {{ row.responses?.declinedIds?.length || 0 }}</span>
                  <span class="text-gray-600">? {{ row.responses?.unansweredIds?.length || 0 }}</span>
                </div>
              </template>
            </ResponsiveTable>

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
                  color="neutral"
                  variant="outline"
                  icon="i-heroicons-chevron-double-left"
                  :disabled="currentPage === 1"
                  @click="goToFirstPage"
                />
                <UButton
                  size="sm"
                  color="neutral"
                  variant="outline"
                  icon="i-heroicons-chevron-left"
                  :disabled="currentPage === 1"
                  @click="previousPage"
                />
                <div class="text-sm text-gray-700 dark:text-gray-300 px-3">
                  Page {{ currentPage }} of {{ totalPages }}
                </div>
                <UButton
                  size="sm"
                  color="neutral"
                  variant="outline"
                  icon="i-heroicons-chevron-right"
                  :disabled="currentPage === totalPages"
                  @click="nextPage"
                />
                <UButton
                  size="sm"
                  color="neutral"
                  variant="outline"
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
const authStore = useAuthStore()

const events = ref<any[]>([])
const total = ref(0)

const eventCols = [
  { key: 'heading', label: 'Event', primary: true, sortable: true },
  { key: 'start_time', label: 'Date', sortable: true },
  { key: 'event_type', label: 'Type' },
  { key: 'status', label: 'Status' },
  { key: 'sync', label: 'Sync' },
  { key: 'responses', label: 'Responses' },
] as const
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
  include_hidden: true,    // visible+hidden by default
  include_archived: false, // active & upcoming by default
  start_date: '',
  end_date: '',
  skip: 0,
  limit: 20,
  order_by: 'start_time',
  order_desc: true, // Show newest events first
})

// Filter options
const eventTypeOptions = [
  { label: 'All types', value: '' },
  { label: 'Regular events', value: 'EVENT' },
  { label: 'Recurring events', value: 'RECURRING' },
  { label: 'Availability', value: 'AVAILABILITY' },
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
  return !!filters.search ||
         !!filters.event_type ||
         filters.include_hidden === false ||
         filters.include_archived === true ||
         !!filters.start_date ||
         !!filters.end_date
})

const activeFilterChips = computed(() => {
  const chips: { key: string; label: string }[] = []

  if (filters.search) {
    chips.push({ key: 'search', label: `Search: "${filters.search}"` })
  }

  if (filters.event_type) {
    const typeOption = eventTypeOptions.find(opt => opt.value === filters.event_type)
    chips.push({ key: 'event_type', label: `Type: ${typeOption?.label}` })
  }

  if (filters.include_hidden === false) {
    chips.push({ key: 'include_hidden', label: 'Hidden: excluded' })
  }

  if (filters.include_archived === true) {
    chips.push({ key: 'include_archived', label: 'Archived: included' })
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

// Watch for group changes and reload events
watch(() => authStore.selectedGroupId, () => {
  filters.skip = 0 // Reset to first page on group change
  loadEvents()
})

const loadEvents = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: filters.skip,
      limit: filters.limit,
      order_by: filters.order_by,
      order_desc: filters.order_desc,
    }

    params.include_hidden = !!filters.include_hidden
    params.include_archived = !!filters.include_archived

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
  filters.include_hidden = true
  filters.include_archived = false
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
      filters.include_hidden = true
      break
    case 'include_archived':
      filters.include_archived = false
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

  const accepted = responses.acceptedIds?.length || 0
  const declined = responses.declinedIds?.length || 0
  const unanswered = responses.unansweredIds?.length || 0

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
  // When calendar navigation changes, update filters to fetch events for the visible range
  if (selectedView.value === 'calendar') {
    filters.start_date = dateRange.start.split('T')[0] // Extract date part
    filters.end_date = dateRange.end.split('T')[0]
    filters.limit = 500 // Increase limit to get all events in the range
    filters.skip = 0
    loadEvents()
  }
}

const handleCalendarViewChange = (viewType: string) => {
  // This is already saved in the FullCalendar component
  // Just a placeholder for any additional logic if needed
}

// Watch for view changes to adjust filters
watch(selectedView, (newView, oldView) => {
  if (newView === 'calendar') {
    // When switching to calendar, we'll let the calendar component trigger date changes
    // which will update filters through handleCalendarDatesChange
  } else if (newView === 'upcoming') {
    // When switching to upcoming view, load more events and clear date filters
    filters.start_date = ''
    filters.end_date = ''
    filters.limit = 100 // Load more events for better grouping
    filters.skip = 0
    loadEvents()
  } else if (oldView === 'calendar' || oldView === 'upcoming') {
    // When leaving calendar or upcoming view, restore normal list filters
    filters.start_date = ''
    filters.end_date = ''
    filters.limit = 20
    filters.skip = 0
    loadEvents()
  }
})
</script>
