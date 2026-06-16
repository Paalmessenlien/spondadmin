<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Competition Scraper' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Competition Scraper</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Configure and manage competition data scraping from bueskyting.no
      </p>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else>
      <!-- Configuration -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold">Configuration</h2>
        </template>

        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Club ID</label>
              <UInput v-model="configForm.club_id" placeholder="e.g. 55" />
              <p class="text-xs text-gray-500 mt-1">Your club ID on resultat.bueskyting.no</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Scrape Interval (hours)</label>
              <UInput v-model.number="configForm.scrape_interval_hours" type="number" min="1" max="168" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Results Base URL</label>
              <UInput v-model="configForm.base_url" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Records Base URL</label>
              <UInput v-model="configForm.records_url" />
            </div>
          </div>

          <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-2">
              <UToggle v-model="configForm.auto_scrape_enabled" />
              <span class="text-sm text-gray-700 dark:text-gray-300">Enable automatic scraping</span>
            </div>
            <UButton @click="saveConfig" :loading="savingConfig">Save Configuration</UButton>
          </div>
        </div>
      </UCard>

      <!-- Manual Triggers -->
      <UCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold">Manual Scraping</h2>
            <UBadge v-if="scrapeRunning" color="blue" variant="subtle">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin w-3 h-3 mr-1" />
              Running...
            </UBadge>
          </div>
        </template>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <UCard>
            <div class="text-center space-y-3">
              <UIcon name="i-heroicons-users" class="w-8 h-8 text-blue-600 mx-auto" />
              <h3 class="font-medium">Full Scrape</h3>
              <p class="text-xs text-gray-500">Club + all archers</p>
              <UButton size="sm" block :disabled="scrapeRunning || !configForm.club_id" @click="runScrape('full')">
                Run Full Scrape
              </UButton>
            </div>
          </UCard>
          <UCard>
            <div class="text-center space-y-3">
              <UIcon name="i-heroicons-trophy" class="w-8 h-8 text-amber-600 mx-auto" />
              <h3 class="font-medium">Records Scrape</h3>
              <p class="text-xs text-gray-500">Norwegian records</p>
              <UButton size="sm" block color="amber" :disabled="scrapeRunning" @click="runScrape('records')">
                Scrape Records
              </UButton>
            </div>
          </UCard>
          <UCard>
            <div class="text-center space-y-3">
              <UIcon name="i-heroicons-calendar" class="w-8 h-8 text-green-600 mx-auto" />
              <h3 class="font-medium">Fix Missing Dates</h3>
              <p class="text-xs text-gray-500">Scrape event pages</p>
              <UButton size="sm" block color="green" :disabled="scrapeRunning" @click="runScrape('event_dates')">
                Fix Dates
              </UButton>
            </div>
          </UCard>
        </div>
      </UCard>

      <!-- Unmatched Archers -->
      <UCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold">Unmatched Archers ({{ unmatchedArchers.length }})</h2>
            <UButton size="sm" variant="outline" color="neutral" :loading="autoMatching" @click="runAutoMatch">
              Auto-Match
            </UButton>
          </div>
        </template>

        <div v-if="unmatchedArchers.length === 0" class="text-center py-6 text-gray-500">
          <p>All archers are matched to members</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="archer in unmatchedArchers"
            :key="archer.id"
            class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-900 dark:text-white">{{ archer.name }}</div>
              <div class="text-xs text-gray-500">
                ID: {{ archer.bueskyting_id }}
                <span v-if="!archer.is_active" class="ml-2 text-red-500">Inactive</span>
              </div>
              <div v-if="archer.suggested_spond_id" class="text-xs text-blue-500 mt-1">
                Suggested match ({{ Math.round(archer.match_confidence || 0) }}% confidence)
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-2 sm:ml-4">
              <UInput
                v-model="matchForms[archer.bueskyting_id]"
                placeholder="Spond ID"
                size="sm"
                class="w-full sm:w-32"
              />
              <UButton
                size="xs"
                color="green"
                :disabled="!matchForms[archer.bueskyting_id]"
                @click="matchArcherAction(archer.bueskyting_id)"
              >
                Match
              </UButton>
              <UButton size="xs" color="gray" variant="ghost" @click="dismissArcher(archer.id)">
                Dismiss
              </UButton>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Scrape Logs -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold">Scrape History</h2>
        </template>

        <div v-if="logs.length === 0" class="text-center py-6 text-gray-500">
          <p>No scrape history yet</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="log in logs"
            :key="log.id"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm"
          >
            <div class="flex items-center space-x-3">
              <UBadge :color="log.status === 'completed' ? 'green' : log.status === 'running' ? 'blue' : 'red'" size="sm">
                {{ log.status }}
              </UBadge>
              <span class="font-medium">{{ log.scrape_type }}</span>
            </div>
            <div class="flex items-center space-x-4 text-gray-500">
              <span>{{ log.items_found }} found</span>
              <span>{{ log.items_created }} new</span>
              <span>{{ log.items_updated }} updated</span>
              <span>{{ formatDate(log.created_at) }}</span>
            </div>
          </div>
        </div>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const { canManageSystem } = usePermissions()
