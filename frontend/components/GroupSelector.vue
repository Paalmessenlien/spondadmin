<template>
  <div class="w-full">
    <USelectMenu
      v-model="selectedGroup"
      :items="groupItems"
      :loading="loading"
      placeholder="Select a group..."
      aria-label="Select group"
      @update:model-value="handleGroupChange"
    >
      <template #label>
        <span v-if="selectedGroup">{{ selectedGroup.label || selectedGroup.name }}</span>
        <span v-else class="text-gray-500 dark:text-gray-400">Select a group...</span>
      </template>
    </USelectMenu>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()
const filtersStore = useFiltersStore()
const toast = useToast()
const config = useRuntimeConfig()

const selectedGroup = ref<any>(null)
const groups = ref<any[]>([])
const loading = ref(false)

// Map groups to items with label property for USelectMenu
// Add "All Groups" option at the top
const groupItems = computed(() => {
  const allGroupsOption = {
    id: null,
    name: 'All Groups',
    label: 'All Groups',
  }

  const mappedGroups = groups.value.map(group => ({
    ...group,
    label: group.name
  }))

  return [allGroupsOption, ...mappedGroups]
})

// Load groups function
const loadGroups = async () => {
  if (!authStore.token) {
    console.log('[GroupSelector] No token, skipping load')
    return
  }

  console.log('[GroupSelector] Loading groups...')
  loading.value = true

  try {
    const response = await $fetch<any>('/groups/', {
      baseURL: config.public.apiBase,
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      query: { limit: 100 },
    })

    console.log('[GroupSelector] Received response:', response)

    // Extract groups array from response
    if (response && response.groups && Array.isArray(response.groups)) {
      groups.value = response.groups
      console.log('[GroupSelector] Loaded', groups.value.length, 'groups')

      // Set selected group if one was previously selected
      if (filtersStore.selectedGroupId && groups.value.length > 0) {
        const found = groupItems.value.find((g: any) => g.id === filtersStore.selectedGroupId)
        if (found) {
          selectedGroup.value = found
          console.log('[GroupSelector] Restored selected group:', found.label)
        }
      } else if (filtersStore.selectedGroupId === null) {
        // "All Groups" is selected
        selectedGroup.value = groupItems.value[0] // First item is "All Groups"
        console.log('[GroupSelector] Restored "All Groups" selection')
      }
    } else {
      console.error('[GroupSelector] Unexpected response format:', response)
      groups.value = []
    }
  } catch (error: any) {
    console.error('[GroupSelector] Failed to load groups:', error)
    toast.add({
      title: 'Error loading groups',
      description: error.message || 'Failed to load groups',
      color: 'red',
    })
  } finally {
    loading.value = false
  }
}

// Initialize on mount
onMounted(async () => {
  console.log('[GroupSelector] Component mounted')

  // Initialize filters from localStorage
  filtersStore.initFilters()

  // Initialize auth if needed
  if (!authStore.token) {
    console.log('[GroupSelector] Initializing auth from localStorage')
    await authStore.initAuth()
  }

  // Load groups if we have a token
  if (authStore.token) {
    await loadGroups()
  } else {
    console.log('[GroupSelector] No token after init, cannot load groups')
  }
})

// Watch for token changes (e.g., when user logs in)
watch(() => authStore.token, (newToken, oldToken) => {
  console.log('[GroupSelector] Token changed:', { had: !!oldToken, has: !!newToken })
  if (newToken && !oldToken) {
    // Token was just added (user logged in)
    loadGroups()
  }
})

const handleGroupChange = (group: any) => {
  console.log('[GroupSelector] Group changed:', group)

  if (group) {
    filtersStore.setSelectedGroup(group.id)

    const groupName = group.label || group.name
    toast.add({
      title: 'Group selected',
      description: groupName === 'All Groups'
        ? 'Showing data from all groups'
        : `Selected group: ${groupName}`,
      color: 'green',
    })
  } else {
    filtersStore.setSelectedGroup(null)
  }
}
</script>
