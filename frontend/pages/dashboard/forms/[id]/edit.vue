<template>
  <div class="space-y-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Skjema', to: '/dashboard/forms' },
      { label: form?.title || 'Skjema' },
    ]" />

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else-if="form">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <UIcon name="i-heroicons-clipboard-document-list" class="w-7 h-7 text-primary-500 shrink-0" />
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white truncate">{{ meta.title || 'Uten tittel' }}</h1>
          <UBadge :color="statusMeta(form.status).color" :icon="statusMeta(form.status).icon" variant="subtle">
            {{ statusMeta(form.status).label }}
          </UBadge>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <UButton color="neutral" variant="outline" icon="i-heroicons-eye" @click="previewMode = !previewMode">
            {{ previewMode ? 'Rediger' : 'Forhåndsvis' }}
          </UButton>
          <UButton color="neutral" :loading="saving" icon="i-heroicons-check" @click="saveAll">Lagre</UButton>
          <UButton v-if="form.status === 'utkast'" color="primary" icon="i-heroicons-globe-alt"
            :loading="publishing" @click="publish">Publiser</UButton>
          <UButton v-else-if="form.status === 'publisert'" color="warning" variant="soft"
            icon="i-heroicons-lock-closed" @click="closeForm">Lukk</UButton>
          <UButton v-else-if="form.status === 'lukket'" color="primary" variant="soft"
            icon="i-heroicons-globe-alt" :loading="publishing" @click="publish">Gjenåpne</UButton>
        </div>
      </div>

      <!-- Locked note for published forms -->
      <UCard v-if="form.status !== 'utkast'" class="border-amber-300 dark:border-amber-800">
        <div class="flex items-center justify-between gap-3 text-sm">
          <span class="text-amber-700 dark:text-amber-300">
            <UIcon name="i-heroicons-lock-closed" class="w-4 h-4 inline" />
            Spørsmålene er låst mens skjemaet er {{ statusMeta(form.status).label.toLowerCase() }}.
          </span>
          <UButton v-if="form.response_count === 0" size="xs" color="neutral" variant="outline"
            @click="reopen">Sett tilbake til utkast</UButton>
        </div>
      </UCard>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Builder / preview -->
        <div class="lg:col-span-2 space-y-4">
          <!-- Preview -->
          <UCard v-if="previewMode">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-heroicons-eye" class="w-5 h-5 text-gray-400" />
                <h2 class="font-semibold">Forhåndsvisning</h2>
              </div>
            </template>
            <h2 class="text-xl font-bold mb-4">{{ meta.title }}</h2>
            <FormFiller :form="previewForm" disabled submit-label="Send inn (forhåndsvisning)" />
          </UCard>

          <!-- Edit -->
          <template v-else>
            <UCard>
              <UFormField label="Tittel">
                <UInput v-model="meta.title" placeholder="Skjematittel" class="w-full" size="lg" />
              </UFormField>
              <UFormField label="Beskrivelse (valgfritt)" class="mt-3">
                <UTextarea v-model="meta.description" :rows="2" placeholder="Kort introduksjon" class="w-full" />
              </UFormField>
            </UCard>

            <div v-if="fields.length === 0" class="text-center text-sm text-gray-400 py-6">
              Ingen spørsmål ennå — legg til et felt nedenfor.
            </div>

            <FieldEditor
              v-for="(field, idx) in fields"
              :key="field._key"
              :field="field"
              :is-first="idx === 0"
              :is-last="idx === fields.length - 1"
              :class="form.status !== 'utkast' ? 'opacity-60 pointer-events-none' : ''"
              @move-up="move(idx, -1)"
              @move-down="move(idx, 1)"
              @remove="removeField(idx)"
            />

            <!-- Add-field palette -->
            <UCard v-if="form.status === 'utkast'">
              <template #header><h2 class="font-semibold text-sm text-gray-500">Legg til felt</h2></template>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <button v-for="t in FIELD_TYPES" :key="t.value" type="button"
                  class="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors text-left"
                  @click="addField(t.value)">
                  <UIcon :name="t.icon" class="w-4 h-4 text-gray-400 shrink-0" />
                  <span class="truncate">{{ t.label }}</span>
                </button>
              </div>
            </UCard>
          </template>
        </div>

        <!-- Settings -->
        <div class="space-y-4">
          <UCard>
            <template #header><h2 class="font-semibold">Tilgang</h2></template>
            <div class="space-y-2">
              <label v-for="m in ACCESS_MODE_OPTIONS" :key="m.value"
                class="flex items-start gap-2 cursor-pointer rounded-lg border px-3 py-2 transition-colors"
                :class="meta.access_mode === m.value ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-200 dark:border-gray-700'">
                <input type="radio" name="access" :value="m.value" :checked="meta.access_mode === m.value"
                  class="mt-1 accent-primary-500" @change="meta.access_mode = m.value" />
                <span>
                  <span class="block text-sm font-medium">{{ m.label }}</span>
                  <span class="block text-xs text-gray-500">{{ m.description }}</span>
                </span>
              </label>
            </div>
            <div class="flex items-center gap-2 mt-3">
              <USwitch v-model="meta.one_response_per_user" />
              <span class="text-sm text-gray-600 dark:text-gray-400">Ett svar per innlogget bruker</span>
            </div>
          </UCard>

          <!-- Share -->
          <UCard v-if="form.status === 'publisert' && form.access_mode !== 'innlogget'">
            <template #header><h2 class="font-semibold">Del</h2></template>
            <p class="text-xs text-gray-500 mb-2">Alle med lenken kan svare:</p>
            <div class="flex gap-2">
              <UInput :model-value="shareUrl" readonly size="sm" class="flex-1" />
              <UButton size="sm" color="neutral" variant="outline" icon="i-heroicons-clipboard"
                @click="copyLink" />
            </div>
            <UButton size="sm" color="neutral" variant="ghost" icon="i-heroicons-arrow-top-right-on-square"
              :to="`/f/${form.slug}`" target="_blank" class="mt-2">Åpne skjema</UButton>
          </UCard>
          <UCard v-else-if="form.status !== 'publisert'">
            <p class="text-sm text-gray-500">
              <UIcon name="i-heroicons-information-circle" class="w-4 h-4 inline" />
              Publiser skjemaet for å få en delingslenke og ta imot svar.
            </p>
          </UCard>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import FieldEditor from '~/components/forms/FieldEditor.vue'
