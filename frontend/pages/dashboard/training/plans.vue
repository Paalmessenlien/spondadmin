<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Training plan', to: '/dashboard/training' },
      { label: 'Plans' }
    ]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Training plans</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Named periods that own their own session-type lists. The active plan is
          shared with the calendar — switching here also switches there.
        </p>
      </div>
      <UButton v-if="isAdmin && activeTab === 'plans'" icon="i-heroicons-plus" @click="openNew">
        New plan
      </UButton>
    </div>

    <UTabs v-model="activeTab" :items="tabItems" class="w-full">
      <template #content="{ item }">
        <!-- Plans list -->
        <div v-if="item.value === 'plans'" class="space-y-6 pt-2">

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <UCard v-else-if="plans.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-document-text" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-700 dark:text-gray-300 font-medium">No training plans yet</p>
      <p class="text-sm text-gray-500 mt-1">
        Create one to start grouping session types and shifts by period.
      </p>
      <div v-if="isAdmin" class="mt-4">
        <UButton icon="i-heroicons-plus" @click="openNew">New plan</UButton>
      </div>
    </UCard>

    <UCard v-else>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-2 px-3 font-medium text-gray-500"></th>
              <th class="text-left py-2 px-3 font-medium text-gray-500">Name</th>
              <th class="text-left py-2 px-3 font-medium text-gray-500">Period</th>
              <th class="text-right py-2 px-3 font-medium text-gray-500">Session types</th>
              <th class="text-right py-2 px-3 font-medium text-gray-500">Shifts</th>
              <th class="text-right py-2 px-3 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="plan in plans"
              :key="plan.id"
              class="border-b border-gray-100 dark:border-gray-800"
            >
              <td class="py-2 px-3 w-8">
                <UBadge
                  v-if="plan.id === authStore.selectedPlanId"
                  color="primary"
                  variant="solid"
                  size="xs"
                  title="Active plan"
                >
                  Active
                </UBadge>
              </td>
              <td class="py-2 px-3 font-medium text-gray-900 dark:text-white">
                <div>{{ plan.name }}</div>
                <div
                  v-if="plan.description"
                  class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 max-w-md"
                >
                  {{ plan.description }}
                </div>
              </td>
              <td class="py-2 px-3 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                {{ formatDate(plan.period_start) }} – {{ formatDate(plan.period_end) }}
              </td>
              <td class="py-2 px-3 text-right tabular-nums text-gray-700 dark:text-gray-300">
                {{ plan.session_type_count }}
              </td>
              <td class="py-2 px-3 text-right tabular-nums text-gray-700 dark:text-gray-300">
                {{ plan.shift_count }}
              </td>
              <td class="py-2 px-3 text-right space-x-1 whitespace-nowrap">
                <UButton
                  v-if="plan.id !== authStore.selectedPlanId"
                  size="xs"
                  color="primary"
                  variant="soft"
                  icon="i-heroicons-cursor-arrow-rays"
                  @click="activate(plan)"
                >
                  Activate
                </UButton>
                <UButton
                  size="xs"
                  color="neutral"
                  variant="soft"
                  icon="i-heroicons-eye"
                  :loading="!!plan._viewing"
                  @click="viewReport(plan)"
                >
                  View
                </UButton>
                <UButton
                  size="xs"
                  color="neutral"
                  variant="soft"
                  icon="i-heroicons-arrow-down-tray"
                  :loading="!!plan._exporting"
                  @click="exportPdf(plan)"
                >
                  PDF
                </UButton>
                <UButton
                  v-if="isAdmin"
                  size="xs"
                  color="neutral"
                  variant="soft"
                  icon="i-heroicons-pencil-square"
                  @click="openEdit(plan)"
                >
                  Edit
                </UButton>
                <UButton
                  v-if="isAdmin"
                  size="xs"
                  color="red"
                  variant="soft"
                  icon="i-heroicons-trash"
                  :disabled="plan.session_type_count > 0"
                  :title="plan.session_type_count > 0 ? 'Cannot delete — session types still reference this plan' : 'Delete plan'"
                  @click="confirmDelete(plan)"
                >
                  Delete
                </UButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

        </div>

        <!-- Statistics -->
        <div v-else-if="item.value === 'stats'" class="pt-2">
          <TrainingStatistics :plans="plans" />
        </div>
      </template>
    </UTabs>

    <!-- New / edit modal -->
    <UModal v-model:open="editorOpen" :ui="{ content: 'max-w-xl' }">
      <template #content>
        <div v-if="draft" class="p-6 space-y-4">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ draft.id ? 'Edit plan' : 'New plan' }}
          </h2>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <UInput
              v-model="draft.name"
              placeholder="e.g. Vaktliste OKT–DES 2026"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Period start</label>
              <DateInputISO v-model="draft.period_start" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Period end</label>
              <DateInputISO v-model="draft.period_end" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
            <UTextarea
              v-model="draft.description"
              :rows="3"
              placeholder="Optional notes about this period."
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </div>

          <p v-if="draftError" class="text-sm text-red-600 dark:text-red-400">
            {{ draftError }}
          </p>

          <div class="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <UButton color="neutral" variant="outline" @click="editorOpen = false">
              Cancel
            </UButton>
            <UButton
              icon="i-heroicons-check"
              :loading="saving"
              :disabled="!isDraftValid"
              @click="saveDraft"
            >
              Save
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- In-app report viewer — renders the same PDF inline (browser's PDF
         viewer) so admins can read the report without downloading it. -->
    <UModal v-model:open="viewerOpen" :ui="{ content: 'max-w-5xl' }">
      <template #content>
        <div class="flex flex-col h-[85vh]">
          <div class="flex items-center justify-between gap-3 p-3 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white truncate">
              {{ viewerTitle }}
            </h2>
            <div class="flex items-center gap-2 shrink-0">
              <a
                v-if="viewerUrl"
                :href="viewerUrl"
                :download="`${viewerTitle}.pdf`"
                class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
              >
                <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4" />
                Download
              </a>
              <UButton
                size="xs"
                color="neutral"
                variant="ghost"
                icon="i-heroicons-x-mark"
                aria-label="Close"
                @click="viewerOpen = false"
              />
            </div>
          </div>
          <iframe
            v-if="viewerUrl"
            :src="viewerUrl"
            class="flex-1 w-full rounded-b-lg bg-white"
            title="Training plan report"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const authStore = useAuthStore()
