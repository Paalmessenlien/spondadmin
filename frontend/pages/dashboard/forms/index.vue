<template>
  <div class="space-y-6">
    <Breadcrumb :items="[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Skjema' }]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Skjema</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Lag spørreskjemaer og samle inn svar — fra innloggede medlemmer eller anonymt
        </p>
      </div>
      <div class="flex items-center gap-2">
        <UButton color="neutral" variant="outline" icon="i-heroicons-arrow-up-tray" @click="fileInput?.click()">Importer</UButton>
        <UButton color="primary" icon="i-heroicons-plus" to="/dashboard/forms/new">Nytt skjema</UButton>
      </div>
      <input ref="fileInput" type="file" accept="application/json,.json" class="hidden" @change="onImportFile" />
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <UCard v-else-if="forms.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-clipboard-document-list" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-500 mb-4">Ingen skjemaer ennå.</p>
      <UButton color="primary" icon="i-heroicons-plus" to="/dashboard/forms/new">Lag ditt første skjema</UButton>
    </UCard>

    <div v-else class="space-y-3">
      <UCard v-for="f in forms" :key="f.id" class="hover:border-primary-300 dark:hover:border-primary-700 transition-colors">
        <div class="flex flex-col sm:flex-row sm:items-center gap-4">
          <div class="flex-1 min-w-0 cursor-pointer" @click="openForm(f)">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-lg font-semibold text-gray-900 dark:text-white truncate">{{ f.title }}</span>
              <UBadge :color="statusMeta(f.status).color" :icon="statusMeta(f.status).icon" variant="subtle">
                {{ statusMeta(f.status).label }}
              </UBadge>
            </div>
            <div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-queue-list" class="w-4 h-4" />{{ f.field_count }} spørsmål
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-chat-bubble-left-right" class="w-4 h-4" />{{ f.response_count }} svar
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-lock-open" class="w-4 h-4" />{{ accessLabel(f.access_mode) }}
              </span>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
            <UButton size="sm" color="neutral" variant="outline" icon="i-heroicons-chart-bar"
              :to="`/dashboard/forms/${f.id}/responses`">Svar</UButton>
            <UButton size="sm" color="neutral" variant="outline" icon="i-heroicons-pencil-square"
              :to="`/dashboard/forms/${f.id}/edit`">Rediger</UButton>
            <UButton size="sm" color="neutral" variant="ghost" icon="i-heroicons-link"
              title="Kopier delingslenke" @click="copyLink(f)" />
            <UButton size="sm" color="neutral" variant="ghost" icon="i-heroicons-document-duplicate"
              title="Dupliser" @click="duplicate(f)" />
            <UButton size="sm" color="neutral" variant="ghost" icon="i-heroicons-arrow-down-tray"
              title="Eksporter (.json)" @click="exportOne(f)" />
            <UButton size="sm" color="error" variant="ghost" icon="i-heroicons-trash"
              title="Slett" @click="remove(f)" />
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const { statusMeta, accessLabel, publicFormUrl } = useForms()

const forms = ref<any[]>([])
const loading = ref(true)
const fileInput = ref<HTMLInputElement | null>(null)

const load = async () => {
  loading.value = true
  try {
    const data: any = await api.getForms()
    forms.value = data.forms || []
  } catch (err) {
    console.error('Failed to load forms:', err)
  } finally {
    loading.value = false
  }
}

const openForm = (f: any) => navigateTo(`/dashboard/forms/${f.id}/edit`)

const copyLink = async (f: any) => {
  const url = publicFormUrl(f.slug)
  try {
    await navigator.clipboard.writeText(url)
    toast.add({ title: 'Lenke kopiert', description: url, color: 'success' })
  } catch {
    toast.add({ title: 'Kopier lenken', description: url })
  }
}

const duplicate = async (f: any) => {
  try {
    await api.duplicateForm(f.id)
    toast.add({ title: 'Skjema duplisert', color: 'success' })
    load()
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke duplisere', description: err?.data?.detail, color: 'error' })
  }
}

const remove = async (f: any) => {
  if (!confirm(`Slette «${f.title}» og alle svar? Dette kan ikke angres.`)) return
  try {
    await api.deleteForm(f.id)
    toast.add({ title: 'Skjema slettet', color: 'success' })
    load()
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke slette', description: err?.data?.detail, color: 'error' })
  }
}

const exportOne = async (f: any) => {
  try {
    const def: any = await api.exportForm(f.id)
    const blob = new Blob([JSON.stringify(def, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${f.slug || 'skjema'}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    toast.add({ title: 'Eksport feilet', description: err?.data?.detail, color: 'error' })
  }
}

const onImportFile = async (ev: Event) => {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const parsed = JSON.parse(await file.text())
    if (parsed?._type && parsed._type !== 'spondadmin.form') throw new Error('Ukjent filformat')
    const form: any = await api.importForm({
      title: parsed.title || file.name.replace(/\.json$/i, '') || 'Importert skjema',
      description: parsed.description ?? null,
      access_mode: parsed.access_mode || 'begge',
      one_response_per_user: !!parsed.one_response_per_user,
      settings: parsed.settings ?? null,
      fields: Array.isArray(parsed.fields) ? parsed.fields : [],
    })
    toast.add({ title: 'Skjema importert', color: 'success' })
    navigateTo(`/dashboard/forms/${form.id}/edit`)
  } catch (err: any) {
    toast.add({ title: 'Import feilet', description: err?.data?.detail || err?.message || 'Ugyldig fil', color: 'error' })
  } finally {
    input.value = ''
  }
}

onMounted(load)
</script>
