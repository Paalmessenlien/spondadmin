<template>
  <div class="space-y-3">
    <div v-for="grp in groups" :key="grp.group">
      <p class="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">{{ grp.group }}</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-1">
        <label
          v-for="m in grp.modules"
          :key="m.key"
          class="flex items-center space-x-2 rounded-md px-2 py-1.5 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700/50"
        >
          <input
            type="checkbox"
            :checked="selected.includes(m.key)"
            class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
            @change="$emit('toggle', m.key)"
          />
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ m.label }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * A grouped grid of module checkboxes. Controlled: the parent owns the
 * selected array and mutates it in response to `toggle` events. Used by both
 * the role/group editors (settings/access) and the per-user override editor.
 */
interface ModuleDef { key: string; label: string; group: string }
defineProps<{
  groups: { group: string; modules: ModuleDef[] }[]
  selected: string[]
}>()
defineEmits<{ (e: 'toggle', key: string): void }>()
</script>
