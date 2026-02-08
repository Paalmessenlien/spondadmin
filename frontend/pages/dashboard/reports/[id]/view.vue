<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

import CategoryDistributionChart from '~/components/charts/CategoryDistributionChart.vue'
import CategoryComparisonChart from '~/components/charts/CategoryComparisonChart.vue'
import AttendanceTrendChart from '~/components/AttendanceTrendChart.vue'
import ResponseRateChart from '~/components/ResponseRateChart.vue'
import Breadcrumb from '~/components/Breadcrumb.vue'
import ReportExportButton from '~/components/ReportExportButton.vue'
import MemberParticipationTable from '~/components/reports/MemberParticipationTable.vue'
import EventDetailsTable from '~/components/reports/EventDetailsTable.vue'
import CategoryDetailsTable from '~/components/reports/CategoryDetailsTable.vue'
import AttendanceLogTable from '~/components/reports/AttendanceLogTable.vue'
import OrganizerStatisticsTable from '~/components/reports/OrganizerStatisticsTable.vue'

const route = useRoute()
const reportStore = useReportStore()
const toast = useToast()

const reportId = computed(() => parseInt(route.params.id as string))

onMounted(async () => {
  await reportStore.fetchReport(reportId.value)
  await generateReport()
})

const generating = ref(false)

const generateReport = async () => {
  generating.value = true
  try {
    await reportStore.generateReport(reportId.value)
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  } finally {
    generating.value = false
  }
}

