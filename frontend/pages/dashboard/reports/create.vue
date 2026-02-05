<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const router = useRouter()
const reportStore = useReportStore()
const toast = useToast()

const formData = ref({
  name: '',
  description: '',
  report_type: 'comprehensive',
  configuration: {
    date_range: {
      start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    category_ids: [],
    metrics: ['summary']
  },
  is_public: false,
  is_favorite: false
})

const handleSubmit = async () => {
  if (!formData.value.name || !formData.value.report_type) {
    toast.add({ title: 'Error', description: 'Name and type are required', color: 'red' })
    return
  }

  try {
    const report = await reportStore.createReport(formData.value)
    toast.add({ title: 'Success', description: 'Report created', color: 'green' })
    router.push(`/dashboard/reports/${report.id}/view`)
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
      { label: 'Create' }
    ]" />

    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Create Report</h1>

      <UCard>
        <ReportConfigurationForm v-model="formData" mode="create" />

        <template #footer>
          <div class="flex gap-2">
            <UButton @click="handleSubmit">Create & View Report</UButton>
            <UButton to="/dashboard/reports" color="gray" variant="soft">Cancel</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