if (!canManageSystem.value) navigateTo('/dashboard')

const api = useApi()
const toast = useToast()

const loading = ref(true)
const savingConfig = ref(false)
const scrapeRunning = ref(false)
const autoMatching = ref(false)

const configForm = ref({
  club_id: '',
  base_url: 'https://resultat.bueskyting.no',
  records_url: 'https://rekord.bueskyting.no',
  auto_scrape_enabled: false,
  scrape_interval_hours: 24,
})

const unmatchedArchers = ref<any[]>([])
const logs = ref<any[]>([])
const matchForms = ref<Record<string, string>>({})

onMounted(async () => {
  try {
    const [config, unmatched, logData, status]: any[] = await Promise.all([
      api.getScrapingConfig(),
      api.getUnmatchedArchers(),
      api.getScrapeLogs(),
      api.getScrapeStatus(),
    ])

    configForm.value = {
      club_id: config.club_id || '',
      base_url: config.base_url || 'https://resultat.bueskyting.no',
      records_url: config.records_url || 'https://rekord.bueskyting.no',
      auto_scrape_enabled: config.auto_scrape_enabled || false,
      scrape_interval_hours: config.scrape_interval_hours || 24,
    }

    unmatchedArchers.value = unmatched.archers || []
    logs.value = logData.logs || []
    scrapeRunning.value = status.running || false
  } catch (err) {
    console.error('Failed to load scraper settings:', err)
  } finally {
    loading.value = false
  }
})

const saveConfig = async () => {
  savingConfig.value = true
  try {
    await api.updateScrapingConfig(configForm.value)
    toast.add({ title: 'Configuration saved', color: 'green' })
  } catch (err) {
    toast.add({ title: 'Failed to save configuration', color: 'red' })
  } finally {
    savingConfig.value = false
  }
}

let pollInterval: ReturnType<typeof setInterval> | null = null

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onBeforeUnmount(() => {
  stopPolling()
})

const runScrape = async (type: string) => {
  try {
    await api.triggerScrape({ type })
    scrapeRunning.value = true
    toast.add({ title: `${type} scrape started`, color: 'blue' })

    // Poll for completion
    stopPolling()
    pollInterval = setInterval(async () => {
      try {
        const status: any = await api.getScrapeStatus()
        if (!status.running) {
          stopPolling()
          scrapeRunning.value = false
          toast.add({ title: 'Scrape completed', color: 'green' })
          // Refresh logs and unmatched
          const [logData, unmatched]: any[] = await Promise.all([
            api.getScrapeLogs(),
            api.getUnmatchedArchers(),
          ])
          logs.value = logData.logs || []
          unmatchedArchers.value = unmatched.archers || []
        }
      } catch {
        stopPolling()
        scrapeRunning.value = false
      }
    }, 5000)
  } catch (err: any) {
    toast.add({
      title: 'Failed to start scrape',
      description: err?.data?.detail || 'Unknown error',
      color: 'red',
    })
  }
}

const runAutoMatch = async () => {
  autoMatching.value = true
  try {
    const result: any = await api.runAutoMatch()
    toast.add({
      title: `Auto-match complete: ${result.matched} matched, ${result.suggested} suggested`,
      color: 'green',
    })
    const unmatched: any = await api.getUnmatchedArchers()
    unmatchedArchers.value = unmatched.archers || []
  } catch (err) {
    toast.add({ title: 'Auto-match failed', color: 'red' })
  } finally {
    autoMatching.value = false
  }
}

const matchArcherAction = async (bueskytingId: string) => {
  const spondId = matchForms.value[bueskytingId]
  if (!spondId) return
  try {
    await api.matchArcher({ bueskyting_id: bueskytingId, spond_id: spondId })
    toast.add({ title: 'Archer matched successfully', color: 'green' })
    unmatchedArchers.value = unmatchedArchers.value.filter(a => a.bueskyting_id !== bueskytingId)
    delete matchForms.value[bueskytingId]
  } catch (err: any) {
    toast.add({
      title: 'Failed to match archer',
      description: err?.data?.detail || 'Unknown error',
      color: 'red',
    })
  }
}

const dismissArcher = async (id: number) => {
  try {
    await api.dismissUnmatched(id)
    unmatchedArchers.value = unmatchedArchers.value.filter(a => a.id !== id)
    toast.add({ title: 'Archer dismissed', color: 'gray' })
  } catch (err) {
    toast.add({ title: 'Failed to dismiss', color: 'red' })
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
</script>
