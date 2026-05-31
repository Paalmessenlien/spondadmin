<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Scores & Records', to: '/dashboard/scores' },
      { label: 'Records' }
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Norwegian Records</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Club records from rekord.bueskyting.no
      </p>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="flex flex-wrap gap-4">
        <USelectMenu
          v-if="filterValues.divisions?.length"
          v-model="selectedDivision"
          :options="[{ label: 'All Divisions', value: '' }, ...filterValues.divisions.map((d: string) => ({ label: d, value: d }))]"
          placeholder="Division"
          class="w-48"
        />
        <USelectMenu
          v-if="filterValues.categories?.length"
          v-model="selectedCategory"
          :options="[{ label: 'All Categories', value: '' }, ...filterValues.categories.map((c: string) => ({ label: c, value: c }))]"
          placeholder="Category"
          class="w-48"
        />
        <USelectMenu
          v-model="selectedType"
          :options="[
            { label: 'All Types', value: '' },
            { label: 'Individual', value: 'individual' },
            { label: 'Team', value: 'team' },
          ]"
          placeholder="Type"
          class="w-40"
        />
      </div>
    </UCard>

    <!-- Records Table -->
    <UCard>
      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
      </div>

      <div v-else-if="records.length === 0" class="text-center py-8 text-gray-500">
        <UIcon name="i-heroicons-trophy" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>No records found</p>
      </div>

      <div v-else>
        <ResponsiveTable :columns="recordCols" :rows="records" empty-text="No records found">
          <template #cell-division="{ row }">
            <UBadge color="blue" variant="subtle" size="sm">{{ row.division }}</UBadge>
          </template>
          <template #cell-distance="{ row }">{{ row.distance || '-' }}</template>
          <template #cell-archer_name="{ row }">
            <NuxtLink
              v-if="row.record_type !== 'team' && row.member_id"
              :to="`/dashboard/members/${row.member_id}`"
              class="text-blue-600 dark:text-blue-400 hover:underline"
              title="View member profile"
            >{{ row.archer_name || 'Unknown' }}</NuxtLink>
            <span v-else>{{ row.record_type === 'team' ? 'Team' : (row.archer_name || 'Unknown') }}</span>
            <div v-if="row.team_members?.members" class="text-xs text-gray-500">{{ row.team_members.members }}</div>
          </template>
          <template #cell-score="{ row }"><span class="font-bold text-amber-600">{{ row.score }}</span></template>
          <template #cell-record_date="{ row }">{{ formatDate(row.record_date) }}</template>
          <template #cell-record_type="{ row }">
            <UBadge :color="row.record_type === 'team' ? 'purple' : 'green'" variant="subtle" size="sm">{{ row.record_type }}</UBadge>
          </template>
        </ResponsiveTable>

        <!-- Pagination -->
        <div v-if="total > pageSize" class="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Showing {{ skip + 1 }}-{{ Math.min(skip + pageSize, total) }} of {{ total }}
          </div>
          <div class="flex items-center space-x-2">
            <UButton size="sm" color="neutral" variant="outline" :disabled="skip === 0" @click="skip -= pageSize; loadRecords()">
              Previous
            </UButton>
            <UButton size="sm" color="neutral" variant="outline" :disabled="skip + pageSize >= total" @click="skip += pageSize; loadRecords()">
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

const records = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const skip = ref(0)

const recordCols = [
  { key: 'division', label: 'Division' },
  { key: 'category', label: 'Category' },
  { key: 'round_type', label: 'Round' },
  { key: 'distance', label: 'Distance' },
  { key: 'archer_name', label: 'Archer', primary: true },
  { key: 'score', label: 'Score', align: 'right' },
  { key: 'record_date', label: 'Date' },
  { key: 'record_type', label: 'Type' },
] as const
const pageSize = ref(100)
const filterValues = ref<any>({ divisions: [], categories: [] })
const selectedDivision = ref<any>({ label: 'All Divisions', value: '' })
const selectedCategory = ref<any>({ label: 'All Categories', value: '' })
const selectedType = ref<any>({ label: 'All Types', value: '' })

const loadRecords = async () => {
  loading.value = true
  try {
    const params: Record<string, string> = {
      skip: skip.value.toString(),
      limit: pageSize.value.toString(),
    }
    if (selectedDivision.value?.value) params.division = selectedDivision.value.value
    if (selectedCategory.value?.value) params.category = selectedCategory.value.value
    if (selectedType.value?.value) params.record_type = selectedType.value.value

    const data: any = await api.getRecords(params)
    records.value = data.records || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Failed to load records:', err)
  } finally {
    loading.value = false
  }
}

watch([selectedDivision, selectedCategory, selectedType], () => {
  skip.value = 0
  loadRecords()
})

onMounted(async () => {
  try {
    filterValues.value = await api.getRecordFilters()
  } catch (err) {
    console.error('Failed to load filter values:', err)
  }
  await loadRecords()
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
