<script setup lang="ts">
interface AttendanceLogEntry {
  date: string
  total_events: number
  accepted: number
  declined: number
  unanswered: number
  acceptance_rate: number
}

interface AttendanceLogData {
  period: string
  data: AttendanceLogEntry[]
}

const props = defineProps<{
  data: AttendanceLogData
}>()

// Custom filtering
const logEntries = computed(() => props.data?.data || [])
const startDateFilter = ref<string>('')
const endDateFilter = ref<string>('')

const filteredEntries = computed(() => {
  let result = [...logEntries.value]

  // Date range filter
  if (startDateFilter.value) {
    result = result.filter(e => e.date >= startDateFilter.value)
  }
  if (endDateFilter.value) {
    result = result.filter(e => e.date <= endDateFilter.value)
  }

  return result
})

// Use composable for table state (with filtered data)
const tableState = useTableState(filteredEntries, 'date' as keyof AttendanceLogEntry, true)

// Watch for filter changes to reset page
watch([startDateFilter, endDateFilter], () => {
  tableState.currentPage.value = 0
})

// Calculations
const calculations = computed(() => {
  const visible = tableState.sortedData.value
  if (visible.length === 0) {
    return {
      totalDays: 0,
      totalEvents: 0,
      totalAccepted: 0,
      totalDeclined: 0,
      totalUnanswered: 0,
      avgAcceptanceRate: '0.0'
    }
  }

  return {
    totalDays: visible.length,
    totalEvents: visible.reduce((sum, e) => sum + e.total_events, 0),
    totalAccepted: visible.reduce((sum, e) => sum + e.accepted, 0),
    totalDeclined: visible.reduce((sum, e) => sum + e.declined, 0),
    totalUnanswered: visible.reduce((sum, e) => sum + e.unanswered, 0),
    avgAcceptanceRate: (
      visible.reduce((sum, e) => sum + e.acceptance_rate, 0) / visible.length
    ).toFixed(1)
  }
})

// Page size options
const pageSizeOptions = [
  { label: '10', value: 10 },
  { label: '20', value: 20 },
  { label: '50', value: 50 },
  { label: '100', value: 100 }
]

// Get sort icon
const getSortIcon = (field: keyof AttendanceLogEntry) => {
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
    weekday: 'short'
  })
}

// Get acceptance rate color
const getAcceptanceRateColor = (rate: number) => {
  if (rate >= 80) return 'text-green-600'
  if (rate >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

// Clear date filters
const clearDateFilters = () => {
  startDateFilter.value = ''
  endDateFilter.value = ''
}

const hasDateFilters = computed(() => startDateFilter.value || endDateFilter.value)
</script>

<template>
  <div class="space-y-4">
    <!-- Filters -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
      <UInput
        v-model="startDateFilter"
        type="date"
        label="Start Date"
        placeholder="Start date"
      />
      <UInput
        v-model="endDateFilter"
        type="date"
        label="End Date"
        placeholder="End date"
      />
      <div class="flex items-end">
        <UButton
          v-if="hasDateFilters"
          icon="i-heroicons-x-mark"
          @click="clearDateFilters"
          variant="soft"
          class="w-full"
        >
          Clear Filters
        </UButton>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              @click="tableState.toggleSort('date')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Date
                <UIcon v-if="getSortIcon('date')" :name="getSortIcon('date')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('total_events')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Total Events
                <UIcon v-if="getSortIcon('total_events')" :name="getSortIcon('total_events')!" class="w-4 h-4" />
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
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
              No attendance data found
            </td>
          </tr>
          <tr
            v-for="entry in tableState.paginatedData.value"
            :key="entry.date"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ formatDate(entry.date) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700 font-medium">
              {{ entry.total_events }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ entry.accepted }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ entry.declined }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-400">
              {{ entry.unanswered }}
            </td>
            <td
              class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold"
              :class="getAcceptanceRateColor(entry.acceptance_rate)"
            >
              {{ entry.acceptance_rate.toFixed(1) }}%
            </td>
          </tr>
        </tbody>
        <!-- Calculations Footer -->
        <tfoot class="bg-gray-100 font-semibold">
          <tr>
            <td class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalDays }} {{ props.data?.period || 'day' }}s)
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalEvents }}
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
