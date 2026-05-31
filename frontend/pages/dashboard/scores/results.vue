<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Scores & Records', to: '/dashboard/scores' },
      { label: 'Results' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Competition Results</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Browse and filter all competition results
      </p>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="flex flex-wrap gap-4">
        <UInput
          v-model="search"
          placeholder="Search archer or event..."
          icon="i-heroicons-magnifying-glass"
          class="w-full md:w-64"
          @input="debouncedLoad"
        />
        <UInput
          v-model="filters.equipment_class"
          placeholder="Equipment class"
          class="w-40"
          @input="debouncedLoad"
        />
        <UInput
          v-model="filters.distance"
          placeholder="Distance"
          class="w-32"
          @input="debouncedLoad"
        />
        <DateInputISO v-model="filters.date_from" @change="loadResults" />
        <DateInputISO v-model="filters.date_to" @change="loadResults" />
      </div>
    </UCard>

    <!-- Results Table -->
    <UCard>
      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>

      <div v-else-if="results.length === 0" class="text-center py-8 text-gray-500">
        <p>No results found</p>
      </div>

      <div v-else>
        <ResponsiveTable
          :columns="resultCols"
          :rows="results"
          :sort-field="sortBy"
          :sort-desc="sortDir === 'desc'"
          @sort="toggleSort"
        >
          <template #cell-date="{ row }">
            <span class="text-gray-600 dark:text-gray-400">{{ formatDate(row.date) }}</span>
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
          <template #cell-ranking="{ row }">
            <UBadge v-if="row.ranking" :color="row.ranking <= 3 ? 'amber' : 'gray'" size="sm">#{{ row.ranking }}</UBadge>
          </template>
        </ResponsiveTable>

        <!-- Pagination -->
        <div class="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Showing {{ skip + 1 }}-{{ Math.min(skip + pageSize, total) }} of {{ total }}
          </div>
          <div class="flex items-center space-x-2">
            <UButton size="sm" color="neutral" variant="outline" :disabled="skip === 0" @click="previousPage">
              Previous
            </UButton>
            <span class="text-sm text-gray-600 dark:text-gray-400">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <UButton size="sm" color="neutral" variant="outline" :disabled="skip + pageSize >= total" @click="nextPage">
              Next
            </UButton>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()

const results = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const search = ref('')
const skip = ref(0)
const pageSize = ref(50)
const sortBy = ref('date')
const sortDir = ref<'asc' | 'desc'>('desc')

const filters = ref({
  equipment_class: '',
  distance: '',
  date_from: '',
  date_to: '',
})

const currentPage = computed(() => Math.floor(skip.value / pageSize.value) + 1)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const resultCols = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'archer_name', label: 'Archer', primary: true, sortable: true },
  { key: 'event_name', label: 'Event' },
  { key: 'distance', label: 'Distance' },
  { key: 'equipment_class', label: 'Class' },
  { key: 'score', label: 'Score', align: 'right', sortable: true },
  { key: 'ranking', label: 'Rank', align: 'right', sortable: true },
] as const

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedLoad = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    skip.value = 0
    loadResults()
  }, 300)
}

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
})

const loadResults = async () => {
  loading.value = true
  try {
    const params: Record<string, string> = {
      skip: skip.value.toString(),
      limit: pageSize.value.toString(),
      sort_by: sortBy.value,
      sort_dir: sortDir.value,
    }
    if (search.value) params.search = search.value
    if (filters.value.equipment_class) params.equipment_class = filters.value.equipment_class
    if (filters.value.distance) params.distance = filters.value.distance
    if (filters.value.date_from) params.date_from = filters.value.date_from
    if (filters.value.date_to) params.date_to = filters.value.date_to

    const data: any = await api.getResults(params)
    results.value = data.results || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Failed to load results:', err)
  } finally {
    loading.value = false
  }
}

const toggleSort = (field: string) => {
  if (sortBy.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortDir.value = 'desc'
  }
  skip.value = 0
  loadResults()
}

const sortIcon = (field: string) => {
  if (sortBy.value !== field) return ''
  return sortDir.value === 'asc' ? '\u25B2' : '\u25BC'
}

const nextPage = () => { skip.value += pageSize.value; loadResults() }
const previousPage = () => { skip.value = Math.max(0, skip.value - pageSize.value); loadResults() }

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(() => loadResults())
</script>
