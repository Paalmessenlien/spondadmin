<template>
  <div class="space-y-6">
    <div v-if="form.description" class="text-gray-600 dark:text-gray-300 whitespace-pre-line">
      {{ form.description }}
    </div>

    <div v-for="field in sortedFields" :key="field.id">
      <FieldRenderer
        :field="field"
        :model-value="answers[field.id]"
        :disabled="disabled || loading"
        @update:model-value="(v: any) => setAnswer(field.id, v)"
      />
      <p v-if="errors[field.id]" class="text-xs text-red-500 mt-1">{{ errors[field.id] }}</p>
    </div>

    <!-- Optional identity capture for anonymous respondents -->
    <UFormField v-if="showAnonLabel" label="Navn eller e-post (valgfritt)">
      <UInput v-model="respondentLabel" placeholder="Hvem svarer? (valgfritt)" class="w-full" />
    </UFormField>

    <div class="flex justify-end pt-2">
      <UButton size="lg" color="primary" :loading="loading" :disabled="disabled"
        icon="i-heroicons-paper-airplane" @click="onSubmit">
        {{ submitLabel }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Shared form-fill experience: renders fields, holds answer state, does client
 * validation (required) and emits a submit payload. The parent owns the actual
 * API call + the thank-you state.
 */
import FieldRenderer from '~/components/forms/FieldRenderer.vue'

const props = withDefaults(defineProps<{
  form: any
  loading?: boolean
  disabled?: boolean
  showAnonLabel?: boolean
  submitLabel?: string
}>(), { loading: false, disabled: false, showAnonLabel: false, submitLabel: 'Send inn' })

const emitEvent = defineEmits<{ submit: [payload: { answers: any[]; respondent_label?: string }] }>()

const LAYOUT_TYPES = ['overskrift']

const answers = reactive<Record<number, any>>({})
const errors = reactive<Record<number, string>>({})
const respondentLabel = ref('')

const sortedFields = computed(() =>
  [...(props.form?.fields || [])].sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
)

const setAnswer = (id: number, v: any) => {
  answers[id] = v
  if (errors[id]) delete errors[id]
}

const isEmpty = (v: any) =>
  v === undefined || v === null || v === '' ||
  (Array.isArray(v) && v.length === 0)

const onSubmit = () => {
  // Clear + revalidate required.
  Object.keys(errors).forEach((k) => delete errors[Number(k)])
  let ok = true
  for (const f of sortedFields.value) {
    if (LAYOUT_TYPES.includes(f.field_type)) continue
    if (f.required && isEmpty(answers[f.id])) {
      errors[f.id] = 'Dette feltet er påkrevd'
      ok = false
    }
  }
  if (!ok) return

  const payload = {
    answers: sortedFields.value
      .filter((f) => !LAYOUT_TYPES.includes(f.field_type) && !isEmpty(answers[f.id]))
      .map((f) => ({ field_id: f.id, value: answers[f.id] })),
    respondent_label: respondentLabel.value || undefined,
  }
  emitEvent('submit', payload)
}
</script>
