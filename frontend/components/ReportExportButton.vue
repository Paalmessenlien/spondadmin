<script setup lang="ts">
/**
 * ReportExportButton Component
 * Export dropdown button with format options
 */

const props = defineProps<{
  reportId: number
  loading?: boolean
}>()

const emit = defineEmits<{
  export: [format: string]
}>()

const exportFormats = [
  { label: 'CSV', value: 'csv', icon: 'i-heroicons-table-cells' },
  { label: 'PDF (Coming Soon)', value: 'pdf', icon: 'i-heroicons-document-text', disabled: true },
]

const isExporting = ref(false)

const handleExport = async (format: string) => {
  if (format === 'pdf') {
    useToast().add({
      title: 'Coming Soon',
      description: 'PDF export is not yet available',
      color: 'amber'
    })
    return
  }

  isExporting.value = true
  try {
    emit('export', format)
  } finally {
    // Keep loading for a moment to show feedback
    setTimeout(() => {
      isExporting.value = false
    }, 500)
  }
}
</script>

<template>
  <UDropdown
    :items="[exportFormats]"
    :popper="{ placement: 'bottom-end' }"
  >
    <UButton
      icon="i-heroicons-arrow-down-tray"
      :loading="loading || isExporting"
      :disabled="loading || isExporting"
    >
      Export
    </UButton>

    <template #item="{ item }">
      <div class="flex items-center gap-2 w-full">
        <UIcon :name="item.icon" class="w-4 h-4" />
        <span class="flex-1">{{ item.label }}</span>
      </div>
    </template>
  </UDropdown>
</template>
