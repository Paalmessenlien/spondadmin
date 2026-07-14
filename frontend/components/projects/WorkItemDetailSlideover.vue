<template>
  <USlideover v-model:open="openModel" side="right" :ui="{ content: 'max-w-2xl' }">
    <template #content>
      <div class="flex flex-col h-full">
        <!-- Fixed header: navigation + close (body scrolls below, actions stay reachable) -->
        <div class="flex items-center justify-between gap-2 px-6 py-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
          <div class="flex items-center gap-2 min-w-0">
            <UButton
              v-if="stack.length"
              color="neutral"
              variant="ghost"
              size="xs"
              icon="i-heroicons-arrow-left"
              @click="goBack"
            >
              Tilbake til {{ stack[stack.length - 1].identifier }}
            </UButton>
            <UBadge v-if="item" color="neutral" variant="subtle" class="font-mono shrink-0">
              {{ item.identifier }}
            </UBadge>
          </div>
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-heroicons-x-mark"
            aria-label="Lukk"
            @click="openModel = false"
          />
        </div>

        <div v-if="loading" class="flex-1 flex items-center justify-center">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
        </div>

        <div v-else-if="item" class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- 1. Header: name + quick fields -->
          <div class="space-y-3">
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Opprettet av {{ item.created_by_name || 'ukjent' }} · {{ formatDateTime(item.created_at) }}
            </p>
            <UInput
              v-if="editingName"
              v-model="nameDraft"
              class="w-full"
              :ui="{ base: 'w-full text-lg font-semibold' }"
              autofocus
              @keyup.enter="saveName"
              @blur="saveName"
            />
            <h2
              v-else
              class="text-lg font-semibold text-gray-900 dark:text-white"
              :class="canEdit ? 'cursor-text hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded px-1 -mx-1' : ''"
              @click="startEditName"
            >
              {{ item.name }}
            </h2>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <UFormField label="Status">
                <USelectMenu
                  v-model="selectedState"
                  :items="stateOptions"
                  :disabled="!canEdit"
                  class="w-full"
                  @update:model-value="onStateChange"
                />
              </UFormField>
              <UFormField label="Prioritet">
                <USelectMenu
                  v-model="selectedPriority"
                  :items="priorityOptions"
                  :disabled="!canEdit"
                  class="w-full"
                  @update:model-value="onPriorityChange"
                />
              </UFormField>
              <UFormField label="Startdato">
                <UInput
                  v-model="startDate"
                  type="date"
                  class="w-full"
                  :disabled="!canEdit"
                  @change="onDatesChange"
                />
              </UFormField>
              <UFormField label="Frist">
                <UInput
                  v-model="targetDate"
                  type="date"
                  class="w-full"
                  :disabled="!canEdit"
                  @change="onDatesChange"
                />
              </UFormField>
            </div>
          </div>

          <!-- 2. Description -->
          <div class="space-y-2">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Beskrivelse</h3>
            <template v-if="canEdit">
              <UTextarea
                v-model="descriptionDraft"
                :rows="4"
                placeholder="Legg til en beskrivelse…"
                class="w-full"
                :ui="{ base: 'w-full' }"
              />
              <div v-if="descriptionDraft !== (item.description || '')" class="flex justify-end">
                <UButton size="xs" color="primary" :loading="saving" @click="saveDescription">
                  Lagre
                </UButton>
              </div>
            </template>
            <p v-else-if="item.description" class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {{ item.description }}
            </p>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500">Ingen beskrivelse</p>
          </div>

          <!-- 3. Details -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Detaljer</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <UFormField label="Etiketter">
                <USelectMenu
                  v-model="selectedLabels"
                  :items="labelOptions"
                  multiple
                  :disabled="!canEdit"
                  placeholder="Ingen etiketter"
                  class="w-full"
                  @update:model-value="onLabelsChange"
                />
              </UFormField>
              <UFormField label="Syklus">
                <USelectMenu
                  v-model="selectedCycles"
                  :items="cycleOptions"
                  multiple
                  :disabled="!canEdit"
                  placeholder="Ingen syklus"
                  class="w-full"
                  @update:model-value="onCyclesChange"
                />
              </UFormField>
              <UFormField label="Modul">
                <USelectMenu
                  v-model="selectedModules"
                  :items="moduleOptions"
                  multiple
                  :disabled="!canEdit"
                  placeholder="Ingen modul"
                  class="w-full"
                  @update:model-value="onModulesChange"
                />
              </UFormField>
            </div>

            <!-- Assignees -->
            <div>
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Ansvarlige</p>
              <div class="flex flex-wrap items-center gap-1.5">
                <span
                  v-for="p in item.assignees"
                  :key="p.id"
                  class="inline-flex items-center gap-1 rounded-full bg-gray-100 dark:bg-gray-800 px-2 py-0.5 text-xs text-gray-700 dark:text-gray-300"
                >
                  <UIcon
                    v-if="p.member_id || p.admin_id"
                    name="i-heroicons-link"
                    class="w-3 h-3 text-green-600 dark:text-green-400"
                    title="Koblet til medlemsregisteret"
                  />
                  {{ p.display_name }}
                  <button
                    v-if="canEdit"
                    type="button"
                    class="text-gray-400 hover:text-red-500"
                    aria-label="Fjern"
                    @click="removePerson('assignees', p)"
                  >
                    ×
                  </button>
                </span>
                <span v-if="!item.assignees?.length" class="text-xs text-gray-400 dark:text-gray-500">
                  Ingen ansvarlige
                </span>
              </div>
              <div v-if="canEdit" class="flex gap-2 mt-2">
                <UInput
                  v-model="newAssignee"
                  size="sm"
                  placeholder="Navn…"
                  class="flex-1"
                  @keyup.enter="addPerson('assignees')"
                />
                <UButton
                  size="sm"
                  color="neutral"
                  variant="outline"
                  icon="i-heroicons-plus"
                  :disabled="!newAssignee.trim()"
                  @click="addPerson('assignees')"
                >
                  Legg til
                </UButton>
              </div>
            </div>

            <!-- Subscribers (collapsed) -->
            <div>
              <button
                type="button"
                class="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300"
                @click="showSubscribers = !showSubscribers"
              >
                <UIcon
                  :name="showSubscribers ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-right'"
                  class="w-4 h-4"
                />
                Abonnenter ({{ item.subscribers?.length || 0 }})
              </button>
              <div v-if="showSubscribers" class="mt-2 space-y-2">
                <div class="flex flex-wrap items-center gap-1.5">
                  <span
                    v-for="p in item.subscribers"
                    :key="p.id"
                    class="inline-flex items-center gap-1 rounded-full bg-gray-100 dark:bg-gray-800 px-2 py-0.5 text-xs text-gray-700 dark:text-gray-300"
                  >
                    <UIcon
                      v-if="p.member_id || p.admin_id"
                      name="i-heroicons-link"
                      class="w-3 h-3 text-green-600 dark:text-green-400"
                    />
                    {{ p.display_name }}
                    <button
                      v-if="canEdit"
                      type="button"
                      class="text-gray-400 hover:text-red-500"
                      aria-label="Fjern"
                      @click="removePerson('subscribers', p)"
                    >
                      ×
                    </button>
                  </span>
                  <span v-if="!item.subscribers?.length" class="text-xs text-gray-400 dark:text-gray-500">
                    Ingen abonnenter
                  </span>
                </div>
                <div v-if="canEdit" class="flex gap-2">
                  <UInput
                    v-model="newSubscriber"
                    size="sm"
                    placeholder="Navn…"
                    class="flex-1"
                    @keyup.enter="addPerson('subscribers')"
                  />
                  <UButton
                    size="sm"
                    color="neutral"
                    variant="outline"
                    icon="i-heroicons-plus"
                    :disabled="!newSubscriber.trim()"
                    @click="addPerson('subscribers')"
                  >
                    Legg til
                  </UButton>
                </div>
              </div>
            </div>
          </div>

          <!-- 4. Sub-items -->
          <div class="space-y-2">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
              Underoppgaver ({{ item.children?.length || 0 }})
            </h3>
            <div v-if="item.children?.length" class="divide-y divide-gray-100 dark:divide-gray-800 border border-gray-200 dark:border-gray-800 rounded-lg">
              <button
                v-for="child in item.children"
                :key="child.id"
                type="button"
                class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50"
                @click="openChild(child.id)"
              >
                <span
                  class="w-2 h-2 rounded-full shrink-0"
                  :style="{ backgroundColor: child.state?.color || '#9CA3AF' }"
                  :title="child.state?.name"
                />
                <span class="text-xs font-mono text-gray-500 dark:text-gray-400 shrink-0">
                  {{ child.identifier }}
                </span>
                <span class="text-sm text-gray-900 dark:text-white truncate">{{ child.name }}</span>
              </button>
            </div>
            <div v-if="canEdit" class="flex gap-2">
              <UInput
                v-model="quickChildName"
                size="sm"
                placeholder="Legg til underoppgave…"
                class="flex-1"
                @keyup.enter="addChild"
              />
              <UButton
                size="sm"
                color="neutral"
                variant="outline"
                icon="i-heroicons-plus"
                :loading="addingChild"
                :disabled="!quickChildName.trim()"
                @click="addChild"
              >
                Legg til
              </UButton>
            </div>
          </div>

          <!-- 5. Relations -->
          <div class="space-y-2">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
              Relasjoner ({{ item.relations?.length || 0 }})
            </h3>
            <div v-if="item.relations?.length" class="space-y-1">
              <div
                v-for="rel in item.relations"
                :key="rel.id"
                class="flex items-center gap-2 text-sm"
              >
                <span class="text-gray-500 dark:text-gray-400 shrink-0">
                  {{ relationTypeLabel(rel.relation_type) }}
                </span>
                <template v-if="rel.related_work_item_id">
                  <button
                    type="button"
                    class="flex items-center gap-1.5 min-w-0 text-left hover:underline"
                    @click="openChild(rel.related_work_item_id)"
                  >
                    <span class="font-mono text-xs text-gray-600 dark:text-gray-300 shrink-0">
                      {{ rel.related_identifier }}
                    </span>
                    <span v-if="rel.related_name" class="text-gray-900 dark:text-white truncate">
                      {{ rel.related_name }}
                    </span>
                  </button>
                </template>
                <template v-else>
                  <span class="font-mono text-xs text-gray-600 dark:text-gray-300 shrink-0">
                    {{ rel.related_identifier }}
                  </span>
                  <UBadge color="neutral" variant="subtle" size="sm">ekstern</UBadge>
                </template>
                <UButton
                  v-if="canEdit"
                  color="error"
                  variant="ghost"
                  size="xs"
                  icon="i-heroicons-trash"
                  class="ml-auto shrink-0"
                  aria-label="Slett relasjon"
                  @click="removeRelation(rel)"
                />
              </div>
            </div>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500">Ingen relasjoner</p>
            <div v-if="canEdit" class="flex flex-col sm:flex-row gap-2">
              <USelectMenu v-model="newRelationType" :items="relationTypeOptions" class="sm:w-40" />
              <UInput
                v-model="newRelationIdentifier"
                size="sm"
                placeholder="F.eks. STYRE-13"
                class="flex-1 font-mono"
                @keyup.enter="addRelation"
              />
              <UButton
                size="sm"
                color="neutral"
                variant="outline"
                icon="i-heroicons-plus"
                :disabled="!newRelationIdentifier.trim()"
                @click="addRelation"
              >
                Legg til
              </UButton>
            </div>
          </div>

          <!-- 6. Links -->
          <div class="space-y-2">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
              Lenker ({{ item.links?.length || 0 }})
            </h3>
            <div v-if="item.links?.length" class="space-y-1">
              <div v-for="link in item.links" :key="link.id" class="flex items-center gap-2 text-sm">
                <a
                  :href="link.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-1 min-w-0 text-blue-600 dark:text-blue-400 hover:underline"
                >
                  <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-4 h-4 shrink-0" />
                  <span class="truncate">{{ link.title || link.url }}</span>
                </a>
                <UButton
                  v-if="canEdit"
                  color="error"
                  variant="ghost"
                  size="xs"
                  icon="i-heroicons-trash"
                  class="ml-auto shrink-0"
                  aria-label="Slett lenke"
                  @click="removeLink(link)"
                />
              </div>
            </div>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500">Ingen lenker</p>
            <div v-if="canEdit" class="flex flex-col sm:flex-row gap-2">
              <UInput v-model="newLinkUrl" size="sm" placeholder="https://…" class="flex-1" />
              <UInput v-model="newLinkTitle" size="sm" placeholder="Tittel (valgfritt)" class="flex-1" />
              <UButton
                size="sm"
                color="neutral"
                variant="outline"
                icon="i-heroicons-plus"
                :disabled="!newLinkUrl.trim()"
                @click="addLink"
              >
                Legg til
              </UButton>
            </div>
          </div>

          <!-- 7. Comments -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
              Kommentarer ({{ item.comments?.length || 0 }})
            </h3>
            <div v-for="c in item.comments" :key="c.id" class="text-sm space-y-1">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-gray-900 dark:text-white">
                  {{ c.created_by_name || 'Ukjent' }}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500">
                  {{ formatDateTime(c.created_at) }}
                </span>
                <template v-if="canEditComment(c) && editingCommentId !== c.id">
                  <UButton
                    color="neutral"
                    variant="ghost"
                    size="xs"
                    icon="i-heroicons-pencil-square"
                    class="ml-auto"
                    aria-label="Rediger kommentar"
                    @click="startEditComment(c)"
                  />
                  <UButton
                    color="error"
                    variant="ghost"
                    size="xs"
                    icon="i-heroicons-trash"
                    aria-label="Slett kommentar"
                    @click="removeComment(c)"
                  />
                </template>
              </div>
              <template v-if="editingCommentId === c.id">
                <UTextarea v-model="commentDraft" :rows="3" class="w-full" :ui="{ base: 'w-full' }" />
                <div class="flex justify-end gap-2">
                  <UButton size="xs" color="neutral" variant="ghost" @click="editingCommentId = null">
                    Avbryt
                  </UButton>
                  <UButton size="xs" color="primary" :loading="saving" @click="saveComment(c)">
                    Lagre
                  </UButton>
                </div>
              </template>
              <p v-else class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ c.body }}</p>
            </div>
            <p v-if="!item.comments?.length" class="text-sm text-gray-400 dark:text-gray-500">
              Ingen kommentarer ennå
            </p>
            <div v-if="canEdit" class="space-y-2">
              <UTextarea
                v-model="newComment"
                :rows="3"
                placeholder="Skriv en kommentar…"
                class="w-full"
                :ui="{ base: 'w-full' }"
              />
              <div class="flex justify-end">
                <UButton
                  color="primary"
                  size="sm"
                  :loading="commenting"
                  :disabled="!newComment.trim()"
                  @click="addComment"
                >
                  Kommenter
                </UButton>
              </div>
            </div>
          </div>
        </div>

        <!-- 8. Fixed footer -->
        <div
          v-if="canEdit && item && !loading"
          class="px-6 py-3 border-t border-gray-200 dark:border-gray-800 shrink-0"
        >
          <UButton color="error" variant="ghost" icon="i-heroicons-trash" @click="removeItem">
            Slett sak
          </UButton>
        </div>
      </div>
    </template>
  </USlideover>
