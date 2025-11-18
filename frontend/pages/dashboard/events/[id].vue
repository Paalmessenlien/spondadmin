<template>
  <div class="space-y-6">
        <!-- Breadcrumb -->
        <Breadcrumb
          :items="[
            { label: 'Dashboard', to: '/dashboard' },
            { label: 'Events', to: '/dashboard/events' },
            { label: event?.heading || 'Event Details' }
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
            <h3 class="text-lg font-semibold text-red-600 mb-2">Error Loading Event</h3>
            <p class="text-gray-600 dark:text-gray-400">{{ error }}</p>
          </div>
        </UCard>

        <!-- Event Details -->
        <template v-else-if="event">
          <!-- Header Card -->
          <UCard>
            <div class="space-y-4">
              <div class="flex justify-between items-start">
                <div>
                  <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    {{ event.heading }}
                  </h1>
                  <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                    <div class="flex items-center space-x-1">
                      <UIcon name="i-heroicons-calendar" />
                      <span>{{ formatDate(event.start_time) }}</span>
                    </div>
                    <div class="flex items-center space-x-1">
                      <UIcon name="i-heroicons-clock" />
                      <span>{{ formatTime(event.start_time) }} - {{ formatTime(event.end_time) }}</span>
                    </div>
                    <UBadge :color="getEventTypeColor(event.event_type)">
                      {{ event.event_type || 'Event' }}
                    </UBadge>
                  </div>
                </div>
              </div>

              <!-- Description -->
              <div v-if="event.description" class="prose dark:prose-invert max-w-none">
                <p class="text-gray-700 dark:text-gray-300">{{ event.description }}</p>
              </div>

              <!-- Location -->
              <div v-if="event.location" class="flex items-start space-x-2">
                <UIcon name="i-heroicons-map-pin" class="mt-1 text-gray-500" />
                <div>
                  <div class="font-semibold">Location</div>
                  <div class="text-sm text-gray-600 dark:text-gray-400">
                    {{ event.location.feature || event.location.address }}
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Statistics Cards -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600">{{ responseStats.accepted }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Accepted</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-red-600">{{ responseStats.declined }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Declined</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-gray-600">{{ responseStats.unanswered }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Unanswered</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-blue-600">{{ responseStats.total }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Total Invited</div>
              </div>
            </UCard>
          </div>

          <!-- Attendees List -->
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h2 class="text-xl font-bold">Attendees</h2>
                <UInput
                  v-model="searchQuery"
                  placeholder="Search attendees..."
                  icon="i-heroicons-magnifying-glass"
                  class="w-64"
                />
              </div>
            </template>

            <!-- Tabs for response types -->
            <UTabs
              :items="tabs"
              v-model="selectedTab"
            >
              <template #item="{ item }">
                <div class="space-y-2">
                  <div v-if="filteredAttendees(item.value).length === 0" class="text-center py-8 text-gray-500">
                    No attendees in this category
                  </div>

                  <div
                    v-for="attendee in filteredAttendees(item.value)"
                    :key="attendee.profile?.id"
                    class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div class="flex items-center space-x-3">
                      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold">
                        {{ getInitials(attendee.profile) }}
                      </div>
                      <div>
                        <div class="font-medium">
                          {{ attendee.profile?.firstName }} {{ attendee.profile?.lastName }}
                        </div>
                        <div v-if="attendee.profile?.email" class="text-sm text-gray-600 dark:text-gray-400">
                          {{ attendee.profile.email }}
                        </div>
                      </div>
                    </div>
                    <UBadge :color="getResponseColor(attendee.answer)">
                      {{ formatAnswer(attendee.answer) }}
                    </UBadge>
                  </div>
                </div>
              </template>
            </UTabs>
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

const eventId = computed(() => parseInt(route.params.id as string))

const event = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const searchQuery = ref('')
const selectedTab = ref(0)

const tabs = [
  { label: 'All', value: 'all' },
  { label: 'Accepted', value: 'accepted' },
  { label: 'Declined', value: 'declined' },
  { label: 'Unanswered', value: 'unanswered' }
]

onMounted(async () => {
  await loadEvent()
})

const loadEvent = async () => {
  loading.value = true
  error.value = null
  try {
    event.value = await api.getEvent(eventId.value)
  } catch (err: any) {
    console.error('Failed to load event:', err)
    error.value = err?.data?.detail || 'Failed to load event details'
    toast.add({ title: 'Error', description: error.value, color: 'red' })
  } finally {
    loading.value = false
  }
}

const responseStats = computed(() => {
  if (!event.value?.responses?.responses) {
    return { accepted: 0, declined: 0, unanswered: 0, total: 0 }
  }

  const responses = event.value.responses.responses
  return {
    accepted: responses.filter((r: any) => r.answer?.toLowerCase() === 'accepted').length,
    declined: responses.filter((r: any) => r.answer?.toLowerCase() === 'declined').length,
    unanswered: responses.filter((r: any) =>
      !r.answer || r.answer.toLowerCase() === 'unanswered'
    ).length,
    total: responses.length
  }
})

const filteredAttendees = (type: string) => {
  if (!event.value?.responses?.responses) return []

  let attendees = event.value.responses.responses

  // Filter by response type
  if (type !== 'all') {
    attendees = attendees.filter((r: any) => {
      const answer = r.answer?.toLowerCase() || 'unanswered'
      if (type === 'unanswered') {
        return !r.answer || answer === 'unanswered'
      }
      return answer === type
    })
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    attendees = attendees.filter((r: any) => {
      const name = `${r.profile?.firstName || ''} ${r.profile?.lastName || ''}`.toLowerCase()
      const email = r.profile?.email?.toLowerCase() || ''
      return name.includes(query) || email.includes(query)
    })
  }

  return attendees
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getInitials = (profile: any) => {
  if (!profile) return '?'
  const first = profile.firstName?.[0] || ''
  const last = profile.lastName?.[0] || ''
  return (first + last).toUpperCase() || '?'
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
