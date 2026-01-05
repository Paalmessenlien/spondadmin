<template>
  <div class="w-full">
    <USelectMenu
      v-model="selectedMembers"
      :items="memberItems"
      :loading="loading"
      multiple
      searchable
      :search-attributes="['label', 'email']"
      :placeholder="placeholder"
      :disabled="disabled"
      @update:model-value="handleSelectionChange"
    >
      <template #label>
        <span v-if="selectedMembers.length === 0" class="text-gray-500 dark:text-gray-400">
          {{ placeholder }}
        </span>
        <span v-else-if="selectedMembers.length === 1">
          {{ selectedMembers[0]?.label || selectedMembers[0]?.name }}
        </span>
        <span v-else>
          {{ selectedMembers.length }} members selected
        </span>
      </template>
      <template #option="{ option }">
        <div class="flex flex-col">
          <span>{{ option.label }}</span>
          <span v-if="option.email" class="text-xs text-gray-500 dark:text-gray-400">
            {{ option.email }}
          </span>
        </div>
      </template>
    </USelectMenu>
  </div>
</template>

<script setup lang="ts">
interface Member {
  id: number
  spond_id: string
  first_name: string
  last_name: string
  email?: string
  profile?: {
    id?: string
    [key: string]: any
  }
}

interface MemberItem {
  id: number
  spond_id: string
  profile_id?: string
  label: string
  email?: string
  name: string
}

const props = defineProps<{
  groupId?: string | null
  modelValue?: string[]
  placeholder?: string
  disabled?: boolean
  useProfileId?: boolean // If true, use profile.id instead of spond_id (for owners)
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const config = useRuntimeConfig()
const authStore = useAuthStore()
const toast = useToast()

const members = ref<Member[]>([])
const selectedMembers = ref<MemberItem[]>([])
const loading = ref(false)

const placeholder = computed(() => props.placeholder || 'Select members...')

// Map members to items with label property for USelectMenu
const memberItems = computed<MemberItem[]>(() => {
  return members.value.map(member => ({
    id: member.id,
    spond_id: member.spond_id,
    profile_id: member.profile?.id,
    label: `${member.first_name} ${member.last_name}`,
    email: member.email,
    name: `${member.first_name} ${member.last_name}`
  }))
})

// Load members for the group
const loadMembers = async () => {
  const groupToLoad = props.groupId || authStore.selectedGroupId

  if (!authStore.token) {
    console.log('[MemberSelect] No token, skipping load')
    return
  }

  if (!groupToLoad) {
    console.log('[MemberSelect] No group selected, skipping load')
    members.value = []
    return
  }

  console.log('[MemberSelect] Loading members for group:', groupToLoad)
  loading.value = true

  try {
    const response = await $fetch<any>('/members/', {
      baseURL: config.public.apiBase,
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      query: {
        group_id: groupToLoad,
        limit: 500 // Load all members for selection
      },
    })

    if (response && response.members && Array.isArray(response.members)) {
      members.value = response.members
      console.log('[MemberSelect] Loaded', members.value.length, 'members')

      // Restore selection from modelValue if provided
      if (props.modelValue && props.modelValue.length > 0) {
        restoreSelection(props.modelValue)
      }
    } else {
      console.error('[MemberSelect] Unexpected response format:', response)
      members.value = []
    }
  } catch (error: any) {
    console.error('[MemberSelect] Failed to load members:', error)
    toast.add({
      title: 'Error loading members',
      description: error.message || 'Failed to load members',
      color: 'red',
    })
  } finally {
    loading.value = false
  }
}

// Restore selection from modelValue (array of IDs)
const restoreSelection = (ids: string[]) => {
  const selected: MemberItem[] = []

  for (const id of ids) {
    const found = memberItems.value.find((m: MemberItem) => {
      if (props.useProfileId) {
        return m.profile_id === id
      }
      return m.spond_id === id
    })
    if (found) {
      selected.push(found)
    }
  }

  selectedMembers.value = selected
  console.log('[MemberSelect] Restored selection:', selected.length, 'members')
}

// Handle selection change
const handleSelectionChange = (members: MemberItem[]) => {
  console.log('[MemberSelect] Selection changed:', members.length, 'members')

  // Extract the appropriate IDs based on useProfileId prop
  const ids = members.map(m => {
    if (props.useProfileId) {
      return m.profile_id || m.spond_id // Fallback to spond_id if no profile_id
    }
    return m.spond_id
  })

  emit('update:modelValue', ids)
}

// Watch for group changes
watch(() => props.groupId, (newGroupId, oldGroupId) => {
  console.log('[MemberSelect] Group ID changed:', { from: oldGroupId, to: newGroupId })
  if (newGroupId !== oldGroupId) {
    selectedMembers.value = []
    emit('update:modelValue', [])
    loadMembers()
  }
}, { immediate: false })

// Watch for external modelValue changes
watch(() => props.modelValue, (newValue) => {
  if (newValue && memberItems.value.length > 0) {
    restoreSelection(newValue)
  }
}, { deep: true })

// Initialize on mount
onMounted(() => {
  console.log('[MemberSelect] Component mounted, groupId:', props.groupId)
  loadMembers()
})
</script>
