<template>
  <div class="space-y-4">
    <div v-if="canCreate && sessionTypes.length" class="flex justify-end">
      <UButton size="sm" color="primary" variant="soft" icon="i-heroicons-plus" @click="addShift">
        Add shift
      </UButton>
    </div>

    <div v-if="!dayGroups.length" class="text-center py-8 text-sm text-gray-500">
      No shifts this month.
    </div>

    <div v-for="grp in dayGroups" :key="grp.date" class="space-y-1.5">
      <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">
        {{ grp.weekday }} {{ grp.day }}
      </h3>
      <button
        v-for="item in grp.items"
        :key="item.key"
        type="button"
        class="w-full flex items-center justify-between gap-2 rounded-lg border px-3 py-2.5 text-left"
        :class="cardClass(item.shift)"
        @click="emit('cell-click', item.sessionTypeId, grp.date, item.shift)"
      >
        <span class="min-w-0">
          <span class="font-medium block truncate">{{ item.sessionTypeName }}</span>
          <span class="text-xs opacity-80">{{ leaderLabel(item.shift) }}</span>
        </span>
        <UIcon
          v-if="item.shift.status === 'published'"
          name="i-heroicons-check-badge"
          class="w-4 h-4 shrink-0"
        />
        <UIcon
          v-else-if="!item.shift.leader_member_id && item.shift.raw_initials"
          name="i-heroicons-question-mark-circle"
          class="w-4 h-4 shrink-0"
        />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Mobile agenda for the training calendar — the phone-friendly counterpart to
 * CalendarGrid (the session-type × day matrix). Shows shifts grouped by day as
 * tappable cards and emits the same `cell-click(sessionTypeId, date, shift)`
 * so the existing TrainingShiftEditor flow is reused unchanged.
 */
interface SessionType {
  id: number
  name: string
  default_start_time: string
  default_end_time: string
}
interface Shift {
  id: number
  session_type_id: number
  date: string
  leader_member_id: number | null
  leader: { id: number; first_name: string; last_name: string } | null
  raw_initials: string | null
  status: 'draft' | 'published' | 'cancelled'
}
interface Day {
  date: string
  day: number
  weekday: string
  isWeekend: boolean
}

const props = defineProps<{
  sessionTypes: SessionType[]
  days: Day[]
  shiftsByKey: Record<string, Shift>
  canEdit: boolean
  canCreate: boolean
}>()

const emit = defineEmits<{
  (e: 'cell-click', sessionTypeId: number, date: string, shift: Shift | null): void
}>()

const dayGroups = computed(() =>
  props.days
    .map(d => ({
      ...d,
      items: props.sessionTypes
        .map(st => {
          const shift = props.shiftsByKey[`${st.id}|${d.date}`]
          return shift
            ? { key: `${st.id}|${d.date}`, sessionTypeId: st.id, sessionTypeName: st.name, shift }
            : null
        })
        .filter((x): x is NonNullable<typeof x> => x !== null),
    }))
    .filter(g => g.items.length > 0)
)

const cardClass = (s: Shift): string => {
  if (s.status === 'cancelled') {
    return 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-500 line-through'
  }
  if (s.status === 'published') {
    return 'bg-green-100 dark:bg-green-900/30 border-green-500 text-green-800 dark:text-green-300'
  }
  if (!s.leader_member_id && s.raw_initials) {
    return 'bg-amber-100 dark:bg-amber-900/30 border-amber-400 text-amber-800 dark:text-amber-300'
  }
  return 'bg-blue-100 dark:bg-blue-900/30 border-blue-400 text-blue-800 dark:text-blue-300'
}

const leaderLabel = (s: Shift): string => {
  if (s.leader) {
    const last = s.leader.last_name || ''
    return last ? `${s.leader.first_name} ${last.charAt(0)}.` : s.leader.first_name
  }
  if (s.raw_initials) return s.raw_initials
  return '—'
}

const addShift = () => {
  if (!props.sessionTypes.length) return
  emit('cell-click', props.sessionTypes[0].id, props.days[0]?.date ?? '', null)
}
</script>
