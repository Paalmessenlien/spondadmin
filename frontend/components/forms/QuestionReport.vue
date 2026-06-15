<template>
  <UCard>
    <div class="flex items-start justify-between gap-3 mb-3">
      <h3 class="font-semibold text-gray-900 dark:text-white">{{ question.label }}</h3>
      <span class="text-xs text-gray-500 whitespace-nowrap">{{ question.answered_count }} svar</span>
    </div>

    <!-- Choice / yes-no: horizontal bars -->
    <div v-if="bars.length" class="space-y-2">
      <div v-for="bar in bars" :key="bar.label">
        <div class="flex justify-between text-sm mb-0.5">
          <span class="text-gray-700 dark:text-gray-300">{{ bar.label }}</span>
          <span class="text-gray-500">{{ bar.count }} · {{ bar.pct }}%</span>
        </div>
        <div class="h-2.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
          <div class="h-full rounded-full bg-primary-500 transition-all" :style="{ width: bar.pct + '%' }" />
        </div>
      </div>
    </div>

    <!-- Scale / number: stats + distribution -->
    <div v-else-if="isNumeric" class="space-y-3">
      <div class="flex gap-4 text-sm">
        <div><span class="text-gray-500">Snitt:</span> <span class="font-semibold">{{ fmt(question.summary.avg) }}</span></div>
        <div><span class="text-gray-500">Min:</span> {{ fmt(question.summary.min) }}</div>
        <div><span class="text-gray-500">Maks:</span> {{ fmt(question.summary.max) }}</div>
      </div>
      <div v-if="distBars.length" class="space-y-1.5">
        <div v-for="d in distBars" :key="d.label" class="flex items-center gap-2">
          <span class="w-8 text-sm text-gray-600 text-right">{{ d.label }}</span>
          <div class="flex-1 h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
            <div class="h-full bg-primary-400" :style="{ width: d.pct + '%' }" />
          </div>
          <span class="w-8 text-xs text-gray-500">{{ d.count }}</span>
        </div>
      </div>
    </div>

    <!-- Free text: sample list -->
    <div v-else-if="samples.length" class="space-y-2 max-h-72 overflow-y-auto">
      <div v-for="(s, i) in samples" :key="i"
        class="text-sm text-gray-700 dark:text-gray-300 border-l-2 border-gray-200 dark:border-gray-700 pl-3 py-0.5">
        {{ s }}
      </div>
    </div>

    <p v-else class="text-sm text-gray-400">Ingen svar ennå.</p>
  </UCard>
</template>

<script setup lang="ts">
const props = defineProps<{ question: any }>()

const fmt = (n: any) => (n == null ? '—' : n)

const bars = computed(() => {
  const s = props.question.summary || {}
  if (Array.isArray(s.options)) {
    return s.options.map((o: any) => ({ label: o.label, count: o.count, pct: o.pct }))
  }
  if ('ja' in s || 'nei' in s) {
    const total = (s.ja || 0) + (s.nei || 0)
    const pct = (n: number) => (total ? Math.round((1000 * n) / total) / 10 : 0)
    return [
      { label: 'Ja', count: s.ja || 0, pct: pct(s.ja || 0) },
      { label: 'Nei', count: s.nei || 0, pct: pct(s.nei || 0) },
    ]
  }
  return []
})

const isNumeric = computed(() => ['skala', 'tall'].includes(props.question.field_type))

const distBars = computed(() => {
  const dist = props.question.summary?.distribution || {}
  const entries = Object.entries(dist) as [string, number][]
  if (!entries.length) return []
  // Sort numerically by key when possible.
  entries.sort((a, b) => Number(a[0]) - Number(b[0]))
  const max = Math.max(...entries.map(([, c]) => c))
  return entries.map(([label, count]) => ({ label, count, pct: max ? Math.round((100 * count) / max) : 0 }))
})

const samples = computed<string[]>(() => props.question.summary?.samples || [])
</script>