</template>

<script setup lang="ts">
const props = defineProps<{
  open: boolean
  itemId: number | null
  project: any
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'updated'): void
  (e: 'deleted'): void
}>()

const api = useApi()
const toast = useToast()
const authStore = useAuthStore()
const { canEdit, isAdmin } = usePermissions()

const openModel = computed({
  get: () => props.open,
  set: (v: boolean) => emit('update:open', v),
})

const item = ref<any | null>(null)
const loading = ref(false)
const saving = ref(false)
const currentItemId = ref<number | null>(null)
const stack = ref<{ id: number; identifier: string }[]>([])

// Local drafts (synced from the loaded item)
const editingName = ref(false)
const nameDraft = ref('')
const descriptionDraft = ref('')
const selectedState = ref<any>(null)
const selectedPriority = ref<any>(null)
const startDate = ref('')
const targetDate = ref('')
const selectedLabels = ref<any[]>([])
const selectedCycles = ref<any[]>([])
const selectedModules = ref<any[]>([])
const showSubscribers = ref(false)
const newAssignee = ref('')
const newSubscriber = ref('')
const quickChildName = ref('')
const addingChild = ref(false)
const newRelationType = ref<any>(RELATION_TYPE_OPTIONS[0])
const newRelationIdentifier = ref('')
const newLinkUrl = ref('')
const newLinkTitle = ref('')
const newComment = ref('')
const commenting = ref(false)
const editingCommentId = ref<number | null>(null)
const commentDraft = ref('')

