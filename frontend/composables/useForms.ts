/**
 * Shared display metadata for the feedback form builder (skjema).
 * Keep keys in sync with the backend FORM_FIELD_TYPES / FORM_STATUSES /
 * FORM_ACCESS_MODES vocabularies.
 */
export interface FieldTypeMeta {
  value: string
  label: string
  icon: string
  // hasOptions: choice list; isScale: linear scale config; isLayout: no answer.
  hasOptions?: boolean
  isScale?: boolean
  isLayout?: boolean
  description?: string
}

export const FIELD_TYPES: FieldTypeMeta[] = [
  { value: 'kort_tekst', label: 'Kort tekst', icon: 'i-heroicons-bars-2', description: 'Én linje tekst' },
  { value: 'lang_tekst', label: 'Langt svar', icon: 'i-heroicons-bars-3-bottom-left', description: 'Flerlinjet tekst' },
  { value: 'enkeltvalg', label: 'Enkeltvalg', icon: 'i-heroicons-check-circle', hasOptions: true, description: 'Velg ett alternativ' },
  { value: 'flervalg', label: 'Flervalg', icon: 'i-heroicons-list-bullet', hasOptions: true, description: 'Velg flere alternativer' },
  { value: 'nedtrekk', label: 'Nedtrekksliste', icon: 'i-heroicons-chevron-up-down', hasOptions: true, description: 'Velg fra liste' },
  { value: 'skala', label: 'Skala', icon: 'i-heroicons-star', isScale: true, description: 'Vurdering på en skala' },
  { value: 'tall', label: 'Tall', icon: 'i-heroicons-hashtag', description: 'Numerisk svar' },
  { value: 'dato', label: 'Dato', icon: 'i-heroicons-calendar-days', description: 'Datovelger' },
  { value: 'epost', label: 'E-post', icon: 'i-heroicons-envelope', description: 'E-postadresse' },
  { value: 'ja_nei', label: 'Ja / Nei', icon: 'i-heroicons-check', description: 'Ja eller nei' },
  { value: 'overskrift', label: 'Overskrift', icon: 'i-heroicons-rectangle-group', isLayout: true, description: 'Seksjon / mellomtittel' },
]

export const FORM_STATUS_META: Record<string, { label: string; color: string; icon: string }> = {
  utkast: { label: 'Utkast', color: 'neutral', icon: 'i-heroicons-pencil-square' },
  publisert: { label: 'Publisert', color: 'success', icon: 'i-heroicons-globe-alt' },
  lukket: { label: 'Lukket', color: 'warning', icon: 'i-heroicons-lock-closed' },
}

export const ACCESS_MODE_OPTIONS = [
  { value: 'begge', label: 'Begge', description: 'Innloggede (sporet) og anonyme via delt lenke' },
  { value: 'offentlig', label: 'Offentlig', description: 'Hvem som helst med lenken — anonymt' },
  { value: 'innlogget', label: 'Kun innlogget', description: 'Bare registrerte brukere — identitet lagres' },
]

export const useForms = () => {
  const fieldMeta = (type?: string | null): FieldTypeMeta =>
    FIELD_TYPES.find((f) => f.value === type) || FIELD_TYPES[0]

  const statusMeta = (status?: string | null) =>
    (status && FORM_STATUS_META[status]) || FORM_STATUS_META.utkast

  const accessLabel = (mode?: string | null) =>
    ACCESS_MODE_OPTIONS.find((m) => m.value === mode)?.label ?? mode ?? ''

  const isLayout = (type?: string | null) => fieldMeta(type).isLayout === true
  const hasOptions = (type?: string | null) => fieldMeta(type).hasOptions === true
  const isScale = (type?: string | null) => fieldMeta(type).isScale === true

  // Build the public fill URL for a slug (uses the app origin).
  const publicFormUrl = (slug: string) => {
    const origin = import.meta.client ? window.location.origin : ''
    return `${origin}/f/${slug}`
  }

  return {
    FIELD_TYPES, FORM_STATUS_META, ACCESS_MODE_OPTIONS,
    fieldMeta, statusMeta, accessLabel, isLayout, hasOptions, isScale, publicFormUrl,
  }
}
