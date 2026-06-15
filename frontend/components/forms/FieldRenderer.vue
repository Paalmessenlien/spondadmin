<template>
  <div>
    <!-- Layout block: section heading -->
    <div v-if="type === 'overskrift'" class="pt-2">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ field.label }}</h3>
      <p v-if="field.help_text" class="text-sm text-gray-500 mt-1">{{ field.help_text }}</p>
    </div>

    <!-- Answerable field -->
    <div v-else class="space-y-1.5">
      <label class="block text-sm font-medium text-gray-900 dark:text-white">
        {{ field.label }}
        <span v-if="field.required" class="text-red-500">*</span>
      </label>
      <p v-if="field.help_text" class="text-xs text-gray-500">{{ field.help_text }}</p>

      <UInput v-if="type === 'kort_tekst'" :model-value="modelValue" :placeholder="placeholder"
        :disabled="disabled" class="w-full" @update:model-value="emit" />

      <UTextarea v-else-if="type === 'lang_tekst'" :model-value="modelValue" :rows="3"
        :placeholder="placeholder" :disabled="disabled" class="w-full" @update:model-value="emit" />

      <UInput v-else-if="type === 'tall'" type="number" :model-value="modelValue"
        :placeholder="placeholder" :disabled="disabled" class="w-full" @update:model-value="emit" />

      <UInput v-else-if="type === 'dato'" type="date" :model-value="modelValue"
        :disabled="disabled" class="w-full" @update:model-value="emit" />

      <UInput v-else-if="type === 'epost'" type="email" :model-value="modelValue"
        placeholder="navn@eksempel.no" :disabled="disabled" class="w-full" @update:model-value="emit" />

      <!-- Single choice (radio) -->
      <div v-else-if="type === 'enkeltvalg'" class="space-y-2">
        <label v-for="opt in options" :key="opt.value"
          class="flex items-center gap-2 cursor-pointer rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 hover:border-primary-400 transition-colors"
          :class="modelValue === opt.value ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : ''">
          <input type="radio" :name="`f-${field.id}`" :value="opt.value" :checked="modelValue === opt.value"
            :disabled="disabled" class="accent-primary-500" @change="emit(opt.value)" />
          <span class="text-sm">{{ opt.label }}</span>
        </label>
      </div>

      <!-- Multiple choice (checkboxes) -->
      <div v-else-if="type === 'flervalg'" class="space-y-2">
        <label v-for="opt in options" :key="opt.value"
          class="flex items-center gap-2 cursor-pointer rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 hover:border-primary-400 transition-colors"
          :class="selectedSet.has(opt.value) ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : ''">
          <input type="checkbox" :value="opt.value" :checked="selectedSet.has(opt.value)"
            :disabled="disabled" class="accent-primary-500" @change="toggleMulti(opt.value)" />
          <span class="text-sm">{{ opt.label }}</span>
        </label>
      </div>

      <!-- Dropdown -->
      <select v-else-if="type === 'nedtrekk'" :value="modelValue" :disabled="disabled"
        class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-sm"
        @change="emit(($event.target as HTMLSelectElement).value)">
        <option value="" disabled>Velg…</option>
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>

      <!-- Scale -->
      <div v-else-if="type === 'skala'" class="flex flex-wrap items-center gap-2">
        <button v-for="n in scaleRange" :key="n" type="button" :disabled="disabled"
          class="w-10 h-10 rounded-lg border text-sm font-medium transition-colors"
          :class="Number(modelValue) === n
            ? 'border-primary-500 bg-primary-500 text-white'
            : 'border-gray-300 dark:border-gray-700 hover:border-primary-400'"
          @click="emit(n)">{{ n }}</button>
        <span v-if="scaleLabels.min || scaleLabels.max" class="text-xs text-gray-500 ml-1">
          {{ scaleLabels.min }} – {{ scaleLabels.max }}
        </span>
      </div>

      <!-- Yes / No -->
      <div v-else-if="type === 'ja_nei'" class="flex gap-2">
        <button type="button" :disabled="disabled"
          class="px-4 py-2 rounded-lg border text-sm font-medium transition-colors"
          :class="modelValue === true ? 'border-green-500 bg-green-500 text-white' : 'border-gray-300 dark:border-gray-700 hover:border-green-400'"
          @click="emit(true)">Ja</button>
        <button type="button" :disabled="disabled"
          class="px-4 py-2 rounded-lg border text-sm font-medium transition-colors"
          :class="modelValue === false ? 'border-red-500 bg-red-500 text-white' : 'border-gray-300 dark:border-gray-700 hover:border-red-400'"
          @click="emit(false)">Nei</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Renders a single form field as an input. Shared by the public/in-app fill
 * experience and the builder preview. Emits update:modelValue with the typed
 * answer value (string | number | boolean | string[]).
 */
const props = withDefaults(defineProps<{
  field: any
  modelValue?: any
  disabled?: boolean
}>(), { disabled: false })

const emitEvent = defineEmits<{ 'update:modelValue': [value: any] }>()
const emit = (v: any) => emitEvent('update:modelValue', v)

const type = computed(() => props.field?.field_type)
const placeholder = computed(() => props.field?.settings?.placeholder || '')

// Normalize options ([{value,label}] or ["a","b"]) → {value,label}[].
const options = computed(() => {
  const raw = props.field?.options
  if (!Array.isArray(raw)) return []
  return raw.map((o: any) =>
    typeof o === 'object' && o !== null
      ? { value: String(o.value ?? o.label), label: String(o.label ?? o.value) }
      : { value: String(o), label: String(o) }
  )
})

const selectedSet = computed(() => new Set(Array.isArray(props.modelValue) ? props.modelValue : []))
const toggleMulti = (val: string) => {
  const cur = Array.isArray(props.modelValue) ? [...props.modelValue] : []
  const idx = cur.indexOf(val)
  if (idx >= 0) cur.splice(idx, 1)
  else cur.push(val)
  emit(cur)
}

const scaleLabels = computed(() => {
  const o = props.field?.options || {}
  return { min: o.min_label || '', max: o.max_label || '' }
})
const scaleRange = computed(() => {
  const o = props.field?.options || {}
  const lo = Number(o.min ?? 1)
  const hi = Number(o.max ?? 5)
  const out: number[] = []
  for (let i = lo; i <= hi; i++) out.push(i)
  return out
})
</script>
