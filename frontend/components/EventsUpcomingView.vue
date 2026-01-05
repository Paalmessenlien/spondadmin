<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin w-8 h-8 text-gray-400" />
    </div>

    <!-- Empty state -->
    <div v-else-if="groupedEvents.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-calendar-days" class="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Upcoming Events</h3>
      <p class="text-gray-600 dark:text-gray-400">
        {{ events.length === 0 ? 'Create your first event to get started' : 'No events match your filters' }}
      </p>
    </div>

    <!-- Grouped events -->
    <div v-else class="space-y-6">
      <div
        v-for="group in groupedEvents"
        :key="group.label"
        class="space-y-3"
      >
        <!-- Group header -->
        <div class="sticky top-0 z-10 bg-gray-50 dark:bg-gray-800 -mx-6 px-6 py-2 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
            {{ group.label }}
          </h3>
        </div>

        <!-- Events in group -->
        <div class="space-y-3">
          <UCard
            v-for="event in group.events"
            :key="event.id"
            class="cursor-pointer hover:shadow-md transition-shadow"
            @click="navigateTo(`/dashboard/events/${event.id}`)"
          >
            <div class="flex flex-col sm:flex-row sm:items-start gap-4">
              <!-- Time indicator -->
              <div class="flex-shrink-0 text-center sm:w-20">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ formatDay(event.start_time) }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">
                  {{ formatMonth(event.start_time) }}
                </div>
                <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {{ formatTime(event.start_time) }}
                </div>
              </div>

              <!-- Event details -->
              <div class="flex-1 min-w-0">
                <!-- Title and status -->
                <div class="flex items-start justify-between gap-3 mb-2">
                  <h4 class="text-base font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
                    {{ event.heading }}
                  </h4>
                  <div class="flex gap-2 flex-shrink-0">
                    <SyncStatusBadge
                      :status="event.sync_status"
                      :error="event.sync_error"
                    />
                  </div>
                </div>

                <!-- Description -->
                <p
                  v-if="event.description"
                  class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3"
                >
                  {{ event.description }}
                </p>

                <!-- Metadata row -->
                <div class="flex flex-wrap items-center gap-4 text-sm">
                  <!-- Event type -->
                  <UBadge :color="getEventTypeColor(event.event_type)" size="xs">
                    {{ event.event_type }}
                  </UBadge>

                  <!-- Status -->
                  <UBadge v-if="event.cancelled" color="red" size="xs">
                    Cancelled
                  </UBadge>
                  <UBadge v-else-if="event.hidden" color="orange" size="xs">
                    Hidden
                  </UBadge>

                  <!-- Location -->
                  <div
                    v-if="event.location_address"
                    class="flex items-center gap-1 text-gray-600 dark:text-gray-400"
                  >
                    <UIcon name="i-heroicons-map-pin" class="w-4 h-4" />
                    <span class="truncate max-w-xs">{{ event.location_address }}</span>
                  </div>

                  <!-- Responses -->
                  <div
                    v-if="event.responses"
                    class="flex items-center gap-2"
                    :title="getResponsesTooltip(event.responses)"
                  >
                    <div class="flex items-center gap-1">
                      <UIcon name="i-heroicons-check-circle" class="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span class="text-green-600 dark:text-green-400">{{ event.responses.acceptedIds?.length || 0 }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <UIcon name="i-heroicons-x-circle" class="w-4 h-4 text-red-600 dark:text-red-400" />
                      <span class="text-red-600 dark:text-red-400">{{ event.responses.declinedIds?.length || 0 }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span class="text-gray-600 dark:text-gray-400">{{ event.responses.unansweredIds?.length || 0 }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Duration badge -->
              <div class="flex-shrink-0 text-right">
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  {{ formatDuration(event.start_time, event.end_time) }}
                </div>
              </div>
            </div>
          </UCard>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  events: any[]
  loading?: boolean
}>()

// Group events by relative time periods
const groupedEvents = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const thisWeekEnd = new Date(today)
  thisWeekEnd.setDate(thisWeekEnd.getDate() + (7 - today.getDay()))
  const nextWeekEnd = new Date(thisWeekEnd)
  nextWeekEnd.setDate(nextWeekEnd.getDate() + 7)
  const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1)

  const groups = [
    { label: 'Today', events: [] as any[], order: 1 },
    { label: 'Tomorrow', events: [] as any[], order: 2 },
    { label: 'This Week', events: [] as any[], order: 3 },
    { label: 'Next Week', events: [] as any[], order: 4 },
    { label: 'This Month', events: [] as any[], order: 5 },
    { label: 'Later', events: [] as any[], order: 6 },
  ]

  // Sort events by start time
  const sortedEvents = [...props.events].sort((a, b) => {
    return new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  })

  // Group events
  sortedEvents.forEach(event => {
    const eventDate = new Date(event.start_time)
    const eventDay = new Date(eventDate.getFullYear(), eventDate.getMonth(), eventDate.getDate())

    if (eventDay.getTime() === today.getTime()) {
      groups[0].events.push(event) // Today
    } else if (eventDay.getTime() === tomorrow.getTime()) {
      groups[1].events.push(event) // Tomorrow
    } else if (eventDate > tomorrow && eventDate <= thisWeekEnd) {
      groups[2].events.push(event) // This Week
    } else if (eventDate > thisWeekEnd && eventDate <= nextWeekEnd) {
      groups[3].events.push(event) // Next Week
    } else if (eventDate > nextWeekEnd && eventDate < nextMonth) {
      groups[4].events.push(event) // This Month
    } else {
      groups[5].events.push(event) // Later
    }
  })

  // Return only groups with events
  return groups.filter(group => group.events.length > 0)
})

// Helper functions
const formatDay = (dateString: string) => {
  return new Date(dateString).getDate()
}

const formatMonth = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', { month: 'short' })
}

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

const formatDuration = (startTime: string, endTime: string) => {
  const start = new Date(startTime)
  const end = new Date(endTime)
  const durationMs = end.getTime() - start.getTime()
  const hours = Math.floor(durationMs / (1000 * 60 * 60))
  const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))

  if (hours === 0) {
    return `${minutes}m`
  } else if (minutes === 0) {
    return `${hours}h`
  } else {
    return `${hours}h ${minutes}m`
  }
}

const getEventTypeColor = (type: string) => {
  switch (type) {
    case 'RECURRING':
      return 'blue'
    case 'AVAILABILITY':
      return 'purple'
    default:
      return 'gray'
  }
}

const getResponsesTooltip = (responses: any) => {
  if (!responses) return 'No responses yet'

  const accepted = responses.acceptedIds?.length || 0
  const declined = responses.declinedIds?.length || 0
  const unanswered = responses.unansweredIds?.length || 0

  return `${accepted} accepted, ${declined} declined, ${unanswered} unanswered`
}
</script>
