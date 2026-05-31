<script setup lang="ts">
/**
 * ReportConfigurationForm Component
 * Form for configuring report settings
 */

interface ReportConfiguration {
  date_range?: {
    start: string
    end: string
  }
  group_ids?: string[]
  category_ids?: number[]
  exclude_category_ids?: number[]
  metrics?: string[]
  chart_types?: string[]
  comparison_period?: string
}

interface FormData {
  name: string
  description?: string
  report_type: string
  configuration: ReportConfiguration
  is_public: boolean
  is_favorite: boolean
}

const props = defineProps<{
  modelValue: Partial<FormData>
  mode?: 'create' | 'edit'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Partial<FormData>]
}>()

// Form state
const localValue = ref<Partial<FormData>>({ ...props.modelValue })

// Report type options
const reportTypes = [
  { value: 'category_breakdown', label: 'Category Breakdown', description: 'Event distribution by category' },
  { value: 'attendance_trends', label: 'Attendance Trends', description: 'Attendance over time' },
  { value: 'comprehensive', label: 'Comprehensive Report', description: 'All metrics combined' },
]

// Metric options
const metricOptions = [
  { value: 'summary', label: 'Summary Statistics' },
  { value: 'category_distribution', label: 'Category Distribution' },
  { value: 'attendance_trends', label: 'Attendance Trends' },
  { value: 'response_rates', label: 'Response Rates' },
  { value: 'member_participation', label: 'Member Participation Details' },
  { value: 'event_details', label: 'Event Details with Responses' },
  { value: 'category_details', label: 'Category Breakdown Details' },
  { value: 'attendance_log', label: 'Daily Attendance Log' },
  { value: 'organizer_statistics', label: 'Organizer Statistics' },
]

// Load categories and groups
const categoryStore = useCategoryStore()
const authStore = useAuthStore()

onMounted(async () => {
  if (categoryStore.categories.length === 0) {
    await categoryStore.fetchCategories()
  }
})

// Date range helpers
const today = new Date().toISOString().split('T')[0]
const threeMonthsAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

// Initialize default configuration if needed
if (!localValue.value.configuration) {
  localValue.value.configuration = {
    date_range: {
      start: threeMonthsAgo,
      end: today
    },
    category_ids: [],
    exclude_category_ids: [],
    metrics: ['summary']
  }
} else {
  // Ensure category_ids is always an array
  if (!localValue.value.configuration.category_ids) {
    localValue.value.configuration.category_ids = []
  }
  // Ensure exclude_category_ids is always an array
  if (!localValue.value.configuration.exclude_category_ids) {
    localValue.value.configuration.exclude_category_ids = []
  }
}

// Update parent
const updateValue = () => {
  emit('update:modelValue', localValue.value)
}

watch(localValue, () => {
  updateValue()
}, { deep: true })
</script>

<template>
  <div class="space-y-6">
    <!-- Basic Info -->
    <div class="space-y-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Basic Information</h3>

      <UFormGroup label="Report Name" required>
        <UInput
          v-model="localValue.name"
          placeholder="Enter report name..."
        />
      </UFormGroup>

      <UFormGroup label="Description">
        <UTextarea
          v-model="localValue.description"
          placeholder="Enter report description..."
          :rows="2"
        />
      </UFormGroup>

      <UFormGroup label="Report Type" required>
        <USelectMenu
          v-model="localValue.report_type"
          :items="reportTypes"
          value-key="value"
          placeholder="Select report type..."
        >
          <template #label>
            <span v-if="localValue.report_type">
              {{ reportTypes.find(t => t.value === localValue.report_type)?.label }}
            </span>
            <span v-else class="text-gray-500">Select report type...</span>
          </template>
          <template #item="{ item }">
            <div class="flex flex-col">
              <span class="font-medium">{{ item.label }}</span>
              <span class="text-xs text-gray-500">{{ item.description }}</span>
            </div>
          </template>
        </USelectMenu>
      </UFormGroup>
    </div>

    <!-- Date Range -->
    <div class="space-y-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Date Range</h3>

      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Start Date">
          <UInput type="date" class="w-full" v-model="localValue.configuration!.date_range!.start" />
        </UFormGroup>

        <UFormGroup label="End Date">
          <UInput type="date" class="w-full" v-model="localValue.configuration!.date_range!.end" />
        </UFormGroup>
      </div>
    </div>

    <!-- Categories Filter -->
    <div class="space-y-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Category Filters</h3>

      <UFormGroup
        label="Include Categories"
        help="Leave empty to include all categories"
      >
        <CategorySelector
          v-model="localValue.configuration!.category_ids!"
          :multiple="true"
          placeholder="All categories"
        />
      </UFormGroup>

      <UFormGroup
        label="Exclude Categories"
        help="Select categories to exclude from the report"
      >
        <CategorySelector
          v-model="localValue.configuration!.exclude_category_ids!"
          :multiple="true"
          placeholder="No exclusions"
        />
      </UFormGroup>

      <div
        v-if="localValue.configuration!.category_ids!.length > 0 && localValue.configuration!.exclude_category_ids!.length > 0"
        class="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
      >
        <div class="flex items-start gap-2">
          <UIcon name="i-heroicons-exclamation-triangle" class="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5" />
          <p class="text-sm text-amber-800 dark:text-amber-300">
            Note: Exclude filters are applied after include filters. Only included categories that are not excluded will appear in the report.
          </p>
        </div>
      </div>
    </div>

    <!-- Metrics (for comprehensive reports) -->
    <div v-if="localValue.report_type === 'comprehensive'" class="space-y-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Metrics to Include</h3>

      <div class="space-y-2">
        <UCheckbox
          v-for="metric in metricOptions"
          :key="metric.value"
          :model-value="localValue.configuration!.metrics?.includes(metric.value)"
          :label="metric.label"
          @update:model-value="(checked: boolean) => {
            if (!localValue.configuration!.metrics) localValue.configuration!.metrics = []
            if (checked) {
              localValue.configuration!.metrics.push(metric.value)
            } else {
              localValue.configuration!.metrics = localValue.configuration!.metrics.filter(m => m !== metric.value)
            }
          }"
        />
      </div>
    </div>

    <!-- Report Options -->
    <div class="space-y-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Options</h3>

      <div class="space-y-2">
        <UCheckbox
          v-model="localValue.is_public"
          label="Make report public (visible to all admins)"
        />

        <UCheckbox
          v-model="localValue.is_favorite"
          label="Add to favorites"
        />
      </div>
    </div>
  </div>
</template>
