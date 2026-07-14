/**
 * Shared display metadata for the project system (Prosjekter).
 * The backend keeps Plane-compatible English vocabulary tokens
 * (WORK_ITEM_PRIORITIES / STATE_GROUPS / RELATION_TYPES) for import
 * fidelity — this composable maps them to Norwegian labels, colors
 * and icons for the UI. Keep keys in sync with backend
 * app/models/project.py.
 */

type BadgeColor = 'neutral' | 'primary' | 'info' | 'success' | 'warning' | 'error'

export interface PriorityMeta {
  label: string
  color: BadgeColor
  icon: string
}

export interface StateGroupMeta {
  label: string
  color: BadgeColor
  icon: string
}

export const PRIORITY_META: Record<string, PriorityMeta> = {
  none: { label: 'Ingen', color: 'neutral', icon: 'i-heroicons-minus' },
  low: { label: 'Lav', color: 'info', icon: 'i-heroicons-arrow-down' },
  medium: { label: 'Middels', color: 'warning', icon: 'i-heroicons-bars-2' },
  high: { label: 'Høy', color: 'warning', icon: 'i-heroicons-arrow-up' },
  urgent: { label: 'Haster', color: 'error', icon: 'i-heroicons-exclamation-triangle' },
}

export const STATE_GROUP_META: Record<string, StateGroupMeta> = {
  backlog: { label: 'Backlogg', color: 'neutral', icon: 'i-heroicons-inbox' },
  unstarted: { label: 'Å gjøre', color: 'info', icon: 'i-heroicons-circle-stack' },
  started: { label: 'Pågår', color: 'warning', icon: 'i-heroicons-play' },
  completed: { label: 'Fullført', color: 'success', icon: 'i-heroicons-check-circle' },
  cancelled: { label: 'Avbrutt', color: 'error', icon: 'i-heroicons-x-circle' },
}

export const RELATION_TYPE_LABELS: Record<string, string> = {
  relates_to: 'Relatert til',
  blocks: 'Blokkerer',
  blocked_by: 'Blokkert av',
  duplicate: 'Duplikat av',
}

// Whole {label, value} objects for USelectMenu (never value-attribute).
export const PRIORITY_OPTIONS = Object.entries(PRIORITY_META).map(([value, meta]) => ({
  label: meta.label,
  value,
  icon: meta.icon,
}))

export const RELATION_TYPE_OPTIONS = Object.entries(RELATION_TYPE_LABELS).map(
  ([value, label]) => ({ label, value })
)

export const priorityMeta = (p?: string | null): PriorityMeta =>
  (p && PRIORITY_META[p]) || PRIORITY_META.none

export const stateGroupMeta = (g?: string | null): StateGroupMeta =>
  (g && STATE_GROUP_META[g]) || STATE_GROUP_META.unstarted

export const relationTypeLabel = (t?: string | null): string =>
  (t && RELATION_TYPE_LABELS[t]) || RELATION_TYPE_LABELS.relates_to

export const useProjects = () => {
  return {
    PRIORITY_META,
    STATE_GROUP_META,
    RELATION_TYPE_LABELS,
    PRIORITY_OPTIONS,
    RELATION_TYPE_OPTIONS,
    priorityMeta,
    stateGroupMeta,
    relationTypeLabel,
  }
}
