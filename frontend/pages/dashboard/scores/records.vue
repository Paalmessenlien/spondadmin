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

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-3 px-2 font-medium text-gray-500">Division</th>
              <th class="text-left py-3 px-2 font-medium text-gray-500">Category</th>
              <th class="text-left py-3 px-2 font-medium text-gray-500">Round</th>
              <th class="text-left py-3 px-2 font-medium text-gray-500">Distance</th>
              <th class="text-left py-3 px-2 font-medium text-gray-500">Archer</th>
              <th class="text-right py-3 px-2 font-medium text-gray-500">Score</th>
              <th class="text-left py-3 px-2 font-medium text-gray-500">Date</th>
              <th class="text-left py-3 px-2 font-medium text-gray-500">Type</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in records"
              :key="record.id"
              class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
            >
              <td class="py-2 px-2">
                <UBadge color="blue" variant="subtle" size="sm">{{ record.division }}</UBadge>
              </td>
              <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ record.category }}</td>
              <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ record.round_type }}</td>
              <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ record.distance || '-' }}</td>
              <td class="py-2 px-2 font-medium text-gray-900 dark:text-white">
                {{ record.record_type === 'team' ? 'Team' : (record.archer_name || 'Unknown') }}
                <div v-if="record.team_members?.members" class="text-xs text-gray-500">
                  {{ record.team_members.members }}
                </div>
              </td>
              <td class="py-2 px-2 text-right font-bold text-amber-600">{{ record.score }}</td>
              <td class="py-2 px-2 text-gray-600 dark:text-gray-400">{{ formatDate(record.record_date) }}</td>
              <td class="py-2 px-2">
                <UBadge :color="record.record_type === 'team' ? 'purple' : 'green'" variant="subtle" size="sm">
                  {{ record.record_type }}
                </UBadge>
              </td>
            </tr>
          </tbody>
        </table>

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
