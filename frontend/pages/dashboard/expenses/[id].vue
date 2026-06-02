<template>
  <div class="space-y-6 max-w-2xl">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Utlegg', to: '/dashboard/expenses' },
      { label: expense?.title || 'Utlegg' }
    ]" />

    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
    </div>

    <template v-else-if="expense">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ expense.title }}</h1>
          <UBadge :color="statusMeta(expense.status).color" :icon="statusMeta(expense.status).icon" variant="subtle">
            {{ statusMeta(expense.status).label }}
          </UBadge>
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ formatAmount(expense.amount, expense.currency) }}
        </div>
      </div>

      <!-- Rejection / approval note -->
      <UCard v-if="expense.kasserer_note" :class="expense.status === 'avvist' ? 'border-red-300 dark:border-red-800' : ''">
        <p class="text-sm">
          <span class="font-medium">Kommentar fra kasserer:</span> {{ expense.kasserer_note }}
        </p>
      </UCard>

      <!-- Details (read mode) -->
      <UCard v-if="!editing">
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-y-3 gap-x-6 text-sm">
          <div><dt class="text-gray-500">Kategori</dt><dd>{{ categoryLabel(expense.category) || '—' }}</dd></div>
          <div><dt class="text-gray-500">Dato</dt><dd>{{ expense.expense_date ? formatDate(expense.expense_date) : '—' }}</dd></div>
          <div><dt class="text-gray-500">Mottaker</dt><dd>{{ expense.payee_name || '—' }}</dd></div>
          <div><dt class="text-gray-500">Kontonummer</dt><dd>{{ expense.bank_account || '—' }}</dd></div>
          <div class="sm:col-span-2"><dt class="text-gray-500">Beskrivelse</dt><dd>{{ expense.description || '—' }}</dd></div>
          <div v-if="expense.submitter_name"><dt class="text-gray-500">Innsendt av</dt><dd>{{ expense.submitter_name }}</dd></div>
        </dl>
      </UCard>

      <!-- Details (edit mode, owner + utkast/avvist) -->
      <UCard v-else>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <UFormField label="Tittel" class="sm:col-span-2"><UInput v-model="form.title" class="w-full" /></UFormField>
          <UFormField label="Kategori"><USelectMenu v-model="selectedCategory" :items="EXPENSE_CATEGORY_OPTIONS" placeholder="Velg" class="w-full" /></UFormField>
          <UFormField label="Beløp (NOK)"><UInput v-model="form.amount" type="number" step="0.01" min="0" class="w-full" /></UFormField>
          <UFormField label="Dato"><UInput v-model="form.expense_date" type="date" class="w-full" /></UFormField>
          <UFormField label="Mottaker"><UInput v-model="form.payee_name" class="w-full" /></UFormField>
          <UFormField label="Kontonummer" class="sm:col-span-2"><UInput v-model="form.bank_account" class="w-full" /></UFormField>
          <UFormField label="Beskrivelse" class="sm:col-span-2"><UTextarea v-model="form.description" :rows="3" class="w-full" /></UFormField>
        </div>
      </UCard>

      <!-- Receipts -->
      <UCard>
        <template #header><h2 class="font-semibold">Kvitteringer</h2></template>
        <div v-if="!expense.attachments?.length" class="text-sm text-gray-500">Ingen kvitteringer.</div>
        <div v-else class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <a v-for="att in expense.attachments" :key="att.id" :href="att.cdn_url" target="_blank" class="block">
            <img v-if="att.content_type?.startsWith('image/')" :src="att.cdn_url" class="w-full h-28 object-cover rounded border border-gray-200 dark:border-gray-800" />
            <div v-else class="w-full h-28 flex flex-col items-center justify-center gap-1 rounded border border-gray-200 dark:border-gray-800">
              <UIcon name="i-heroicons-document" class="w-8 h-8 text-gray-400" />
              <span class="text-xs text-gray-500 truncate max-w-full px-1">{{ att.filename }}</span>
            </div>
          </a>
        </div>
      </UCard>

      <!-- Status timeline -->
      <UCard>
        <template #header><h2 class="font-semibold">Status</h2></template>
        <ul class="space-y-2 text-sm">
          <li class="flex justify-between"><span class="text-gray-500">Opprettet</span><span>{{ formatDateTime(expense.created_at) }}</span></li>
          <li v-if="expense.submitted_at" class="flex justify-between"><span class="text-gray-500">Sendt</span><span>{{ formatDateTime(expense.submitted_at) }}</span></li>
          <li v-if="expense.reviewed_at" class="flex justify-between"><span class="text-gray-500">Behandlet</span><span>{{ formatDateTime(expense.reviewed_at) }}<template v-if="expense.reviewed_by_name"> av {{ expense.reviewed_by_name }}</template></span></li>
          <li v-if="expense.paid_at" class="flex justify-between"><span class="text-gray-500">Utbetalt</span><span>{{ formatDateTime(expense.paid_at) }}</span></li>
        </ul>
      </UCard>

      <!-- Actions -->
      <div class="flex flex-col sm:flex-row gap-3 sm:justify-end">
        <!-- Owner actions on draft/rejected -->
        <template v-if="isOwner && ['utkast', 'avvist'].includes(expense.status)">
          <UButton color="error" variant="ghost" icon="i-heroicons-trash" @click="remove">Slett</UButton>
          <template v-if="editing">
            <UButton color="neutral" variant="outline" @click="editing = false">Avbryt</UButton>
            <UButton color="neutral" :loading="saving" @click="save">Lagre</UButton>
          </template>
          <UButton v-else color="neutral" variant="outline" icon="i-heroicons-pencil-square" @click="startEdit">Rediger</UButton>
          <UButton color="primary" icon="i-heroicons-paper-airplane" :loading="submitting" @click="submit">Send til kasserer</UButton>
        </template>

        <!-- Reviewer actions -->
        <template v-if="canReviewExpenses && expense.status === 'sendt'">
          <UButton color="error" variant="soft" icon="i-heroicons-x-circle" @click="openReview('avvis')">Avvis</UButton>
          <UButton color="success" icon="i-heroicons-check-circle" @click="openReview('godkjenn')">Godkjenn</UButton>
        </template>
        <template v-if="canReviewExpenses && expense.status === 'godkjent'">
          <UButton color="primary" icon="i-heroicons-banknotes" :loading="reviewing" @click="doReview('utbetalt')">Marker utbetalt</UButton>
        </template>
      </div>
    </template>

    <!-- Review note modal -->
    <UModal v-model:open="reviewModalOpen">
      <template #content>
        <div class="p-4 space-y-4">
          <h3 class="font-semibold">{{ reviewAction === 'godkjenn' ? 'Godkjenn utlegg' : 'Avvis utlegg' }}</h3>
          <UFormField :label="reviewAction === 'avvis' ? 'Begrunnelse (vises til innsender)' : 'Kommentar (valgfritt)'">
            <UTextarea v-model="reviewNote" :rows="3" class="w-full" />
          </UFormField>
          <div class="flex justify-end gap-2">
            <UButton color="neutral" variant="outline" @click="reviewModalOpen = false">Avbryt</UButton>
            <UButton :color="reviewAction === 'avvis' ? 'error' : 'success'" :loading="reviewing" @click="doReview(reviewAction)">
              Bekreft
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const toast = useToast()
const authStore = useAuthStore()
const { canReviewExpenses } = usePermissions()
const { statusMeta, categoryLabel, formatAmount, EXPENSE_CATEGORY_OPTIONS } = useExpenseMeta()

