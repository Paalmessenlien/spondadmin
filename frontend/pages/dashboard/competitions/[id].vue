<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Konkurranser', to: '/dashboard/competitions' },
      { label: event?.name || 'Laster...' }
    ]" />

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <!-- Error -->
    <UCard v-else-if="error" class="text-center py-8">
      <UIcon name="i-heroicons-exclamation-triangle" class="w-12 h-12 mx-auto mb-3 text-red-400" />
      <p class="text-red-500">{{ error }}</p>
      <UButton class="mt-4" variant="outline" @click="navigateTo('/dashboard/competitions')">
        Tilbake til konkurranser
      </UButton>
    </UCard>

    <template v-else-if="event">
      <!-- Header -->
      <UCard>
        <div class="space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ event.name }}</h1>
              <div class="flex flex-wrap gap-2 mt-2">
                <UBadge v-if="event.event_type_raw" color="neutral" variant="subtle">
                  {{ event.event_type_raw }}
                </UBadge>
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
                  v-if="isUpcoming"
                  color="success"
                  variant="subtle"
                >
                  Kommende
                </UBadge>
              </div>
            </div>
            <UButton
              variant="outline"
              color="neutral"
              icon="i-heroicons-arrow-top-right-on-square"
              :to="event.source_url"
              target="_blank"
            >
              Åpne på bueskyting.no
            </UButton>
          </div>

          <!-- Details grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div v-if="event.date_start" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-calendar" class="w-5 h-5 text-gray-400" />
              <span class="text-gray-600 dark:text-gray-400">Dato:</span>
              <span class="font-medium text-gray-900 dark:text-white">
                {{ formatDate(event.date_start) }}
                <template v-if="event.date_end && event.date_end !== event.date_start">
                  – {{ formatDate(event.date_end) }}
                </template>
              </span>
            </div>
            <div v-if="event.location" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-map-pin" class="w-5 h-5 text-gray-400" />
              <span class="text-gray-600 dark:text-gray-400">Sted:</span>
              <span class="font-medium text-gray-900 dark:text-white">{{ event.location }}</span>
            </div>
            <div v-if="event.address" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-map" class="w-5 h-5 text-gray-400" />
              <span class="text-gray-600 dark:text-gray-400">Adresse:</span>
              <span class="font-medium text-gray-900 dark:text-white">{{ event.address }}</span>
            </div>
            <div v-if="event.organizer" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-building-office" class="w-5 h-5 text-gray-400" />
              <span class="text-gray-600 dark:text-gray-400">Arrangør:</span>
              <span class="font-medium text-gray-900 dark:text-white">{{ event.organizer }}</span>
            </div>
            <div v-if="event.distance" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-arrows-right-left" class="w-5 h-5 text-gray-400" />
              <span class="text-gray-600 dark:text-gray-400">Distanse:</span>
              <span class="font-medium text-gray-900 dark:text-white">{{ event.distance }}</span>
            </div>
            <div v-if="event.format" class="flex items-center gap-2 text-sm">
              <UIcon name="i-heroicons-list-bullet" class="w-5 h-5 text-gray-400" />
              <span class="text-gray-600 dark:text-gray-400">Format:</span>
              <span class="font-medium text-gray-900 dark:text-white">{{ event.format }}</span>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Registration info -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Påmelding</h2>
        </template>

        <div class="space-y-4">
          <div v-if="event.registration_deadline" class="flex items-center gap-2 text-sm">
            <UIcon name="i-heroicons-clock" class="w-5 h-5 text-gray-400" />
            <span class="text-gray-600 dark:text-gray-400">Påmeldingsfrist:</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ event.registration_deadline }}</span>
          </div>
          <div v-if="event.registration_type_raw" class="flex items-center gap-2 text-sm">
            <UIcon name="i-heroicons-user-group" class="w-5 h-5 text-gray-400" />
            <span class="text-gray-600 dark:text-gray-400">Påmeldingstype:</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ event.registration_type_raw }}</span>
          </div>
          <div v-if="event.fees" class="flex items-center gap-2 text-sm">
            <UIcon name="i-heroicons-banknotes" class="w-5 h-5 text-gray-400" />
            <span class="text-gray-600 dark:text-gray-400">Avgifter:</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ event.fees }}</span>
          </div>
          <div v-if="event.contact_email" class="flex items-center gap-2 text-sm">
            <UIcon name="i-heroicons-envelope" class="w-5 h-5 text-gray-400" />
            <span class="text-gray-600 dark:text-gray-400">Kontakt:</span>
            <a :href="`mailto:${event.contact_email}`" class="font-medium text-blue-600 hover:underline">
              {{ event.contact_email }}
            </a>
          </div>

          <div class="flex flex-wrap gap-2 pt-2">
            <UButton
              v-if="event.registration_url"
              color="primary"
              icon="i-heroicons-pencil-square"
              :to="event.registration_url"
              target="_blank"
            >
              Åpne påmelding
            </UButton>
            <UButton
              v-if="event.info_url"
              color="neutral"
              variant="outline"
              icon="i-heroicons-information-circle"
              :to="event.info_url"
              target="_blank"
            >
              Mer informasjon
            </UButton>
            <UButton
              v-if="event.results_url"
              color="neutral"
              variant="outline"
              icon="i-heroicons-trophy"
              :to="event.results_url"
              target="_blank"
            >
              Resultater
            </UButton>
          </div>

          <div v-if="!event.registration_deadline && !event.registration_type_raw && !event.fees && !event.contact_email && !event.registration_url && !event.info_url" class="text-sm text-gray-500">
            Ingen påmeldingsinformasjon tilgjengelig.
          </div>
        </div>
      </UCard>

      <!-- AI Analysis -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">AI-analyse</h2>
            <UButton
              v-if="isAdmin"
              size="sm"
              color="neutral"
              variant="outline"
              icon="i-heroicons-sparkles"
              :loading="analyzingOne"
              @click="handleAnalyze"
            >
              Analyser på nytt
            </UButton>
          </div>
        </template>

        <div v-if="event.ai_summary" class="space-y-4">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Oppsummering</p>
            <p class="text-gray-900 dark:text-white">{{ event.ai_summary }}</p>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Klassifisering</p>
            <div class="flex items-center gap-2">
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
                v-else
                color="neutral"
                variant="subtle"
              >
                Ukjent
              </UBadge>
              <span class="text-xs text-gray-400">
                {{ event.ai_event_category === 'personlig' ? 'Skytteren kan melde seg på selv' : event.ai_event_category === 'klubb' ? 'Klubben sender påmelding' : 'Ikke nok informasjon til å klassifisere' }}
              </span>
            </div>
          </div>
          <p v-if="event.ai_analyzed_at" class="text-xs text-gray-400">
            Sist analysert: {{ formatDateTime(event.ai_analyzed_at) }}
          </p>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <UIcon name="i-heroicons-sparkles" class="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p>Ingen AI-analyse tilgjengelig.</p>
          <p v-if="isAdmin" class="text-sm mt-1">Klikk "Analyser på nytt" for å kjøre analyse.</p>
        </div>
      </UCard>

      <!-- Cross-links: Spond event / results -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Koblinger</h2>
            <UButton
              v-if="isAdmin"
              size="sm"
              color="neutral"
              variant="outline"
              icon="i-heroicons-magnifying-glass"
              :loading="loadingSuggestions"
              @click="loadSuggestions"
            >
              Foreslå treff
            </UButton>
          </div>
        </template>

        <div class="space-y-4">
          <!-- Current links -->
          <div class="space-y-2">
            <div v-if="event.linked_event_id" class="flex items-center justify-between gap-2 text-sm">
              <span class="flex items-center gap-2">
                <UIcon name="i-heroicons-calendar-days" class="w-5 h-5 text-green-600" />
                Spond-arrangement:
                <NuxtLink
                  :to="`/dashboard/events/${event.linked_event_id}`"
                  class="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {{ event.linked_event_heading || `#${event.linked_event_id}` }}
                </NuxtLink>
              </span>
              <UButton
                v-if="isAdmin"
                size="xs"
                color="error"
                variant="ghost"
                icon="i-heroicons-x-mark"
                :loading="savingLink"
                aria-label="Fjern kobling"
                @click="unlink('event')"
              />
            </div>
            <div v-if="event.linked_competition_id" class="flex items-center justify-between gap-2 text-sm">
              <span class="flex items-center gap-2">
                <UIcon name="i-heroicons-trophy" class="w-5 h-5 text-amber-600" />
                Resultater:
                <NuxtLink
                  :to="`/dashboard/scores/competitions/${event.linked_competition_id}`"
                  class="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {{ event.linked_competition_name || `#${event.linked_competition_id}` }}
                </NuxtLink>
              </span>
              <UButton
                v-if="isAdmin"
                size="xs"
                color="error"
                variant="ghost"
                icon="i-heroicons-x-mark"
                :loading="savingLink"
                aria-label="Fjern kobling"
                @click="unlink('competition')"
              />
            </div>
            <p v-if="!event.linked_event_id && !event.linked_competition_id" class="text-sm text-gray-500">
              Ingen koblinger ennå.<span v-if="isAdmin"> Klikk «Foreslå treff» for å finne et matchende Spond-arrangement.</span>
            </p>
          </div>

          <!-- Suggestions (admin) -->
          <div v-if="isAdmin && suggestions" class="space-y-3 pt-2 border-t border-gray-200 dark:border-gray-700">
            <div v-if="suggestions.events.length">
              <p class="text-xs font-medium text-gray-500 mb-1">Foreslåtte Spond-arrangementer</p>
              <div
                v-for="s in suggestions.events"
                :key="s.event_id"
                class="flex items-center justify-between gap-2 text-sm py-1"
              >
                <span class="truncate">
                  {{ s.heading }}
                  <span class="text-gray-400">· {{ Math.round(s.score) }}%</span>
                </span>
                <UButton size="xs" color="primary" variant="soft" :loading="savingLink" @click="linkTo('event', s.event_id)">
                  Lenk
                </UButton>
              </div>
            </div>
            <div v-if="suggestions.competitions.length">
              <p class="text-xs font-medium text-gray-500 mb-1">Foreslåtte resultater</p>
              <div
                v-for="s in suggestions.competitions"
                :key="s.competition_id"
                class="flex items-center justify-between gap-2 text-sm py-1"
              >
                <span class="truncate">
                  {{ s.name }}
                  <span class="text-gray-400">· {{ Math.round(s.score) }}%</span>
                </span>
                <UButton size="xs" color="primary" variant="soft" :loading="savingLink" @click="linkTo('competition', s.competition_id)">
                  Lenk
                </UButton>
              </div>
            </div>
            <p v-if="!suggestions.events.length && !suggestions.competitions.length" class="text-sm text-gray-500">
              Fant ingen sannsynlige treff (samme dato ± noen dager og lignende navn).
            </p>
          </div>
        </div>
      </UCard>

      <!-- Description -->
      <UCard v-if="event.description">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Beskrivelse</h2>
        </template>
        <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ event.description }}</p>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const toast = useToast()
