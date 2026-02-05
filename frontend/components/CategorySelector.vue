<script setup lang="ts">
/**
 * CategorySelector Component
 * Multi-select dropdown for filtering by categories
 */

interface Category {
  id: number
  name: string
  color: string
  icon: string
}

const props = withDefaults(defineProps<{
  modelValue?: number[]
  multiple?: boolean
  placeholder?: string
  activeOnly?: boolean
}>(), {
  modelValue: () => [],
  multiple: true,
  placeholder: 'Select categories...',
  activeOnly: true
})

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
}>()

const categoryStore = useCategoryStore()

// Load categories on mount
onMounted(async () => {
  console.log('CategorySelector - onMounted, categories.length:', categoryStore.categories.length)
  if (categoryStore.categories.length === 0) {
    console.log('CategorySelector - fetching categories...')
    await categoryStore.fetchCategories(props.activeOnly)
    console.log('CategorySelector - after fetch, categories.length:', categoryStore.categories.length)
  }
})

// Map categories to USelectMenu items
const categoryItems = computed(() => {
  const categories = props.activeOnly
    ? categoryStore.activeCategories
    : categoryStore.categories

  console.log('CategorySelector - categories from store:', categories)
  console.log('CategorySelector - activeOnly:', props.activeOnly)
  console.log('CategorySelector - store.categories.length:', categoryStore.categories.length)

  const items = categories.map(cat => ({
    ...cat,
    label: cat.name,
    value: cat.id
  }))

  console.log('CategorySelector - mapped items:', items)
  return items
})

// Selected categories for display (now working with IDs directly)
const selected = computed({
  get: () => {
    if (!props.multiple) {
      return props.modelValue[0] || null
    }
    return props.modelValue
  },
  set: (value) => {
    if (!props.multiple) {
      emit('update:modelValue', value ? [value] : [])
    } else {
      emit('update:modelValue', Array.isArray(value) ? value : [])
    }
  }
})

// Get selected category objects for display
const selectedCategories = computed(() => {
  if (!props.multiple && selected.value) {
    return categoryItems.value.find(item => item.id === selected.value) || null
  }
  return categoryItems.value.filter(item => props.modelValue.includes(item.id))
})

// Color helper for badges
const getCategoryColor = (categoryId: number) => {
  const category = categoryStore.getCategoryById(categoryId)
  return category?.color || '#6B7280'
}
</script>

<template>
  <div class="w-full">
    <USelectMenu
      v-model="selected"
      :options="categoryItems"
      :loading="categoryStore.loading"
      :placeholder="placeholder"
      :multiple="multiple"
      option-attribute="label"
      value-attribute="id"
      aria-label="Select categories"
      :ui="{
        width: 'w-full'
      }"
    >
      <template #label>
        <span v-if="!multiple && selectedCategories" class="flex items-center gap-2">
          <UIcon :name="selectedCategories.icon" class="w-4 h-4" :style="{ color: selectedCategories.color }" />
          <span>{{ selectedCategories.label }}</span>
        </span>
        <div v-else-if="multiple && Array.isArray(selectedCategories) && selectedCategories.length > 0" class="flex items-center gap-1 flex-wrap">
          <span
            v-for="cat in selectedCategories.slice(0, 3)"
            :key="cat.id"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium"
            :style="{
              backgroundColor: `${cat.color}20`,
              color: cat.color,
              borderColor: `${cat.color}40`,
              border: '1px solid'
            }"
          >
            <UIcon :name="cat.icon" class="w-3 h-3" />
            {{ cat.label }}
          </span>
          <span v-if="selectedCategories.length > 3" class="text-xs text-gray-500">
            +{{ selectedCategories.length - 3 }} more
          </span>
        </div>
        <span v-else class="text-gray-500 dark:text-gray-400">{{ placeholder }}</span>
      </template>

      <template #item="{ item, active, selected: isSelected }">
        <div class="flex items-center gap-2 w-full">
          <UIcon :name="item.icon" class="w-4 h-4 flex-shrink-0" :style="{ color: item.color }" />
          <span class="flex-1 truncate">{{ item.label }}</span>
          <UIcon
            v-if="isSelected"
            name="i-heroicons-check"
            class="w-4 h-4 flex-shrink-0 text-primary"
          />
        </div>
      </template>
    </USelectMenu>
  </div>
</template>
