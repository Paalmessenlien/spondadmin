<template>
  <div class="space-y-6">
    <Breadcrumb :items="[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Prosjekter' }]" />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Prosjekter</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Prosjekter og arbeidsoppgaver for klubben
        </p>
      </div>
      <div v-if="canEdit" class="flex items-center gap-2">
        <UButton
          color="neutral"
          variant="outline"
          icon="i-heroicons-arrow-up-tray"
          :loading="importing"
          @click="fileInput?.click()"
        >
          Importer fra Plane
        </UButton>
        <UButton color="primary" icon="i-heroicons-plus" @click="openCreate">Nytt prosjekt</UButton>
      </div>
      <input ref="fileInput" type="file" accept="application/json,.json" class="hidden" @change="onImportFile" />
    </div>

    <!-- Import result details (dangling relations / missing parents / warnings) -->
    <UCard v-if="importResult && importResultHasNotes">
      <div class="flex items-start justify-between gap-3">
        <div class="space-y-3 min-w-0">
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-exclamation-triangle" class="w-5 h-5 text-amber-500 shrink-0" />
            <h2 class="text-base font-semibold text-gray-900 dark:text-white">
              Import fullført med merknader
            </h2>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ importResult.items_created }} nye og {{ importResult.items_updated }} oppdaterte saker.
          </p>
          <div v-if="importResult.dangling_relations?.length" class="text-sm">
            <p class="font-medium text-gray-700 dark:text-gray-300">
              Relasjoner til saker utenfor eksporten ({{ importResult.dangling_relations.length }}):
            </p>
            <p class="text-gray-500 dark:text-gray-400 break-words">
              {{ importResult.dangling_relations.join(', ') }}
            </p>
          </div>
          <div v-if="importResult.parents_missing?.length" class="text-sm">
            <p class="font-medium text-gray-700 dark:text-gray-300">
              Overordnede saker som ikke ble funnet ({{ importResult.parents_missing.length }}):
            </p>
            <p class="text-gray-500 dark:text-gray-400 break-words">
              {{ importResult.parents_missing.join(', ') }}
            </p>
          </div>
          <div v-if="importResult.people_unmatched?.length" class="text-sm">
            <p class="font-medium text-gray-700 dark:text-gray-300">
              Personer uten treff i medlemsregisteret ({{ importResult.people_unmatched.length }}):
            </p>
            <p class="text-gray-500 dark:text-gray-400 break-words">
              {{ importResult.people_unmatched.join(', ') }}
            </p>
          </div>
          <div v-if="importResult.warnings?.length" class="text-sm">
            <p class="font-medium text-gray-700 dark:text-gray-300">
              Advarsler ({{ importResult.warnings.length }}):
            </p>
            <ul class="list-disc list-inside text-gray-500 dark:text-gray-400">
              <li v-for="(w, i) in importResult.warnings" :key="i" class="break-words">{{ w }}</li>
            </ul>
          </div>
        </div>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-heroicons-x-mark"
          size="xs"
          aria-label="Lukk"
          @click="importResult = null"
        />
      </div>
    </UCard>

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <UCard v-else-if="projects.length === 0" class="text-center py-12">
      <UIcon name="i-heroicons-rectangle-stack" class="w-12 h-12 mx-auto mb-3 text-gray-300" />
      <p class="text-gray-500 mb-4">Ingen prosjekter ennå. Opprett et prosjekt eller importer fra Plane.</p>
      <UButton v-if="canEdit" color="primary" icon="i-heroicons-plus" @click="openCreate">
        Opprett ditt første prosjekt
      </UButton>
    </UCard>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard
        v-for="p in projects"
        :key="p.id"
        class="hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer"
        @click="navigateTo(`/dashboard/projects/${p.id}`)"
      >
        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <UBadge color="neutral" variant="subtle" class="font-mono">{{ p.identifier }}</UBadge>
            <UBadge v-if="p.is_archived" color="warning" variant="subtle">Arkivert</UBadge>
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white truncate">{{ p.name }}</h2>
            <p v-if="p.description" class="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
              {{ p.description }}
            </p>
          </div>
          <div>
            <div class="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
              <div
                class="h-2.5 rounded-full bg-green-500 transition-all"
                :style="{ width: `${progressPct(p)}%` }"
              />
            </div>
            <p class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
              {{ p.completed_items }} av {{ p.total_items }} saker fullført
            </p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Create project modal -->
    <UModal v-model:open="createOpen" :ui="{ content: 'max-w-xl' }">
      <template #content>
        <div class="p-6 space-y-4 max-h-[85vh] overflow-y-auto">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">Nytt prosjekt</h2>

          <UFormField label="Navn" required>
            <UInput v-model="form.name" placeholder="F.eks. Styret" class="w-full" :ui="{ base: 'w-full' }" />
          </UFormField>

          <UFormField label="Prosjekt-ID" required hint="2–12 store bokstaver, f.eks. STYRE">
            <UInput
              v-model="form.identifier"
              placeholder="STYRE"
              class="w-full font-mono"
              :ui="{ base: 'w-full' }"
              maxlength="12"
              @input="normalizeIdentifier"
            />
          </UFormField>

          <UFormField label="Beskrivelse">
            <UTextarea
              v-model="form.description"
              :rows="3"
              placeholder="Hva handler prosjektet om?"
              class="w-full"
              :ui="{ base: 'w-full' }"
            />
          </UFormField>

          <div v-if="formError" class="text-sm text-red-600 dark:text-red-400">
            {{ formError }}
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <UButton color="neutral" variant="ghost" @click="createOpen = false">Avbryt</UButton>
            <UButton color="primary" :loading="saving" @click="save">Lagre</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const { canEdit } = usePermissions()

