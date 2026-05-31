<template>
  <div class="space-y-6">
    <!-- Controls -->
    <UCard>
      <div class="flex flex-col lg:flex-row lg:items-end gap-4">
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Plan</label>
          <select
            v-model.number="planId"
            class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="p in plans" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">From</label>
          <UInput type="date" class="w-full" v-model="startDate" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">To</label>
          <UInput type="date" class="w-full" v-model="endDate" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bucket</label>
          <div class="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600">
            <button
              v-for="opt in ['month', 'week']"
              :key="opt"
              type="button"
              class="px-3 py-2 text-sm capitalize"
              :class="period === opt ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'"
              @click="period = opt"
            >
              {{ opt }}
            </button>
          </div>
        </div>
        <UButton color="neutral" variant="outline" icon="i-heroicons-arrow-uturn-left" @click="resetToPlanPeriod">
          Plan period
        </UButton>
      </div>
    </UCard>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else-if="data">
      <!-- Summary cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">{{ data.summary.total_shifts }}</div>
          <div class="text-xs text-gray-500">Shifts</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-green-600 tabular-nums">{{ data.summary.published }}</div>
          <div class="text-xs text-gray-500">Published</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-blue-600 tabular-nums">{{ data.summary.draft }}</div>
          <div class="text-xs text-gray-500">Draft</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-gray-500 tabular-nums">{{ data.summary.cancelled }}</div>
          <div class="text-xs text-gray-500">Cancelled</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">{{ data.summary.session_type_count }}</div>
          <div class="text-xs text-gray-500">Setups</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">{{ data.summary.leader_count }}</div>
          <div class="text-xs text-gray-500">Leaders</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="text-2xl font-bold text-green-700 tabular-nums">{{ data.summary.accepted }}</div>
          <div class="text-xs text-gray-500">Accepted (Spond)</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <UCard>
          <template #header><h3 class="font-semibold text-gray-900 dark:text-white">Status</h3></template>
          <div class="relative h-56"><Doughnut :data="statusChart" :options="doughnutOpts" /></div>
        </UCard>
        <UCard class="lg:col-span-2">
          <template #header><h3 class="font-semibold text-gray-900 dark:text-white">Shifts over time</h3></template>
          <div class="relative h-56"><Bar :data="overTimeChart" :options="stackedBarOpts" /></div>
        </UCard>
      </div>

      <UCard>
        <template #header><h3 class="font-semibold text-gray-900 dark:text-white">Shifts per leader (top 12)</h3></template>
        <div class="relative h-72"><Bar :data="leaderChart" :options="horizontalBarOpts" /></div>
      </UCard>

      <!-- By-setup table -->
      <UCard>
        <template #header>
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <h3 class="font-semibold text-gray-900 dark:text-white">By training setup</h3>
            <UInput v-model="setupSearch" placeholder="Filter setups…" icon="i-heroicons-magnifying-glass" class="w-full sm:w-56" />
          </div>
        </template>
        <ResponsiveTable
          :columns="setupCols"
          :rows="setupTable.sortedData.value"
          row-key="session_type_id"
          :sort-field="setupTable.sortField.value"
          :sort-desc="setupTable.sortDesc.value"
          empty-text="No setups in range."
          @sort="setupTable.toggleSort"
        >
          <template #cell-total="{ row }"><span class="tabular-nums">{{ row.total }}</span></template>
          <template #cell-published="{ row }"><span class="tabular-nums text-green-600">{{ row.published }}</span></template>
          <template #cell-draft="{ row }"><span class="tabular-nums text-blue-600">{{ row.draft }}</span></template>
          <template #cell-cancelled="{ row }"><span class="tabular-nums text-gray-500">{{ row.cancelled }}</span></template>
          <template #cell-distinct_leaders="{ row }"><span class="tabular-nums">{{ row.distinct_leaders }}</span></template>
          <template #cell-accepted="{ row }"><span class="tabular-nums text-green-700">{{ row.accepted }}</span></template>
          <template #cell-declined="{ row }"><span class="tabular-nums text-red-600">{{ row.declined }}</span></template>
          <template #cell-unanswered="{ row }"><span class="tabular-nums text-gray-400">{{ row.unanswered }}</span></template>
          <template #foot-name>Total</template>
          <template #foot-total><span class="tabular-nums">{{ sum('total') }}</span></template>
          <template #foot-published><span class="tabular-nums text-green-600">{{ sum('published') }}</span></template>
          <template #foot-draft><span class="tabular-nums text-blue-600">{{ sum('draft') }}</span></template>
          <template #foot-cancelled><span class="tabular-nums text-gray-500">{{ sum('cancelled') }}</span></template>
          <template #foot-accepted><span class="tabular-nums text-green-700">{{ sum('accepted') }}</span></template>
          <template #foot-declined><span class="tabular-nums text-red-600">{{ sum('declined') }}</span></template>
          <template #foot-unanswered><span class="tabular-nums text-gray-400">{{ sum('unanswered') }}</span></template>
        </ResponsiveTable>
      </UCard>

      <!-- By-leader table -->
      <UCard>
        <template #header>
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <h3 class="font-semibold text-gray-900 dark:text-white">By leader</h3>
            <UInput v-model="leaderSearch" placeholder="Filter leaders…" icon="i-heroicons-magnifying-glass" class="w-full sm:w-56" />
          </div>
        </template>
        <ResponsiveTable
          :columns="leaderCols"
          :rows="leaderTable.sortedData.value"
          row-key="label"
          :sort-field="leaderTable.sortField.value"
          :sort-desc="leaderTable.sortDesc.value"
          empty-text="No leaders in range."
          @sort="leaderTable.toggleSort"
        >
          <template #cell-label="{ row }">
            <NuxtLink v-if="row.leader_member_id" :to="`/dashboard/members/${row.leader_member_id}`"
                      class="text-blue-600 dark:text-blue-400 hover:underline">{{ row.label }}</NuxtLink>
            <span v-else>{{ row.label }}</span>
          </template>
          <template #cell-total="{ row }"><span class="tabular-nums">{{ row.total }}</span></template>
          <template #cell-published="{ row }"><span class="tabular-nums text-green-600">{{ row.published }}</span></template>
          <template #cell-draft="{ row }"><span class="tabular-nums text-blue-600">{{ row.draft }}</span></template>
          <template #cell-cancelled="{ row }"><span class="tabular-nums text-gray-500">{{ row.cancelled }}</span></template>
        </ResponsiveTable>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  Chart as ChartJS,
  ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend,
} from 'chart.js'
import { Doughnut, Bar } from 'vue-chartjs'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

