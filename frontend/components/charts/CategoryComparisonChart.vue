<script setup lang="ts">
/**
 * CategoryComparisonChart Component
 * Horizontal bar chart comparing attendance rates across categories
 */
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

interface CategoryAttendanceStats {
  category_id: number
  category_name: string
  color: string
  icon: string
  total_events: number
  avg_attendance_rate: number
  total_responses: number
  accepted: number
  declined: number
}

const props = defineProps<{
  data: CategoryAttendanceStats[]
}>()

const chartData = computed(() => {
  if (!props.data || props.data.length === 0) return null

  return {
    labels: props.data.map(item => item.category_name),
    datasets: [
      {
        label: 'Attendance Rate (%)',
        data: props.data.map(item => item.avg_attendance_rate),
        backgroundColor: props.data.map(item => item.color),
        borderColor: props.data.map(item => item.color),
        borderWidth: 1
      }
    ]
  }
})

const chartOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          const value = context.parsed.x || 0
          const dataIndex = context.dataIndex
          const category = props.data[dataIndex]
          return [
            `Attendance Rate: ${value.toFixed(1)}%`,
            `Total Events: ${category.total_events}`,
            `Accepted: ${category.accepted}`,
            `Declined: ${category.declined}`
          ]
        }
      }
    }
  },
  scales: {
    x: {
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
    <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-full text-gray-500">
      <div class="text-center">
        <UIcon name="i-heroicons-chart-bar-square" class="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No comparison data available</p>
      </div>
    </div>
  </div>
</template>
