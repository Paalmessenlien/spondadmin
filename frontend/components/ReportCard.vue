<script setup lang="ts">
/**
 * ReportCard Component
 * Display report in grid view with actions
 */

interface Report {
  id: number
  name: string
  description?: string
  report_type: string
  is_public: boolean
  is_favorite: boolean
  created_by: number
  last_generated_at?: string
  created_at: string
}

const props = defineProps<{
  report: Report
}>()

const emit = defineEmits<{
  view: []
  edit: []
  delete: []
  toggleFavorite: []
  export: []
}>()

const reportStore = useReportStore()

// Format date
const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const lastGenerated = computed(() => {
  if (!props.report.last_generated_at) return 'Never generated'
  return `Generated ${formatDate(props.report.last_generated_at)}`
})

// Report type icon
const reportTypeIcon = computed(() => {
  const icons: Record<string, string> = {
    category_breakdown: 'i-heroicons-chart-pie',
    attendance_trends: 'i-heroicons-chart-bar',
    comprehensive: 'i-heroicons-document-chart-bar',
    custom: 'i-heroicons-adjustments-horizontal'
  }
  return icons[props.report.report_type] || 'i-heroicons-document-text'
})
</script>

<template>
  <UCard class="hover:shadow-lg transition-shadow">
    <template #header>
      <div class="flex items-start justify-between gap-2">
        <div class="flex items-start gap-3 flex-1 min-w-0">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
              <UIcon :name="reportTypeIcon" class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-semibold text-gray-900 dark:text-white truncate">
              {{ report.name }}
            </h3>
            <p v-if="report.description" class="text-sm text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-2">
              {{ report.description }}
            </p>
          </div>
        </div>

        <!-- Favorite button -->
        <UButton
          :icon="report.is_favorite ? 'i-heroicons-star-solid' : 'i-heroicons-star'"
          size="xs"
          :color="report.is_favorite ? 'amber' : 'gray'"
          variant="ghost"
          @click.stop="emit('toggleFavorite')"
          :title="report.is_favorite ? 'Remove from favorites' : 'Add to favorites'"
        />
      </div>
    </template>

    <div class="space-y-3">
      <!-- Badges -->
      <div class="flex items-center gap-2 flex-wrap">
        <UBadge
          :color="report.is_public ? 'green' : 'gray'"
          variant="subtle"
          size="xs"
        >
          <UIcon :name="report.is_public ? 'i-heroicons-globe-alt' : 'i-heroicons-lock-closed'" class="w-3 h-3" />
          {{ report.is_public ? 'Public' : 'Private' }}
        </UBadge>
        <UBadge color="blue" variant="subtle" size="xs">
          {{ report.report_type.replace('_', ' ') }}
        </UBadge>
      </div>

      <!-- Last generated -->
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <UIcon name="i-heroicons-clock" class="w-4 h-4" />
        <span>{{ lastGenerated }}</span>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-2">
        <UButton
          size="xs"
          color="primary"
          @click="emit('view')"
        >
          View Report
        </UButton>

        <div class="flex items-center gap-1">
          <UButton
            icon="i-heroicons-arrow-down-tray"
            size="xs"
            color="gray"
            variant="ghost"
            @click.stop="emit('export')"
            title="Export"
          />
          <UButton
            icon="i-heroicons-pencil"
            size="xs"
            color="gray"
            variant="ghost"
            @click.stop="emit('edit')"
            title="Edit"
          />
          <UButton
            icon="i-heroicons-trash"
            size="xs"
            color="red"
            variant="ghost"
            @click.stop="emit('delete')"
            title="Delete"
          />
        </div>
      </div>
    </template>
  </UCard>
</template>
