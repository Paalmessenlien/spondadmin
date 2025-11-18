<template>
  <div class="space-y-6">
        <!-- Breadcrumb -->
        <Breadcrumb
          :items="[
            { label: 'Dashboard', to: '/dashboard' },
            { label: 'Groups', to: '/dashboard/groups' },
            { label: group?.name || 'Group Details' }
          ]"
        />

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center py-12">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
        </div>

        <!-- Error State -->
        <UCard v-else-if="error">
          <div class="text-center py-8">
            <UIcon name="i-heroicons-exclamation-triangle" class="h-12 w-12 mx-auto text-red-500 mb-4" />
            <h3 class="text-lg font-semibold text-red-600 mb-2">Error Loading Group</h3>
            <p class="text-gray-600 dark:text-gray-400">{{ error }}</p>
          </div>
        </UCard>

        <!-- Group Details -->
        <template v-else-if="group">
          <!-- Header Card -->
          <UCard>
            <div class="space-y-4">
              <div class="flex justify-between items-start">
                <div>
                  <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    {{ group.name }}
                  </h1>
                  <p v-if="group.description" class="text-gray-600 dark:text-gray-400 mt-2">
                    {{ group.description }}
                  </p>
                </div>
              </div>

              <!-- Stats -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div class="flex items-center space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <UIcon name="i-heroicons-users" class="h-8 w-8 text-blue-600" />
                  <div>
                    <div class="text-2xl font-bold text-blue-600">{{ groupMembers.length }}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Members</div>
                  </div>
                </div>

                <div class="flex items-center space-x-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <UIcon name="i-heroicons-user-group" class="h-8 w-8 text-purple-600" />
                  <div>
                    <div class="text-2xl font-bold text-purple-600">{{ subgroupCount }}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Subgroups</div>
                  </div>
                </div>

                <div class="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <UIcon name="i-heroicons-shield-check" class="h-8 w-8 text-green-600" />
                  <div>
                    <div class="text-2xl font-bold text-green-600">{{ roleCount }}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Roles</div>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Subgroups -->
          <UCard v-if="group.subgroups && group.subgroups.length > 0">
            <template #header>
              <h2 class="text-xl font-bold">Subgroups</h2>
            </template>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="subgroup in group.subgroups"
                :key="subgroup.id"
                class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div class="font-medium">{{ subgroup.name }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {{ getMemberCountInSubgroup(subgroup.id) }} members
                </div>
              </div>
            </div>
          </UCard>

          <!-- Roles -->
          <UCard v-if="group.roles && group.roles.length > 0">
            <template #header>
              <h2 class="text-xl font-bold">Roles</h2>
            </template>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="role in group.roles"
                :key="role.id"
                class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div class="font-medium">{{ role.name }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {{ getMemberCountInRole(role.id) }} members
                </div>
              </div>
            </div>
          </UCard>

          <!-- Members List -->
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h2 class="text-xl font-bold">Members</h2>
                <UInput
                  v-model="searchQuery"
                  placeholder="Search members..."
                  icon="i-heroicons-magnifying-glass"
                  class="w-64"
                />
              </div>
            </template>

            <div v-if="loadingMembers" class="flex justify-center py-8">
              <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
            </div>

            <div v-else-if="filteredMembers.length === 0" class="text-center py-8 text-gray-500">
              No members found
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="member in filteredMembers"
                :key="member.id"
                class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                @click="navigateTo(`/dashboard/members/${member.id}`)"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold">
                    {{ getInitials(member) }}
                  </div>
                  <div>
                    <div class="font-medium hover:text-blue-600 dark:hover:text-blue-400">
                      {{ member.first_name }} {{ member.last_name }}
                    </div>
                    <div v-if="member.email" class="text-sm text-gray-600 dark:text-gray-400">
                      {{ member.email }}
                    </div>
                  </div>
                </div>

                <div class="text-sm text-gray-600 dark:text-gray-400">
                  {{ member.subgroup_uids?.length || 0 }} subgroup(s)
                </div>
              </div>
            </div>
          </UCard>
        </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const route = useRoute()
const api = useApi()
const toast = useToast()

const groupId = computed(() => parseInt(route.params.id as string))

const group = ref<any>(null)
const members = ref<any[]>([])
const loading = ref(true)
const loadingMembers = ref(true)
const error = ref<string | null>(null)
const searchQuery = ref('')

onMounted(async () => {
  await loadGroup()
  await loadMembers()
})

const loadGroup = async () => {
  loading.value = true
  error.value = null
  try {
    group.value = await api.getGroup(groupId.value)
  } catch (err: any) {
    console.error('Failed to load group:', err)
    error.value = err?.data?.detail || 'Failed to load group details'
    toast.add({ title: 'Error', description: error.value, color: 'red' })
  } finally {
    loading.value = false
  }
}

const loadMembers = async () => {
  loadingMembers.value = true
  try {
    // Load all members (filtered by group on backend would be better)
    const response = await api.getMembers({ limit: 1000 })
    members.value = response.members || []
  } catch (err: any) {
    console.error('Failed to load members:', err)
  } finally {
    loadingMembers.value = false
  }
}

const groupMembers = computed(() => {
  // Filter members who belong to this group
  // Since we're using group_id in members, we can filter by spond_id
  return members.value.filter(m => m.group_id === group.value?.spond_id)
})

const filteredMembers = computed(() => {
  let filtered = groupMembers.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(m => {
      const name = `${m.first_name} ${m.last_name}`.toLowerCase()
      const email = m.email?.toLowerCase() || ''
      return name.includes(query) || email.includes(query)
    })
  }

  return filtered
})

const subgroupCount = computed(() => {
  return group.value?.subgroups?.length || 0
})

const roleCount = computed(() => {
  return group.value?.roles?.length || 0
})

const getMemberCountInSubgroup = (subgroupId: string) => {
  return groupMembers.value.filter(m =>
    m.subgroup_uids?.includes(subgroupId)
  ).length
}

const getMemberCountInRole = (roleId: string) => {
  return groupMembers.value.filter(m =>
    m.role_uids?.includes(roleId)
  ).length
}

const getInitials = (member: any) => {
  if (!member) return '?'
  const first = member.first_name?.[0] || ''
  const last = member.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}
</script>