const { isAdmin } = usePermissions()

interface PlanRow {
  id: number
  name: string
  period_start: string
  period_end: string
  description: string | null
  is_active: boolean
  session_type_count: number
  shift_count: number
  _exporting?: boolean
  _viewing?: boolean
}

const plans = ref<PlanRow[]>([])
const loading = ref(true)

const activeTab = ref('plans')
const tabItems = [
  { label: 'Plans', value: 'plans', icon: 'i-heroicons-document-text' },
  { label: 'Statistics', value: 'stats', icon: 'i-heroicons-chart-bar' },
]

const editorOpen = ref(false)
const draft = ref<{
  id: number | null
  name: string
  period_start: string
  period_end: string
  description: string
} | null>(null)
const saving = ref(false)
const draftError = ref('')

const isDraftValid = computed(() => {
  if (!draft.value) return false
  if (!draft.value.name?.trim()) return false
  if (!draft.value.period_start || !draft.value.period_end) return false
  return draft.value.period_start <= draft.value.period_end
})

const formatDate = (iso: string): string => {
  if (!iso) return ''
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!m) return iso
  return `${m[3]}.${m[2]}.${m[1]}`
}

const load = async () => {
  loading.value = true
  try {
    const resp: any = await api.getTrainingPlans()
    plans.value = (resp.items || []).map((p: any) => ({
      ...p,
      _exporting: false,
    }))

    // First-time UX: if nothing is selected yet but a plan exists, snap
    // to the newest one. That way the calendar isn't empty on the very
    // first visit after this feature lands.
    if (
      authStore.selectedPlanId === null &&
      plans.value.length > 0
    ) {
      authStore.setSelectedPlan(plans.value[0].id)
    }
  } catch (err: any) {
    toast.add({
      title: 'Load failed',
      description: err?.data?.detail || 'Could not load training plans',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

const openNew = () => {
  draftError.value = ''
  // Default period: today → today+3 months
  const today = new Date()
  const end = new Date(today)
  end.setMonth(end.getMonth() + 3)
  const iso = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  draft.value = {
    id: null,
    name: '',
    period_start: iso(today),
    period_end: iso(end),
    description: '',
  }
  editorOpen.value = true
}

const openEdit = (plan: PlanRow) => {
  draftError.value = ''
  draft.value = {
    id: plan.id,
    name: plan.name,
    period_start: plan.period_start,
    period_end: plan.period_end,
    description: plan.description ?? '',
  }
  editorOpen.value = true
}

const saveDraft = async () => {
  if (!draft.value || !isDraftValid.value) return
  draftError.value = ''
  saving.value = true
  try {
    const d = draft.value
    const body = {
      name: d.name.trim(),
      period_start: d.period_start,
      period_end: d.period_end,
      description: d.description?.trim() ? d.description : null,
    }
    if (d.id) {
      await api.updateTrainingPlan(d.id, body)
      toast.add({ title: 'Saved', description: `${body.name} updated`, color: 'success' })
    } else {
      const created: any = await api.createTrainingPlan(body)
      toast.add({ title: 'Created', description: `${body.name} added`, color: 'success' })
      // Auto-activate the freshly-created plan so the calendar reflects it.
      if (created?.id) authStore.setSelectedPlan(created.id)
    }
    editorOpen.value = false
    await load()
  } catch (err: any) {
    draftError.value = err?.data?.detail || 'Could not save plan'
  } finally {
    saving.value = false
  }
}

const confirmDelete = async (plan: PlanRow) => {
  if (plan.session_type_count > 0) return
  if (!confirm(`Delete training plan "${plan.name}"? This cannot be undone.`)) return
  try {
    await api.deleteTrainingPlan(plan.id)
    if (authStore.selectedPlanId === plan.id) {
      authStore.setSelectedPlan(null)
    }
    toast.add({ title: 'Deleted', description: `${plan.name} removed`, color: 'success' })
    await load()
  } catch (err: any) {
    toast.add({
      title: 'Delete failed',
      description: err?.data?.detail || 'Could not delete plan',
      color: 'error',
    })
  }
}

const activate = (plan: PlanRow) => {
  authStore.setSelectedPlan(plan.id)
  toast.add({
    title: 'Activated',
    description: `${plan.name} is now the active training plan.`,
    color: 'success',
  })
}

// In-app report viewer. We reuse the existing PDF blob and render it inline
// in an <iframe> (the browser's PDF viewer) so no file hits the download
// folder. The object URL is revoked when the modal closes to free memory.
const viewerOpen = ref(false)
const viewerUrl = ref<string | null>(null)
const viewerTitle = ref('')

const viewReport = async (plan: PlanRow) => {
  plan._viewing = true
  try {
    const blob: Blob = await api.exportTrainingPlanPdf(plan.id)
    if (viewerUrl.value) URL.revokeObjectURL(viewerUrl.value)
    viewerUrl.value = URL.createObjectURL(blob)
    viewerTitle.value = plan.name
    viewerOpen.value = true
  } catch (err: any) {
    toast.add({
      title: 'Could not open report',
      description: err?.data?.detail || 'Failed to render the report',
      color: 'error',
    })
  } finally {
    plan._viewing = false
  }
}

watch(viewerOpen, (open) => {
  if (!open && viewerUrl.value) {
    URL.revokeObjectURL(viewerUrl.value)
    viewerUrl.value = null
  }
})

const exportPdf = async (plan: PlanRow) => {
  plan._exporting = true
  try {
    const blob: Blob = await api.exportTrainingPlanPdf(plan.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${plan.name}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err: any) {
    toast.add({
      title: 'Export failed',
      description: err?.data?.detail || 'Could not generate PDF',
      color: 'error',
    })
  } finally {
    plan._exporting = false
  }
}

onMounted(load)
</script>