interface PlanLite { id: number; name: string; period_start: string; period_end: string }

const props = defineProps<{ plans: PlanLite[] }>()

const api = useApi()
const authStore = useAuthStore()

const planId = ref<number | null>(null)
const startDate = ref('')
const endDate = ref('')
const period = ref('month')
const data = ref<any>(null)
const loading = ref(false)

const setupSearch = ref('')
const leaderSearch = ref('')

const currentPlan = computed(() => props.plans.find(p => p.id === planId.value) || null)

const resetToPlanPeriod = () => {
  if (currentPlan.value) {
    startDate.value = currentPlan.value.period_start
    endDate.value = currentPlan.value.period_end
  }
}

const load = async () => {
  if (!planId.value) return
  loading.value = true
  try {
    data.value = await api.getTrainingStatistics({
      plan_id: planId.value,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
      period: period.value,
    })
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}

// Pick initial plan (active plan if present, else first) and seed dates.
watch(() => props.plans, (plans) => {
  if (planId.value || !plans.length) return
  const active = plans.find(p => p.id === authStore.selectedPlanId)
  planId.value = active ? active.id : plans[0].id
}, { immediate: true })

// When the plan changes, reset the range to that plan's period (then load).
watch(planId, () => {
  resetToPlanPeriod()
  load()
})
// Re-fetch on range / bucket changes.
watch([startDate, endDate, period], load)

// ---- Tables (sortable + filterable via useTableState) ----
const filteredSetups = computed(() => {
  const q = setupSearch.value.trim().toLowerCase()
  const rows = data.value?.by_setup ?? []
  return q ? rows.filter((r: any) => r.name.toLowerCase().includes(q)) : rows
})
const filteredLeaders = computed(() => {
  const q = leaderSearch.value.trim().toLowerCase()
  const rows = data.value?.by_leader ?? []
  return q ? rows.filter((r: any) => r.label.toLowerCase().includes(q)) : rows
})
const setupTable = useTableState(filteredSetups as any, 'total' as any, true)
const leaderTable = useTableState(filteredLeaders as any, 'total' as any, true)

const setupCols = [
  { key: 'name', label: 'Setup', primary: true, sortable: true },
  { key: 'total', label: 'Total', align: 'right', sortable: true },
  { key: 'published', label: 'Pub.', align: 'right', sortable: true },
  { key: 'draft', label: 'Draft', align: 'right', sortable: true },
  { key: 'cancelled', label: 'Canc.', align: 'right', sortable: true },
  { key: 'distinct_leaders', label: 'Leaders', align: 'right', sortable: true },
  { key: 'accepted', label: 'Acc.', align: 'right', sortable: true },
  { key: 'declined', label: 'Dec.', align: 'right', sortable: true },
  { key: 'unanswered', label: 'Unans.', align: 'right', sortable: true },
] as const
const leaderCols = [
  { key: 'label', label: 'Leader', primary: true, sortable: true },
  { key: 'total', label: 'Total', align: 'right', sortable: true },
  { key: 'published', label: 'Pub.', align: 'right', sortable: true },
  { key: 'draft', label: 'Draft', align: 'right', sortable: true },
  { key: 'cancelled', label: 'Canc.', align: 'right', sortable: true },
] as const

const sum = (key: string) =>
  (filteredSetups.value as any[]).reduce((acc, r) => acc + (r[key] || 0), 0)

// ---- Charts ----
const C = { green: 'rgb(22,163,74)', blue: 'rgb(59,130,246)', gray: 'rgb(107,114,128)', red: 'rgb(239,68,68)' }

const statusChart = computed(() => ({
  labels: ['Published', 'Draft', 'Cancelled'],
  datasets: [{
    data: [data.value?.summary.published || 0, data.value?.summary.draft || 0, data.value?.summary.cancelled || 0],
    backgroundColor: [C.green, C.blue, C.gray], borderWidth: 2, borderColor: '#fff',
  }],
}))

const overTimeChart = computed(() => {
  const b = data.value?.over_time ?? []
  return {
    labels: b.map((x: any) => x.label),
    datasets: [
      { label: 'Published', data: b.map((x: any) => x.published), backgroundColor: C.green, stack: 's' },
      { label: 'Draft', data: b.map((x: any) => x.draft), backgroundColor: C.blue, stack: 's' },
      { label: 'Cancelled', data: b.map((x: any) => x.cancelled), backgroundColor: C.gray, stack: 's' },
    ],
  }
})

const leaderChart = computed(() => {
  const rows = [...(data.value?.by_leader ?? [])].sort((a: any, b: any) => b.total - a.total).slice(0, 12)
  return {
    labels: rows.map((r: any) => r.label),
    datasets: [{ label: 'Shifts', data: rows.map((r: any) => r.total), backgroundColor: C.blue }],
  }
})

const doughnutOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' as const } } }
const stackedBarOpts = {
  responsive: true, maintainAspectRatio: false,
  scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } },
  plugins: { legend: { position: 'bottom' as const } },
}
const horizontalBarOpts = {
  indexAxis: 'y' as const, responsive: true, maintainAspectRatio: false,
  scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
  plugins: { legend: { display: false } },
}
</script>
