<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 py-8 px-4">
    <div class="max-w-xl mx-auto">
      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-24 gap-3">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8 text-gray-400" />
      </div>

      <!-- Unavailable -->
      <UCard v-else-if="error" class="text-center py-12">
        <UIcon name="i-heroicons-exclamation-circle" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <h1 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">{{ error.title }}</h1>
        <p class="text-sm text-gray-500">{{ error.message }}</p>
      </UCard>

      <!-- Thank you -->
      <UCard v-else-if="submitted" class="text-center py-12">
        <UIcon name="i-heroicons-check-circle" class="w-14 h-14 mx-auto mb-3 text-green-500" />
        <h1 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Takk for svaret!</h1>
        <p class="text-sm text-gray-500">{{ confirmationMessage }}</p>
      </UCard>

      <!-- Form -->
      <UCard v-else-if="form">
        <template #header>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ form.title }}</h1>
        </template>
        <FormFiller
          :form="form"
          :loading="submitting"
          show-anon-label
          submit-label="Send inn svar"
          @submit="onSubmit"
        />
      </UCard>

      <p class="text-center text-xs text-gray-400 mt-6">Drevet av {{ clubName }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// Public, unauthenticated fill page — no dashboard layout, no auth middleware.
import FormFiller from '~/components/forms/FormFiller.vue'

definePageMeta({ layout: false, middleware: [] })

const route = useRoute()
const api = useApi()
const config = useRuntimeConfig()

const slug = computed(() => route.params.slug as string)
const form = ref<any>(null)
const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const error = ref<{ title: string; message: string } | null>(null)

const clubName = computed(() => (config.public as any).clubName || 'Spond Admin')
const confirmationMessage = computed(
  () => form.value?.settings?.confirmation || 'Svaret ditt er registrert.'
)

const load = async () => {
  loading.value = true
  error.value = null
  try {
    form.value = await api.getPublicForm(slug.value)
  } catch (err: any) {
    const status = err?.response?.status || err?.statusCode
    if (status === 403) {
      error.value = { title: 'Krever innlogging', message: 'Dette skjemaet er kun for innloggede medlemmer.' }
    } else {
      error.value = { title: 'Skjema ikke tilgjengelig', message: 'Skjemaet finnes ikke eller er ikke publisert.' }
    }
  } finally {
    loading.value = false
  }
}

const onSubmit = async (payload: { answers: any[]; respondent_label?: string }) => {
  submitting.value = true
  try {
    await api.submitPublicForm(slug.value, payload.answers, payload.respondent_label)
    submitted.value = true
  } catch (err: any) {
    const detail = err?.data?.detail || 'Kunne ikke sende inn. Sjekk svarene og prøv igjen.'
    useToast().add({ title: 'Innsending feilet', description: detail, color: 'error' })
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