const expenseId = computed(() => parseInt(route.params.id as string))
const expense = ref<any>(null)
const loading = ref(true)
const editing = ref(false)
const saving = ref(false)
const submitting = ref(false)
const reviewing = ref(false)

const reviewModalOpen = ref(false)
const reviewAction = ref<'godkjenn' | 'avvis'>('godkjenn')
const reviewNote = ref('')

const form = reactive({ title: '', amount: '' as string | number, expense_date: '', payee_name: '', bank_account: '', description: '' })
const selectedCategory = ref<any>(null)

const isOwner = computed(() => expense.value?.submitter_admin_id === authStore.user?.id)

const formatDate = (d: string) => new Date(d).toLocaleDateString('nb-NO')
const formatDateTime = (d: string) => new Date(d).toLocaleString('nb-NO', { dateStyle: 'short', timeStyle: 'short' })

const load = async () => {
  loading.value = true
  try {
    expense.value = await api.getExpense(expenseId.value)
  } catch (err) {
    toast.add({ title: 'Kunne ikke laste utlegg', color: 'error' })
  } finally {
    loading.value = false
  }
}

const startEdit = () => {
  form.title = expense.value.title
  form.amount = expense.value.amount ?? ''
  form.expense_date = expense.value.expense_date || ''
  form.payee_name = expense.value.payee_name || ''
  form.bank_account = expense.value.bank_account || ''
  form.description = expense.value.description || ''
  selectedCategory.value = EXPENSE_CATEGORY_OPTIONS.find((c) => c.value === expense.value.category) || null
  editing.value = true
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

const save = async () => {
  saving.value = true
  try {
    expense.value = await api.updateExpense(expenseId.value, payload())
    editing.value = false
    toast.add({ title: 'Lagret', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke lagre', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    saving.value = false
  }
}

const submit = async () => {
  submitting.value = true
  try {
    if (editing.value) await api.updateExpense(expenseId.value, payload())
    expense.value = await api.submitExpense(expenseId.value)
    editing.value = false
    toast.add({ title: 'Sendt til kasserer', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Innsending feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    submitting.value = false
  }
}

const remove = async () => {
  try {
    await api.deleteExpense(expenseId.value)
    toast.add({ title: 'Utlegg slettet', color: 'success' })
    navigateTo('/dashboard/expenses')
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke slette', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  }
}

const openReview = (action: 'godkjenn' | 'avvis') => {
  reviewAction.value = action
  reviewNote.value = ''
  reviewModalOpen.value = true
}

const doReview = async (action: string) => {
  reviewing.value = true
  try {
    expense.value = await api.reviewExpense(expenseId.value, action, reviewNote.value || undefined)
    reviewModalOpen.value = false
    toast.add({ title: 'Utlegg oppdatert', color: 'success' })
  } catch (err: any) {
    toast.add({ title: 'Handling feilet', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
  } finally {
    reviewing.value = false
  }
}

onMounted(load)
</script>
