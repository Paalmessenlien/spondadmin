<script setup lang="ts">
interface CategoryDetail {
  category_id: number
  category_name: string
  color: string
  icon?: string
  total_events: number
  avg_attendance_rate: number
  total_responses: number
  accepted: number
  declined?: number
}

interface ColumnConfig {
  key: keyof CategoryDetail
  label: string
  defaultVisible: boolean
  alwaysVisible?: boolean
}

const props = defineProps<{
  data: CategoryDetail[]
}>()

// Column configuration
const availableColumns: ColumnConfig[] = [
  { key: 'category_name', label: 'Category', defaultVisible: true, alwaysVisible: true },
  { key: 'total_events', label: 'Total Events', defaultVisible: true },
  { key: 'avg_attendance_rate', label: 'Avg Attendance Rate', defaultVisible: true },
  { key: 'total_responses', label: 'Total Responses', defaultVisible: true },
  { key: 'accepted', label: 'Accepted', defaultVisible: true },
  { key: 'declined', label: 'Declined', defaultVisible: true }
]

const visibleColumns = ref<Set<keyof CategoryDetail>>(
  new Set(availableColumns.filter(col => col.defaultVisible).map(col => col.key))
)

const isColumnVisible = (key: keyof CategoryDetail) => visibleColumns.value.has(key)

const toggleColumn = (key: keyof CategoryDetail) => {
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
const categories = computed(() => props.data || [])
const searchQuery = ref('')

const filteredCategories = computed(() => {
  let result = [...categories.value]

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(c => c.category_name.toLowerCase().includes(query))
  }

  return result
})

// Use composable for table state (with filtered data)
const tableState = useTableState(filteredCategories, 'total_events' as keyof CategoryDetail, true)

// Calculations
const calculations = computed(() => {
  const visible = tableState.sortedData.value
  if (visible.length === 0) {
    return {
      totalCategories: 0,
      totalEvents: 0,
      totalResponses: 0,
      totalAccepted: 0,
      totalDeclined: 0,
      avgAttendanceRate: '0.0'
    }
  }

  return {
    totalCategories: visible.length,
    totalEvents: visible.reduce((sum, c) => sum + c.total_events, 0),
    totalResponses: visible.reduce((sum, c) => sum + c.total_responses, 0),
    totalAccepted: visible.reduce((sum, c) => sum + c.accepted, 0),
    totalDeclined: visible.reduce((sum, c) => sum + (c.declined || 0), 0),
    avgAttendanceRate: (
      visible.reduce((sum, c) => sum + c.avg_attendance_rate, 0) / visible.length
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
const getSortIcon = (field: keyof CategoryDetail) => {
  if (tableState.sortField.value !== field) return null
  return tableState.sortDesc.value ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-up'
}

// Get attendance rate color
const getAttendanceRateColor = (rate: number) => {
  if (rate >= 80) return 'text-green-600'
  if (rate >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

// CSV Export
const { exportToCSV } = useCsvExport()

const exportTableToCSV = () => {
  const headers = [
    { key: 'category_name', label: 'Category' },
    { key: 'total_events', label: 'Total Events' },
    { key: 'avg_attendance_rate', label: 'Avg Attendance Rate (%)' },
    { key: 'total_responses', label: 'Total Responses' },
    { key: 'accepted', label: 'Accepted' },
    { key: 'declined', label: 'Declined' }
  ]

  const exportData = tableState.sortedData.value.map(cat => ({
    ...cat,
    avg_attendance_rate: cat.avg_attendance_rate.toFixed(1)
  }))

  const timestamp = new Date().toISOString().split('T')[0]
  exportToCSV(exportData, headers, `category-details-${timestamp}.csv`)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Filters and Actions -->
    <div class="flex flex-col gap-2">
      <div class="flex gap-2">
        <UInput
          v-model="searchQuery"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search categories..."
          class="flex-1"
        />
        <UButton
          v-if="searchQuery"
          icon="i-heroicons-x-mark"
          @click="searchQuery = ''; tableState.currentPage.value = 0"
          variant="soft"
        >
          Clear
        </UButton>
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
              v-if="isColumnVisible('category_name')"
              @click="tableState.toggleSort('category_name')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Category
                <UIcon v-if="getSortIcon('category_name')" :name="getSortIcon('category_name')!" class="w-4 h-4" />
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
              v-if="isColumnVisible('avg_attendance_rate')"
              @click="tableState.toggleSort('avg_attendance_rate')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Avg Attendance Rate
                <UIcon v-if="getSortIcon('avg_attendance_rate')" :name="getSortIcon('avg_attendance_rate')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('total_responses')"
              @click="tableState.toggleSort('total_responses')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Total Responses
                <UIcon v-if="getSortIcon('total_responses')" :name="getSortIcon('total_responses')!" class="w-4 h-4" />
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
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="tableState.paginatedData.value.length === 0">
            <td :colspan="visibleColumnCount" class="px-6 py-8 text-center text-gray-500">
              No categories found
            </td>
          </tr>
          <tr
            v-for="category in tableState.paginatedData.value"
            :key="category.category_id"
            class="hover:bg-gray-50"
          >
            <td v-if="isColumnVisible('category_name')" class="px-6 py-4 whitespace-nowrap text-sm">
              <div class="flex items-center gap-2">
                <UIcon
                  v-if="category.icon"
                  :name="category.icon"
                  class="w-5 h-5"
                  :style="{ color: category.color }"
                />
                <UBadge :style="{ backgroundColor: category.color }" class="text-white">
                  {{ category.category_name }}
                </UBadge>
              </div>
            </td>
            <td v-if="isColumnVisible('total_events')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700 font-medium">
              {{ category.total_events }}
            </td>
            <td
              v-if="isColumnVisible('avg_attendance_rate')"
              class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold"
              :class="getAttendanceRateColor(category.avg_attendance_rate)"
            >
              {{ category.avg_attendance_rate.toFixed(1) }}%
            </td>
            <td v-if="isColumnVisible('total_responses')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
              {{ category.total_responses }}
            </td>
            <td v-if="isColumnVisible('accepted')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ category.accepted }}
            </td>
            <td v-if="isColumnVisible('declined')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ category.declined || 0 }}
            </td>
          </tr>
        </tbody>
        <!-- Calculations Footer -->
        <tfoot class="bg-gray-100 font-semibold">
          <tr>
            <td v-if="isColumnVisible('category_name')" class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalCategories }} categories)
            </td>
            <td v-if="isColumnVisible('total_events')" class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalEvents }}
            </td>
            <td v-if="isColumnVisible('avg_attendance_rate')" class="px-6 py-3 text-sm text-right text-gray-700">
              Avg: {{ calculations.avgAttendanceRate }}%
            </td>
            <td v-if="isColumnVisible('total_responses')" class="px-6 py-3 text-sm text-right text-gray-500">
              {{ calculations.totalResponses }}
            </td>
            <td v-if="isColumnVisible('accepted')" class="px-6 py-3 text-sm text-right text-green-600">
              {{ calculations.totalAccepted }}
            </td>
            <td v-if="isColumnVisible('declined')" class="px-6 py-3 text-sm text-right text-red-600">
              {{ calculations.totalDeclined }}
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
