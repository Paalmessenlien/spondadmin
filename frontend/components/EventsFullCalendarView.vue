<template>
  <div class="fullcalendar-wrapper">
    <ClientOnly>
      <FullCalendar
        v-if="calendarOptions"
        :options="calendarOptions"
      />
      <template #fallback>
        <div class="flex items-center justify-center h-96">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin w-8 h-8 text-gray-400" />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import FullCalendar from '@fullcalendar/vue3'
import type { CalendarOptions, EventInput, EventClickArg, DatesSetArg } from '@fullcalendar/core'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'

const props = defineProps<{
  events: any[]
  filters: any
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:dates': [{ start: string, end: string }]
  'update:calendarView': [string]
}>()

const router = useRouter()

// Stored calendar view preference
const storedCalendarView = ref(
  process.client ? localStorage.getItem('calendar-view-preference') || 'dayGridMonth' : 'dayGridMonth'
)

// Transform events to FullCalendar format
const calendarEvents = computed((): EventInput[] => {
  return props.events.map(event => {
    // Determine background color based on event type
    let backgroundColor = '#6b7280' // gray for EVENT
    if (event.event_type === 'RECURRING') {
      backgroundColor = '#3b82f6' // blue
    } else if (event.event_type === 'AVAILABILITY') {
      backgroundColor = '#a855f7' // purple
    }

    // Adjust opacity for cancelled or hidden events
    if (event.cancelled) {
      backgroundColor = '#ef4444' // red for cancelled
    } else if (event.hidden) {
      backgroundColor = '#f97316' // orange for hidden
    }

    // Build title with responses
    const accepted = event.responses?.accepted_uids?.length || 0
    const declined = event.responses?.declined_uids?.length || 0
    const unanswered = event.responses?.unanswered_uids?.length || 0
    const responseText = ` (✓${accepted} ✗${declined} ?${unanswered})`

    return {
      id: String(event.id),
      title: event.heading + responseText,
      start: event.start_time,
      end: event.end_time,
      backgroundColor,
      borderColor: backgroundColor,
      extendedProps: {
        ...event,
      },
    }
  })
})

// Calendar configuration
const calendarOptions = computed((): CalendarOptions => {
  return {
    plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
    initialView: storedCalendarView.value,
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay',
    },
    events: calendarEvents.value,
    eventClick: handleEventClick,
    datesSet: handleDatesSet,
    height: 'auto',
    contentHeight: 'auto',
    aspectRatio: 1.8,
    navLinks: true,
    editable: false,
    selectable: false,
    selectMirror: true,
    dayMaxEvents: true,
    weekends: true,
    nowIndicator: true,
    eventTimeFormat: {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    },
    slotLabelFormat: {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    },
    // Event display
    eventDisplay: 'block',
    displayEventTime: true,
    displayEventEnd: false,
    // View-specific options
    views: {
      dayGridMonth: {
        dayMaxEvents: 3,
      },
      timeGridWeek: {
        slotMinTime: '06:00:00',
        slotMaxTime: '23:00:00',
        allDaySlot: true,
      },
      timeGridDay: {
        slotMinTime: '06:00:00',
        slotMaxTime: '23:00:00',
        allDaySlot: true,
      },
    },
  }
})

// Handle event click - navigate to event detail
const handleEventClick = (clickInfo: EventClickArg) => {
  const eventId = clickInfo.event.id
  router.push(`/dashboard/events/${eventId}`)
}

// Handle calendar view/date changes
const handleDatesSet = (dateInfo: DatesSetArg) => {
  // Save the current view preference
  if (process.client) {
    localStorage.setItem('calendar-view-preference', dateInfo.view.type)
  }
  emit('update:calendarView', dateInfo.view.type)

  // Emit date range for filtering
  emit('update:dates', {
    start: dateInfo.startStr,
    end: dateInfo.endStr,
  })
}
</script>

<style>
/* FullCalendar Custom Styling for Nuxt UI Theme */
.fullcalendar-wrapper {
  @apply relative;
}

/* General calendar styles */
:root {
  --fc-border-color: rgb(229 231 235);
  --fc-button-bg-color: rgb(59 130 246);
  --fc-button-border-color: rgb(59 130 246);
  --fc-button-hover-bg-color: rgb(37 99 235);
  --fc-button-hover-border-color: rgb(37 99 235);
  --fc-button-active-bg-color: rgb(29 78 216);
  --fc-button-active-border-color: rgb(29 78 216);
  --fc-today-bg-color: rgba(59, 130, 246, 0.1);
}

/* Dark mode colors */
.dark {
  --fc-border-color: rgb(55 65 81);
  --fc-neutral-bg-color: rgb(31 41 55);
  --fc-page-bg-color: rgb(17 24 39);
  --fc-today-bg-color: rgba(59, 130, 246, 0.15);
}

/* Calendar container */
.fullcalendar-wrapper :deep(.fc) {
  @apply font-sans;
}

