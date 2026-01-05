<template>
  <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 class="text-2xl font-bold">Groups</h1>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Manage and view all club groups and subgroups
            </p>
          </div>
          <UButton icon="i-heroicons-arrow-path" :loading="syncing" @click="handleSync" aria-label="Sync groups from Spond">
            Sync Groups
          </UButton>
        </div>

        <!-- Search and Filters -->
        <UCard>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UInput
              v-model="searchQuery"
              placeholder="Search groups..."
              icon="i-heroicons-magnifying-glass"
              aria-label="Search groups"
              @input="debouncedSearch"
            />
            <div class="md:col-span-2 flex justify-end">
              <UButton
                v-if="searchQuery"
                color="neutral"
                variant="outline"
                icon="i-heroicons-x-mark"
                @click="clearFilters"
              >
                Clear Filters
              </UButton>
            </div>
          </div>
        </UCard>

        <UCard>
          <template v-if="loading">
            <div class="flex justify-center py-12">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
            </div>
          </template>

          <div v-else-if="groups.length === 0">
            <EmptyState
              icon="i-heroicons-user-group"
              title="No groups found"
              :description="searchQuery ? 'No groups match your search criteria. Try adjusting your filters.' : 'No groups have been synced yet. Sync groups from Spond to get started.'"
              :action-label="searchQuery ? undefined : 'Sync Groups'"
              action-icon="i-heroicons-arrow-path"
              :action-loading="syncing"
              @action="handleSync"
            />
          </div>

          <div v-else>
            <div class="space-y-4">
              <div
                v-for="group in groups"
                :key="group.id"
                class="p-4 border rounded-lg dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                @click="navigateTo(`/dashboard/groups/${group.id}`)"
              >
                <h3 class="font-semibold text-lg hover:text-blue-600 dark:hover:text-blue-400">{{ group.name }}</h3>
                <p v-if="group.description" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {{ group.description }}
                </p>
                <div class="mt-2 flex gap-4 text-sm text-gray-700 dark:text-gray-300">
                  <span>Subgroups: {{ group.subgroups?.length || 0 }}</span>
                  <span>Roles: {{ group.roles?.length || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- Enhanced Pagination -->
            <div class="flex flex-col sm:flex-row justify-between items-center gap-4 mt-4 px-4 py-3 border-t border-gray-200 dark:border-gray-700">
              <div class="text-sm text-gray-700 dark:text-gray-300">
                Showing {{ skip + 1 }}-{{ Math.min(skip + groups.length, total) }} of {{ total }} groups
                <select
                  v-model="limit"
                  class="ml-2 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-gray-800"
                  aria-label="Items per page"
                  @change="handleLimitChange"
                >
                  <option :value="10">10 per page</option>
                  <option :value="20">20 per page</option>
                  <option :value="50">50 per page</option>
                  <option :value="100">100 per page</option>
                </select>
              </div>
              <div class="flex items-center space-x-2">
                <UButton size="sm" color="neutral" variant="outline" :disabled="skip === 0" aria-label="First page" @click="firstPage">
                  First
                </UButton>
                <UButton size="sm" color="neutral" variant="outline" :disabled="skip === 0" aria-label="Previous page" @click="previousPage">
                  Previous
                </UButton>
                <span class="text-sm text-gray-700 dark:text-gray-300">
                  Page {{ currentPage }} of {{ totalPages }}
                </span>
                <UButton size="sm" color="neutral" variant="outline" :disabled="skip + limit >= total" aria-label="Next page" @click="nextPage">
                  Next
                </UButton>
                <UButton size="sm" color="neutral" variant="outline" :disabled="skip + limit >= total" aria-label="Last page" @click="lastPage">
                  Last
                </UButton>
              </div>
            </div>
          </div>
        </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const api = useApi()
const toast = useToast()

const groups = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const syncing = ref(false)
const skip = ref(0)
const limit = ref(20)
const searchQuery = ref('')

onMounted(() => loadGroups())

const loadGroups = async () => {
  loading.value = true
  try {
    const params: any = { skip: skip.value, limit: limit.value }
    if (searchQuery.value) params.search = searchQuery.value

    const response = await api.getGroups(params)
    groups.value = response.groups || []
    total.value = response.total || 0
  } catch (error) {
    toast.add({ title: 'Error', description: 'Failed to load groups', color: 'red' })
  } finally {
    loading.value = false
  }
}

// Debounced search function
let searchTimeout: NodeJS.Timeout
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    skip.value = 0 // Reset to first page on search
    loadGroups()
  }, 300)
}

// Clear filters function
const clearFilters = () => {
  searchQuery.value = ''
  skip.value = 0
  loadGroups()
}

const handleSync = async () => {
  syncing.value = true
  try {
    await api.syncGroups()
    toast.add({ title: 'Success', description: 'Groups synced', color: 'green' })
    await loadGroups()
  } catch (error) {
    toast.add({ title: 'Error', description: 'Failed to sync groups', color: 'red' })
  } finally {
    syncing.value = false
  }
}

// Computed properties for pagination
const currentPage = computed(() => Math.floor(skip.value / limit.value) + 1)
const totalPages = computed(() => Math.ceil(total.value / limit.value))

// Pagination methods
const nextPage = () => {
  skip.value += limit.value
  loadGroups()
}

const previousPage = () => {
  skip.value = Math.max(0, skip.value - limit.value)
  loadGroups()
}

const firstPage = () => {
  skip.value = 0
  loadGroups()
}

const lastPage = () => {
  skip.value = Math.floor(total.value / limit.value) * limit.value
  loadGroups()
}

const handleLimitChange = () => {
  skip.value = 0 // Reset to first page when changing page size
  loadGroups()
}
</script>
