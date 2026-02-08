<script setup lang="ts">
interface MemberStat {
  member_id: number
  member_name: string
  total_events: number
  attended: number
  declined: number
  no_response: number
  attendance_rate: number
}

interface MemberParticipationData {
  members: MemberStat[]
  total: number
}

interface ColumnConfig {
  key: keyof MemberStat
  label: string
  defaultVisible: boolean
  alwaysVisible?: boolean
}

const props = defineProps<{
  data: MemberParticipationData
}>()

// Column configuration
const availableColumns: ColumnConfig[] = [
  { key: 'member_name', label: 'Member Name', defaultVisible: true, alwaysVisible: true },
  { key: 'total_events', label: 'Total Events', defaultVisible: true },
  { key: 'attended', label: 'Attended', defaultVisible: true },
  { key: 'declined', label: 'Declined', defaultVisible: true },
  { key: 'no_response', label: 'No Response', defaultVisible: true },
  { key: 'attendance_rate', label: 'Attendance Rate', defaultVisible: true }
]

const visibleColumns = ref<Set<keyof MemberStat>>(
  new Set(availableColumns.filter(col => col.defaultVisible).map(col => col.key))
)

const isColumnVisible = (key: keyof MemberStat) => visibleColumns.value.has(key)

const toggleColumn = (key: keyof MemberStat) => {
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

// Custom filtering logic
const members = computed(() => props.data?.members || [])

const filteredMembers = computed(() => {
  let result = [...members.value]

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(m => m.member_name.toLowerCase().includes(query))
  }

  return result
})

// Use composable for table state (with filtered data)
const searchQuery = ref('')
const tableState = useTableState(filteredMembers, 'attendance_rate' as keyof MemberStat, true)

// Calculations based on visible (sorted) data
const calculations = computed(() => {
  const visible = tableState.sortedData.value
  if (visible.length === 0) {
    return {
      totalMembers: 0,
      totalEvents: 0,
      totalAttended: 0,
      totalDeclined: 0,
      totalNoResponse: 0,
      avgAttendanceRate: '0.0'
    }
  }

  return {
    totalMembers: visible.length,
    totalEvents: visible.reduce((sum, m) => sum + m.total_events, 0),
    totalAttended: visible.reduce((sum, m) => sum + m.attended, 0),
    totalDeclined: visible.reduce((sum, m) => sum + m.declined, 0),
    totalNoResponse: visible.reduce((sum, m) => sum + m.no_response, 0),
    avgAttendanceRate: (visible.reduce((sum, m) => sum + m.attendance_rate, 0) / visible.length).toFixed(1)
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
const getSortIcon = (field: keyof MemberStat) => {
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
    { key: 'member_name', label: 'Member Name' },
    { key: 'total_events', label: 'Total Events' },
    { key: 'attended', label: 'Attended' },
    { key: 'declined', label: 'Declined' },
    { key: 'no_response', label: 'No Response' },
    { key: 'attendance_rate', label: 'Attendance Rate (%)' }
  ]

  const timestamp = new Date().toISOString().split('T')[0]
  exportToCSV(tableState.sortedData.value, headers, `member-participation-${timestamp}.csv`)
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
          placeholder="Search members..."
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
            v-click-outside="() => showColumnMenu = false"
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
              v-if="isColumnVisible('member_name')"
              @click="tableState.toggleSort('member_name')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Member Name
                <UIcon v-if="getSortIcon('member_name')" :name="getSortIcon('member_name')!" class="w-4 h-4" />
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
              v-if="isColumnVisible('attended')"
              @click="tableState.toggleSort('attended')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Attended
                <UIcon v-if="getSortIcon('attended')" :name="getSortIcon('attended')!" class="w-4 h-4" />
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
              v-if="isColumnVisible('no_response')"
              @click="tableState.toggleSort('no_response')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                No Response
                <UIcon v-if="getSortIcon('no_response')" :name="getSortIcon('no_response')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              v-if="isColumnVisible('attendance_rate')"
              @click="tableState.toggleSort('attendance_rate')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Attendance Rate
                <UIcon v-if="getSortIcon('attendance_rate')" :name="getSortIcon('attendance_rate')!" class="w-4 h-4" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="tableState.paginatedData.value.length === 0">
            <td :colspan="visibleColumnCount" class="px-6 py-8 text-center text-gray-500">
              No members found
            </td>
          </tr>
          <tr
            v-for="member in tableState.paginatedData.value"
            :key="member.member_id"
            class="hover:bg-gray-50"
          >
            <td v-if="isColumnVisible('member_name')" class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ member.member_name }}
            </td>
            <td v-if="isColumnVisible('total_events')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
              {{ member.total_events }}
            </td>
            <td v-if="isColumnVisible('attended')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ member.attended }}
            </td>
            <td v-if="isColumnVisible('declined')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ member.declined }}
            </td>
            <td v-if="isColumnVisible('no_response')" class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-400">
              {{ member.no_response }}
            </td>
            <td
              v-if="isColumnVisible('attendance_rate')"
              class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold"
              :class="getAttendanceRateColor(member.attendance_rate)"
            >
              {{ member.attendance_rate }}%
            </td>
          </tr>
        </tbody>
        <!-- Calculations Footer -->
        <tfoot class="bg-gray-100 font-semibold">
          <tr>
            <td v-if="isColumnVisible('member_name')" class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalMembers }} members)
            </td>
            <td v-if="isColumnVisible('total_events')" class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalEvents }}
            </td>
            <td v-if="isColumnVisible('attended')" class="px-6 py-3 text-sm text-right text-green-600">
              {{ calculations.totalAttended }}
            </td>
            <td v-if="isColumnVisible('declined')" class="px-6 py-3 text-sm text-right text-red-600">
              {{ calculations.totalDeclined }}
            </td>
            <td v-if="isColumnVisible('no_response')" class="px-6 py-3 text-sm text-right text-gray-400">
              {{ calculations.totalNoResponse }}
            </td>
            <td v-if="isColumnVisible('attendance_rate')" class="px-6 py-3 text-sm text-right text-gray-700">
              Avg: {{ calculations.avgAttendanceRate }}%
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