const priorityOptions = PRIORITY_OPTIONS
const relationTypeOptions = RELATION_TYPE_OPTIONS

const stateOptions = computed(() =>
  (props.project?.states || []).map((s: any) => ({ label: s.name, value: s.id }))
)
const labelOptions = computed(() =>
  (props.project?.labels || []).map((l: any) => ({ label: l.name, value: l.id }))
)
const cycleOptions = computed(() =>
  (props.project?.cycles || []).map((c: any) => ({ label: c.name, value: c.id }))
)
const moduleOptions = computed(() =>
  (props.project?.modules || []).map((m: any) => ({ label: m.name, value: m.id }))
)

const syncLocal = () => {
  const it = item.value
  if (!it) return
  editingName.value = false
  nameDraft.value = it.name
  descriptionDraft.value = it.description || ''
  selectedState.value = stateOptions.value.find((o: any) => o.value === it.state?.id) || null
  selectedPriority.value =
    priorityOptions.find((o: any) => o.value === (it.priority || 'none')) || priorityOptions[0]
  startDate.value = it.start_date || ''
  targetDate.value = it.target_date || ''
  selectedLabels.value = labelOptions.value.filter((o: any) =>
    (it.labels || []).some((l: any) => l.id === o.value)
  )
  selectedCycles.value = cycleOptions.value.filter((o: any) =>
    (it.cycles || []).some((c: any) => c.id === o.value)
  )
  selectedModules.value = moduleOptions.value.filter((o: any) =>
    (it.modules || []).some((m: any) => m.id === o.value)
  )
}

