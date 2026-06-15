<template>
  <UCard class="relative">
    <!-- Header: type + controls -->
    <div class="flex items-center justify-between gap-2 mb-3">
      <div class="flex items-center gap-2 text-sm font-medium text-gray-500">
        <UIcon :name="meta.icon" class="w-4 h-4" />
        <span>{{ meta.label }}</span>
      </div>
      <div class="flex items-center gap-1">
        <UButton size="xs" color="neutral" variant="ghost" icon="i-heroicons-arrow-up"
          :disabled="isFirst" @click="$emit('move-up')" />
        <UButton size="xs" color="neutral" variant="ghost" icon="i-heroicons-arrow-down"
          :disabled="isLast" @click="$emit('move-down')" />
        <UButton size="xs" color="error" variant="ghost" icon="i-heroicons-trash"
          @click="$emit('remove')" />
      </div>
    </div>

    <div class="space-y-3">
      <UInput v-model="field.label"
        :placeholder="meta.isLayout ? 'Seksjonstittel' : 'Spørsmålstekst'"
        class="w-full" :ui="{ base: 'font-medium' }" />

      <UInput v-model="field.help_text" placeholder="Hjelpetekst (valgfritt)" size="sm" class="w-full" />

      <!-- Choice options editor -->
      <div v-if="meta.hasOptions" class="space-y-2 pl-1">
        <div v-for="(opt, i) in optionList" :key="i" class="flex items-center gap-2">
          <UIcon :name="field.field_type === 'flervalg' ? 'i-heroicons-stop' : 'i-heroicons-stop-circle'"
            class="w-4 h-4 text-gray-400 shrink-0" />
          <UInput :model-value="opt" size="sm" class="flex-1" placeholder="Alternativ"
            @update:model-value="(v: string) => setOption(i, v)" />
          <UButton size="xs" color="error" variant="ghost" icon="i-heroicons-x-mark"
            :disabled="optionList.length <= 1" @click="removeOption(i)" />
        </div>
        <UButton size="xs" color="neutral" variant="soft" icon="i-heroicons-plus" @click="addOption">
          Legg til alternativ
        </UButton>
      </div>

      <!-- Scale config -->
      <div v-else-if="meta.isScale" class="grid grid-cols-2 gap-3 pl-1">
        <UFormField label="Fra" size="sm">
          <UInput v-model.number="scale.min" type="number" size="sm" class="w-full" @update:model-value="syncScale" />
        </UFormField>
        <UFormField label="Til" size="sm">
          <UInput v-model.number="scale.max" type="number" size="sm" class="w-full" @update:model-value="syncScale" />
        </UFormField>
        <UFormField label="Etikett lav (valgfritt)" size="sm">
          <UInput v-model="scale.min_label" size="sm" class="w-full" @update:model-value="syncScale" />
        </UFormField>
        <UFormField label="Etikett høy (valgfritt)" size="sm">
          <UInput v-model="scale.max_label" size="sm" class="w-full" @update:model-value="syncScale" />
        </UFormField>
      </div>

      <!-- Required toggle (not for layout blocks) -->
      <div v-if="!meta.isLayout" class="flex items-center gap-2 pt-1">
        <USwitch v-model="field.required" />
        <span class="text-sm text-gray-600 dark:text-gray-400">Påkrevd</span>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
/**
 * Builder editor for a single field. Mutates the passed-in reactive field
 * object in place (the parent owns the fields array). Emits reorder/remove.
 */
const props = defineProps<{
  field: any
  isFirst?: boolean
  isLast?: boolean
}>()

defineEmits<{ 'move-up': []; 'move-down': []; 'remove': [] }>()

const { fieldMeta } = useForms()
const meta = computed(() => fieldMeta(props.field.field_type))

// ---- choice options (stored as string[]) ----
const optionList = computed<string[]>(() =>
  Array.isArray(props.field.options) ? props.field.options : []
)
const setOption = (i: number, v: string) => {
  if (!Array.isArray(props.field.options)) props.field.options = []
  props.field.options[i] = v
}
const addOption = () => {
  if (!Array.isArray(props.field.options)) props.field.options = []
  props.field.options.push(`Alternativ ${props.field.options.length + 1}`)
}
const removeOption = (i: number) => {
  props.field.options.splice(i, 1)
}

// ---- scale config (stored as object) ----
const scale = reactive({
  min: props.field.options?.min ?? 1,
  max: props.field.options?.max ?? 5,
  min_label: props.field.options?.min_label ?? '',
  max_label: props.field.options?.max_label ?? '',
})
const syncScale = () => {
  props.field.options = {
    min: Number(scale.min) || 1,
    max: Number(scale.max) || 5,
    min_label: scale.min_label || '',
    max_label: scale.max_label || '',
  }
}

// Initialize option/scale shape when the editor mounts for a fresh field.
onMounted(() => {
  if (meta.value.hasOptions && !Array.isArray(props.field.options)) {
    props.field.options = ['Alternativ 1', 'Alternativ 2']
  } else if (meta.value.isScale) {
    syncScale()
  }
})
</script>
