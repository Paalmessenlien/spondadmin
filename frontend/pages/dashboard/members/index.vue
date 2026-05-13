<template>
  <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 class="text-2xl font-bold">Members</h1>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Manage and view all club members
            </p>
          </div>
          <UButton icon="i-heroicons-arrow-path" :loading="syncing" @click="handleSync" aria-label="Sync members from Spond">
            Sync Members
          </UButton>
        </div>

        <!-- Search and Filters -->
        <UCard>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
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
            <select
              v-model="groupFilter"
              class="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-sm bg-white dark:bg-gray-800"
              aria-label="Filter by group"
              @change="onFilterChange"
            >
              <option value="">All groups</option>
              <option v-for="g in availableGroups" :key="g.spond_id" :value="g.spond_id">
                {{ g.name }}
              </option>
            </select>
            <select
              v-model="subgroupFilter"
              class="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-sm bg-white dark:bg-gray-800"
              aria-label="Filter by subgroup"
              @change="onFilterChange"
            >
              <option value="">All subgroups</option>
              <optgroup v-for="g in groupsWithSubgroups" :key="g.spond_id" :label="g.name">
                <option v-for="s in g.subgroups" :key="s.id" :value="s.id">
                  {{ s.name }}
                </option>
              </optgroup>
            </select>
            <select
              v-model="sortValue"
              class="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-sm bg-white dark:bg-gray-800"
              aria-label="Sort members"
              @change="onFilterChange"
            >
              <option value="name:asc">Name (A→Z)</option>
              <option value="name:desc">Name (Z→A)</option>
              <option value="email:asc">Email (A→Z)</option>
              <option value="email:desc">Email (Z→A)</option>
              <option value="group_count:desc">Most groups first</option>
              <option value="group_count:asc">Fewest groups first</option>
              <option value="subgroup_count:desc">Most subgroups first</option>
              <option value="subgroup_count:asc">Fewest subgroups first</option>
              <option value="last_synced_at:desc">Recently synced first</option>
              <optgroup label="Group: members in this group first">
                <option v-for="g in availableGroups" :key="`g-${g.spond_id}`" :value="`group:${g.spond_id}`">
                  {{ g.name }}
                </option>
              </optgroup>
              <optgroup label="Subgroup: members in this subgroup first">
                <option v-for="s in flatSubgroups" :key="`s-${s.id}`" :value="`subgroup:${s.id}`">
                  {{ s.groupName }} › {{ s.name }}
                </option>
              </optgroup>
            </select>
            <UButton
              v-if="hasActiveFilters"
              color="neutral"
              variant="outline"
              icon="i-heroicons-x-mark"
              class="md:col-span-2 lg:col-span-3 xl:col-span-5 justify-self-start"
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
              :description="hasActiveFilters ? 'No members match your search criteria. Try adjusting your filters.' : 'No members have been synced yet. Sync members from Spond to get started.'"
              :action-label="hasActiveFilters ? undefined : 'Sync Members'"
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
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium uppercase text-gray-700 dark:text-gray-300">Groups</th>
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
                      <div v-if="member.groups?.length" class="flex flex-wrap gap-1">
                        <span
                          v-for="g in member.groups"
                          :key="g.group_id"
                          class="inline-flex items-center rounded-full bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-300"
                        >
                          {{ g.name }}
                        </span>
                      </div>
                      <span v-else>-</span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                      {{ totalSubgroups(member) }}
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
const authStore = useAuthStore()

interface Subgroup {
  id: string
  name: string
}
interface AvailableGroup {
  spond_id: string
  name: string
  subgroups: Subgroup[]
}

const members = ref<any[]>([])
const availableGroups = ref<AvailableGroup[]>([])
const totalSubgroups = (m: any) =>
  (m.groups || []).reduce((sum: number, g: any) => sum + (g.subgroup_uids?.length || 0), 0)