const { isAdmin } = usePermissions()

const eventId = computed(() => parseInt(route.params.id as string))
const event = ref<any>(null)
const loading = ref(true)
const error = ref('')
const analyzingOne = ref(false)

const isUpcoming = computed(() => {
  if (!event.value?.date_start) return false
  return new Date(event.value.date_start) >= new Date(new Date().toDateString())
})

// Cross-link suggestions / confirmation (admin).
const loadingSuggestions = ref(false)
const savingLink = ref(false)
const suggestions = ref<{ events: any[]; competitions: any[] } | null>(null)

const loadSuggestions = async () => {
  loadingSuggestions.value = true
  try {
    suggestions.value = await api.getExternalEventLinkSuggestions(eventId.value)
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke hente forslag', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    loadingSuggestions.value = false
  }
}

const linkTo = async (kind: 'event' | 'competition', id: number) => {
  savingLink.value = true
  try {
    const body = kind === 'event' ? { event_id: id } : { competition_id: id }
    event.value = await api.setExternalEventLink(eventId.value, body)
    suggestions.value = null
    toast.add({ title: 'Koblet', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kobling feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    savingLink.value = false
  }
}

const unlink = async (kind: 'event' | 'competition') => {
  savingLink.value = true
  try {
    const body = kind === 'event' ? { event_id: null } : { competition_id: null }
    event.value = await api.setExternalEventLink(eventId.value, body)
    toast.add({ title: 'Kobling fjernet', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke fjerne', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    savingLink.value = false
  }
}

const loadEvent = async () => {
  loading.value = true
  error.value = ''
  try {
    event.value = await api.getExternalEvent(eventId.value)
  } catch (err: any) {
    error.value = err?.data?.detail || 'Kunne ikke laste konkurranse'
  } finally {
    loading.value = false
  }
}

const handleAnalyze = async () => {
  analyzingOne.value = true
  try {
    await api.analyzeExternalEvent(eventId.value)
    toast.add({ title: 'Analyse fullført', color: 'success' })
    await loadEvent()
  } catch (err: any) {
    toast.add({ title: 'Analyse feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    analyzingOne.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('nb-NO', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('nb-NO', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  loadEvent()
})
</script>
