<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Konkurranser' }
    ]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Konkurranser</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Eksterne konkurranser fra bueskyting.no
        </p>
      </div>
      <div v-if="isAdmin" class="flex gap-2">
        <UButton
          color="primary"
          icon="i-heroicons-arrow-path"
          :loading="scraping"
          :disabled="analyzing"
          @click="handleScrape"
        >
          Hent konkurranser
        </UButton>
        <UButton
          v-if="!analyzing"
          color="neutral"
          variant="outline"
          icon="i-heroicons-sparkles"
          :disabled="scraping"
          @click="handleAnalyzeAll"
        >
          Analyser alle
        </UButton>
        <UButton
          v-else
          color="error"
          variant="soft"
          icon="i-heroicons-stop"
          @click="handleStopAnalysis"
        >
          Stopp analyse
        </UButton>
      </div>
    </div>

    <!-- Analysis progress -->
    <UCard v-if="analyzing || analysisDone" class="border-blue-200 dark:border-blue-800">
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <UIcon
              v-if="analyzing"
              name="i-heroicons-sparkles"
              class="w-5 h-5 text-blue-500 animate-pulse"
            />
            <UIcon
              v-else-if="analysisCancelled"
              name="i-heroicons-stop"
              class="w-5 h-5 text-amber-500"
            />
            <UIcon
              v-else
              name="i-heroicons-check-circle"
              class="w-5 h-5 text-green-500"
            />
            <span class="font-medium text-gray-900 dark:text-white">
              {{ analyzing ? 'Analyserer konkurranser...' : analysisCancelled ? 'Analyse stoppet' : 'Analyse fullført' }}
            </span>
          </div>
          <span class="text-sm text-gray-500">
            {{ analysisProgress.current }} / {{ analysisProgress.total }}
          </span>
        </div>

        <!-- Progress bar -->
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            class="h-2.5 rounded-full transition-all duration-300"
            :class="analysisCancelled ? 'bg-amber-500' : 'bg-blue-600'"
            :style="{ width: `${analysisPercent}%` }"
          />
        </div>

        <div class="flex items-center justify-between text-sm text-gray-500">
          <span v-if="analysisProgress.eventName">
            {{ analyzing ? 'Analyserer:' : 'Sist:' }} {{ analysisProgress.eventName }}
          </span>
          <span v-else>&nbsp;</span>
          <div class="flex gap-3">
            <span class="text-green-600">{{ analysisProgress.analyzed }} analysert</span>
            <span v-if="analysisProgress.errors > 0" class="text-red-500">{{ analysisProgress.errors }} feil</span>
          </div>
        </div>

        <UButton
          v-if="!analyzing"
          size="xs"
          variant="ghost"
          color="neutral"
          @click="analysisDone = false"
        >
          Skjul
        </UButton>
      </div>
    </UCard>

    <!-- Filters -->
    <UCard>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <UInput
          v-model="search"
          placeholder="Søk etter konkurranser..."
          icon="i-heroicons-magnifying-glass"
          @input="debouncedLoad"
        />
        <UInput type="date" class="w-full" v-model="dateFrom" @change="loadEvents" />
        <UInput type="date" class="w-full" v-model="dateTo" @change="loadEvents" />
        <USelectMenu
          v-model="selectedCategory"
          :items="categoryOptions"
          placeholder="Alle kategorier"
          @change="loadEvents"
        />
      </div>
    </UCard>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <!-- Empty state -->
    <UCard v-else-if="events.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-trophy" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-500">Ingen konkurranser funnet.</p>
      <p v-if="isAdmin" class="text-sm text-gray-400 mt-1">
        Klikk "Hent konkurranser" for å hente data fra bueskyting.no
      </p>
    </UCard>

    <!-- Event list -->
    <template v-else>
      <div class="space-y-3">
        <UCard
          v-for="event in events"
          :key="event.id"
          class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
        >
          <div class="flex flex-col sm:flex-row sm:items-center gap-4">
            <!-- Main info -->
            <div class="flex-1 min-w-0">
              <NuxtLink
                :to="`/dashboard/competitions/${event.id}`"
                class="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
              >
                {{ event.name }}
              </NuxtLink>
              <div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span v-if="event.date_start" class="flex items-center gap-1">
                  <UIcon name="i-heroicons-calendar" class="w-4 h-4" />
                  {{ formatDate(event.date_start) }}
                  <template v-if="event.date_end && event.date_end !== event.date_start">
                    – {{ formatDate(event.date_end) }}
                  </template>
                </span>
                <span v-if="event.location || event.address" class="flex items-center gap-1">
                  <UIcon name="i-heroicons-map-pin" class="w-4 h-4" />
                  {{ event.location || event.address }}
                </span>
                <span v-if="event.organizer" class="flex items-center gap-1">
                  <UIcon name="i-heroicons-building-office" class="w-4 h-4" />
                  {{ event.organizer }}
                </span>
              </div>
            </div>

            <!-- Badges and actions -->
            <div class="flex flex-wrap items-center gap-2 sm:flex-shrink-0">
              <UBadge
                v-if="event.ai_event_category === 'personlig'"
                color="info"
                variant="subtle"
              >
                Personlig påmelding
              </UBadge>
              <UBadge
                v-else-if="event.ai_event_category === 'klubb'"
                color="warning"
                variant="subtle"
              >
                Klubbpåmelding
              </UBadge>
              <UBadge
                v-else-if="event.ai_event_category"
                color="neutral"
                variant="subtle"
              >
                Ukjent type
              </UBadge>

              <UBadge
                v-if="isUpcoming(event)"
                color="success"
                variant="subtle"
              >
                Kommende
              </UBadge>

              <UButton
                v-if="event.registration_url"
                size="xs"
                color="primary"
                variant="soft"
                icon="i-heroicons-pencil-square"
                :to="event.registration_url"
                target="_blank"
              >
                Påmelding
              </UButton>
              <UButton
                v-if="event.info_url"
                size="xs"
                color="neutral"
                variant="soft"
                icon="i-heroicons-information-circle"
                :to="event.info_url"
                target="_blank"
              >
                Info
              </UButton>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Pagination -->
      <div v-if="total > limit" class="flex justify-center">
        <UPagination
          v-model="page"
          :total="total"
          :items-per-page="limit"
          @update:model-value="loadEvents"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const { isAdmin } = usePermissions()

