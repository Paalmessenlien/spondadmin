<template>
  <div class="relative h-64">
    <Line v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-full">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps<{
  data: any
}>()

const chartData = computed(() => {
  if (!props.data || !props.data.data) return null

  return {
    labels: props.data.data.map((d: any) => d.date),
    datasets: [
      {
        label: 'Accepted',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderColor: 'rgb(34, 197, 94)',
        data: props.data.data.map((d: any) => d.accepted),
        fill: true,
        tension: 0.4
      },
      {
        label: 'Declined',
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        borderColor: 'rgb(239, 68, 68)',
        data: props.data.data.map((d: any) => d.declined),
        fill: true,
        tension: 0.4
      },
      {
        label: 'Unanswered',
        backgroundColor: 'rgba(156, 163, 175, 0.2)',
        borderColor: 'rgb(156, 163, 175)',
        data: props.data.data.map((d: any) => d.unanswered),
        fill: true,
        tension: 0.4
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
    title: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        precision: 0
      }
    }
  }
}
</script>