const loadItem = async (soft = false) => {
  if (!currentItemId.value) return
  if (!soft) loading.value = true
  try {
    item.value = await api.getWorkItem(currentItemId.value)
    syncLocal()
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke laste saken',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
    openModel.value = false
  } finally {
    loading.value = false
  }
}

const resetAndLoad = () => {
  stack.value = []
  currentItemId.value = props.itemId
  item.value = null
  editingCommentId.value = null
  showSubscribers.value = false
  newComment.value = ''
  loadItem()
}

// Single watcher so open+itemId changing in the same tick only fetches once.
watch(
  () => [props.open, props.itemId] as const,
  ([open, id]) => {
    if (open && id) resetAndLoad()
  }
)

// ---- generic PATCH helper -------------------------------------------------

const patch = async (payload: Record<string, any>) => {
  if (!currentItemId.value) return
  saving.value = true
  try {
    item.value = await api.updateWorkItem(currentItemId.value, payload)
    syncLocal()
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke lagre endringen',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
    syncLocal() // roll local drafts back to server state
  } finally {
    saving.value = false
  }
}

// ---- header fields ----------------------------------------------------------

const startEditName = () => {
  if (!canEdit.value) return
  nameDraft.value = item.value?.name || ''
  editingName.value = true
}

const saveName = () => {
  if (!editingName.value) return
  editingName.value = false
  const name = nameDraft.value.trim()
  if (name && name !== item.value?.name) patch({ name })
}

