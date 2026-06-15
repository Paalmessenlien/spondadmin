<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Skjema', to: '/dashboard/forms' },
      { label: 'Nytt skjema' },
    ]" />

    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Nytt skjema</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">Start fra bunnen, velg en mal, eller importer et skjema.</p>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Blank -->
      <button type="button" :disabled="busy"
        class="text-left rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-700 p-5 hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors disabled:opacity-50"
        @click="startBlank">
        <UIcon name="i-heroicons-plus" class="w-7 h-7 text-primary-500 mb-2" />
        <div class="font-semibold text-gray-900 dark:text-white">Tomt skjema</div>
        <div class="text-sm text-gray-500 mt-1">Bygg fra bunnen av.</div>
      </button>

      <!-- Import -->
      <button type="button" :disabled="busy"
        class="text-left rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-700 p-5 hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors disabled:opacity-50"
        @click="fileInput?.click()">
        <UIcon name="i-heroicons-arrow-up-tray" class="w-7 h-7 text-primary-500 mb-2" />
        <div class="font-semibold text-gray-900 dark:text-white">Importer skjema</div>
        <div class="text-sm text-gray-500 mt-1">Last opp en .json-fil eksportert fra et skjema.</div>
      </button>
      <input ref="fileInput" type="file" accept="application/json,.json" class="hidden" @change="onImportFile" />

      <!-- Templates -->
      <button v-for="t in templates" :key="t.key" type="button" :disabled="busy"
        class="text-left rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:border-primary-400 hover:shadow-sm transition-all disabled:opacity-50"
        @click="startFromTemplate(t.key)">
        <UIcon name="i-heroicons-document-duplicate" class="w-7 h-7 text-gray-400 mb-2" />
        <div class="font-semibold text-gray-900 dark:text-white">{{ t.title }}</div>
        <div class="text-sm text-gray-500 mt-1">{{ t.description }}</div>
        <div class="text-xs text-gray-400 mt-2">{{ t.field_count }} spørsmål</div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()

const templates = ref<any[]>([])
const loading = ref(true)
const busy = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

onMounted(async () => {
  try {
    const data: any = await api.getFormTemplates()
    templates.value = data.templates || []
  } catch {
    // Templates are optional; the blank/import options still work.
  } finally {
    loading.value = false
  }
})

const goToBuilder = (form: any) => navigateTo(`/dashboard/forms/${form.id}/edit`)

const startBlank = async () => {
  busy.value = true
  try {
    goToBuilder(await api.createForm({ title: 'Nytt skjema' }))
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke opprette skjema', description: err?.data?.detail, color: 'error' })
    busy.value = false
  }
}

const startFromTemplate = async (key: string) => {
  busy.value = true
  try {
    goToBuilder(await api.createFormFromTemplate(key))
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke bruke mal', description: err?.data?.detail, color: 'error' })
    busy.value = false
  }
}

const onImportFile = async (ev: Event) => {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  busy.value = true
  try {
    const text = await file.text()
    const parsed = JSON.parse(text)
    if (parsed?._type && parsed._type !== 'spondadmin.form') {
      throw new Error('Ukjent filformat')
    }
    const payload = {
      title: parsed.title || file.name.replace(/\.json$/i, '') || 'Importert skjema',
      description: parsed.description ?? null,
      access_mode: parsed.access_mode || 'begge',
      one_response_per_user: !!parsed.one_response_per_user,
      settings: parsed.settings ?? null,
      fields: Array.isArray(parsed.fields) ? parsed.fields : [],
    }
    goToBuilder(await api.importForm(payload))
  } catch (err: any) {
    toast.add({
      title: 'Import feilet',
      description: err?.data?.detail || err?.message || 'Ugyldig skjemafil',
      color: 'error',
    })
    busy.value = false
  } finally {
    input.value = ''
  }
}
</script>
