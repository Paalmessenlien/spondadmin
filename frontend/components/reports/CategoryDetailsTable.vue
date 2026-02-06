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

const props = defineProps<{
  data: CategoryDetail[]
}>()

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
</script>

<template>
  <div class="space-y-4">
    <!-- Filters -->
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

    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              @click="tableState.toggleSort('category_name')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Category
                <UIcon v-if="getSortIcon('category_name')" :name="getSortIcon('category_name')!" class="w-4 h-4" />
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
              @click="tableState.toggleSort('avg_attendance_rate')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Avg Attendance Rate
                <UIcon v-if="getSortIcon('avg_attendance_rate')" :name="getSortIcon('avg_attendance_rate')!" class="w-4 h-4" />
              </div>
            </th>
            <th
              @click="tableState.toggleSort('total_responses')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Total Responses
                <UIcon v-if="getSortIcon('total_responses')" :name="getSortIcon('total_responses')!" class="w-4 h-4" />
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
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="tableState.paginatedData.value.length === 0">
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
              No categories found
            </td>
          </tr>
          <tr
            v-for="category in tableState.paginatedData.value"
            :key="category.category_id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4 whitespace-nowrap text-sm">
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
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700 font-medium">
              {{ category.total_events }}
            </td>
            <td
              class="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold"
              :class="getAttendanceRateColor(category.avg_attendance_rate)"
            >
              {{ category.avg_attendance_rate.toFixed(1) }}%
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
              {{ category.total_responses }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ category.accepted }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ category.declined || 0 }}
            </td>
          </tr>
        </tbody>
        <!-- Calculations Footer -->
        <tfoot class="bg-gray-100 font-semibold">
          <tr>
            <td class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalCategories }} categories)
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalEvents }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
              Avg: {{ calculations.avgAttendanceRate }}%
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-500">
              {{ calculations.totalResponses }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-green-600">
              {{ calculations.totalAccepted }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-red-600">
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
