<template>
  <div class="text-center py-12">
    <UIcon
      :name="icon"
      class="h-12 w-12 mx-auto text-gray-400 dark:text-gray-600 mb-4"
    />
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
      {{ title }}
    </h3>
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
      {{ description }}
    </p>
    <slot name="action">
      <UButton
        v-if="actionLabel"
        :icon="actionIcon"
        :loading="actionLoading"
        @click="$emit('action')"
      >
        {{ actionLabel }}
      </UButton>
    </slot>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description: string
  actionLabel?: string
  actionIcon?: string
  actionLoading?: boolean
}>()

defineEmits<{
  action: []
}>()
</script>
