<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const reportStore = useReportStore()
const toast = useToast()

onMounted(() => reportStore.fetchReports())

const handleView = (id: number) => navigateTo(`/dashboard/reports/${id}/view`)
const handleEdit = (id: number) => navigateTo(`/dashboard/reports/${id}/edit`)

const handleDelete = async (id: number) => {
  if (!confirm('Delete this report?')) return
  try {
    await reportStore.deleteReport(id)
    toast.add({ title: 'Success', description: 'Report deleted', color: 'green' })
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}

const handleExport = async (id: number) => {
  try {
    await reportStore.exportReport(id, 'csv')
    toast.add({ title: 'Success', description: 'Report exported', color: 'green' })
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}

const handleToggleFavorite = async (id: number) => {
  try {
    await reportStore.toggleFavorite(id)
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}
</script>

<template>
  <div class="p-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Reports' }
    ]" />

    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">Reports</h1>
      <UButton icon="i-heroicons-plus" to="/dashboard/reports/create">
        Create Report
      </UButton>
    </div>

    <div v-if="reportStore.loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <div v-else-if="reportStore.reports.length === 0" class="text-center py-12">
      <EmptyState
        icon="i-heroicons-document-chart-bar"
        title="No reports yet"
        description="Create your first report to get started"
      />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <ReportCard
        v-for="report in reportStore.reports"
        :key="report.id"
        :report="report"
        @view="handleView(report.id)"
        @edit="handleEdit(report.id)"
        @delete="handleDelete(report.id)"
        @toggle-favorite="handleToggleFavorite(report.id)"
        @export="handleExport(report.id)"
      />
    </div>
  </div>
</template>
