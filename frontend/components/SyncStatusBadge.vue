<script setup lang="ts">
const props = withDefaults(defineProps<{
  status?: 'synced' | 'pending' | 'local_only' | 'error'
  error?: string | null
}>(), {
  status: 'synced',
  error: null
})

const statusConfig: Record<string, { color: string, icon: string, label: string }> = {
  synced: {
    color: 'green',
    icon: 'i-heroicons-check-circle',
    label: 'Synced'
  },
  pending: {
    color: 'amber',
    icon: 'i-heroicons-clock',
    label: 'Pending'
  },
  local_only: {
    color: 'gray',
    icon: 'i-heroicons-computer-desktop',
    label: 'Local Only'
  },
  error: {
    color: 'red',
    icon: 'i-heroicons-exclamation-circle',
    label: 'Error'
  }
}

const config = computed(() => {
  const status = props.status || 'synced'
  return statusConfig[status] || statusConfig.synced
})
</script>

<template>
  <UTooltip :text="error || config.label">
    <UBadge
      :color="config.color"
      variant="subtle"
      size="xs"
      class="gap-1"
    >
      <UIcon :name="config.icon" class="w-3 h-3" />
      {{ config.label }}
    </UBadge>
  </UTooltip>
</template>
