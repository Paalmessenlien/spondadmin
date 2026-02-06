<script setup lang="ts">
interface Organizer {
  id: string
  name: string
  response: string
}

interface EventDetail {
  event_id: number
  heading: string
  start_time: string
  category_name: string
  category_color: string
  total_invites: number
  accepted: number
  declined: number
  unanswered: number
  acceptance_rate: number
  organizers?: Organizer[]
}

const props = defineProps<{
  data: EventDetail[]
}>()

// Custom filtering
const events = computed(() => props.data || [])
const searchQuery = ref('')
const selectedCategories = ref<{ label: string; value: string }[]>([])
const minAcceptanceRate = ref<number | null>(null)

const filteredEvents = computed(() => {
  let result = [...events.value]

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(e => e.heading.toLowerCase().includes(query))
  }

  // Category filter
  if (selectedCategories.value.length > 0) {
    const selectedCategoryNames = selectedCategories.value.map(c => c.value)
    result = result.filter(e => selectedCategoryNames.includes(e.category_name))
  }

  // Acceptance rate filter
  if (minAcceptanceRate.value !== null) {
    result = result.filter(e => e.acceptance_rate >= minAcceptanceRate.value!)
  }

  return result
})

// Use composable for table state (with filtered data)
const tableState = useTableState(filteredEvents, 'start_time' as keyof EventDetail, true)

// Watch for filter changes to reset page
watch([selectedCategories, minAcceptanceRate, searchQuery], () => {
  tableState.currentPage.value = 0
})

// Get unique categories for filter
const categories = computed(() => {
  const uniqueCats = new Set(events.value.map(e => e.category_name))
  return Array.from(uniqueCats).sort()
})

// Calculations
const calculations = computed(() => {
  const visible = tableState.sortedData.value
  if (visible.length === 0) {
    return {
      totalEvents: 0,
      totalInvites: 0,
      totalAccepted: 0,
      totalDeclined: 0,
      totalUnanswered: 0,
      avgAcceptanceRate: '0.0'
    }
  }

  return {
    totalEvents: visible.length,
    totalInvites: visible.reduce((sum, e) => sum + e.total_invites, 0),
    totalAccepted: visible.reduce((sum, e) => sum + e.accepted, 0),
    totalDeclined: visible.reduce((sum, e) => sum + e.declined, 0),
    totalUnanswered: visible.reduce((sum, e) => sum + e.unanswered, 0),
    avgAcceptanceRate: (visible.reduce((sum, e) => sum + e.acceptance_rate, 0) / visible.length).toFixed(1)
  }
})

// Page size options
const pageSizeOptions = [
  { label: '10', value: 10 },
  { label: '20', value: 20 },
  { label: '50', value: 50 },
  { label: '100', value: 100 }
]

// Category options for filter
const categoryOptions = computed(() =>
  categories.value.map(cat => ({ label: cat, value: cat }))
)

// Get sort icon
const getSortIcon = (field: keyof EventDetail) => {
  if (tableState.sortField.value !== field) return null
  return tableState.sortDesc.value ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-up'
}

