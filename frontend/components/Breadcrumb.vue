<template>
  <nav aria-label="Breadcrumb" class="mb-4">
    <ol class="flex items-center space-x-2 text-sm">
      <li v-for="(item, index) in items" :key="index" class="flex items-center">
        <NuxtLink
          v-if="item.to && index < items.length - 1"
          :to="item.to"
          class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
        >
          {{ item.label }}
        </NuxtLink>
        <span
          v-else
          class="text-gray-900 dark:text-white font-medium"
          :aria-current="index === items.length - 1 ? 'page' : undefined"
        >
          {{ item.label }}
        </span>
        <UIcon
          v-if="index < items.length - 1"
          name="i-heroicons-chevron-right"
          class="h-4 w-4 mx-2 text-gray-400"
        />
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
interface BreadcrumbItem {
  label: string
  to?: string
}

defineProps<{
  items: BreadcrumbItem[]
}>()
</script>
