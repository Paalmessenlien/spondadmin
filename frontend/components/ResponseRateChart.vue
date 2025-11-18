<template>
  <div class="relative h-64">
    <Doughnut v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-full">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Doughnut } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  data: any
}>()

const chartData = computed(() => {
  if (!props.data) return null

  return {
    labels: ['Accepted', 'Declined', 'Unanswered'],
    datasets: [
      {
        data: [
          props.data.accepted,
          props.data.declined,
          props.data.unanswered
        ],
        backgroundColor: [
          'rgb(34, 197, 94)',
          'rgb(239, 68, 68)',
          'rgb(156, 163, 175)'
        ],
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
          return `${label}: ${value} (${percentage}%)`
        }
      }
    }
  }
}
</script>