const events = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const scraping = ref(false)
const analyzing = ref(false)
const analysisDone = ref(false)
const analysisCancelled = ref(false)
const analysisTaskId = ref('')

const analysisProgress = ref({
  current: 0,
  total: 0,
  analyzed: 0,
  errors: 0,
  eventName: '',
})

const analysisPercent = computed(() => {
  if (analysisProgress.value.total === 0) return 0
  return Math.round((analysisProgress.value.current / analysisProgress.value.total) * 100)
})

const search = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const selectedCategory = ref<any>(null)
const page = ref(1)
const limit = 20

const categoryOptions = [
  { label: 'Alle kategorier', value: '' },
  { label: 'Personlig påmelding', value: 'personlig' },
  { label: 'Klubbpåmelding', value: 'klubb' },
  { label: 'Ukjent', value: 'ukjent' },
]

let debounceTimer: ReturnType<typeof setTimeout> | null = null
const debouncedLoad = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => loadEvents(), 300)
}

const loadEvents = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: String((page.value - 1) * limit),
      limit: String(limit),
    }
    if (search.value) params.search = search.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    const catValue = selectedCategory.value?.value || ''
    if (catValue) params.ai_event_category = catValue

    const data: any = await api.getExternalEvents(params)
    events.value = data.events || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Failed to load events:', err)
  } finally {
    loading.value = false
  }
}

const handleScrape = async () => {
  scraping.value = true
  try {
    const result: any = await api.scrapeExternalEvents()
    toast.add({ title: 'Henting fullført', description: `Nye: ${result.stats?.new || 0}, Oppdatert: ${result.stats?.updated || 0}`, color: 'success' })
    await loadEvents()
  } catch (err: any) {
    toast.add({ title: 'Henting feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    scraping.value = false
  }
}

let abortController: AbortController | null = null

const handleAnalyzeAll = async () => {
  const { url, token } = api.analyzeAllExternalEvents()

  analyzing.value = true
  analysisDone.value = false
  analysisCancelled.value = false
  analysisTaskId.value = ''
  analysisProgress.value = { current: 0, total: 0, analyzed: 0, errors: 0, eventName: '' }

  abortController = new AbortController()

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream',
      },
      signal: abortController.signal,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw { data: errorData || { detail: `HTTP ${response.status}` } }
    }

    const contentType = response.headers.get('content-type') || ''

    // If backend returned JSON (0 events or error), handle directly
    if (contentType.includes('application/json')) {
      const data = await response.json()
      analyzing.value = false
      if (data.analyzed === 0) {
        toast.add({ title: 'Ingenting å analysere', description: data.message || 'Alle konkurranser er allerede analysert', color: 'info' })
      }
      return
    }

    // Read SSE stream
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          handleSSEEvent(event)
        } catch {
          // Ignore parse errors
        }
      }
    }
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      // User cancelled via abort
      return
    }
    const detail = err?.data?.detail || err?.message || 'Ukjent feil'
    toast.add({ title: 'Analyse feilet', description: detail, color: 'error' })
  } finally {
    analyzing.value = false
    abortController = null
    await loadEvents()
  }
}

const handleSSEEvent = (event: any) => {
  switch (event.type) {
    case 'start':
      analysisTaskId.value = event.task_id
      analysisProgress.value.total = event.total
      break
    case 'progress':
      analysisProgress.value.current = event.current
      analysisProgress.value.analyzed = event.analyzed
      analysisProgress.value.errors = event.errors
      analysisProgress.value.eventName = event.event_name || ''
      break
    case 'done':
      analysisProgress.value.current = event.total
      analysisProgress.value.analyzed = event.analyzed
      analysisProgress.value.errors = event.errors
      analysisDone.value = true
      toast.add({
        title: 'Analyse fullført',
        description: `${event.analyzed} analysert${event.errors > 0 ? `, ${event.errors} feil` : ''}`,
        color: 'success',
      })
      break
    case 'cancelled':
      analysisProgress.value.analyzed = event.analyzed
      analysisProgress.value.errors = event.errors
      analysisCancelled.value = true
      analysisDone.value = true
      toast.add({
        title: 'Analyse stoppet',
        description: `${event.analyzed} analysert før stopp`,
        color: 'warning',
      })
      break
  }
}

const handleStopAnalysis = async () => {
  // Signal stop via backend
  if (analysisTaskId.value) {
    try {
      await api.stopExternalEventAnalysis(analysisTaskId.value)
    } catch {
      // If stop endpoint fails, abort the fetch
      abortController?.abort()
      analyzing.value = false
      analysisCancelled.value = true
      analysisDone.value = true
    }
  } else {
    // No task ID yet, abort the fetch
    abortController?.abort()
    analyzing.value = false
    analysisCancelled.value = true
    analysisDone.value = true
  }
}

const isUpcoming = (event: any) => {
  if (!event.date_start) return false
  return new Date(event.date_start) >= new Date(new Date().toDateString())
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('nb-NO', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

onMounted(() => {
  loadEvents()
})
</script>
