<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Skjema', to: '/dashboard/forms' },
      { label: form?.title || 'Svar' },
    ]" />

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else-if="form">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ form.title }}</h1>
          <p class="mt-1 text-sm text-gray-500">{{ report?.response_count ?? 0 }} svar totalt</p>
        </div>
        <div class="flex items-center gap-2">
          <UButton color="neutral" variant="outline" icon="i-heroicons-pencil-square"
            :to="`/dashboard/forms/${formId}/edit`">Rediger</UButton>
          <UButton color="neutral" variant="outline" icon="i-heroicons-arrow-down-tray"
            :loading="exporting" :disabled="!report?.response_count" @click="downloadCsv">CSV</UButton>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-2 border-b border-gray-200 dark:border-gray-800">
        <button v-for="t in tabs" :key="t.value" type="button"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
          :class="tab === t.value ? 'border-primary-500 text-primary-600 dark:text-primary-400'
            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
          @click="tab = t.value">{{ t.label }}</button>
      </div>

      <div v-if="(report?.response_count ?? 0) === 0" class="text-center py-12">
        <UIcon name="i-heroicons-inbox" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p class="text-gray-500">Ingen svar ennå.</p>
      </div>

      <!-- Summary tab -->
      <div v-else-if="tab === 'summary'" class="space-y-4">
        <QuestionReport v-for="q in report.questions" :key="q.field_id" :question="q" />
      </div>

      <!-- Individual responses tab -->
      <div v-else class="space-y-3">
        <UCard v-for="r in responses" :key="r.id">
          <div class="flex items-center justify-between gap-2 mb-3 pb-2 border-b border-gray-100 dark:border-gray-800">
            <div class="flex items-center gap-2 text-sm">
              <UIcon :name="r.is_anonymous ? 'i-heroicons-user-circle' : 'i-heroicons-user'" class="w-4 h-4 text-gray-400" />
              <span class="font-medium">{{ r.is_anonymous ? (r.respondent_label || 'Anonym') : r.respondent_name }}</span>
              <UBadge v-if="r.is_anonymous" size="xs" color="neutral" variant="subtle">Anonym</UBadge>
            </div>
            <span class="text-xs text-gray-400">{{ formatDateTime(r.submitted_at) }}</span>
          </div>
          <dl class="space-y-2">
            <div v-for="a in r.answers" :key="a.field_id" class="text-sm">
              <dt class="text-gray-500">{{ fieldLabel(a.field_id) }}</dt>
              <dd class="text-gray-900 dark:text-white">{{ a.value_text || '—' }}</dd>
            </div>
          </dl>
        </UCard>
        <div v-if="total > responses.length" class="flex justify-center">
          <UButton color="neutral" variant="outline" :loading="loadingMore" @click="loadMore">Last inn flere</UButton>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import QuestionReport from '~/components/forms/QuestionReport.vue'

definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const toast = useToast()

const formId = computed(() => parseInt(route.params.id as string))
const form = ref<any>(null)
const report = ref<any>(null)
const responses = ref<any[]>([])
const fieldMap = ref<Record<number, string>>({})
const total = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const exporting = ref(false)
const tab = ref<'summary' | 'individual'>('summary')

const tabs = [
  { label: 'Oppsummering', value: 'summary' },
  { label: 'Individuelle svar', value: 'individual' },
]

const formatDateTime = (d: string) => new Date(d).toLocaleString('nb-NO', { dateStyle: 'short', timeStyle: 'short' })
const fieldLabel = (id: number) => fieldMap.value[id] || 'Spørsmål'

const load = async () => {
  loading.value = true
  try {
    const [f, rep, resp]: any = await Promise.all([
      api.getForm(formId.value),
      api.getFormReport(formId.value),
      api.getFormResponses(formId.value, { skip: 0, limit: 50 }),
    ])
    form.value = f
    report.value = rep
    responses.value = resp.responses || []
    total.value = resp.total || 0
    fieldMap.value = Object.fromEntries((resp.fields || []).map((x: any) => [x.id, x.label]))
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke laste svar', description: err?.data?.detail, color: 'error' })
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  loadingMore.value = true
  try {
    const resp: any = await api.getFormResponses(formId.value, { skip: responses.value.length, limit: 50 })
    responses.value.push(...(resp.responses || []))
  } finally {
    loadingMore.value = false
  }
}

const downloadCsv = async () => {
  exporting.value = true
  try {
    const blob = await api.exportFormResponsesCsv(formId.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `skjema-${formId.value}-svar.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    toast.add({ title: 'Eksport feilet', description: err?.data?.detail, color: 'error' })
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>
