<script setup lang="ts">
/**
 * CategoryTrendChart Component
 * Multi-line chart showing attendance trends by category
 */
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface CategoryTrendPoint {
  date: string
  category_id: number
  category_name: string
  color: string
  total_events: number
  accepted: number
  attendance_rate: number
}

interface CategoryTrendsData {
  period: string
  categories: string[]
  data: CategoryTrendPoint[]
}

const props = defineProps<{
  data: CategoryTrendsData
  selectedCategories?: number[]
}>()

const chartData = computed(() => {
  if (!props.data || !props.data.data || props.data.data.length === 0) return null

  // Group data by category
  const categoriesMap = new Map<number, { name: string, color: string, points: Map<string, number> }>()

  props.data.data.forEach(point => {
    if (!categoriesMap.has(point.category_id)) {
      categoriesMap.set(point.category_id, {
        name: point.category_name,
        color: point.color,
        points: new Map()
      })
    }

    const category = categoriesMap.get(point.category_id)!
    category.points.set(point.date, point.attendance_rate)
  })

  // Get unique dates (sorted)
  const dates = Array.from(new Set(props.data.data.map(d => d.date))).sort()

  // Build datasets
  const datasets = Array.from(categoriesMap.entries())
    .filter(([catId]) => {
      if (!props.selectedCategories || props.selectedCategories.length === 0) return true
      return props.selectedCategories.includes(catId)
    })
    .map(([catId, category]) => ({
      label: category.name,
      borderColor: category.color,
      backgroundColor: `${category.color}20`,
      data: dates.map(date => category.points.get(date) || 0),
      tension: 0.4,
      borderWidth: 2
    }))

  return {
    labels: dates,
    datasets
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false
  },
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          const label = context.dataset.label || ''
          const value = context.parsed.y || 0
          return `${label}: ${value.toFixed(1)}% attendance`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      ticks: {
        callback: function(value: any) {
          return value + '%'
        }
      }
    }
  }
}
</script>

<template>
  <div class="relative h-64">
    <Line v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-full text-gray-500">
      <div class="text-center">
        <UIcon name="i-heroicons-chart-bar" class="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No trend data available</p>
      </div>
    </div>
  </div>
</template>
