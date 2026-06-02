/**
 * Shared display metadata for expenses (utlegg): status badges + category
 * labels. Keep keys in sync with the backend EXPENSE_STATUSES / EXPENSE_CATEGORIES.
 */
export const EXPENSE_STATUS_META: Record<string, { label: string; color: string; icon: string }> = {
  utkast: { label: 'Utkast', color: 'neutral', icon: 'i-heroicons-pencil-square' },
  sendt: { label: 'Sendt', color: 'info', icon: 'i-heroicons-paper-airplane' },
  godkjent: { label: 'Godkjent', color: 'success', icon: 'i-heroicons-check-circle' },
  avvist: { label: 'Avvist', color: 'error', icon: 'i-heroicons-x-circle' },
  utbetalt: { label: 'Utbetalt', color: 'primary', icon: 'i-heroicons-banknotes' },
}

export const EXPENSE_CATEGORY_OPTIONS = [
  { label: 'Utstyr', value: 'utstyr' },
  { label: 'Reise', value: 'reise' },
  { label: 'Bevertning', value: 'bevertning' },
  { label: 'Kontor', value: 'kontor' },
  { label: 'Premier', value: 'premier' },
  { label: 'Bane/anlegg', value: 'bane_anlegg' },
  { label: 'Kurs', value: 'kurs' },
  { label: 'Annet', value: 'annet' },
]

export const useExpenseMeta = () => {
  const statusMeta = (status?: string | null) =>
    (status && EXPENSE_STATUS_META[status]) || EXPENSE_STATUS_META.utkast

  const categoryLabel = (value?: string | null) =>
    EXPENSE_CATEGORY_OPTIONS.find((c) => c.value === value)?.label ?? value ?? ''

  const formatAmount = (amount?: number | string | null, currency = 'NOK') => {
    if (amount == null || amount === '') return '—'
    const n = typeof amount === 'string' ? parseFloat(amount) : amount
    if (!Number.isFinite(n)) return '—'
    return `${n.toLocaleString('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`
  }

  return { statusMeta, categoryLabel, formatAmount, EXPENSE_CATEGORY_OPTIONS }
}
