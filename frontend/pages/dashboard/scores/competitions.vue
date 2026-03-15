<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Scores & Records', to: '/dashboard/scores' },
      { label: 'Competitions' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Competitions</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Browse competitions and their results
      </p>
    </div>

    <!-- Search -->
    <UCard>
      <div class="flex flex-wrap gap-4">
        <UInput
          v-model="search"
          placeholder="Search competitions..."
          icon="i-heroicons-magnifying-glass"
          class="w-full md:w-64"
          @input="debouncedLoad"
        />
      </div>
    </UCard>

    <!-- Competitions List -->
    <UCard>
      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>

      <div v-else-if="competitions.length === 0" class="text-center py-8 text-gray-500">
        <p>No competitions found</p>
      </div>

      <div v-else>
        <div class="space-y-3">
          <div
            v-for="comp in competitions"
            :key="comp.id"
            class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            @click="navigateTo(`/dashboard/scores/competitions/${comp.id}`)"
          >
            <div class="flex-1">
              <div class="font-medium text-gray-900 dark:text-white">{{ comp.name }}</div>
              <div class="text-sm text-gray-500 mt-1">
                <span v-if="comp.date">{{ formatDate(comp.date) }}</span>
                <span v-else class="italic">Date unknown</span>
                <span v-if="comp.location" class="ml-3">{{ comp.location }}</span>
              </div>
            </div>
            <UIcon name="i-heroicons-chevron-right" class="w-5 h-5 text-gray-400" />
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="total > pageSize" class="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Showing {{ skip + 1 }}-{{ Math.min(skip + pageSize, total) }} of {{ total }}
          </div>
          <div class="flex items-center space-x-2">
            <UButton size="sm" color="neutral" variant="outline" :disabled="skip === 0" @click="skip -= pageSize; loadCompetitions()">
              Previous
            </UButton>
            <UButton size="sm" color="neutral" variant="outline" :disabled="skip + pageSize >= total" @click="skip += pageSize; loadCompetitions()">
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

const competitions = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const search = ref('')
const skip = ref(0)
const pageSize = ref(50)

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedLoad = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    skip.value = 0
    loadCompetitions()
  }, 300)
}

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
})

const loadCompetitions = async () => {
  loading.value = true
  try {
    const params: Record<string, string> = {
      skip: skip.value.toString(),
      limit: pageSize.value.toString(),
    }
    if (search.value) params.search = search.value
    const data: any = await api.getCompetitions(params)
    competitions.value = data.competitions || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Failed to load competitions:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

onMounted(() => loadCompetitions())
</script>
