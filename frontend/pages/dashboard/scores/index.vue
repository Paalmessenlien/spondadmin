<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Scores & Records' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Scores & Records</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Competition results, records, and statistics from bueskyting.no
      </p>
    </div>

    <!-- Summary Cards -->
    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <UCard>
          <div class="text-center">
            <div class="text-3xl font-bold text-blue-600">{{ summary.total_results }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Competition Results</div>
          </div>
        </UCard>
        <UCard>
          <div class="text-center">
            <div class="text-3xl font-bold text-purple-600">{{ summary.total_competitions }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Competitions</div>
          </div>
        </UCard>
        <UCard>
          <div class="text-center">
            <div class="text-3xl font-bold text-amber-600">{{ summary.total_records }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Norwegian Records</div>
          </div>
        </UCard>
        <UCard>
          <div class="text-center">
            <div class="text-3xl font-bold text-green-600">{{ summary.total_archers }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Archers Tracked</div>
          </div>
        </UCard>
      </div>

      <!-- Unmatched archers alert -->
      <UCard v-if="summary.unmatched_archers > 0" class="border-amber-300 dark:border-amber-700">
        <div class="flex items-center space-x-3">
          <UIcon name="i-heroicons-exclamation-triangle" class="w-5 h-5 text-amber-500 flex-shrink-0" />
          <div class="flex-1">
            <span class="text-sm font-medium text-gray-900 dark:text-white">
              {{ summary.unmatched_archers }} archer(s) need matching
            </span>
            <span class="text-sm text-gray-500 ml-2">
              Link bueskyting.no archers to Spond members
            </span>
          </div>
          <UButton size="sm" color="amber" variant="soft" @click="navigateTo('/dashboard/settings/scraper')">
            Manage
          </UButton>
        </div>
      </UCard>

      <!-- Quick links -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <UCard class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/scores/results')">
          <div class="flex items-start space-x-4">
            <div class="w-12 h-12 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
              <UIcon name="i-heroicons-table-cells" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Results Browser</h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Search and filter all competition results.
              </p>
            </div>
          </div>
        </UCard>

        <UCard class="hover:border-amber-300 dark:hover:border-amber-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/scores/records')">
          <div class="flex items-start space-x-4">
            <div class="w-12 h-12 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center flex-shrink-0">
              <UIcon name="i-heroicons-trophy" class="w-6 h-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Norwegian Records</h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Club records from rekord.bueskyting.no.
              </p>
            </div>
          </div>
        </UCard>

        <UCard class="hover:border-purple-300 dark:hover:border-purple-700 transition-colors cursor-pointer" @click="navigateTo('/dashboard/scores/competitions')">
          <div class="flex items-start space-x-4">
            <div class="w-12 h-12 rounded-lg bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
              <UIcon name="i-heroicons-calendar-days" class="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Competitions</h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Browse competitions and their results.
              </p>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Recent Results -->
      <UCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold">Recent Results</h2>
            <UButton size="sm" variant="outline" color="neutral" @click="navigateTo('/dashboard/scores/results')">
              View All
            </UButton>
          </div>
        </template>

        <div v-if="loadingResults" class="flex justify-center py-8">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-6 w-6" />
        </div>

        <div v-else-if="recentResults.length === 0" class="text-center py-8 text-gray-500">
          <UIcon name="i-heroicons-viewfinder-circle" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>No competition results yet.</p>
          <p class="text-sm mt-1">Configure the scraper in Settings to start importing data.</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="result in recentResults"
            :key="result.id"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-900 dark:text-white truncate">{{ result.archer_name }}</div>
              <div class="text-sm text-gray-500 truncate">{{ result.event_name }}</div>
            </div>
            <div class="flex items-center space-x-3 ml-4">
              <div class="text-right">
                <div class="font-bold text-blue-600">{{ result.score }}</div>
                <div class="text-xs text-gray-500">{{ result.distance }}</div>
              </div>
              <UBadge v-if="result.ranking" :color="result.ranking <= 3 ? 'amber' : 'gray'" size="sm">
                #{{ result.ranking }}
              </UBadge>
            </div>
          </div>
        </div>

        <div v-if="summary.latest_scrape" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p class="text-xs text-gray-400">
            Last scraped: {{ formatDate(summary.latest_scrape) }}
          </p>
        </div>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()

const summary = ref<any>({
  total_results: 0, total_competitions: 0, total_records: 0,
  total_archers: 0, unmatched_archers: 0, latest_scrape: null,
})
const recentResults = ref<any[]>([])
const loading = ref(true)
const loadingResults = ref(true)

onMounted(async () => {
  try {
    summary.value = await api.getScoresSummary()
  } catch (err) {
    console.error('Failed to load scores summary:', err)
  } finally {
    loading.value = false
  }

  try {
    const data: any = await api.getResults({ limit: '10' })
    recentResults.value = data.results || []
  } catch (err) {
    console.error('Failed to load recent results:', err)
  } finally {
    loadingResults.value = false
  }
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>
