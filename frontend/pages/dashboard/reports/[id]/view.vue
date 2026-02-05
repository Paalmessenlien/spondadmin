<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const reportStore = useReportStore()
const toast = useToast()

const reportId = computed(() => parseInt(route.params.id as string))

onMounted(async () => {
  await reportStore.fetchReport(reportId.value)
  await generateReport()
})

const generating = ref(false)

const generateReport = async () => {
  generating.value = true
  try {
    await reportStore.generateReport(reportId.value)
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  } finally {
    generating.value = false
  }
}

const handleExport = async () => {
  try {
    await reportStore.exportReport(reportId.value, 'csv')
    toast.add({ title: 'Success', description: 'Report exported', color: 'green' })
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
      { label: reportStore.currentReport?.name || 'View' }
    ]" />

    <div v-if="reportStore.currentReport" class="space-y-6">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-3xl font-bold">{{ reportStore.currentReport.name }}</h1>
          <p v-if="reportStore.currentReport.description" class="text-gray-600 mt-1">
            {{ reportStore.currentReport.description }}
          </p>
        </div>
        <div class="flex gap-2">
          <UButton icon="i-heroicons-arrow-path" @click="generateReport" :loading="generating" variant="soft">
            Refresh
          </UButton>
          <ReportExportButton :report-id="reportId" @export="handleExport" />
        </div>
      </div>

      <div v-if="generating" class="flex justify-center py-12">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>

      <div v-else-if="reportStore.reportData" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Category Distribution -->
        <UCard v-if="reportStore.reportData.data.category_distribution">
          <template #header>
            <h2 class="text-lg font-semibold">Category Distribution</h2>
          </template>
          <CategoryDistributionChart :data="reportStore.reportData.data.category_distribution" />
        </UCard>

        <!-- Attendance Trends -->
        <UCard v-if="reportStore.reportData.data.attendance_trends">
          <template #header>
            <h2 class="text-lg font-semibold">Attendance Trends</h2>
          </template>
          <AttendanceTrendChart :data="reportStore.reportData.data.attendance_trends" />
        </UCard>

        <!-- Response Rates -->
        <UCard v-if="reportStore.reportData.data.response_rates">
          <template #header>
            <h2 class="text-lg font-semibold">Response Rates</h2>
          </template>
          <ResponseRateChart :data="reportStore.reportData.data.response_rates" />
        </UCard>

        <!-- Summary Statistics -->
        <UCard v-if="reportStore.reportData.data.summary">
          <template #header>
            <h2 class="text-lg font-semibold">Summary</h2>
          </template>
          <div class="space-y-4">
            <div v-for="(value, key) in reportStore.reportData.data.summary" :key="key" class="flex justify-between">
              <span class="text-gray-600 capitalize">{{ key.replace(/_/g, ' ') }}</span>
              <span class="font-semibold">{{ value }}</span>
            </div>
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>
