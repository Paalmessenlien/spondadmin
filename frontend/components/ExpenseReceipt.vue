<template>
  <a
    v-if="objectUrl"
    :href="objectUrl"
    target="_blank"
    rel="noopener"
    class="block"
    :title="attachment.filename"
  >
    <img
      v-if="isImage"
      :src="objectUrl"
      :class="thumb
        ? 'w-full h-28 object-cover rounded border border-gray-200 dark:border-gray-800'
        : 'w-12 h-12 object-cover rounded'"
    />
    <div
      v-else
      :class="thumb
        ? 'w-full h-28 flex flex-col items-center justify-center gap-1 rounded border border-gray-200 dark:border-gray-800'
        : 'flex items-center gap-2'"
    >
      <UIcon name="i-heroicons-document" :class="thumb ? 'w-8 h-8 text-gray-400' : 'w-10 h-10 text-gray-400'" />
      <span class="text-xs text-gray-500 truncate max-w-full px-1">{{ attachment.filename }}</span>
    </div>
  </a>

  <!-- Loading / error placeholder -->
  <div
    v-else
    :class="thumb
      ? 'w-full h-28 flex items-center justify-center rounded border border-gray-200 dark:border-gray-800'
      : 'w-12 h-12 flex items-center justify-center rounded border border-gray-200 dark:border-gray-800'"
  >
    <UIcon
      :name="failed ? 'i-heroicons-exclamation-triangle' : 'i-heroicons-arrow-path'"
      :class="['w-5 h-5', failed ? 'text-amber-500' : 'text-gray-400 animate-spin']"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * Renders a receipt attachment. Receipts aren't public — we fetch the bytes
 * with the user's auth token and expose them via an object URL for the <img>
 * and the "open in new tab" link.
 */
const props = withDefaults(defineProps<{
  expenseId: number
  attachment: { id: number; filename: string; content_type?: string | null }
  thumb?: boolean
}>(), { thumb: true })

const api = useApi()
const objectUrl = ref<string | null>(null)
const failed = ref(false)

const isImage = computed(() => (props.attachment.content_type || '').startsWith('image/'))

onMounted(async () => {
  try {
    const blob = await api.fetchExpenseAttachmentFile(props.expenseId, props.attachment.id)
    objectUrl.value = URL.createObjectURL(blob)
  } catch {
    failed.value = true
  }
})

onBeforeUnmount(() => {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
})
</script>
