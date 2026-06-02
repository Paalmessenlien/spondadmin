<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Utlegg' }
    ]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Utlegg</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Send inn utlegg med kvittering til kasserer
        </p>
      </div>
      <UButton color="primary" icon="i-heroicons-plus" to="/dashboard/expenses/new">
        Nytt utlegg
      </UButton>
    </div>

    <!-- Tabs: kasserer/admin also get the review queue -->
    <div v-if="canReviewExpenses" class="flex gap-2 border-b border-gray-200 dark:border-gray-800">
      <button
        v-for="t in tabs"
        :key="t.value"
        type="button"
        class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        :class="activeTab === t.value
          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
          : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="setTab(t.value)"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <USelectMenu v-model="selectedStatus" :items="statusOptions" placeholder="Alle statuser" @change="loadExpenses" />
        <USelectMenu v-model="selectedCategory" :items="categoryFilterOptions" placeholder="Alle kategorier" @change="loadExpenses" />
        <UInput type="date" class="w-full" v-model="dateFrom" @change="loadExpenses" />
        <UInput type="date" class="w-full" v-model="dateTo" @change="loadExpenses" />
      </div>
      <div v-if="canReviewExpenses && activeTab === 'queue'" class="mt-3 flex justify-end">
        <UButton size="sm" color="neutral" variant="outline" icon="i-heroicons-arrow-down-tray" :loading="exporting" @click="downloadCsv">
          Eksporter CSV
        </UButton>
      </div>
    </UCard>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <UCard v-else-if="expenses.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-banknotes" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-500">Ingen utlegg her ennå.</p>
    </UCard>

    <template v-else>
      <div class="space-y-3">
        <UCard
          v-for="e in expenses"
          :key="e.id"
          class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer"
          @click="navigateTo(`/dashboard/expenses/${e.id}`)"
        >
          <div class="flex flex-col sm:flex-row sm:items-center gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-lg font-semibold text-gray-900 dark:text-white truncate">{{ e.title }}</span>
                <UBadge :color="statusMeta(e.status).color" :icon="statusMeta(e.status).icon" variant="subtle">
                  {{ statusMeta(e.status).label }}
                </UBadge>
              </div>
              <div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span v-if="e.category">{{ categoryLabel(e.category) }}</span>
                <span v-if="e.expense_date" class="flex items-center gap-1">
                  <UIcon name="i-heroicons-calendar" class="w-4 h-4" />{{ formatDate(e.expense_date) }}
                </span>
                <span v-if="canReviewExpenses && e.submitter_name" class="flex items-center gap-1">
                  <UIcon name="i-heroicons-user" class="w-4 h-4" />{{ e.submitter_name }}
                </span>
                <span v-if="e.attachments?.length" class="flex items-center gap-1">
                  <UIcon name="i-heroicons-paper-clip" class="w-4 h-4" />{{ e.attachments.length }}
                </span>
              </div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ formatAmount(e.amount, e.currency) }}
              </div>
            </div>
          </div>
        </UCard>
      </div>

      <div v-if="total > limit" class="flex justify-center">
        <UPagination v-model="page" :total="total" :items-per-page="limit" @update:model-value="loadExpenses" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const { canReviewExpenses } = usePermissions()
const { statusMeta, categoryLabel, formatAmount, EXPENSE_CATEGORY_OPTIONS } = useExpenseMeta()

const expenses = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const exporting = ref(false)
const page = ref(1)
const limit = 20

const tabs = [
  { label: 'Mine utlegg', value: 'mine' },
  { label: 'Til behandling', value: 'queue' },
]
const activeTab = ref<'mine' | 'queue'>('mine')

const selectedStatus = ref<any>(null)
const selectedCategory = ref<any>(null)
const dateFrom = ref('')
const dateTo = ref('')

const statusOptions = [
  { label: 'Alle statuser', value: '' },
  { label: 'Utkast', value: 'utkast' },
  { label: 'Sendt', value: 'sendt' },
  { label: 'Godkjent', value: 'godkjent' },
  { label: 'Avvist', value: 'avvist' },
  { label: 'Utbetalt', value: 'utbetalt' },
]
const categoryFilterOptions = [{ label: 'Alle kategorier', value: '' }, ...EXPENSE_CATEGORY_OPTIONS]

const setTab = (t: 'mine' | 'queue') => {
  activeTab.value = t
  page.value = 1
  // The queue defaults to showing submitted items awaiting action.
  selectedStatus.value = t === 'queue' ? statusOptions.find((s) => s.value === 'sendt') : null
  loadExpenses()
}

const formatDate = (d: string) => new Date(d).toLocaleDateString('nb-NO')

const buildParams = () => {
  const params: Record<string, any> = {
    skip: String((page.value - 1) * limit),
    limit: String(limit),
  }
  if (selectedStatus.value?.value) params.status = selectedStatus.value.value
  if (selectedCategory.value?.value) params.category = selectedCategory.value.value
  if (dateFrom.value) params.date_from = dateFrom.value
  if (dateTo.value) params.date_to = dateTo.value
  // In "Mine utlegg" a reviewer restricts to their own submissions.
  if (canReviewExpenses.value && activeTab.value === 'mine') params.mine_only = 'true'
  return params
}

const loadExpenses = async () => {
  loading.value = true
  try {
    const data: any = await api.getExpenses(buildParams())
    expenses.value = data.expenses || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Failed to load expenses:', err)
  } finally {
    loading.value = false
  }
}

const downloadCsv = async () => {
  exporting.value = true
  try {
    const params: Record<string, any> = {}
    if (selectedStatus.value?.value) params.status = selectedStatus.value.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    const blob = await api.exportExpensesCsv(params)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'utlegg.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    toast.add({ title: 'Eksport feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    exporting.value = false
  }
}

onMounted(loadExpenses)
</script>
