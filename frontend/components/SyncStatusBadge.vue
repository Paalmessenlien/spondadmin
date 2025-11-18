<script setup lang="ts">
const props = defineProps<{
  status: 'synced' | 'pending' | 'local_only' | 'error'
  error?: string | null
}>()

const statusConfig = {
  synced: {
    color: 'green' as const,
    icon: 'i-heroicons-check-circle',
    label: 'Synced'
  },
  pending: {
    color: 'amber' as const,
    icon: 'i-heroicons-clock',
    label: 'Pending'
  },
  local_only: {
    color: 'gray' as const,
    icon: 'i-heroicons-computer-desktop',
    label: 'Local Only'
  },
  error: {
    color: 'red' as const,
    icon: 'i-heroicons-exclamation-circle',
    label: 'Error'
  }
}

const config = computed(() => statusConfig[props.status])
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
