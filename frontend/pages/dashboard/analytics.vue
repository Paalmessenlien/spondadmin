<template>
  <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h1>
            <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Insights and trends from your Spond data
            </p>
          </div>
          <UButton
            icon="i-heroicons-arrow-path"
            label="Refresh Data"
            @click="refreshAllAnalytics"
            :loading="isRefreshing"
            color="primary"
          />
        </div>

        <!-- Warning Banner for Empty Data -->
        <UAlert
          v-if="summary && summary.total_responses === 0 && summary.total_events > 0"
          color="yellow"
          icon="i-heroicons-exclamation-triangle"
          title="No Analytics Data Available"
          description="Events exist but analytics data is missing. Try refreshing or re-syncing from the Events page."
        />

        <!-- Summary Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <UCard>
            <div class="flex flex-col">
              <span class="text-sm text-gray-600 dark:text-gray-400">Total Events</span>
              <span class="text-2xl font-bold mt-1">{{ summary?.total_events || 0 }}</span>
            </div>
          </UCard>

          <UCard>
            <div class="flex flex-col">
              <span class="text-sm text-gray-600 dark:text-gray-400">Total Members</span>
              <span class="text-2xl font-bold mt-1">{{ summary?.total_members || 0 }}</span>
            </div>
          </UCard>

          <UCard>
            <div class="flex flex-col">
              <span class="text-sm text-gray-600 dark:text-gray-400">Attendance Rate</span>
              <span class="text-2xl font-bold mt-1 text-green-600">
                {{ summary?.average_attendance_rate?.toFixed(1) || 0 }}%
              </span>
            </div>
          </UCard>

          <UCard>
            <div class="flex flex-col">
              <span class="text-sm text-gray-600 dark:text-gray-400">Total Responses</span>
              <span class="text-2xl font-bold mt-1">{{ summary?.total_responses || 0 }}</span>
            </div>
          </UCard>
        </div>

        <!-- Charts Row 1 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Attendance Trends -->
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-semibold">Attendance Trends</h3>
                <USelectMenu
                  v-model="selectedPeriod"
                  :options="periodOptions"
                  value-attribute="value"
                  @update:model-value="loadAttendanceTrends"
                />
              </div>
            </template>

            <AttendanceTrendChart :data="attendanceTrends" />
          </UCard>

          <!-- Response Rates -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">Response Distribution</h3>
            </template>

            <ResponseRateChart :data="responseRates" />

            <template #footer>
              <div class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <div class="flex justify-between">
                  <span>Response Rate:</span>
                  <span class="font-semibold">{{ responseRates?.response_rate || 0 }}%</span>
                </div>
                <div class="flex justify-between">
                  <span>Total Responses:</span>
                  <span class="font-semibold">{{ responseRates?.total_responses || 0 }}</span>
                </div>
              </div>
            </template>
          </UCard>
        </div>

        <!-- Charts Row 2 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Event Types -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">Event Types Distribution</h3>
            </template>

            <EventTypeChart :data="eventTypes" />
          </UCard>

          <!-- Top Participants -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">Most Active Members</h3>
            </template>

            <div class="space-y-3">
              <div
                v-for="(member, index) in topMembers"
                :key="member.member_id"
                class="flex items-center justify-between"
              >
                <div class="flex items-center space-x-3">
                  <div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 font-semibold text-sm">
                    {{ index + 1 }}
                  </div>
                  <div>
                    <div class="font-medium">{{ member.member_name }}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                      {{ member.total_events }} events
                    </div>
                  </div>
                </div>
                <div class="text-right">
                  <div class="font-semibold text-green-600">
                    {{ member.attendance_rate }}%
                  </div>
                  <div class="text-xs text-gray-600 dark:text-gray-400">
                    {{ member.attended }} attended
                  </div>
                </div>
              </div>

              <div v-if="!topMembers || topMembers.length === 0" class="text-center py-8 text-gray-500">
                No participation data available
              </div>
            </div>
          </UCard>
        </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

import AttendanceTrendChart from '~/components/AttendanceTrendChart.vue'
import ResponseRateChart from '~/components/ResponseRateChart.vue'
import EventTypeChart from '~/components/EventTypeChart.vue'

const config = useRuntimeConfig()
const authStore = useAuthStore()

const selectedPeriod = ref('month')
const periodOptions = [
  { label: 'Weekly', value: 'week' },
  { label: 'Monthly', value: 'month' },
  { label: 'Yearly', value: 'year' }
]

// Create headers with auth token
const headers = computed(() => ({
  Authorization: authStore.token ? `Bearer ${authStore.token}` : ''
}))

// Build query params for group filtering
const groupQuery = computed(() => {
  if (authStore.selectedGroupId) {
    return { group_id: authStore.selectedGroupId }
  }
  return {}
})

// Fetch analytics summary
const { data: summary, pending: summaryPending, refresh: refreshSummary } = await useFetch('/analytics/summary', {
  baseURL: config.public.apiBase,
  headers: headers.value,
  query: groupQuery,
  lazy: true,
  key: 'analytics-summary',
  watch: [() => authStore.selectedGroupId],
})

// Fetch attendance trends (reactive to selectedPeriod and group)
const trendsQuery = computed(() => ({
  period: selectedPeriod.value,
  ...groupQuery.value
}))

const { data: attendanceTrends, pending: trendsPending, refresh: refreshTrends } = await useFetch(
  '/analytics/attendance-trends',
  {
    baseURL: config.public.apiBase,
    headers: headers.value,
    query: trendsQuery,
    lazy: true,
    key: 'attendance-trends',
    watch: [selectedPeriod, () => authStore.selectedGroupId],
  }
)

// Fetch response rates
const { data: responseRates, pending: ratesPending, refresh: refreshRates } = await useFetch('/analytics/response-rates', {
  baseURL: config.public.apiBase,
  headers: headers.value,
  query: groupQuery,
  lazy: true,
  key: 'response-rates',
  watch: [() => authStore.selectedGroupId],
})

// Fetch event type distribution
const { data: eventTypes, pending: typesPending, refresh: refreshEventTypes } = await useFetch<any[]>('/analytics/event-types', {
  baseURL: config.public.apiBase,
  headers: headers.value,
  query: groupQuery,
  lazy: true,
  key: 'event-types',
  default: () => [],
  watch: [() => authStore.selectedGroupId],
})

// Fetch top members
const membersQuery = computed(() => ({
  limit: 5,
  ...groupQuery.value
}))

const { data: memberParticipation, pending: membersPending, refresh: refreshMembers } = await useFetch(
  '/analytics/member-participation',
  {
    baseURL: config.public.apiBase,
    headers: headers.value,
    query: membersQuery,
    lazy: true,
    key: 'member-participation',
    watch: [() => authStore.selectedGroupId],
  }
)

const topMembers = computed(() => memberParticipation.value?.members || [])

// Refresh state
const isRefreshing = ref(false)

// Refresh all analytics data
const refreshAllAnalytics = async () => {
  isRefreshing.value = true
  try {
    await Promise.all([
      refreshSummary(),
      refreshTrends(),
      refreshRates(),
      refreshEventTypes(),
      refreshMembers()
    ])
  } finally {
    isRefreshing.value = false
  }
}

// Manual refresh function for attendance trends when period changes
const loadAttendanceTrends = async () => {
  await refreshTrends()
}
</script>
