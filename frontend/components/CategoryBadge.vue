<script setup lang="ts">
/**
 * CategoryBadge Component
 * Displays an event category as a colored badge with icon
 */

interface Category {
  id: number
  name: string
  color: string
  icon: string
}

const props = withDefaults(defineProps<{
  category?: Category | null
  categoryId?: number | null
  size?: 'xs' | 'sm' | 'md' | 'lg'
  showIcon?: boolean
}>(), {
  category: null,
  categoryId: null,
  size: 'sm',
  showIcon: true
})

const categoryStore = useCategoryStore()

// If only categoryId is provided, fetch the category from store
const displayCategory = computed(() => {
  if (props.category) {
    return props.category
  }
  if (props.categoryId) {
    return categoryStore.getCategoryById(props.categoryId)
  }
  return null
})

// Extract RGB values from hex color for custom styling
const colorStyle = computed(() => {
  if (!displayCategory.value?.color) return {}

  const hex = displayCategory.value.color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  return {
    '--category-color': `${r}, ${g}, ${b}`,
    backgroundColor: `rgba(${r}, ${g}, ${b}, 0.1)`,
    borderColor: `rgba(${r}, ${g}, ${b}, 0.3)`,
    color: displayCategory.value.color
  }
})
</script>

<template>
  <span
    v-if="displayCategory"
    class="inline-flex items-center gap-1 px-2 py-1 rounded-md border font-medium category-badge"
    :class="{
      'text-xs': size === 'xs',
      'text-sm': size === 'sm',
      'text-base': size === 'md',
      'text-lg': size === 'lg',
    }"
    :style="colorStyle"
    :title="displayCategory.name"
  >
    <UIcon
      v-if="showIcon"
      :name="displayCategory.icon"
      :class="{
        'w-3 h-3': size === 'xs',
        'w-3.5 h-3.5': size === 'sm',
        'w-4 h-4': size === 'md',
        'w-5 h-5': size === 'lg',
      }"
    />
    <span>{{ displayCategory.name }}</span>
  </span>
  <span
    v-else
    class="inline-flex items-center gap-1 px-2 py-1 rounded-md border text-gray-500 bg-gray-50 border-gray-200"
    :class="{
      'text-xs': size === 'xs',
      'text-sm': size === 'sm',
      'text-base': size === 'md',
      'text-lg': size === 'lg',
    }"
  >
    <UIcon
      name="i-heroicons-question-mark-circle"
      :class="{
        'w-3 h-3': size === 'xs',
        'w-3.5 h-3.5': size === 'sm',
        'w-4 h-4': size === 'md',
        'w-5 h-5': size === 'lg',
      }"
    />
    <span>Uncategorized</span>
  </span>
</template>

<style scoped>
.category-badge {
  transition: all 0.2s ease;
}

.category-badge:hover {
  opacity: 0.8;
}
</style>
