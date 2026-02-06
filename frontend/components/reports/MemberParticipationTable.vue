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

const props = defineProps<{
  data: MemberParticipationData
}>()

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
</script>

<template>
  <div class="space-y-4">
    <!-- Filters -->
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

    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              @click="tableState.toggleSort('member_name')"
              class="cursor-pointer px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center gap-1">
                Member Name
                <UIcon v-if="getSortIcon('member_name')" :name="getSortIcon('member_name')!" class="w-4 h-4" />
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
              @click="tableState.toggleSort('attended')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                Attended
                <UIcon v-if="getSortIcon('attended')" :name="getSortIcon('attended')!" class="w-4 h-4" />
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
              @click="tableState.toggleSort('no_response')"
              class="cursor-pointer px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hover:bg-gray-100"
            >
              <div class="flex items-center justify-end gap-1">
                No Response
                <UIcon v-if="getSortIcon('no_response')" :name="getSortIcon('no_response')!" class="w-4 h-4" />
              </div>
            </th>
            <th
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
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
              No members found
            </td>
          </tr>
          <tr
            v-for="member in tableState.paginatedData.value"
            :key="member.member_id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ member.member_name }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
              {{ member.total_events }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
              {{ member.attended }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
              {{ member.declined }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-400">
              {{ member.no_response }}
            </td>
            <td
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
            <td class="px-6 py-3 text-sm text-gray-700">
              Totals ({{ calculations.totalMembers }} members)
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
              {{ calculations.totalEvents }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-green-600">
              {{ calculations.totalAttended }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-red-600">
              {{ calculations.totalDeclined }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-400">
              {{ calculations.totalNoResponse }}
            </td>
            <td class="px-6 py-3 text-sm text-right text-gray-700">
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