const projects = ref<any[]>([])
const loading = ref(true)
const fileInput = ref<HTMLInputElement | null>(null)
const importing = ref(false)
const importResult = ref<any | null>(null)

const createOpen = ref(false)
const saving = ref(false)
const formError = ref('')
const form = ref({ name: '', identifier: '', description: '' })

const load = async () => {
  loading.value = true
  try {
    const data: any = await api.getProjects()
    projects.value = data.items || []
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loading.value = false
  }
}

const progressPct = (p: any) => {
  if (!p.total_items) return 0
  return Math.round((p.completed_items / p.total_items) * 100)
}

const importResultHasNotes = computed(() => {
  const r = importResult.value
  if (!r) return false
  return Boolean(
    r.dangling_relations?.length || r.parents_missing?.length ||
    r.people_unmatched?.length || r.warnings?.length
  )
})

const onImportFile = async (ev: Event) => {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const parsed = JSON.parse(await file.text())
    if (!Array.isArray(parsed) || !parsed[0]?.project_identifier) {
      throw new Error('Ugyldig Plane-eksportfil')
    }
    importing.value = true
    const res: any = await api.importPlaneProjects(parsed)
    importResult.value = res
    toast.add({
      title: 'Import fullført',
      description: `${res.items_created} nye og ${res.items_updated} oppdaterte saker`,
      color: 'success',
    })
    await load()
  } catch (err: any) {
    toast.add({
      title: 'Import feilet',
      description: err?.data?.detail || err?.message || 'Ugyldig fil',
      color: 'error',
    })
  } finally {
    importing.value = false
    input.value = ''
  }
}

const openCreate = () => {
  form.value = { name: '', identifier: '', description: '' }
  formError.value = ''
  createOpen.value = true
}

const normalizeIdentifier = () => {
  form.value.identifier = form.value.identifier
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 12)
}

const save = async () => {
  formError.value = ''
  if (!form.value.name.trim()) {
    formError.value = 'Navn er påkrevd'
    return
  }
  if (!/^[A-Z0-9]{2,12}$/.test(form.value.identifier)) {
    formError.value = 'Prosjekt-ID må være 2–12 store bokstaver eller tall'
    return
  }
  saving.value = true
  try {
    const created: any = await api.createProject({
      name: form.value.name.trim(),
      identifier: form.value.identifier,
      description: form.value.description.trim() || null,
    })
    toast.add({ title: 'Prosjekt opprettet', color: 'success' })
    createOpen.value = false
    navigateTo(`/dashboard/projects/${created.id}`)
  } catch (err: any) {
    formError.value = err?.data?.detail || 'Kunne ikke opprette prosjektet'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
