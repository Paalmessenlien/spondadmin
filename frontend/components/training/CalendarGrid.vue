<template>
  <div class="overflow-x-auto">
    <table class="text-xs border-collapse" style="min-width: 100%;">
      <thead>
        <tr>
          <th class="sticky left-0 z-10 bg-gray-50 dark:bg-gray-800 border-b border-r border-gray-200 dark:border-gray-700 px-3 py-2 text-left font-medium text-gray-600 dark:text-gray-300 min-w-[180px]">
            Session type
          </th>
          <th
            v-for="d in days"
            :key="d.date"
            :class="[
              'border-b border-r border-gray-200 dark:border-gray-700 px-1 py-2 text-center font-medium',
              d.isWeekend ? 'bg-gray-100 dark:bg-gray-900 text-gray-500' : 'bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300',
            ]"
            style="min-width: 44px;"
          >
            <div class="leading-tight">
              <div class="text-[10px] uppercase">{{ d.weekday }}</div>
              <div class="font-semibold">{{ d.day }}</div>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="st in sessionTypes" :key="st.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
          <td class="sticky left-0 z-10 bg-white dark:bg-gray-900 border-b border-r border-gray-200 dark:border-gray-700 px-3 py-2 align-top">
            <div class="font-medium text-gray-900 dark:text-white">{{ st.name }}</div>
            <div class="text-[10px] text-gray-500">
              {{ formatTime(st.default_start_time) }}–{{ formatTime(st.default_end_time) }}
            </div>
          </td>
          <td
            v-for="d in days"
            :key="d.date"
            :class="[
              'border-b border-r border-gray-200 dark:border-gray-700 p-0.5 align-top text-center',
              d.isWeekend ? 'bg-gray-50 dark:bg-gray-900/50' : '',
            ]"
            style="min-width: 44px;"
          >
            <button
              type="button"
              :class="[
                'w-full h-10 rounded text-[11px] font-medium transition-colors flex items-center justify-center px-1',
                cellClasses(st.id, d.date),
                isClickable(st.id, d.date) ? 'cursor-pointer' : 'cursor-default',
              ]"
              :disabled="!isClickable(st.id, d.date)"
              :title="cellTitle(st.id, d.date)"
              @click="onCellClick(st.id, d.date)"
            >
              <template v-if="getShift(st.id, d.date)">
                <span class="truncate">{{ cellLabel(getShift(st.id, d.date)!) }}</span>
                <UIcon
                  v-if="getShift(st.id, d.date)!.status === 'published'"
                  name="i-heroicons-check-badge"
                  class="w-3 h-3 ml-0.5 flex-shrink-0"
                />
                <UIcon
                  v-else-if="!getShift(st.id, d.date)!.leader_member_id && getShift(st.id, d.date)!.raw_initials"
                  name="i-heroicons-question-mark-circle"
                  class="w-3 h-3 ml-0.5 flex-shrink-0"
                />
              </template>
              <template v-else>
                <span v-if="canCreate" class="text-gray-300 dark:text-gray-700">+</span>
              </template>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
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

const getShift = (stId: number, date: string): Shift | null =>
  props.shiftsByKey[`${stId}|${date}`] ?? null

const isClickable = (stId: number, date: string): boolean => {
  const s = getShift(stId, date)
  if (s) return true // always allow viewing existing
  return props.canCreate
}

const cellClasses = (stId: number, date: string): string => {
  const s = getShift(stId, date)
  if (!s) return 'bg-transparent hover:bg-blue-50 dark:hover:bg-blue-900/20 text-gray-400'
  if (s.status === 'cancelled') {
    return 'bg-gray-100 dark:bg-gray-800 text-gray-500 line-through hover:bg-gray-200 dark:hover:bg-gray-700'
  }
  if (s.status === 'published') {
    return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border border-green-500 hover:bg-green-200 dark:hover:bg-green-900/50'
  }
  // draft
  if (!s.leader_member_id && s.raw_initials) {
    return 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 border border-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50'
  }
  return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border border-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50'
}

const cellLabel = (s: Shift): string => {
  if (s.leader) {
    const first = s.leader.first_name || ''
    const last = s.leader.last_name || ''
    // Show short form: first + last initial
    return last ? `${first} ${last.charAt(0)}.` : first
  }
  if (s.raw_initials) return s.raw_initials
  return '—'
}

const cellTitle = (stId: number, date: string): string => {
  const s = getShift(stId, date)
  if (!s) return `${date} — click to add`
  const leader = s.leader
    ? `${s.leader.first_name} ${s.leader.last_name}`
    : (s.raw_initials ? `Unresolved: ${s.raw_initials}` : 'No leader')
  return `${date} — ${leader} (${s.status})`
}

const onCellClick = (stId: number, date: string) => {
  const s = getShift(stId, date)
  if (!s && !props.canCreate) return
  emit('cell-click', stId, date, s)
}

const formatTime = (t: string) => (t ? t.slice(0, 5) : '')
</script>
