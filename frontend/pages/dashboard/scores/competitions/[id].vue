<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Scores & Records', to: '/dashboard/scores' },
      { label: 'Competitions', to: '/dashboard/scores/competitions' },
      { label: competition?.competition?.name || 'Competition' }
    ]" />

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else-if="competition">
      <!-- Competition Header -->
      <UCard>
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ competition.competition.name }}
          </h1>
          <div class="mt-2 flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
            <div v-if="competition.competition.date" class="flex items-center space-x-1">
              <UIcon name="i-heroicons-calendar" class="w-4 h-4" />
              <span>{{ formatDate(competition.competition.date) }}</span>
            </div>
            <div v-if="competition.competition.location" class="flex items-center space-x-1">
              <UIcon name="i-heroicons-map-pin" class="w-4 h-4" />
              <span>{{ competition.competition.location }}</span>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Results -->
      <UCard>
        <template #header>
          <h2 class="text-xl font-bold">Results ({{ competition.results?.length || 0 }})</h2>
        </template>

        <div v-if="!competition.results?.length" class="text-center py-8 text-gray-500">
          No results for this competition
        </div>

        <ResponsiveTable v-else :columns="resultCols" :rows="competition.results" empty-text="No results.">
          <template #cell-ranking="{ row }">
            <UBadge v-if="row.ranking" :color="row.ranking <= 3 ? 'amber' : 'gray'" size="sm">#{{ row.ranking }}</UBadge>
          </template>
          <template #cell-archer_name="{ row }">
            <NuxtLink
              v-if="row.member_id"
              :to="`/dashboard/members/${row.member_id}`"
              class="text-blue-600 dark:text-blue-400 hover:underline"
              title="View member profile"
            >{{ row.archer_name }}</NuxtLink>
            <span v-else>{{ row.archer_name }}</span>
          </template>
          <template #cell-score="{ row }"><span class="font-bold text-blue-600">{{ row.score }}</span></template>
        </ResponsiveTable>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const api = useApi()

const competition = ref<any>(null)
const loading = ref(true)

const resultCols = [
  { key: 'ranking', label: 'Rank', align: 'right' },
  { key: 'archer_name', label: 'Archer', primary: true },
  { key: 'distance', label: 'Distance' },
  { key: 'equipment_class', label: 'Class' },
  { key: 'score', label: 'Score', align: 'right' },
] as const

onMounted(async () => {
  try {
    const id = parseInt(route.params.id as string)
    competition.value = await api.getCompetition(id)
  } catch (err) {
    console.error('Failed to load competition:', err)
  } finally {
    loading.value = false
  }
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>
