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

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="text-right py-3 px-2 font-medium text-gray-500 w-16">Rank</th>
                <th class="text-left py-3 px-2 font-medium text-gray-500">Archer</th>
                <th class="text-left py-3 px-2 font-medium text-gray-500">Distance</th>
                <th class="text-left py-3 px-2 font-medium text-gray-500">Class</th>
                <th class="text-right py-3 px-2 font-medium text-gray-500">Score</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="result in competition.results"
                :key="result.id"
                class="border-b border-gray-100 dark:border-gray-800"
              >
                <td class="py-2 px-2 text-right">
                  <UBadge v-if="result.ranking" :color="result.ranking <= 3 ? 'amber' : 'gray'" size="sm">
                    #{{ result.ranking }}
                  </UBadge>
                </td>
                <td class="py-2 px-2 font-medium text-gray-900 dark:text-white">
                  <NuxtLink
                    v-if="result.member_id"
                    :to="`/dashboard/members/${result.member_id}`"
                    class="text-blue-600 dark:text-blue-400 hover:underline"
                    title="View member profile"
                  >{{ result.archer_name }}</NuxtLink>
                  <span v-else>{{ result.archer_name }}</span>
                </td>
                <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ result.distance }}</td>
                <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ result.equipment_class }}</td>
                <td class="py-2 px-2 text-right font-bold text-blue-600">{{ result.score }}</td>
              </tr>
            </tbody>
          </table>
        </div>
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
