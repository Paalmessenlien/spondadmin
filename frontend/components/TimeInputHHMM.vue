<template>
  <div class="inline-flex items-center gap-0.5 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm text-gray-900 dark:text-white focus-within:ring-2 focus-within:ring-blue-500">
    <input
      ref="hourEl"
      type="text"
      inputmode="numeric"
      maxlength="2"
      :value="hh"
      :placeholder="placeholderHH"
      class="w-7 bg-transparent text-right outline-none tabular-nums"
      :class="{ 'placeholder-gray-400': true }"
      :disabled="disabled"
      @input="onHourInput"
      @blur="onHourBlur"
      @focus="selectAll($event)"
      @keydown.up.prevent="bump('h', 1)"
      @keydown.down.prevent="bump('h', -1)"
    />
    <span class="text-gray-500">:</span>
    <input
      ref="minuteEl"
      type="text"
      inputmode="numeric"
      maxlength="2"
      :value="mm"
      :placeholder="placeholderMM"
      class="w-7 bg-transparent text-left outline-none tabular-nums"
      :class="{ 'placeholder-gray-400': true }"
      :disabled="disabled"
      @input="onMinuteInput"
      @blur="onMinuteBlur"
      @focus="selectAll($event)"
      @keydown.up.prevent="bump('m', 1)"
      @keydown.down.prevent="bump('m', -1)"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * 24-hour HH:MM input. v-model value is either an empty string or a
 * normalized "HH:MM" / "HH:MM:SS" string. The wire format is preserved so
 * callers can swap this in for a native <input type="time"> without
 * changing their save logic.
 *
 * Why custom: Chromium-based browsers ignore document `lang` for native
 * <input type="time"> rendering — they fall back to the OS locale and
 * show AM/PM on US-locale machines. We need a predictable 24-hour widget.
 */
const props = withDefaults(
  defineProps<{
    modelValue?: string | null
    placeholder?: string
    disabled?: boolean
  }>(),
  { modelValue: '', placeholder: '', disabled: false }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}>()

const hourEl = ref<HTMLInputElement | null>(null)
const minuteEl = ref<HTMLInputElement | null>(null)

// Split a model value like "08:30" / "08:30:00" / "" into ("HH","MM") parts.
const parts = computed(() => {
  const raw = (props.modelValue ?? '').toString().trim()
  if (!raw) return { hh: '', mm: '' }
  const m = raw.match(/^(\d{1,2}):(\d{1,2})/)
  if (!m) return { hh: '', mm: '' }
  return { hh: m[1].padStart(2, '0'), mm: m[2].padStart(2, '0') }
})

const hh = computed(() => parts.value.hh)
const mm = computed(() => parts.value.mm)

const placeholderHH = computed(() => {
  if (!props.placeholder) return 'HH'
  return props.placeholder.split(':')[0] || 'HH'
})
const placeholderMM = computed(() => {
  if (!props.placeholder) return 'MM'
  return props.placeholder.split(':')[1] || 'MM'
})

const clampInt = (s: string, min: number, max: number): number | null => {
  const n = parseInt(s, 10)
  if (!Number.isFinite(n)) return null
  return Math.max(min, Math.min(max, n))
}

const emitFromParts = (newHH: string, newMM: string) => {
  // Both blank → empty string (so callers can treat it as "not set").
  if (!newHH && !newMM) {
    emit('update:modelValue', '')
    emit('change', '')
    return
  }
  const value = `${(newHH || '00').padStart(2, '0')}:${(newMM || '00').padStart(2, '0')}`
  emit('update:modelValue', value)
  emit('change', value)
}

const onHourInput = (e: Event) => {
  const el = e.target as HTMLInputElement
  // Strip non-digits.
  const digits = el.value.replace(/\D/g, '').slice(0, 2)
  el.value = digits
  // Don't commit a partial value (e.g. "1" while still typing); wait for
  // blur or the user advancing to minutes. But emit when 2 digits are in.
  if (digits.length === 2) {
    const n = clampInt(digits, 0, 23)
    if (n === null) return
    emitFromParts(String(n).padStart(2, '0'), mm.value)
    minuteEl.value?.focus()
  }
}

const onHourBlur = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '')
  if (!digits) {
    emitFromParts('', mm.value)
    return
  }
  const n = clampInt(digits, 0, 23)
  if (n === null) {
    emitFromParts('', mm.value)
    return
  }
  emitFromParts(String(n).padStart(2, '0'), mm.value)
}

const onMinuteInput = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '').slice(0, 2)
  el.value = digits
  if (digits.length === 2) {
    const n = clampInt(digits, 0, 59)
    if (n === null) return
    emitFromParts(hh.value, String(n).padStart(2, '0'))
  }
}

const onMinuteBlur = (e: Event) => {
  const el = e.target as HTMLInputElement
  const digits = el.value.replace(/\D/g, '')
  if (!digits) {
    emitFromParts(hh.value, '')
    return
  }
  const n = clampInt(digits, 0, 59)
  if (n === null) {
    emitFromParts(hh.value, '')
    return
  }
  emitFromParts(hh.value, String(n).padStart(2, '0'))
}

const bump = (which: 'h' | 'm', delta: number) => {
  if (props.disabled) return
  if (which === 'h') {
    const cur = parseInt(hh.value || '0', 10) || 0
    const next = (cur + delta + 24) % 24
    emitFromParts(String(next).padStart(2, '0'), mm.value || '00')
  } else {
    const cur = parseInt(mm.value || '0', 10) || 0
    const next = (cur + delta + 60) % 60
    emitFromParts(hh.value || '00', String(next).padStart(2, '0'))
  }
}

const selectAll = (e: FocusEvent) => {
  ;(e.target as HTMLInputElement).select()
}
</script>
