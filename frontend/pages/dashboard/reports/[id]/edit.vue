<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const { canEdit } = usePermissions()
if (!canEdit.value) navigateTo('/dashboard/reports')

const route = useRoute()
const router = useRouter()
const reportStore = useReportStore()
const toast = useToast()

const reportId = computed(() => parseInt(route.params.id as string))
const loading = ref(true)

const formData = ref({
  name: '',
  description: '',
  report_type: 'comprehensive',
  configuration: {
    date_range: {
      start: '',
      end: ''
    },
    category_ids: [],
    metrics: []
  },
  is_public: false,
  is_favorite: false
})

onMounted(async () => {
  loading.value = true
  try {
    await reportStore.fetchReport(reportId.value)
    if (reportStore.currentReport) {
      // Populate form with existing data
      formData.value = {
        name: reportStore.currentReport.name,
        description: reportStore.currentReport.description || '',
        report_type: reportStore.currentReport.report_type,
        configuration: reportStore.currentReport.configuration,
        is_public: reportStore.currentReport.is_public,
        is_favorite: reportStore.currentReport.is_favorite
      }
    }
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
    router.push('/dashboard/reports')
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  if (!formData.value.name || !formData.value.report_type) {
    toast.add({ title: 'Error', description: 'Name and type are required', color: 'red' })
    return
  }

  try {
    await reportStore.updateReport(reportId.value, formData.value)
    toast.add({ title: 'Success', description: 'Report updated', color: 'green' })
    router.push(`/dashboard/reports/${reportId.value}/view`)
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}

const handleDelete = async () => {
  if (!confirm('Are you sure you want to delete this report?')) return

  try {
    await reportStore.deleteReport(reportId.value)
    toast.add({ title: 'Success', description: 'Report deleted', color: 'green' })
    router.push('/dashboard/reports')
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}
</script>

<template>
  <div class="p-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Reports', to: '/dashboard/reports' },
      { label: reportStore.currentReport?.name || 'Edit', to: `/dashboard/reports/${reportId}/view` },
      { label: 'Edit' }
    ]" />

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <div v-else class="max-w-4xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Edit Report</h1>
        <UButton
          icon="i-heroicons-trash"
          color="red"
          variant="soft"
          @click="handleDelete"
        >
          Delete Report
        </UButton>
      </div>

      <UCard>
        <ReportConfigurationForm v-model="formData" mode="edit" />

        <template #footer>
          <div class="flex gap-2">
            <UButton @click="handleSubmit">Save Changes</UButton>
            <UButton :to="`/dashboard/reports/${reportId}/view`" color="gray" variant="soft">
              Cancel
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
