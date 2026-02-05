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

// Map categories to USelectMenu items (match working pattern from analytics.vue)
const categoryItems = computed(() => {
  const categories = props.activeOnly
    ? categoryStore.activeCategories
    : categoryStore.categories

  console.log('[CategorySelector] categoryItems computed running')
  console.log('[CategorySelector] categories length:', categories.length)
  console.log('[CategorySelector] categories:', categories)

  // Simple format: label and value for USelectMenu, plus icon/color for templates
  const items = categories.map(cat => ({
    label: cat.name,
    value: cat.id,
    icon: cat.icon,
    color: cat.color,
    id: cat.id
  }))

  console.log('[CategorySelector] mapped items:', items)
  console.log('[CategorySelector] items length:', items.length)

  return items
})

// Selected categories - v-model works with full objects
const selected = computed({
  get: () => {
    if (!props.multiple) {
      const id = props.modelValue[0]
      return categoryItems.value.find(item => item.value === id) || null
    }
    // For multiple, return array of full objects
    return categoryItems.value.filter(item => props.modelValue.includes(item.value))
  },
  set: (value) => {
    if (!props.multiple) {
      emit('update:modelValue', value ? [value.value] : [])
    } else {
      emit('update:modelValue', Array.isArray(value) ? value.map((v: any) => v.value) : [])
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
    <!-- Debug info -->
    <div class="text-xs text-gray-500 mb-2">
      Debug: {{ categoryItems.length }} items, loading: {{ categoryStore.loading }}
    </div>
    <USelectMenu
      v-model="selected"
      :options="categoryItems"
      :multiple="multiple"
      :placeholder="placeholder"
      :loading="categoryStore.loading"
    >
      <template #label>
        <span v-if="!multiple && selected" class="flex items-center gap-2">
          <UIcon :name="(selected as any).icon" class="w-4 h-4" :style="{ color: (selected as any).color }" />
          <span>{{ (selected as any).label }}</span>
        </span>
        <div v-else-if="multiple && Array.isArray(selected) && selected.length > 0" class="flex items-center gap-1 flex-wrap">
          <span
            v-for="cat in (selected as any[]).slice(0, 3)"
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
          <span v-if="(selected as any[]).length > 3" class="text-xs text-gray-500">
            +{{ (selected as any[]).length - 3 }} more
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
