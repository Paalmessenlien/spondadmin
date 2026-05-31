<template>
  <div>
    <!-- Desktop: real table (md and up) -->
    <div class="hidden md:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th
              v-for="col in columns"
              :key="col.key"
              class="py-2 px-2 font-medium text-gray-500 select-none"
              :class="[alignClass(col), col.sortable ? 'cursor-pointer' : '']"
              @click="col.sortable && emit('sort', col.key)"
            >
              {{ col.label }}
              <span v-if="col.sortable && sortField === col.key">{{ sortDesc ? '▾' : '▴' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, i) in rows"
            :key="row[rowKey] ?? i"
            class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
          >
            <td v-for="col in columns" :key="col.key" class="py-2 px-2" :class="alignClass(col)">
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ row[col.key] }}</slot>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td :colspan="columns.length" class="py-6 text-center text-gray-500">{{ emptyText }}</td>
          </tr>
        </tbody>
        <tfoot v-if="hasFooter">
          <tr class="border-t-2 border-gray-200 dark:border-gray-700 font-semibold">
            <td v-for="col in columns" :key="col.key" class="py-2 px-2" :class="alignClass(col)">
              <slot :name="`foot-${col.key}`" />
            </td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Mobile: one card per row (below md) -->
    <div class="md:hidden space-y-2">
      <div v-if="!rows.length" class="py-6 text-center text-gray-500 text-sm">{{ emptyText }}</div>
      <div
        v-for="(row, i) in rows"
        :key="row[rowKey] ?? i"
        class="rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-1.5"
      >
        <div v-if="primaryCol" class="font-semibold text-gray-900 dark:text-white break-words">
          <slot name="card-title" :row="row">
            <slot :name="`cell-${primaryCol.key}`" :row="row" :value="row[primaryCol.key]">{{ row[primaryCol.key] }}</slot>
          </slot>
        </div>
        <dl v-if="cardRows.length" class="space-y-1">
          <div
            v-for="col in cardRows"
            :key="col.key"
            class="flex items-baseline justify-between gap-3 text-sm"
          >
            <dt class="text-gray-500 shrink-0">{{ col.label }}</dt>
            <dd class="text-gray-900 dark:text-white text-right min-w-0 break-words">
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ row[col.key] }}</slot>
            </dd>
          </div>
        </dl>
        <div v-if="actionCols.length" class="flex flex-wrap gap-1 pt-1">
          <template v-for="col in actionCols" :key="col.key">
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]" />
          </template>
        </div>
      </div>
      <!-- Mobile totals summary (mirrors the desktop tfoot) -->
      <div
        v-if="hasFooter && rows.length"
        class="rounded-lg border-2 border-gray-200 dark:border-gray-700 p-3 font-semibold"
      >
        <dl class="space-y-1">
          <div v-for="col in footerCols" :key="col.key" class="flex items-baseline justify-between gap-3 text-sm">
            <dt class="text-gray-500">{{ col.label }}</dt>
            <dd class="text-right"><slot :name="`foot-${col.key}`" /></dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ResponsiveTable — a real <table> on md+, a stacked card list below md.
 *
 * Pass `columns` (with one `primary: true` column used as each card's heading)
 * and `rows`. Custom cells go through `#cell-<key>="{ row, value }"` slots and
 * are reused in both layouts, so links / badges / status colours / action
 * buttons render identically. Totals use `#foot-<key>` slots (rendered as a
 * desktop <tfoot> row and a mobile summary card). Wire sorting by passing
 * `sortField`/`sortDesc` and handling `@sort` (e.g. via useTableState).
 *
 * Column flags: `align` ('right' for numbers), `sortable`, `primary` (card
 * title), `hideOnCard` (omit from the card body), `isAction` (render at the
 * card's bottom as a full-width button row, no label).
 */
interface Column {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  sortable?: boolean
  primary?: boolean
  hideOnCard?: boolean
  isAction?: boolean
}

const props = withDefaults(
  defineProps<{
    columns: Column[]
    rows: any[]
    rowKey?: string
    sortField?: string | null
    sortDesc?: boolean
    emptyText?: string
  }>(),
  { rowKey: 'id', sortField: null, sortDesc: true, emptyText: 'No data.' }
)

const emit = defineEmits<{ (e: 'sort', key: string): void }>()
const slots = useSlots()

const primaryCol = computed(() => props.columns.find(c => c.primary) ?? props.columns[0])
const cardRows = computed(() =>
  props.columns.filter(c => c !== primaryCol.value && !c.isAction && !c.hideOnCard)
)
const actionCols = computed(() => props.columns.filter(c => c.isAction))
const hasFooter = computed(() => Object.keys(slots).some(k => k.startsWith('foot-')))
const footerCols = computed(() => props.columns.filter(c => !!slots[`foot-${c.key}`]))

const alignClass = (col: Column) =>
  col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
</script>
