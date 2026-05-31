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
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="text-left py-3 px-2 font-medium text-gray-500 cursor-pointer" @click="toggleSort('date')">
                  Date {{ sortIcon('date') }}
                </th>
                <th class="text-left py-3 px-2 font-medium text-gray-500 cursor-pointer" @click="toggleSort('archer_name')">
                  Archer {{ sortIcon('archer_name') }}
                </th>
                <th class="text-left py-3 px-2 font-medium text-gray-500">Event</th>
                <th class="text-left py-3 px-2 font-medium text-gray-500">Distance</th>
                <th class="text-left py-3 px-2 font-medium text-gray-500">Class</th>
                <th class="text-right py-3 px-2 font-medium text-gray-500 cursor-pointer" @click="toggleSort('score')">
                  Score {{ sortIcon('score') }}
                </th>
                <th class="text-right py-3 px-2 font-medium text-gray-500 cursor-pointer" @click="toggleSort('ranking')">
                  Rank {{ sortIcon('ranking') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="result in results"
                :key="result.id"
                class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ formatDate(result.date) }}</td>
                <td class="py-2 px-2 font-medium text-gray-900 dark:text-white">
                  <NuxtLink
                    v-if="result.member_id"
                    :to="`/dashboard/members/${result.member_id}`"
                    class="text-blue-600 dark:text-blue-400 hover:underline"
                    title="View member profile"
                  >{{ result.archer_name }}</NuxtLink>
                  <span v-else>{{ result.archer_name }}</span>
                </td>
                <td class="py-2 px-2 text-gray-600 dark:text-gray-400 max-w-xs truncate">{{ result.event_name }}</td>
                <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ result.distance }}</td>
                <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ result.equipment_class }}</td>
                <td class="py-2 px-2 text-right font-bold text-blue-600">{{ result.score }}</td>
                <td class="py-2 px-2 text-right">
                  <UBadge v-if="result.ranking" :color="result.ranking <= 3 ? 'amber' : 'gray'" size="sm">
                    #{{ result.ranking }}
                  </UBadge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

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
