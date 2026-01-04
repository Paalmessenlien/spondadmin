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
const toast = useToast()
const config = useRuntimeConfig()

const selectedGroup = ref<any>(null)
const groups = ref<any[]>([])
const loading = ref(false)

// Special "All Groups" option
const allGroupsOption = {
  id: null,
  spond_id: null,
  name: 'All Groups',
  label: 'All Groups'
}

// Map groups to items with label property for USelectMenu
const groupItems = computed(() => {
  const items = groups.value.map(group => ({
    ...group,
    label: group.name
  }))
  // Add "All Groups" as first option
  return [allGroupsOption, ...items]
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
      if (authStore.selectedGroupId && groups.value.length > 0) {
        const found = groupItems.value.find((g: any) => g.spond_id === authStore.selectedGroupId)
        if (found) {
          selectedGroup.value = found
          console.log('[GroupSelector] Restored selected group:', found.label)
        }
      } else if (!authStore.selectedGroupId) {
        // No group selected means "All Groups"
        selectedGroup.value = allGroupsOption
        console.log('[GroupSelector] Set to All Groups')
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

  if (group && group.spond_id) {
    // Specific group selected - use spond_id (string) not id (number)
    authStore.setSelectedGroup(group.spond_id)
    toast.add({
      title: 'Group selected',
      description: `Filtering by: ${group.label || group.name}`,
      color: 'green',
    })
  } else {
    // "All Groups" selected or cleared
    authStore.setSelectedGroup(null)
    toast.add({
      title: 'All Groups',
      description: 'Showing data from all groups',
      color: 'blue',
    })
  }
}
</script>
