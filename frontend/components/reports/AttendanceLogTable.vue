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

interface ColumnConfig {
  key: keyof AttendanceLogEntry
  label: string
  defaultVisible: boolean
  alwaysVisible?: boolean
}

// Column configuration
const availableColumns: ColumnConfig[] = [
  { key: 'date', label: 'Date', defaultVisible: true, alwaysVisible: true },
  { key: 'total_events', label: 'Total Events', defaultVisible: true },
  { key: 'accepted', label: 'Accepted', defaultVisible: true },
  { key: 'declined', label: 'Declined', defaultVisible: true },
  { key: 'unanswered', label: 'Unanswered', defaultVisible: true },
  { key: 'acceptance_rate', label: 'Acceptance Rate', defaultVisible: true }
]

const visibleColumns = ref<Set<keyof AttendanceLogEntry>>(
  new Set(availableColumns.filter(col => col.defaultVisible).map(col => col.key))
)

const isColumnVisible = (key: keyof AttendanceLogEntry) => visibleColumns.value.has(key)

const toggleColumn = (key: keyof AttendanceLogEntry) => {
  const column = availableColumns.find(col => col.key === key)
  if (column?.alwaysVisible) return

  if (visibleColumns.value.has(key)) {
    visibleColumns.value.delete(key)
  } else {
    visibleColumns.value.add(key)
  }
}

const visibleColumnCount = computed(() => visibleColumns.value.size)

// Column menu toggle
const showColumnMenu = ref(false)

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

// Page size selection (handle object binding)
const selectedPageSize = computed({
  get: () => pageSizeOptions.find(opt => opt.value === tableState.pageSize.value),
  set: (option) => {
    if (option) {
      tableState.pageSize.value = option.value
    }
  }
})

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

// CSV Export
const { exportToCSV } = useCsvExport()

const exportTableToCSV = () => {
  const headers = [
    { key: 'date', label: 'Date' },
    { key: 'total_events', label: 'Total Events' },
    { key: 'accepted', label: 'Accepted' },
    { key: 'declined', label: 'Declined' },
    { key: 'unanswered', label: 'Unanswered' },
    { key: 'acceptance_rate', label: 'Acceptance Rate (%)' }
  ]

  const exportData = tableState.sortedData.value.map(entry => ({
    ...entry,
    date: formatDate(entry.date),
    acceptance_rate: entry.acceptance_rate.toFixed(1)
  }))

  const timestamp = new Date().toISOString().split('T')[0]
  exportToCSV(exportData, headers, `attendance-log-${timestamp}.csv`)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Filters and Actions -->
    <div class="flex flex-col gap-2">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Start Date</label>
          <DateInputISO v-model="startDateFilter" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">End Date</label>
          <DateInputISO v-model="endDateFilter" />
        </div>
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

      <div class="flex justify-end gap-2 relative">
        <div class="relative">
          <UButton
            icon="i-heroicons-view-columns"
            variant="soft"
            color="gray"
            @click="showColumnMenu = !showColumnMenu"
          >
            Columns
          </UButton>

          <div
            v-if="showColumnMenu"
            class="absolute right-0 mt-2 w-64 bg-white shadow-lg rounded-lg border border-gray-200 p-4 z-50"
          >
            <div class="space-y-2">
              <div
                v-for="column in availableColumns"
                :key="column.key"
                class="flex items-center gap-2 hover:bg-gray-50 px-2 py-1 rounded cursor-pointer"
                @click="!column.alwaysVisible && toggleColumn(column.key)"
              >
                <UCheckbox
                  :model-value="isColumnVisible(column.key)"
                  :disabled="column.alwaysVisible"
                  @click.stop
                  @update:model-value="toggleColumn(column.key)"
                />
                <label
                  class="text-sm select-none flex-1"
                  :class="{ 'text-gray-400': column.alwaysVisible, 'cursor-pointer': !column.alwaysVisible }"
                >
                  {{ column.label }}
                </label>
              </div>
            </div>
          </div>
        </div>

        <UButton
          icon="i-heroicons-arrow-down-tray"
          @click="exportTableToCSV"
          variant="soft"
          color="gray"
          :disabled="tableState.sortedData.value.length === 0"
        >
          Export to CSV
        </UButton>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-if="isColumnVisible('date')"
              @click="tableState.toggleSort('date')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Date
                <UIcon v-if="getSortIcon('date')" :name="getSortIcon('date')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('total_events')"
              @click="tableState.toggleSort('total_events')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Total Events
                <UIcon v-if="getSortIcon('total_events')" :name="getSortIcon('total_events')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('accepted')"
              @click="tableState.toggleSort('accepted')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Accepted
                <UIcon v-if="getSortIcon('accepted')" :name="getSortIcon('accepted')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('declined')"
              @click="tableState.toggleSort('declined')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Declined
                <UIcon v-if="getSortIcon('declined')" :name="getSortIcon('declined')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('unanswered')"
              @click="tableState.toggleSort('unanswered')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Unanswered
                <UIcon v-if="getSortIcon('unanswered')" :name="getSortIcon('unanswered')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('acceptance_rate')"
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
            <td :colspan="visibleColumnCount" class="px-6 py-8 text-center text-gray-500">
              No attendance data found
            </td>
          </tr>
          <tr
            v-for="entry in tableState.paginatedData.value"
            :key="entry.date"
            class="hover:bg-gray-50"
          >
            <td v-if="isColumnVisible('date')" class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ formatDate(entry.date) }}
            </td>
            <td v-if="isColumnVisible('total_events')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700 font-medium">
              {{ entry.total_events }}
            </td>
            <td v-if="isColumnVisible('accepted')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ entry.accepted }}
            </td>
            <td v-if="isColumnVisible('declined')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ entry.declined }}
            </td>
            <td v-if="isColumnVisible('unanswered')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-400">
              {{ entry.unanswered }}
            </td>
            <td
              v-if="isColumnVisible('acceptance_rate')"
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
            <td v-if="isColumnVisible('date')" class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalDays }} {{ props.data?.period || 'day' }}s)
            </td>
            <td v-if="isColumnVisible('total_events')" class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalEvents }}
            </td>
            <td v-if="isColumnVisible('accepted')" class="px-6 py-3 text-sm text-right text-green-600">
              {{ calculations.totalAccepted }}
            </td>
            <td v-if="isColumnVisible('declined')" class="px-6 py-3 text-sm text-right text-red-600">
              {{ calculations.totalDeclined }}
            </td>
            <td v-if="isColumnVisible('unanswered')" class="px-6 py-3 text-sm text-right text-gray-400">
              {{ calculations.totalUnanswered }}
            </td>
            <td v-if="isColumnVisible('acceptance_rate')" class="px-6 py-3 text-sm text-right text-gray-700">
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
          v-model="selectedPageSize"
          :items="pageSizeOptions"
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