const onStateChange = () => {
  if (selectedState.value?.value && selectedState.value.value !== item.value?.state?.id) {
    patch({ state_id: selectedState.value.value })
  }
}

const onPriorityChange = () => {
  if (selectedPriority.value?.value && selectedPriority.value.value !== item.value?.priority) {
    patch({ priority: selectedPriority.value.value })
  }
}

const onDatesChange = () => {
  patch({ start_date: startDate.value || null, target_date: targetDate.value || null })
}

const saveDescription = () => patch({ description: descriptionDraft.value.trim() || null })

// ---- details (labels / cycles / modules / people) ---------------------------

const onLabelsChange = () => patch({ label_ids: selectedLabels.value.map((o: any) => o.value) })
const onCyclesChange = () => patch({ cycle_ids: selectedCycles.value.map((o: any) => o.value) })
const onModulesChange = () => patch({ module_ids: selectedModules.value.map((o: any) => o.value) })

const personPayload = (list: any[]) =>
  (list || []).map((p: any) => ({
    display_name: p.display_name,
    member_id: p.member_id ?? null,
    admin_id: p.admin_id ?? null,
  }))

const addPerson = (kind: 'assignees' | 'subscribers') => {
  const draft = kind === 'assignees' ? newAssignee : newSubscriber
  const name = draft.value.trim()
  if (!name || !item.value) return
  if ((item.value[kind] || []).some((p: any) => p.display_name === name)) {
    draft.value = ''
    return
  }
  patch({ [kind]: [...personPayload(item.value[kind]), { display_name: name }] })
  draft.value = ''
}

