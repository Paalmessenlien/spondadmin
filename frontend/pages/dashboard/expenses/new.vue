<template>
  <div class="space-y-6 max-w-2xl">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Utlegg', to: '/dashboard/expenses' },
      { label: 'Nytt utlegg' }
    ]" />

    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Nytt utlegg</h1>

    <!-- Receipts -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Kvitteringer</h2>
          <span class="text-xs text-gray-500">Bilde eller PDF</span>
        </div>
      </template>

      <div class="space-y-3">
        <label
          class="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 cursor-pointer hover:border-blue-400 transition-colors"
        >
          <UIcon name="i-heroicons-camera" class="w-8 h-8 text-gray-400" />
          <span class="text-sm text-gray-600 dark:text-gray-400">Ta bilde eller last opp kvittering</span>
          <input
            type="file"
            accept="image/*,application/pdf"
            capture="environment"
            multiple
            class="hidden"
            @change="onFiles"
          />
        </label>

        <div v-if="uploading" class="flex items-center gap-2 text-sm text-blue-600">
          <UIcon name="i-heroicons-arrow-path" class="w-4 h-4 animate-spin" />
          {{ ocrRunning ? 'Analyserer kvittering…' : 'Laster opp…' }}
        </div>

        <div v-for="att in attachments" :key="att.id" class="flex items-center gap-3 p-2 rounded border border-gray-200 dark:border-gray-800">
          <ExpenseReceipt v-if="expenseId" :expense-id="expenseId" :attachment="att" :thumb="false" />
          <span class="flex-1 text-sm truncate">{{ att.filename }}</span>
          <UButton size="xs" color="error" variant="ghost" icon="i-heroicons-trash" @click="removeAttachment(att.id)" />
        </div>

        <div v-if="lastSuggestion" class="flex items-center justify-between gap-2 p-3 rounded bg-blue-50 dark:bg-blue-900/20 text-sm">
          <span class="text-blue-700 dark:text-blue-300">Forslag funnet fra kvittering.</span>
          <UButton size="xs" color="info" variant="soft" @click="applySuggestion(lastSuggestion)">Bruk forslag</UButton>
        </div>
      </div>
    </UCard>

    <!-- Details -->
    <UCard>
      <template #header><h2 class="font-semibold">Detaljer</h2></template>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <UFormField label="Tittel" class="sm:col-span-2">
          <UInput v-model="form.title" placeholder="Hva gjelder utlegget?" class="w-full" />
        </UFormField>
        <UFormField label="Kategori">
          <USelectMenu v-model="selectedCategory" :items="EXPENSE_CATEGORY_OPTIONS" placeholder="Velg kategori" class="w-full" />
        </UFormField>
        <UFormField label="Beløp (NOK)">
          <UInput v-model="form.amount" type="number" step="0.01" min="0" placeholder="0.00" class="w-full" />
        </UFormField>
        <UFormField label="Dato">
          <UInput v-model="form.expense_date" type="date" class="w-full" />
        </UFormField>
        <UFormField label="Mottaker (navn)">
          <UInput v-model="form.payee_name" class="w-full" />
        </UFormField>
        <UFormField label="Kontonummer" class="sm:col-span-2">
          <UInput v-model="form.bank_account" placeholder="11 siffer" class="w-full" />
        </UFormField>
        <UFormField label="Beskrivelse" class="sm:col-span-2">
          <UTextarea v-model="form.description" :rows="3" class="w-full" />
        </UFormField>
      </div>
    </UCard>

    <div class="flex flex-col sm:flex-row gap-3 sm:justify-end">
      <UButton color="neutral" variant="outline" :loading="saving" @click="saveDraft">Lagre utkast</UButton>
      <UButton color="primary" icon="i-heroicons-paper-airplane" :loading="submitting" @click="submit">
        Send til kasserer
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()
const authStore = useAuthStore()
const { EXPENSE_CATEGORY_OPTIONS } = useExpenseMeta()

const expenseId = ref<number | null>(null)
const attachments = ref<any[]>([])
const uploading = ref(false)
const ocrRunning = ref(false)
const saving = ref(false)
const submitting = ref(false)
const lastSuggestion = ref<any>(null)

const form = reactive({
  title: '',
  amount: '' as string | number,
  expense_date: '',
  payee_name: '',
  bank_account: '',
  description: '',
})
const selectedCategory = ref<any>(null)

onMounted(async () => {
  form.payee_name = authStore.user?.full_name || ''
  // Create the draft up front so receipt uploads have an id to attach to.
  try {
    const draft: any = await api.createExpense({ title: 'Nytt utlegg' })
    expenseId.value = draft.id
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke opprette utlegg', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  }
})

const onFiles = async (ev: Event) => {
  const input = ev.target as HTMLInputElement
  if (!input.files?.length || !expenseId.value) return
  uploading.value = true
  try {
    for (const file of Array.from(input.files)) {
      ocrRunning.value = file.type.startsWith('image/')
      const att: any = await api.uploadExpenseAttachment(expenseId.value, file)
      attachments.value.push(att)
      if (att.ai_suggestions) {
        lastSuggestion.value = att.ai_suggestions
        applySuggestion(att.ai_suggestions, true)
      }
    }
  } catch (err: any) {
    toast.add({ title: 'Opplasting feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    uploading.value = false
    ocrRunning.value = false
    input.value = ''
  }
}

const removeAttachment = async (attId: number) => {
  if (!expenseId.value) return
  try {
    await api.deleteExpenseAttachment(expenseId.value, attId)
    attachments.value = attachments.value.filter((a) => a.id !== attId)
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke fjerne kvittering', color: 'error' })
  }
}

// Fill the form from an OCR suggestion. When `onlyEmpty`, don't overwrite fields
// the user already typed.
const applySuggestion = (s: any, onlyEmpty = false) => {
  if (s.amount != null && (!onlyEmpty || !form.amount)) form.amount = s.amount
  if (s.date && (!onlyEmpty || !form.expense_date)) form.expense_date = s.date
  if (s.payee && (!onlyEmpty || !form.payee_name)) form.payee_name = s.payee
  if (s.description && (!onlyEmpty || !form.description)) form.description = s.description
  if (s.category && (!onlyEmpty || !selectedCategory.value)) {
    selectedCategory.value = EXPENSE_CATEGORY_OPTIONS.find((c) => c.value === s.category) || null
  }
  if (!onlyEmpty) toast.add({ title: 'Felter fylt ut fra kvittering', color: 'success' })
}

const payload = () => ({
  title: form.title || 'Nytt utlegg',
  category: selectedCategory.value?.value || null,
  amount: form.amount === '' ? null : Number(form.amount),
  expense_date: form.expense_date || null,
  payee_name: form.payee_name || null,
  bank_account: form.bank_account || null,
  description: form.description || null,
})

const saveDraft = async () => {
  if (!expenseId.value) return
  saving.value = true
  try {
    await api.updateExpense(expenseId.value, payload())
    toast.add({ title: 'Utkast lagret', color: 'success' })
    navigateTo('/dashboard/expenses')
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke lagre', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    saving.value = false
  }
}

const submit = async () => {
  if (!expenseId.value) return
  submitting.value = true
  try {
    await api.updateExpense(expenseId.value, payload())
    await api.submitExpense(expenseId.value)
    toast.add({ title: 'Sendt til kasserer', color: 'success' })
    navigateTo(`/dashboard/expenses/${expenseId.value}`)
  } catch (err: any) {
    toast.add({ title: 'Innsending feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    submitting.value = false
  }
}
</script>
