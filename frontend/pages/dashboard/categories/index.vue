<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const categoryStore = useCategoryStore()
const toast = useToast()

onMounted(() => categoryStore.fetchCategories(false))

const handleDelete = async (id: number) => {
  if (!confirm('Delete this category? Events will be uncategorized.')) return
  try {
    await categoryStore.deleteCategory(id)
    toast.add({ title: 'Success', description: 'Category deleted', color: 'green' })
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}

const handleBulkCategorize = async () => {
  try {
    const result = await categoryStore.bulkCategorizeEvents({ force_recategorize: false })
    toast.add({ title: 'Success', description: `Categorized ${result.categorized} events`, color: 'green' })
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}
</script>

<template>
  <div class="p-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Categories' }
    ]" />

    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">Event Categories</h1>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" @click="handleBulkCategorize" variant="soft">
          Re-categorize Events
        </UButton>
        <UButton icon="i-heroicons-plus" to="/dashboard/categories/create">
          New Category
        </UButton>
      </div>
    </div>

    <div v-if="categoryStore.loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard v-for="category in categoryStore.sortedCategories" :key="category.id" class="hover:shadow-lg transition">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center" :style="{ backgroundColor: `${category.color}20` }">
              <UIcon :name="category.icon" class="w-6 h-6" :style="{ color: category.color }" />
            </div>
            <div class="flex-1">
              <h3 class="font-semibold">{{ category.name }}</h3>
              <p class="text-xs text-gray-500">Priority: {{ category.priority }}</p>
            </div>
          </div>
        </template>

        <div class="space-y-2">
          <p v-if="category.description" class="text-sm text-gray-600 dark:text-gray-400">
            {{ category.description }}
          </p>
          <div class="flex gap-2">
            <UBadge :color="category.is_active ? 'green' : 'gray'" size="xs">
              {{ category.is_active ? 'Active' : 'Inactive' }}
            </UBadge>
            <UBadge v-if="category.is_default" color="blue" size="xs">Default</UBadge>
          </div>
          <p class="text-xs text-gray-500">
            {{ category.pattern_rules.patterns.length }} pattern(s)
          </p>
        </div>

        <template #footer>
          <div class="flex justify-between">
            <UButton :to="`/dashboard/categories/${category.id}`" size="xs" variant="soft">
              Edit
            </UButton>
            <UButton
              v-if="!category.is_default"
              icon="i-heroicons-trash"
              size="xs"
              color="red"
              variant="ghost"
              @click="handleDelete(category.id)"
            />
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
