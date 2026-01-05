<template>
  <div class="space-y-6">
        <!-- Breadcrumb -->
        <Breadcrumb
          :items="[
            { label: 'Dashboard', to: '/dashboard' },
            { label: 'Members', to: '/dashboard/members' },
            { label: member ? `${member.first_name} ${member.last_name}` : 'Member Details' }
          ]"
        />

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center py-12">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
        </div>

        <!-- Error State -->
        <UCard v-else-if="error">
          <div class="text-center py-8">
            <UIcon name="i-heroicons-exclamation-triangle" class="h-12 w-12 mx-auto text-red-500 mb-4" />
            <h3 class="text-lg font-semibold text-red-600 mb-2">Error Loading Member</h3>
            <p class="text-gray-600 dark:text-gray-400">{{ error }}</p>
          </div>
        </UCard>

        <!-- Member Profile -->
        <template v-else-if="member">
          <!-- Profile Header -->
          <UCard>
            <div class="flex items-start space-x-6">
              <!-- Avatar -->
              <div class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-3xl font-bold flex-shrink-0">
                {{ getInitials(member) }}
              </div>

              <!-- Info -->
              <div class="flex-1">
                <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  {{ member.first_name }} {{ member.last_name }}
                </h1>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div v-if="member.email" class="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                    <UIcon name="i-heroicons-envelope" />
                    <span>{{ member.email }}</span>
                  </div>

                  <div v-if="member.phone_number" class="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                    <UIcon name="i-heroicons-phone" />
                    <span>{{ member.phone_number }}</span>
                  </div>

                  <div v-if="member.subgroup_uids && member.subgroup_uids.length > 0" class="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                    <UIcon name="i-heroicons-user-group" />
                    <span>{{ member.subgroup_uids.length }} subgroup(s)</span>
                  </div>

                  <div v-if="member.member_created_time" class="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                    <UIcon name="i-heroicons-calendar" />
                    <span>Member since {{ formatDate(member.member_created_time) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Statistics -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-blue-600">{{ participationStats.total }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Total Events</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600">{{ participationStats.attended }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Attended</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-red-600">{{ participationStats.declined }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Declined</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-purple-600">{{ participationStats.attendanceRate }}%</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Attendance Rate</div>
              </div>
            </UCard>
          </div>

          <!-- Participation History -->
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h2 class="text-xl font-bold">Participation History</h2>
                <div class="flex items-center space-x-2">
                  <USelectMenu
                    v-model="historyFilter"
                    :options="[
                      { label: 'All', value: 'all' },
                      { label: 'Accepted', value: 'accepted' },
                      { label: 'Declined', value: 'declined' },
                      { label: 'Unanswered', value: 'unanswered' }
                    ]"
                    size="sm"
                  />
                </div>
              </div>
            </template>

            <div v-if="loadingEvents" class="flex justify-center py-8">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
            </div>

            <div v-else-if="filteredHistory.length === 0" class="text-center py-8 text-gray-500">
              <p>No participation history available</p>
              <p v-if="historyFilter !== 'all'" class="text-sm mt-2">
                Try changing the filter to see more results
              </p>
            </div>

            <div v-else>
              <div class="space-y-3">
                <div
                  v-for="event in paginatedHistory"
                  :key="event.id"
                  class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                  @click="navigateTo(`/dashboard/events/${event.id}`)"
                >
                  <div class="flex-1">
                    <div class="font-medium hover:text-blue-600 dark:hover:text-blue-400">{{ event.heading }}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                      {{ formatEventDate(event.start_time) }}
                    </div>
                  </div>

                  <div class="flex items-center space-x-3">
                    <UBadge :color="getEventTypeColor(event.event_type)">
                      {{ event.event_type }}
                    </UBadge>
                    <UBadge :color="getResponseColor(event.response)">
                      {{ formatAnswer(event.response) }}
                    </UBadge>
                  </div>
                </div>
              </div>

              <!-- Pagination for history -->
              <div v-if="filteredHistory.length > historyPageSize" class="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div class="text-sm text-gray-600 dark:text-gray-400">
                  Showing {{ historySkip + 1 }}-{{ Math.min(historySkip + historyPageSize, filteredHistory.length) }} of {{ filteredHistory.length }} events
                </div>
                <div class="flex items-center space-x-2">
                  <UButton
                    size="sm"
                    color="neutral"
                    variant="outline"
                    :disabled="historySkip === 0"
                    @click="historyPreviousPage"
                  >
                    Previous
                  </UButton>
                  <span class="text-sm text-gray-600 dark:text-gray-400">
                    Page {{ historyCurrentPage }} of {{ historyTotalPages }}
                  </span>
                  <UButton
                    size="sm"
                    color="neutral"
                    variant="outline"
                    :disabled="historySkip + historyPageSize >= filteredHistory.length"
                    @click="historyNextPage"
                  >
                    Next
                  </UButton>
                </div>
              </div>
            </div>
          </UCard>
        </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const route = useRoute()
const api = useApi()
const toast = useToast()

const memberId = computed(() => parseInt(route.params.id as string))

const member = ref<any>(null)
const events = ref<any[]>([])
const loading = ref(true)
const loadingEvents = ref(true)
const error = ref<string | null>(null)
const historyFilter = ref('all')
const historySkip = ref(0)
const historyPageSize = ref(10)

onMounted(async () => {
  await loadMember()
  await loadEvents()
})

const loadMember = async () => {
  loading.value = true
  error.value = null
  try {
    member.value = await api.getMember(memberId.value)
  } catch (err: any) {
    console.error('Failed to load member:', err)
    error.value = err?.data?.detail || 'Failed to load member details'
    toast.add({ title: 'Error', description: error.value, color: 'red' })
  } finally {
    loading.value = false
  }
}

const loadEvents = async () => {
  loadingEvents.value = true
  try {
    // Only load recent events to improve performance (reduced from 1000 to 200)
    const response = await api.getEvents({ limit: 200, include_hidden: 'true' })
    events.value = response.events || []
  } catch (err: any) {
    console.error('Failed to load events:', err)
  } finally {
    loadingEvents.value = false
  }
}

const participationHistory = computed(() => {
  if (!member.value || !events.value.length) return []

  // Get member's profile ID from raw_data or profile
  const profileId = member.value.profile?.id || member.value.raw_data?.profile?.id

  if (!profileId) return []

  // Filter events where this member was invited
  const memberEvents = events.value
    .map(event => {
      if (!event.responses?.responses) return null

      const response = event.responses.responses.find((r: any) =>
        r.profile?.id === profileId
      )

      if (!response) return null

      return {
        ...event,
        response: response.answer || 'unanswered'
      }
    })
    .filter(e => e !== null)
    .sort((a: any, b: any) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())

  return memberEvents
})

const participationStats = computed(() => {
  const history = participationHistory.value
  if (!history.length) {
    return { total: 0, attended: 0, declined: 0, attendanceRate: 0 }
  }

  const attended = history.filter((e: any) => e.response?.toLowerCase() === 'accepted').length
  const declined = history.filter((e: any) => e.response?.toLowerCase() === 'declined').length
  const attendanceRate = Math.round((attended / history.length) * 100)

  return {
    total: history.length,
    attended,
    declined,
    attendanceRate
  }
})

// Filtered history based on response type
const filteredHistory = computed(() => {
  const history = participationHistory.value

  if (historyFilter.value === 'all') {
    return history
  }

  return history.filter((e: any) => {
    const response = e.response?.toLowerCase() || 'unanswered'
    if (historyFilter.value === 'unanswered') {
      return !e.response || response === 'unanswered'
    }
    return response === historyFilter.value
  })
})

// Paginated history
const paginatedHistory = computed(() => {
  const start = historySkip.value
  const end = start + historyPageSize.value
  return filteredHistory.value.slice(start, end)
})

// Pagination computed
const historyCurrentPage = computed(() => Math.floor(historySkip.value / historyPageSize.value) + 1)
const historyTotalPages = computed(() => Math.ceil(filteredHistory.value.length / historyPageSize.value))

// Pagination methods
const historyNextPage = () => {
  historySkip.value += historyPageSize.value
}

const historyPreviousPage = () => {
  historySkip.value = Math.max(0, historySkip.value - historyPageSize.value)
}

// Reset pagination when filter changes
watch(historyFilter, () => {
  historySkip.value = 0
})

const getInitials = (member: any) => {
  if (!member) return '?'
  const first = member.first_name?.[0] || ''
  const last = member.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatEventDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatAnswer = (answer: string) => {
  if (!answer) return 'Unanswered'
  return answer.charAt(0).toUpperCase() + answer.slice(1).toLowerCase()
}

const getResponseColor = (answer: string) => {
  const ans = answer?.toLowerCase() || 'unanswered'
  if (ans === 'accepted') return 'green'
  if (ans === 'declined') return 'red'
  return 'gray'
}

const getEventTypeColor = (type: string) => {
  const typeMap: Record<string, string> = {
    'TRAINING': 'blue',
    'EVENT': 'purple',
    'MATCH': 'orange',
    'MEETING': 'cyan'
  }
  return typeMap[type?.toUpperCase()] || 'gray'
}
</script>
