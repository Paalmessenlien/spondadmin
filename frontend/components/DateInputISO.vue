<template>
  <div class="inline-flex items-center gap-0.5 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm text-gray-900 dark:text-white focus-within:ring-2 focus-within:ring-blue-500">
    <input
      ref="dayEl"
      type="text"
      inputmode="numeric"
      maxlength="2"
      :value="dd"
      placeholder="DD"
      class="w-7 bg-transparent text-right outline-none tabular-nums placeholder-gray-400"
      :disabled="disabled"
      @input="onDayInput"
      @blur="onDayBlur"
      @focus="selectAll($event)"
      @keydown.up.prevent="bump('d', 1)"
      @keydown.down.prevent="bump('d', -1)"
    />
    <span class="text-gray-500">.</span>
    <input
      ref="monthEl"
      type="text"
      inputmode="numeric"
      maxlength="2"
      :value="mo"
      placeholder="MM"
      class="w-7 bg-transparent text-center outline-none tabular-nums placeholder-gray-400"
      :disabled="disabled"
      @input="onMonthInput"
      @blur="onMonthBlur"
      @focus="selectAll($event)"
      @keydown.up.prevent="bump('m', 1)"
      @keydown.down.prevent="bump('m', -1)"
    />
    <span class="text-gray-500">.</span>
    <input
      ref="yearEl"
      type="text"
      inputmode="numeric"
      maxlength="4"
      :value="yy"
      placeholder="YYYY"
      class="w-12 bg-transparent text-left outline-none tabular-nums placeholder-gray-400"
      :disabled="disabled"
      @input="onYearInput"
      @blur="onYearBlur"
      @focus="selectAll($event)"
      @keydown.up.prevent="bump('y', 1)"
      @keydown.down.prevent="bump('y', -1)"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * Locale-independent ISO date input. Renders as `DD.MM.YYYY` (which the
 * Norwegian club uses anyway) and v-models a `YYYY-MM-DD` string — the
 * same format a native <input type="date"> emits, so this is a drop-in
 * replacement.
 *
 * Why custom: Chromium ignores document `lang` for native <input type="date">
 * and renders in OS locale (e.g. MM/DD/YYYY on US-locale machines), making
 * the format inconsistent across the team.
 */
const props = withDefaults(
  defineProps<{
    modelValue?: string | null
    disabled?: boolean
  }>(),
  { modelValue: '', disabled: false }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}>()

const dayEl = ref<HTMLInputElement | null>(null)
const monthEl = ref<HTMLInputElement | null>(null)
const yearEl = ref<HTMLInputElement | null>(null)

const parts = computed(() => {
  const raw = (props.modelValue ?? '').toString().trim()
  if (!raw) return { yy: '', mo: '', dd: '' }
  const m = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (!m) return { yy: '', mo: '', dd: '' }
  return {
    yy: m[1],
    mo: m[2].padStart(2, '0'),
    dd: m[3].padStart(2, '0'),
  }
})

const dd = computed(() => parts.value.dd)
const mo = computed(() => parts.value.mo)
const yy = computed(() => parts.value.yy)

const clampInt = (s: string, min: number, max: number): number | null => {
  const n = parseInt(s, 10)
  if (!Number.isFinite(n)) return null
  return Math.max(min, Math.min(max, n))
}

const daysInMonth = (year: number, month1: number): number => {
  // month1 = 1..12
  return new Date(year, month1, 0).getDate()
}

const emitFromParts = (newDD: string, newMO: string, newYY: string) => {
  if (!newDD && !newMO && !newYY) {
    emit('update:modelValue', '')
    emit('change', '')
    return
  }
  // Don't commit a partial value — wait until all three fields look valid.
  // We treat missing pieces as 0 to keep the wire format `YYYY-MM-DD`, but
  // only emit when there's enough to be plausibly meaningful.
  if (!newYY || newYY.length < 4 || !newMO || !newDD) {
    // partial — emit empty string so callers don't store junk
    emit('update:modelValue', '')
    emit('change', '')
    return
  }
  const y = parseInt(newYY, 10)
  const m = parseInt(newMO, 10)
  const d = parseInt(newDD, 10)
  if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) {
    emit('update:modelValue', '')
    emit('change', '')
    return
  }
  // Clamp day to the actual length of the chosen month (e.g. 31 Feb → 28/29).
  const dClamped = Math.min(d, daysInMonth(y, m))
  const value = `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(dClamped).padStart(2, '0')}`
  emit('update:modelValue', value)
  emit('change', value)
}

const onDayInput = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '').slice(0, 2)
  el.value = digits
  if (digits.length === 2) {
    const n = clampInt(digits, 1, 31)
    if (n === null) return
    emitFromParts(String(n).padStart(2, '0'), mo.value, yy.value)
    monthEl.value?.focus()
  }
}

const onDayBlur = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '')
  if (!digits) {
    emitFromParts('', mo.value, yy.value)
    return
  }
  const n = clampInt(digits, 1, 31)
  if (n === null) {
    emitFromParts('', mo.value, yy.value)
    return
  }
  emitFromParts(String(n).padStart(2, '0'), mo.value, yy.value)
}

const onMonthInput = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '').slice(0, 2)
  el.value = digits
  if (digits.length === 2) {
    const n = clampInt(digits, 1, 12)
    if (n === null) return
    emitFromParts(dd.value, String(n).padStart(2, '0'), yy.value)
    yearEl.value?.focus()
  }
}

const onMonthBlur = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '')
  if (!digits) {
    emitFromParts(dd.value, '', yy.value)
    return
  }
  const n = clampInt(digits, 1, 12)
  if (n === null) {
    emitFromParts(dd.value, '', yy.value)
    return
  }
  emitFromParts(dd.value, String(n).padStart(2, '0'), yy.value)
}

const onYearInput = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '').slice(0, 4)
  el.value = digits
  if (digits.length === 4) {
    emitFromParts(dd.value, mo.value, digits)
  }
}

const onYearBlur = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '')
  if (!digits) {
    emitFromParts(dd.value, mo.value, '')
    return
  }
  // If the user typed a 2-digit year, leave it as-is for them to fix; only
  // commit on 4 digits to avoid quietly choosing a century.
  if (digits.length === 4) {
    emitFromParts(dd.value, mo.value, digits)
  }
}

const bump = (which: 'd' | 'm' | 'y', delta: number) => {
  if (props.disabled) return
  // Build a Date from current parts (defaulting missing pieces to today)
  // and shift accordingly.
  const today = new Date()
  const y = parseInt(yy.value, 10) || today.getFullYear()
  const m = parseInt(mo.value, 10) || (today.getMonth() + 1)
  const d = parseInt(dd.value, 10) || today.getDate()
  const dt = new Date(y, m - 1, d)
  if (Number.isNaN(dt.getTime())) return
  if (which === 'd') dt.setDate(dt.getDate() + delta)
  else if (which === 'm') dt.setMonth(dt.getMonth() + delta)
  else dt.setFullYear(dt.getFullYear() + delta)
  const ny = dt.getFullYear()
  const nm = dt.getMonth() + 1
  const nd = dt.getDate()
  emitFromParts(
    String(nd).padStart(2, '0'),
    String(nm).padStart(2, '0'),
    String(ny).padStart(4, '0'),
  )
}

const selectAll = (e: FocusEvent) => {
  ;(e.target as HTMLInputElement).select()
}
</script>
