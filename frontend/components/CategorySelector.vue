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
  if (categoryStore.categories.length === 0) {
    await categoryStore.fetchCategories(props.activeOnly)
  }
})

// Map categories to USelectMenu items
const categoryItems = computed(() => {
  const categories = props.activeOnly
    ? categoryStore.activeCategories
    : categoryStore.categories

  return categories.map(cat => ({
    id: cat.id,
    label: cat.name,
    icon: cat.icon,
    color: cat.color,
    value: cat.id
  }))
})

// Selected categories for display
const selected = computed({
  get: () => {
    if (!props.multiple) {
      const id = props.modelValue[0]
      return categoryItems.value.find(item => item.id === id) || null
    }
    return categoryItems.value.filter(item => props.modelValue.includes(item.id))
  },
  set: (value) => {
    if (!props.multiple) {
      emit('update:modelValue', value ? [value.id] : [])
    } else {
      emit('update:modelValue', Array.isArray(value) ? value.map((v: any) => v.id) : [])
    }
  }
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
      by="id"
      :options="categoryItems"
      :loading="categoryStore.loading"
      :placeholder="placeholder"
      :multiple="multiple"
      aria-label="Select categories"
      :ui="{
        width: 'w-full'
      }"
    >
      <template #label>
        <span v-if="!multiple && selected" class="flex items-center gap-2">
          <UIcon :name="(selected as any).icon" class="w-4 h-4" :style="{ color: (selected as any).color }" />
          <span>{{ (selected as any).label }}</span>
        </span>
        <div v-else-if="multiple && Array.isArray(selected) && selected.length > 0" class="flex items-center gap-1 flex-wrap">
          <span
            v-for="cat in selected.slice(0, 3)"
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
          <span v-if="selected.length > 3" class="text-xs text-gray-500">
            +{{ selected.length - 3 }} more
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
