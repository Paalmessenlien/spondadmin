<template>
  <UCard
    :ui="{ body: 'p-3 sm:p-3' }"
    class="cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
    @click="emit('open', item)"
  >
    <div class="space-y-2">
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="text-xs font-mono text-gray-500 dark:text-gray-400 truncate">{{ item.identifier }}</span>
          <UIcon
            v-if="item.priority && item.priority !== 'none'"
            :name="priorityMeta(item.priority).icon"
            class="w-3.5 h-3.5 shrink-0"
            :class="priorityIconClass"
          />
        </div>
        <!-- State dot: editors get a dropdown to move the card between columns -->
        <UDropdownMenu v-if="canEdit && stateItems.length" :items="stateItems">
          <button
            type="button"
            class="flex items-center gap-1 shrink-0 rounded p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800"
            :title="item.state?.name || 'Endre status'"
            @click.stop
          >
            <span
              class="w-2.5 h-2.5 rounded-full"
              :style="{ backgroundColor: item.state?.color || '#9CA3AF' }"
            />
            <UIcon name="i-heroicons-chevron-down" class="w-3 h-3 text-gray-400" />
          </button>
        </UDropdownMenu>
        <span
          v-else
          class="w-2.5 h-2.5 rounded-full shrink-0"
          :style="{ backgroundColor: item.state?.color || '#9CA3AF' }"
          :title="item.state?.name"
        />
      </div>

      <p class="text-sm font-medium text-gray-900 dark:text-white line-clamp-2">{{ item.name }}</p>

      <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
        <span v-for="l in visibleLabels" :key="l.id" class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: l.color || '#6B7280' }" />
          {{ l.name }}
        </span>
        <span v-if="hiddenLabelCount > 0">+{{ hiddenLabelCount }}</span>
        <span
          v-if="item.target_date"
          class="flex items-center gap-1"
          :class="isOverdue ? 'text-red-600 dark:text-red-400 font-medium' : ''"
        >
          <UIcon name="i-heroicons-calendar" class="w-3.5 h-3.5" />
          {{ formatDate(item.target_date) }}
        </span>
        <span v-if="item.sub_item_count" class="flex items-center gap-1">
          <UIcon name="i-heroicons-squares-2x2" class="w-3.5 h-3.5" />{{ item.sub_item_count }}
        </span>
        <span v-if="item.comment_count" class="flex items-center gap-1">
          <UIcon name="i-heroicons-chat-bubble-left" class="w-3.5 h-3.5" />{{ item.comment_count }}
        </span>
        <span v-if="item.assignees?.length" class="flex -space-x-1 ml-auto">
          <UAvatar
            v-for="a in item.assignees.slice(0, 3)"
            :key="a.id"
            :alt="a.display_name"
            size="3xs"
          />
          <span
            v-if="item.assignees.length > 3"
            class="flex items-center justify-center w-4 h-4 rounded-full bg-gray-200 dark:bg-gray-700 text-[10px]"
          >
            +{{ item.assignees.length - 3 }}
          </span>
        </span>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
const props = defineProps<{
  item: any
  project: any
}>()

const emit = defineEmits<{
  (e: 'open', item: any): void
  (e: 'change-state', item: any, stateId: number): void
}>()

const { canEdit } = usePermissions()

// Badge-color token → tailwind text class (for the priority icon).
const ICON_TEXT_CLASS: Record<string, string> = {
  neutral: 'text-gray-400',
  info: 'text-blue-500',
  warning: 'text-amber-500',
  error: 'text-red-500',
  success: 'text-green-500',
  primary: 'text-blue-500',
}

const priorityIconClass = computed(
  () => ICON_TEXT_CLASS[priorityMeta(props.item.priority).color] || 'text-gray-400'
)

const stateItems = computed(() =>
  (props.project?.states || []).map((s: any) => ({
    label: s.name,
    onSelect: () => emit('change-state', props.item, s.id),
  }))
)

const visibleLabels = computed(() => (props.item.labels || []).slice(0, 3))
const hiddenLabelCount = computed(() => Math.max(0, (props.item.labels || []).length - 3))

const isOverdue = computed(() => {
  if (!props.item.target_date || props.item.state?.group === 'completed') return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return new Date(props.item.target_date) < today
})

const formatDate = (d: string) => new Date(d).toLocaleDateString('nb-NO')
</script>
