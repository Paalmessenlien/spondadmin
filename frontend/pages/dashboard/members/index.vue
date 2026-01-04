<template>
  <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 class="text-2xl font-bold">Members</h1>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Manage and view all club members
            </p>
          </div>
          <UButton icon="i-heroicons-arrow-path" :loading="syncing" @click="handleSync" aria-label="Sync members from Spond">
            Sync Members
          </UButton>
        </div>

        <!-- Search and Filters -->
        <UCard>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UInput
              v-model="searchQuery"
              placeholder="Search members..."
              icon="i-heroicons-magnifying-glass"
              aria-label="Search members"
              @input="debouncedSearch"
            />
            <UInput
              v-model="emailFilter"
              placeholder="Filter by email..."
              icon="i-heroicons-envelope"
              aria-label="Filter by email"
              @input="debouncedSearch"
            />
            <UButton
              v-if="searchQuery || emailFilter"
              color="gray"
              variant="soft"
              icon="i-heroicons-x-mark"
              @click="clearFilters"
            >
              Clear Filters
            </UButton>
          </div>
        </UCard>

        <UCard>
          <template v-if="loading">
            <div class="flex justify-center py-12">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
            </div>
          </template>

          <div v-else-if="members.length === 0">
            <EmptyState
              icon="i-heroicons-users"
              title="No members found"
              :description="searchQuery || emailFilter ? 'No members match your search criteria. Try adjusting your filters.' : 'No members have been synced yet. Sync members from Spond to get started.'"
              :action-label="searchQuery || emailFilter ? undefined : 'Sync Members'"
              action-icon="i-heroicons-arrow-path"
              :action-loading="syncing"
              @action="handleSync"
            />
          </div>

          <div v-else>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-700 dark:text-gray-300">Name</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-700 dark:text-gray-300">Email</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-700 dark:text-gray-300">Phone</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-700 dark:text-gray-300">Subgroups</th>
                  </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  <tr
                    v-for="member in members"
                    :key="member.id"
                    class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                    @click="navigateTo(`/dashboard/members/${member.id}`)"
                  >
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="font-medium hover:text-blue-600 dark:hover:text-blue-400">
                        {{ member.first_name }} {{ member.last_name }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      {{ member.email || '-' }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      {{ member.phone_number || '-' }}
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                      {{ member.subgroup_uids?.length || 0 }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Enhanced Pagination -->
            <div class="flex flex-col sm:flex-row justify-between items-center gap-4 mt-4 px-4 py-3 border-t border-gray-200 dark:border-gray-700">
              <div class="text-sm text-gray-700 dark:text-gray-300">
                Showing {{ skip + 1 }}-{{ Math.min(skip + members.length, total) }} of {{ total }} members
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
                <UButton size="sm" variant="soft" :disabled="skip === 0" aria-label="First page" @click="firstPage">
                  First
                </UButton>
                <UButton size="sm" variant="soft" :disabled="skip === 0" aria-label="Previous page" @click="previousPage">
                  Previous
                </UButton>
                <span class="text-sm text-gray-700 dark:text-gray-300">
                  Page {{ currentPage }} of {{ totalPages }}
                </span>
                <UButton size="sm" variant="soft" :disabled="skip + limit >= total" aria-label="Next page" @click="nextPage">
                  Next
                </UButton>
                <UButton size="sm" variant="soft" :disabled="skip + limit >= total" aria-label="Last page" @click="lastPage">
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
const authStore = useAuthStore()

const members = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const syncing = ref(false)
const skip = ref(0)
const limit = ref(20)
const searchQuery = ref('')
const emailFilter = ref('')

onMounted(() => loadMembers())

// Watch for group changes and reload members
watch(() => authStore.selectedGroupId, () => {
  skip.value = 0 // Reset to first page on group change
  loadMembers()
})

const loadMembers = async () => {
  loading.value = true
  try {
    const params: any = { skip: skip.value, limit: limit.value }
    if (searchQuery.value) params.search = searchQuery.value
    if (emailFilter.value) params.email = emailFilter.value

    const response = await api.getMembers(params)
    members.value = response.members || []
    total.value = response.total || 0
  } catch (error) {
    toast.add({ title: 'Error', description: 'Failed to load members', color: 'red' })
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
    loadMembers()
  }, 300)
}

// Clear filters function
const clearFilters = () => {
  searchQuery.value = ''
  emailFilter.value = ''
  skip.value = 0
  loadMembers()
}

const handleSync = async () => {
  syncing.value = true
  try {
    await api.syncMembers()
    toast.add({ title: 'Success', description: 'Members synced', color: 'green' })
    await loadMembers()
  } catch (error) {
    toast.add({ title: 'Error', description: 'Failed to sync members', color: 'red' })
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
  loadMembers()
}

const previousPage = () => {
  skip.value = Math.max(0, skip.value - limit.value)
  loadMembers()
}

const firstPage = () => {
  skip.value = 0
  loadMembers()
}

const lastPage = () => {
  skip.value = Math.floor(total.value / limit.value) * limit.value
  loadMembers()
}

const handleLimitChange = () => {
  skip.value = 0 // Reset to first page when changing page size
  loadMembers()
}
</script>