const total = ref(0)
const loading = ref(false)
const syncing = ref(false)
const skip = ref(0)
const limit = ref(20)
const searchQuery = ref('')
const emailFilter = ref('')
const groupFilter = ref('')
const subgroupFilter = ref('')
// Combined "field:order" so the dropdown stays a single control.
// A value prefixed with "group:" or "subgroup:" buckets members in that
// group/subgroup to the top (client-side stable re-order).
const sortValue = ref('name:asc')

const groupsWithSubgroups = computed(() =>
  availableGroups.value.filter(g => g.subgroups && g.subgroups.length > 0)
)
const flatSubgroups = computed(() =>
  availableGroups.value.flatMap(g =>
    (g.subgroups || []).map(s => ({ ...s, groupName: g.name }))
  )
)

const hasActiveFilters = computed(
  () =>
    !!(searchQuery.value || emailFilter.value || groupFilter.value || subgroupFilter.value) ||
    sortValue.value !== 'name:asc'
)

onMounted(async () => {
  await loadGroups()
  await loadMembers()
})

// Watch for global group changes and reload members
watch(() => authStore.selectedGroupId, () => {
  skip.value = 0
  loadMembers()
})

const loadGroups = async () => {
  try {
    const response: any = await api.getGroups({ limit: 100 })
    availableGroups.value = (response.groups || []).map((g: any) => ({
      spond_id: g.spond_id,
      name: g.name,
      subgroups: (g.subgroups || []).map((s: any) => ({ id: s.id, name: s.name })),
    }))
  } catch {
    // Non-fatal — dropdown just stays empty.
  }
}

interface ParsedSort {
  sort_by: string
  sort_order: string
  groupBucketSpondId: string | null
  subgroupBucketId: string | null
}

const parseSort = (): ParsedSort => {
  const [field, order] = sortValue.value.split(':')
  // Bucket sorts: pin members in the chosen group/subgroup to the top
  // (frontend stable re-order layered on top of the backend name sort).
  if (field === 'group') {
    return { sort_by: 'name', sort_order: 'asc', groupBucketSpondId: order, subgroupBucketId: null }
  }
  if (field === 'subgroup') {
    return { sort_by: 'name', sort_order: 'asc', groupBucketSpondId: null, subgroupBucketId: order }
  }
  return { sort_by: field, sort_order: order, groupBucketSpondId: null, subgroupBucketId: null }
}

const memberInGroup = (m: any, spondId: string) =>
  m.groups?.some((g: any) => g.spond_id === spondId) ? 0 : 1
const memberInSubgroup = (m: any, sid: string) =>
  m.groups?.some((g: any) => g.subgroup_uids?.includes(sid)) ? 0 : 1

const loadMembers = async () => {
  loading.value = true
  try {
    const sort = parseSort()
    const params: any = {
      skip: skip.value,
      limit: limit.value,
      sort_by: sort.sort_by,
      sort_order: sort.sort_order,
    }
    if (searchQuery.value) params.search = searchQuery.value
    if (emailFilter.value) params.email = emailFilter.value
    if (groupFilter.value) params.group_id = groupFilter.value
    if (subgroupFilter.value) params.subgroup_id = subgroupFilter.value

    const response = await api.getMembers(params)
    let result = response.members || []
    if (sort.groupBucketSpondId) {
      result = [...result].sort(
        (a: any, b: any) =>
          memberInGroup(a, sort.groupBucketSpondId!) - memberInGroup(b, sort.groupBucketSpondId!)
      )
    } else if (sort.subgroupBucketId) {
      result = [...result].sort(
        (a: any, b: any) =>
          memberInSubgroup(a, sort.subgroupBucketId!) - memberInSubgroup(b, sort.subgroupBucketId!)
      )
    }
    members.value = result
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
    skip.value = 0
    loadMembers()
  }, 300)
}

const onFilterChange = () => {
  skip.value = 0
  loadMembers()
}

// Clear filters function
const clearFilters = () => {
  searchQuery.value = ''
  emailFilter.value = ''
  groupFilter.value = ''
  subgroupFilter.value = ''
  sortValue.value = 'name:asc'
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
  skip.value = 0
  loadMembers()
}
</script>