const handleExport = async () => {
  try {
    await reportStore.exportReport(reportId.value, 'csv')
    toast.add({ title: 'Success', description: 'Report exported', color: 'green' })
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}
</script>

<template>
  <div class="p-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Reports', to: '/dashboard/reports' },
      { label: reportStore.currentReport?.name || 'View' }
    ]" />

    <div v-if="reportStore.currentReport" class="space-y-6">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-3xl font-bold">{{ reportStore.currentReport.name }}</h1>
          <p v-if="reportStore.currentReport.description" class="text-gray-600 mt-1">
            {{ reportStore.currentReport.description }}
          </p>
        </div>
        <div class="flex gap-2">
          <UButton icon="i-heroicons-arrow-path" @click="generateReport" :loading="generating" variant="soft">
            Refresh
          </UButton>
          <ReportExportButton :report-id="reportId" @export="handleExport" />
        </div>
      </div>

      <div v-if="generating" class="flex justify-center py-12">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>

      <div v-else-if="reportStore.reportData" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Category Distribution -->
        <UCard v-if="reportStore.reportData.data.category_distribution">
          <template #header>
            <h2 class="text-lg font-semibold">Category Distribution</h2>
          </template>
          <CategoryDistributionChart :data="reportStore.reportData.data.category_distribution" />
        </UCard>

        <!-- Attendance Trends -->
        <UCard v-if="reportStore.reportData.data.attendance_trends">
          <template #header>
            <h2 class="text-lg font-semibold">Attendance Trends</h2>
          </template>
          <AttendanceTrendChart :data="reportStore.reportData.data.attendance_trends" />
        </UCard>

        <!-- Response Rates -->
        <UCard v-if="reportStore.reportData.data.response_rates">
          <template #header>
            <h2 class="text-lg font-semibold">Response Rates</h2>
          </template>
          <ResponseRateChart :data="reportStore.reportData.data.response_rates" />
        </UCard>

        <!-- Summary Statistics -->
        <UCard v-if="reportStore.reportData.data.summary">
          <template #header>
            <h2 class="text-lg font-semibold">Summary</h2>
          </template>
          <div class="space-y-6">
            <!-- Basic Stats -->
            <div class="grid grid-cols-2 gap-4">
              <div v-if="reportStore.reportData.data.summary.total_events !== undefined">
                <div class="text-sm text-gray-600">Total Events</div>
                <div class="text-2xl font-bold">{{ reportStore.reportData.data.summary.total_events }}</div>
              </div>
              <div v-if="reportStore.reportData.data.summary.total_members !== undefined">
                <div class="text-sm text-gray-600">Total Members</div>
                <div class="text-2xl font-bold">{{ reportStore.reportData.data.summary.total_members }}</div>
              </div>
              <div v-if="reportStore.reportData.data.summary.upcoming_events !== undefined && reportStore.reportData.data.summary.upcoming_events > 0">
                <div class="text-sm text-gray-600">Upcoming Events</div>
                <div class="text-2xl font-bold text-blue-600">{{ reportStore.reportData.data.summary.upcoming_events }}</div>
              </div>
              <div v-if="reportStore.reportData.data.summary.past_events !== undefined && reportStore.reportData.data.summary.past_events > 0">
                <div class="text-sm text-gray-600">Past Events</div>
                <div class="text-2xl font-bold text-gray-600">{{ reportStore.reportData.data.summary.past_events }}</div>
              </div>
            </div>

            <!-- Engagement Stats -->
            <div v-if="reportStore.reportData.data.summary.total_responses !== undefined || reportStore.reportData.data.summary.average_attendance_rate !== undefined" class="border-t pt-4">
              <div class="grid grid-cols-2 gap-4">
                <div v-if="reportStore.reportData.data.summary.total_responses !== undefined">
                  <div class="text-sm text-gray-600">Total Responses</div>
                  <div class="text-xl font-semibold">{{ reportStore.reportData.data.summary.total_responses.toLocaleString() }}</div>
                </div>
                <div v-if="reportStore.reportData.data.summary.average_attendance_rate !== undefined">
                  <div class="text-sm text-gray-600">Average Attendance Rate</div>
                  <div class="text-xl font-semibold text-green-600">{{ reportStore.reportData.data.summary.average_attendance_rate }}%</div>
                </div>
              </div>
            </div>

            <!-- Most Active Members -->
            <div v-if="reportStore.reportData.data.summary.most_active_members && Array.isArray(reportStore.reportData.data.summary.most_active_members)" class="border-t pt-4">
              <h3 class="text-sm font-semibold text-gray-700 mb-3">Most Active Members</h3>
              <div class="space-y-2">
                <div
                  v-for="member in reportStore.reportData.data.summary.most_active_members"
                  :key="member.member_id"
                  class="flex items-center justify-between p-2 bg-gray-50 rounded"
                >
                  <span class="text-sm font-medium">{{ member.member_name }}</span>
                  <div class="flex items-center gap-3 text-xs">
                    <span class="text-gray-600">{{ member.total_events }} events</span>
                    <span class="font-semibold" :class="member.attendance_rate >= 50 ? 'text-green-600' : 'text-yellow-600'">
                      {{ member.attendance_rate }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Event Type Distribution -->
            <div v-if="reportStore.reportData.data.summary.events_by_type && typeof reportStore.reportData.data.summary.events_by_type === 'object'" class="border-t pt-4">
              <h3 class="text-sm font-semibold text-gray-700 mb-3">Event Type Distribution</h3>
              <div class="space-y-2">
                <div
                  v-for="(count, type) in reportStore.reportData.data.summary.events_by_type"
                  :key="type"
                  class="flex items-center justify-between"
                >
                  <span class="text-sm text-gray-600 capitalize">{{ type }}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-semibold">{{ count }}</span>
                    <span class="text-xs text-gray-500">
                      ({{ ((count / reportStore.reportData.data.summary.total_events) * 100).toFixed(1) }}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Detailed Statistics Section -->
      <div v-if="reportStore.reportData && !generating" class="space-y-6 mt-8">
        <div class="border-t pt-6">
          <h2 class="text-2xl font-bold mb-4">Detailed Statistics</h2>
        </div>

        <!-- Member Participation -->
        <UCard v-if="reportStore.reportData.data.member_participation">
          <template #header>
            <h3 class="text-lg font-semibold">Member Participation Details</h3>
          </template>
          <MemberParticipationTable :data="reportStore.reportData.data.member_participation" />
        </UCard>

        <!-- Event Details -->
        <UCard v-if="reportStore.reportData.data.event_details">
          <template #header>
            <h3 class="text-lg font-semibold">Event Details</h3>
          </template>
          <EventDetailsTable :data="reportStore.reportData.data.event_details" />
        </UCard>

        <!-- Category Details -->
        <UCard v-if="reportStore.reportData.data.category_details">
          <template #header>
            <h3 class="text-lg font-semibold">Category Breakdown Details</h3>
          </template>
          <CategoryDetailsTable :data="reportStore.reportData.data.category_details" />
        </UCard>

        <!-- Attendance Log -->
        <UCard v-if="reportStore.reportData.data.attendance_log">
          <template #header>
            <h3 class="text-lg font-semibold">Daily Attendance Log</h3>
          </template>
          <AttendanceLogTable :data="reportStore.reportData.data.attendance_log" />
        </UCard>

        <!-- Organizer Statistics -->
        <UCard v-if="reportStore.reportData.data.organizer_statistics">
          <template #header>
            <h3 class="text-lg font-semibold">Organizer Statistics</h3>
          </template>
          <OrganizerStatisticsTable :data="reportStore.reportData.data.organizer_statistics" />
        </UCard>
      </div>
    </div>
  </div>
</template>