// Format date
const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Get acceptance rate color
const getAcceptanceRateColor = (rate: number) => {
  if (rate >= 80) return 'text-green-600'
  if (rate >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

// Clear all filters
const clearAllFilters = () => {
  searchQuery.value = ''
  selectedCategories.value = []
  minAcceptanceRate.value = null
  tableState.currentPage.value = 0
}

const hasActiveFilters = computed(() =>
  searchQuery.value ||
  selectedCategories.value.length > 0 ||
  minAcceptanceRate.value !== null
)
</script>

<template>
  <div class="space-y-4">
    <!-- Filters -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
      <UInput
        v-model="searchQuery"
        icon="i-heroicons-magnifying-glass"
        placeholder="Search events..."
      />

      <USelectMenu
        v-model="selectedCategories"
        :items="categoryOptions"
        multiple
        placeholder="Filter by category..."
      />

      <div class="flex gap-2">
        <UInput
          v-model.number="minAcceptanceRate"
          type="number"
          min="0"
          max="100"
          placeholder="Min acceptance rate %"
        />
        <UButton
          v-if="hasActiveFilters"
          icon="i-heroicons-x-mark"
          @click="clearAllFilters"
          variant="soft"
        >
          Clear
        </UButton>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              @click="tableState.toggleSort('heading')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Event Name
                <UIcon v-if="getSortIcon('heading')" :name="getSortIcon('heading')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('start_time')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Date
                <UIcon v-if="getSortIcon('start_time')" :name="getSortIcon('start_time')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('category_name')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Category
                <UIcon v-if="getSortIcon('category_name')" :name="getSortIcon('category_name')!" class="w-4 h-4" />
              </div>
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Organizers
            </th>
            <th
              @click="tableState.toggleSort('total_invites')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Total Invites
                <UIcon v-if="getSortIcon('total_invites')" :name="getSortIcon('total_invites')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('accepted')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Accepted
                <UIcon v-if="getSortIcon('accepted')" :name="getSortIcon('accepted')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('declined')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Declined
                <UIcon v-if="getSortIcon('declined')" :name="getSortIcon('declined')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('unanswered')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Unanswered
                <UIcon v-if="getSortIcon('unanswered')" :name="getSortIcon('unanswered')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('acceptance_rate')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Acceptance Rate
                <UIcon v-if="getSortIcon('acceptance_rate')" :name="getSortIcon('acceptance_rate')!" class="w-4 h-4" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="tableState.paginatedData.value.length === 0">
            <td colspan="9" class="px-6 py-8 text-center text-gray-500">
              No events found
            </td>
          </tr>
          <tr
            v-for="event in tableState.paginatedData.value"
            :key="event.event_id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              <NuxtLink
                :to="`/dashboard/events/${event.event_id}`"
                class="text-blue-600 hover:text-blue-800 hover:underline"
              >
                {{ event.heading }}
              </NuxtLink>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(event.start_time) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <UBadge :style="{ backgroundColor: event.category_color }" class="text-white">
                {{ event.category_name }}
              </UBadge>
            </td>
            <td class="px-6 py-4 text-sm">
              <div v-if="event.organizers && event.organizers.length > 0" class="flex flex-wrap gap-1">
                <span
                  v-for="org in event.organizers"
                  :key="org.id"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                  :class="{
                    'bg-green-100 text-green-800': org.response === 'accepted',
                    'bg-red-100 text-red-800': org.response === 'declined',
                    'bg-gray-100 text-gray-600': org.response === 'unanswered'
                  }"
                >
                  {{ org.name }}
                </span>
              </div>
              <span v-else class="text-gray-400 text-xs">No organizers</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
              {{ event.total_invites }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ event.accepted }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ event.declined }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-400">
              {{ event.unanswered }}
            </td>
            <td
              class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold"
              :class="getAcceptanceRateColor(event.acceptance_rate)"
            >
              {{ event.acceptance_rate }}%
            </td>
          </tr>
        </tbody>
        <!-- Calculations Footer -->
        <tfoot class="bg-gray-100 font-semibold">
          <tr>
            <td colspan="4" class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalEvents }} events)
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalInvites }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-green-600">
              {{ calculations.totalAccepted }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-red-600">
              {{ calculations.totalDeclined }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-400">
              {{ calculations.totalUnanswered }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
              Avg: {{ calculations.avgAcceptanceRate }}%
            </td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm text-gray-700">Show</span>
        <USelectMenu
          v-model="tableState.pageSize.value"
          :items="pageSizeOptions"
          value-attribute="value"
        />
        <span class="text-sm text-gray-700">per page</span>
      </div>

      <div class="flex items-center gap-2">
        <UButton
          icon="i-heroicons-chevron-left"
          :disabled="tableState.currentPage.value === 0"
          @click="tableState.prevPage"
          variant="soft"
        />
        <span class="text-sm text-gray-700">
          {{ tableState.currentPage.value * tableState.pageSize.value + 1 }}-{{
            Math.min(
              (tableState.currentPage.value + 1) * tableState.pageSize.value,
              tableState.sortedData.value.length
            )
          }}
          of {{ tableState.sortedData.value.length }}
        </span>
        <UButton
          icon="i-heroicons-chevron-right"
          :disabled="
            (tableState.currentPage.value + 1) * tableState.pageSize.value >=
            tableState.sortedData.value.length
          "
          @click="tableState.nextPage"
          variant="soft"
        />
      </div>
    </div>
  </div>
</template>