import FormFiller from '~/components/forms/FormFiller.vue'

definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const toast = useToast()
const { statusMeta, publicFormUrl, FIELD_TYPES, ACCESS_MODE_OPTIONS } = useForms()

const formId = computed(() => parseInt(route.params.id as string))
const form = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const publishing = ref(false)
const previewMode = ref(false)

const meta = reactive({ title: '', description: '', access_mode: 'begge', one_response_per_user: false })
const fields = ref<any[]>([])
let keyCounter = 0

const shareUrl = computed(() => (form.value ? publicFormUrl(form.value.slug) : ''))

const toLocalField = (f: any) => ({
  _key: ++keyCounter,
  field_type: f.field_type,
  label: f.label || '',
  help_text: f.help_text || '',
  required: !!f.required,
  options: f.options ?? null,
  settings: f.settings ?? null,
})

const previewForm = computed(() => ({
  title: meta.title,
  description: meta.description,
  fields: fields.value.map((f, i) => ({ ...f, id: f._key, position: i })),
}))

const load = async () => {
  loading.value = true
  try {
    const data: any = await api.getForm(formId.value)
    form.value = data
    meta.title = data.title
    meta.description = data.description || ''
    meta.access_mode = data.access_mode
    meta.one_response_per_user = data.one_response_per_user
    fields.value = (data.fields || []).map(toLocalField)
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke laste skjema', description: err?.data?.detail, color: 'error' })
  } finally {
    loading.value = false
  }
}

const addField = (type: string) => {
  fields.value.push(toLocalField({ field_type: type, label: '', required: false }))
}
const removeField = (idx: number) => fields.value.splice(idx, 1)
const move = (idx: number, dir: number) => {
  const j = idx + dir
  if (j < 0 || j >= fields.value.length) return
  const arr = fields.value
  ;[arr[idx], arr[j]] = [arr[j], arr[idx]]
}

const cleanFields = () =>
  fields.value.map((f) => ({
    field_type: f.field_type,
    label: f.label || (f.field_type === 'overskrift' ? 'Seksjon' : 'Spørsmål'),
    help_text: f.help_text || null,
    required: !!f.required,
    options: f.options ?? null,
    settings: f.settings ?? null,
  }))

const saveMeta = async () =>
  api.updateForm(formId.value, {
    title: meta.title || 'Nytt skjema',
    description: meta.description || null,
    access_mode: meta.access_mode,
    one_response_per_user: meta.one_response_per_user,
  })

const saveAll = async () => {
  saving.value = true
  try {
    await saveMeta()
    // Fields can only be saved while a draft.
    if (form.value.status === 'utkast') {
      form.value = await api.saveFormFields(formId.value, cleanFields())
    } else {
      form.value = await api.getForm(formId.value)
    }
    toast.add({ title: 'Lagret', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke lagre', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    saving.value = false
  }
}

const publish = async () => {
  publishing.value = true
  try {
    await saveMeta()
    if (form.value.status === 'utkast') {
      await api.saveFormFields(formId.value, cleanFields())
    }
    form.value = await api.publishForm(formId.value)
    toast.add({ title: 'Skjema publisert', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke publisere', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    publishing.value = false
  }
}

const closeForm = async () => {
  try {
    form.value = await api.closeForm(formId.value)
    toast.add({ title: 'Skjema lukket', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke lukke', description: err?.data?.detail, color: 'error' })
  }
}

const reopen = async () => {
  try {
    form.value = await api.reopenForm(formId.value)
    fields.value = (form.value.fields || []).map(toLocalField)
    toast.add({ title: 'Satt tilbake til utkast', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke endre', description: err?.data?.detail, color: 'error' })
  }
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    toast.add({ title: 'Lenke kopiert', color: 'success' })
  } catch {
    toast.add({ title: shareUrl.value })
  }
}

onMounted(load)
</script>