/* Toolbar */
.fullcalendar-wrapper :deep(.fc-toolbar) {
  @apply mb-4 gap-2;
}

.fullcalendar-wrapper :deep(.fc-toolbar-title) {
  @apply text-xl font-semibold text-gray-900 dark:text-white;
}

/* Buttons */
.fullcalendar-wrapper :deep(.fc-button) {
  @apply px-4 py-2 rounded-md text-sm font-medium transition-colors;
  @apply bg-blue-600 text-white border-blue-600;
  @apply hover:bg-blue-700 hover:border-blue-700;
  @apply focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none;
  text-transform: capitalize !important;
  box-shadow: none !important;
}

.fullcalendar-wrapper :deep(.fc-button:disabled) {
  @apply opacity-50 cursor-not-allowed;
}

.fullcalendar-wrapper :deep(.fc-button-active) {
  @apply bg-blue-800 border-blue-800;
}

.fullcalendar-wrapper :deep(.fc-button-primary:not(:disabled).fc-button-active) {
  @apply bg-blue-800 border-blue-800;
}

/* Table headers */
.fullcalendar-wrapper :deep(.fc-col-header) {
  @apply bg-gray-50 dark:bg-gray-800;
}

.fullcalendar-wrapper :deep(.fc-col-header-cell) {
  @apply border-gray-200 dark:border-gray-700;
}

.fullcalendar-wrapper :deep(.fc-col-header-cell-cushion) {
  @apply py-2 px-3 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider;
}

/* Day cells */
.fullcalendar-wrapper :deep(.fc-daygrid-day) {
  @apply bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700;
}

.fullcalendar-wrapper :deep(.fc-daygrid-day-top) {
  @apply p-2;
}

.fullcalendar-wrapper :deep(.fc-daygrid-day-number) {
  @apply text-gray-900 dark:text-gray-100 font-medium;
}

.fullcalendar-wrapper :deep(.fc-day-today) {
  @apply bg-blue-50 dark:bg-blue-900/20;
}

.fullcalendar-wrapper :deep(.fc-day-past .fc-daygrid-day-number) {
  @apply text-gray-400 dark:text-gray-600;
}

.fullcalendar-wrapper :deep(.fc-day-other .fc-daygrid-day-number) {
  @apply text-gray-400 dark:text-gray-600;
}

/* Events */
.fullcalendar-wrapper :deep(.fc-event) {
  @apply rounded border-l-4 shadow-sm cursor-pointer;
  @apply hover:opacity-80 transition-opacity;
}

.fullcalendar-wrapper :deep(.fc-event-title) {
  @apply font-medium text-xs px-1;
}

.fullcalendar-wrapper :deep(.fc-event-time) {
  @apply text-xs px-1 font-normal;
}

/* "More" link */
.fullcalendar-wrapper :deep(.fc-daygrid-more-link) {
  @apply text-xs text-blue-600 dark:text-blue-400 font-medium hover:underline;
}

/* Time grid (week/day views) */
.fullcalendar-wrapper :deep(.fc-timegrid) {
  @apply bg-white dark:bg-gray-900;
}

.fullcalendar-wrapper :deep(.fc-timegrid-slot) {
  @apply border-gray-200 dark:border-gray-700;
}

.fullcalendar-wrapper :deep(.fc-timegrid-slot-label) {
  @apply text-gray-600 dark:text-gray-400 text-xs;
}

.fullcalendar-wrapper :deep(.fc-timegrid-col) {
  @apply border-gray-200 dark:border-gray-700;
}

.fullcalendar-wrapper :deep(.fc-timegrid-now-indicator-line) {
  @apply border-red-500;
}

.fullcalendar-wrapper :deep(.fc-timegrid-now-indicator-arrow) {
  @apply border-red-500;
}

/* Scrollbar for time grid */
.fullcalendar-wrapper :deep(.fc-scroller) {
  @apply overflow-y-auto;
}

.fullcalendar-wrapper :deep(.fc-scroller::-webkit-scrollbar) {
  @apply w-2;
}

.fullcalendar-wrapper :deep(.fc-scroller::-webkit-scrollbar-track) {
  @apply bg-gray-100 dark:bg-gray-800;
}

.fullcalendar-wrapper :deep(.fc-scroller::-webkit-scrollbar-thumb) {
  @apply bg-gray-300 dark:bg-gray-600 rounded;
}

.fullcalendar-wrapper :deep(.fc-scroller::-webkit-scrollbar-thumb:hover) {
  @apply bg-gray-400 dark:bg-gray-500;
}

/* Popover */
.fullcalendar-wrapper :deep(.fc-popover) {
  @apply bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-lg rounded-lg;
}

.fullcalendar-wrapper :deep(.fc-popover-title) {
  @apply bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600;
  @apply text-gray-900 dark:text-white font-semibold;
}

.fullcalendar-wrapper :deep(.fc-popover-close) {
  @apply text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white;
}
</style>