const removePerson = (kind: 'assignees' | 'subscribers', person: any) => {
  if (!item.value) return
  patch({ [kind]: personPayload((item.value[kind] || []).filter((p: any) => p.id !== person.id)) })
}

// ---- sub-items ---------------------------------------------------------------

const openChild = (id: number) => {
  if (!item.value || id === currentItemId.value) return
  stack.value.push({ id: item.value.id, identifier: item.value.identifier })
  currentItemId.value = id
  loadItem()
}

const goBack = () => {
  const prev = stack.value.pop()
  if (!prev) return
  currentItemId.value = prev.id
  loadItem()
}

const addChild = async () => {
  const name = quickChildName.value.trim()
  if (!name || !currentItemId.value || !props.project?.id) return
  addingChild.value = true
  try {
    await api.createWorkItem(props.project.id, { name, parent_id: currentItemId.value })
    quickChildName.value = ''
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke opprette underoppgaven',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  } finally {
    addingChild.value = false
  }
}

// ---- relations ----------------------------------------------------------------

const addRelation = async () => {
  const identifier = newRelationIdentifier.value.trim().toUpperCase()
  if (!identifier || !currentItemId.value) return
  try {
    await api.addWorkItemRelation(currentItemId.value, {
      relation_type: newRelationType.value?.value || 'relates_to',
      related_identifier: identifier,
    })
    newRelationIdentifier.value = ''
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke legge til relasjonen',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

const removeRelation = async (rel: any) => {
  try {
    await api.deleteWorkItemRelation(rel.id)
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke slette relasjonen',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

// ---- links ---------------------------------------------------------------------

const addLink = async () => {
  const url = newLinkUrl.value.trim()
  if (!url || !currentItemId.value) return
  try {
    await api.addWorkItemLink(currentItemId.value, {
      url,
      title: newLinkTitle.value.trim() || null,
    })
    newLinkUrl.value = ''
    newLinkTitle.value = ''
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke legge til lenken',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

const removeLink = async (link: any) => {
  try {
    await api.deleteWorkItemLink(link.id)
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke slette lenken',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

// ---- comments -------------------------------------------------------------------

const canEditComment = (c: any) =>
  isAdmin.value || (c.created_by_id != null && c.created_by_id === authStore.user?.id)

const addComment = async () => {
  const body = newComment.value.trim()
  if (!body || !currentItemId.value) return
  commenting.value = true
  try {
    await api.addWorkItemComment(currentItemId.value, { body })
    newComment.value = ''
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke legge til kommentaren',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  } finally {
    commenting.value = false
  }
}

const startEditComment = (c: any) => {
  editingCommentId.value = c.id
  commentDraft.value = c.body
}

const saveComment = async (c: any) => {
  const body = commentDraft.value.trim()
  if (!body) return
  saving.value = true
  try {
    await api.updateWorkItemComment(c.id, { body })
    editingCommentId.value = null
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke oppdatere kommentaren',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  } finally {
    saving.value = false
  }
}

const removeComment = async (c: any) => {
  if (!confirm('Slette kommentaren?')) return
  try {
    await api.deleteWorkItemComment(c.id)
    await loadItem(true)
    emit('updated')
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke slette kommentaren',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

// ---- delete item -------------------------------------------------------------------

const removeItem = async () => {
  if (!item.value) return
  if (!confirm(`Slette ${item.value.identifier} «${item.value.name}»? Dette kan ikke angres.`)) return
  try {
    await api.deleteWorkItem(item.value.id)
    toast.add({ title: 'Sak slettet', color: 'success' })
    emit('deleted')
    openModel.value = false
  } catch (err: any) {
    toast.add({
      title: 'Kunne ikke slette saken',
      description: err?.data?.detail || 'Ukjent feil',
      color: 'error',
    })
  }
}

// ---- formatting ---------------------------------------------------------------------

const formatDateTime = (d?: string | null) => {
  if (!d) return ''
  const dt = new Date(d)
  return (
    dt.toLocaleDateString('nb-NO') +
    ' ' +
    dt.toLocaleTimeString('nb-NO', { hour: '2-digit', minute: '2-digit' })
  )
}
</script>
