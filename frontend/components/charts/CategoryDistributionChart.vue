<script setup lang="ts">
/**
 * CategoryDistributionChart Component
 * Doughnut chart showing event distribution by category
 */
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Doughnut } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

interface CategoryDistribution {
  category_id: number
  category_name: string
  color: string
  icon: string
  event_count: number
  percentage: number
}

const props = defineProps<{
  data: CategoryDistribution[] | any
}>()

const chartData = computed(() => {
  // Handle array or object with array
  const dataArray = Array.isArray(props.data) ? props.data : []

  if (!dataArray || dataArray.length === 0) {
    return null
  }

  // Filter out categories with 0 events
  const filteredData = dataArray.filter(item => item.event_count > 0)

  if (filteredData.length === 0) {
    return null
  }

  return {
    labels: filteredData.map(item => item.category_name),
    datasets: [
      {
        data: filteredData.map(item => item.event_count),
        backgroundColor: filteredData.map(item => item.color),
        borderWidth: 2,
        borderColor: '#fff'
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          const label = context.label || ''
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = ((value / total) * 100).toFixed(1)
          return `${label}: ${value} events (${percentage}%)`
        }
      }
    }
  }
}
</script>

<template>
  <div class="relative h-64">
    <ClientOnly>
      <Doughnut v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="flex items-center justify-center h-full text-gray-500">
        <div class="text-center">
          <UIcon name="i-heroicons-chart-pie" class="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p class="text-sm font-medium">No category data available</p>
          <p class="text-xs mt-1">
            {{ Array.isArray(data) ? `Received ${data.length} categories` : 'Invalid data format' }}
          </p>
        </div>
      </div>
      <template #fallback>
        <div class="flex items-center justify-center h-full">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-6 w-6 text-gray-400" />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>
