<template>
  <div class="space-y-6">
        <!-- Breadcrumb -->
        <Breadcrumb
          :items="[
            { label: 'Dashboard', to: '/dashboard' },
            { label: 'Events', to: '/dashboard/events' },
            { label: event?.heading || 'Event Details' }
          ]"
        />

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center py-12">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
        </div>

        <!-- Error State -->
        <UCard v-else-if="error">
          <div class="text-center py-8">
            <UIcon name="i-heroicons-exclamation-triangle" class="h-12 w-12 mx-auto text-red-500 mb-4" />
            <h3 class="text-lg font-semibold text-red-600 mb-2">Error Loading Event</h3>
            <p class="text-gray-600 dark:text-gray-400">{{ error }}</p>
          </div>
        </UCard>

        <!-- Event Details -->
        <template v-else-if="event">
          <!-- Header Card -->
          <UCard>
            <div class="space-y-4">
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    {{ event.heading }}
                  </h1>
                  <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                    <div class="flex items-center space-x-1">
                      <UIcon name="i-heroicons-calendar" />
                      <span>{{ formatDate(event.start_time) }}</span>
                    </div>
                    <div class="flex items-center space-x-1">
                      <UIcon name="i-heroicons-clock" />
                      <span>{{ formatTime(event.start_time) }} - {{ formatTime(event.end_time) }}</span>
                    </div>
                    <UBadge :color="getEventTypeColor(event.event_type)">
                      {{ event.event_type || 'Event' }}
                    </UBadge>
                    <SyncStatusBadge :status="event.sync_status || 'synced'" :error="event.sync_error" />
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-2">
                  <UButton
                    v-if="event.sync_status === 'local_only' || event.sync_status === 'pending' || event.sync_status === 'error'"
                    icon="i-heroicons-arrow-up-tray"
                    color="primary"
                    variant="soft"
                    :loading="pushing"
                    @click="handlePushToSpond"
                  >
                    Push to Spond
                  </UButton>
                  <UButton
                    icon="i-heroicons-pencil-square"
                    color="gray"
                    variant="soft"
                    @click="openEditModal"
                  >
                    Edit
                  </UButton>
                </div>
              </div>

              <!-- Description -->
              <div v-if="event.description" class="prose dark:prose-invert max-w-none">
                <p class="text-gray-700 dark:text-gray-300">{{ event.description }}</p>
              </div>

              <!-- Location -->
              <div v-if="event.location_address || event.location" class="flex items-start space-x-2">
                <UIcon name="i-heroicons-map-pin" class="mt-1 text-gray-500" />
                <div>
                  <div class="font-semibold">Location</div>
                  <div class="text-sm text-gray-600 dark:text-gray-400">
                    {{ event.location_address || event.location?.feature || event.location?.address }}
                  </div>
                </div>
              </div>

              <!-- Max Participants -->
              <div v-if="event.max_accepted > 0" class="flex items-start space-x-2">
                <UIcon name="i-heroicons-users" class="mt-1 text-gray-500" />
                <div>
                  <div class="font-semibold">Maximum Participants</div>
                  <div class="text-sm text-gray-600 dark:text-gray-400">
                    {{ event.max_accepted }} people
                  </div>
                </div>
              </div>

              <!-- Status Badges -->
              <div class="flex items-center gap-2">
                <UBadge v-if="event.cancelled" color="red">Cancelled</UBadge>
                <UBadge v-if="event.hidden" color="orange">Hidden</UBadge>
              </div>
            </div>
          </UCard>

          <!-- Statistics Cards -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600">{{ responseStats.accepted }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Accepted</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-red-600">{{ responseStats.declined }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Declined</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-gray-600">{{ responseStats.unanswered }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Unanswered</div>
              </div>
            </UCard>
            <UCard>
              <div class="text-center">
                <div class="text-3xl font-bold text-blue-600">{{ responseStats.total }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">Total Invited</div>
              </div>
            </UCard>
          </div>

          <!-- Attendees List -->
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h2 class="text-xl font-bold">Attendees</h2>
                <UInput
                  v-model="searchQuery"
                  placeholder="Search attendees..."
                  icon="i-heroicons-magnifying-glass"
                  class="w-64"
                />
              </div>
            </template>

            <!-- Tabs for response types -->
            <UTabs
              :items="tabs"
              v-model="selectedTab"
            >
              <template #item="{ item }">
                <div class="space-y-2">
                  <div v-if="filteredAttendees(item.value).length === 0" class="text-center py-8 text-gray-500">
                    No attendees in this category
                  </div>

                  <div
                    v-for="attendee in filteredAttendees(item.value)"
                    :key="attendee.profile?.id"
                    class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div class="flex items-center space-x-3">
                      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold">
                        {{ getInitials(attendee.profile) }}
                      </div>
                      <div>
                        <div class="font-medium">
                          {{ attendee.profile?.firstName }} {{ attendee.profile?.lastName }}
                        </div>
                        <div v-if="attendee.profile?.email" class="text-sm text-gray-600 dark:text-gray-400">
                          {{ attendee.profile.email }}
                        </div>
                      </div>
                    </div>
                    <UBadge :color="getResponseColor(attendee.answer)">
                      {{ formatAnswer(attendee.answer) }}
                    </UBadge>
                  </div>
                </div>
              </template>
            </UTabs>
          </UCard>
        </template>

        <!-- Edit Modal -->
        <UModal v-model="isEditModalOpen">
          <UCard>
            <template #header>
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-semibold">Edit Event</h3>
                <UButton
                  color="gray"
                  variant="ghost"
                  icon="i-heroicons-x-mark"
                  @click="isEditModalOpen = false"
                />
              </div>
            </template>

            <UForm :schema="editSchema" :state="editState" @submit="handleEditSubmit" class="space-y-4">
              <!-- Basic Information -->
              <UFormGroup label="Event Title" name="heading" required>
                <UInput
                  v-model="editState.heading"
                  placeholder="e.g. Training Session"
                  :disabled="editLoading"
                />
              </UFormGroup>

              <UFormGroup label="Description" name="description">
                <UTextarea
                  v-model="editState.description"
                  placeholder="Event description..."
                  :rows="3"
                  :disabled="editLoading"
                />
              </UFormGroup>

              <!-- Date and Time -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UFormGroup label="Start Time" name="start_time" required>
                  <UInput
                    v-model="editState.start_time"
                    type="datetime-local"
                    :disabled="editLoading"
                  />
                </UFormGroup>

                <UFormGroup label="End Time" name="end_time" required>
                  <UInput
                    v-model="editState.end_time"
                    type="datetime-local"
                    :disabled="editLoading"
                  />
                </UFormGroup>
              </div>

              <!-- Location -->
              <UFormGroup label="Address" name="location_address">
                <UInput
                  v-model="editState.location_address"
                  placeholder="e.g. Main Stadium, 123 Street"
                  :disabled="editLoading"
                />
              </UFormGroup>

              <!-- Settings -->
              <UFormGroup label="Maximum Participants" name="max_accepted">
                <UInput
                  v-model.number="editState.max_accepted"
                  type="number"
                  min="0"
                  placeholder="0 = unlimited"
                  :disabled="editLoading"
                />
              </UFormGroup>

              <UFormGroup name="cancelled">
                <UCheckbox
                  v-model="editState.cancelled"
                  label="Mark as cancelled"
                  :disabled="editLoading"
                />
              </UFormGroup>

              <UFormGroup name="hidden">
                <UCheckbox
                  v-model="editState.hidden"
                  label="Hide event"
                  :disabled="editLoading"
                />
              </UFormGroup>

              <UFormGroup name="sync_to_spond">
                <UCheckbox
                  v-model="editState.sync_to_spond"
                  label="Sync changes to Spond immediately"
                  :disabled="editLoading"
                />
                <template #help>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    If unchecked, changes will be saved locally. You can sync them to Spond later.
                  </p>
                </template>
              </UFormGroup>

              <!-- Actions -->
              <div class="flex justify-end gap-3 pt-4">
                <UButton
                  color="gray"
                  variant="ghost"
                  :disabled="editLoading"
                  @click="isEditModalOpen = false"
                >
                  Cancel
                </UButton>
                <UButton
                  type="submit"
                  color="primary"
                  :loading="editLoading"
                  :disabled="editLoading"
                >
                  Save Changes
                </UButton>
              </div>
            </UForm>
          </UCard>
        </UModal>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '#ui/types'

definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const route = useRoute()
const api = useApi()
const toast = useToast()

const eventId = computed(() => parseInt(route.params.id as string))

const event = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const searchQuery = ref('')
const selectedTab = ref(0)
const pushing = ref(false)
const isEditModalOpen = ref(false)
const editLoading = ref(false)

// Edit form schema
const editSchema = z.object({
  heading: z.string().min(3, 'Heading must be at least 3 characters').optional(),
  description: z.string().optional(),
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  location_address: z.string().optional(),
  max_accepted: z.number().min(0).optional(),
  cancelled: z.boolean().optional(),
  hidden: z.boolean().optional(),
  sync_to_spond: z.boolean().optional()
})

type EditSchema = z.output<typeof editSchema>

// Edit form state
const editState = reactive<EditSchema>({
  heading: '',
  description: '',
  start_time: '',
  end_time: '',
  location_address: '',
  max_accepted: 0,
  cancelled: false,
  hidden: false,
  sync_to_spond: false
})

const tabs = [
  { label: 'All', value: 'all' },
  { label: 'Accepted', value: 'accepted' },
  { label: 'Declined', value: 'declined' },
  { label: 'Unanswered', value: 'unanswered' }
]

onMounted(async () => {
  await loadEvent()
})

const loadEvent = async () => {
  loading.value = true
  error.value = null
  try {
    event.value = await api.getEvent(eventId.value)
  } catch (err: any) {
    console.error('Failed to load event:', err)
    error.value = err?.data?.detail || 'Failed to load event details'
    toast.add({ title: 'Error', description: error.value, color: 'red' })
  } finally {
    loading.value = false
  }
}

const openEditModal = () => {
  // Populate edit form with current event data
  editState.heading = event.value.heading
  editState.description = event.value.description || ''
  editState.start_time = event.value.start_time ? new Date(event.value.start_time).toISOString().slice(0, 16) : ''
  editState.end_time = event.value.end_time ? new Date(event.value.end_time).toISOString().slice(0, 16) : ''
  editState.location_address = event.value.location_address || ''
  editState.max_accepted = event.value.max_accepted || 0
  editState.cancelled = event.value.cancelled || false
  editState.hidden = event.value.hidden || false
  editState.sync_to_spond = false
  isEditModalOpen.value = true
}

const handleEditSubmit = async (submitEvent: FormSubmitEvent<EditSchema>) => {
  editLoading.value = true
  try {
    const { $api } = useNuxtApp()

    // Prepare update data
    const updateData: any = {}

    if (submitEvent.data.heading) updateData.heading = submitEvent.data.heading
    if (submitEvent.data.description !== undefined) updateData.description = submitEvent.data.description
    if (submitEvent.data.start_time) updateData.start_time = new Date(submitEvent.data.start_time).toISOString()
    if (submitEvent.data.end_time) updateData.end_time = new Date(submitEvent.data.end_time).toISOString()
    if (submitEvent.data.location_address !== undefined) updateData.location_address = submitEvent.data.location_address
    if (submitEvent.data.max_accepted !== undefined) updateData.max_accepted = submitEvent.data.max_accepted
    if (submitEvent.data.cancelled !== undefined) updateData.cancelled = submitEvent.data.cancelled
    if (submitEvent.data.hidden !== undefined) updateData.hidden = submitEvent.data.hidden
    if (submitEvent.data.sync_to_spond !== undefined) updateData.sync_to_spond = submitEvent.data.sync_to_spond

    await $api(`/events/${eventId.value}`, {
      method: 'PUT',
      body: updateData
    })

    toast.add({
      title: 'Success',
      description: submitEvent.data.sync_to_spond
        ? 'Event updated and synced to Spond'
        : 'Event updated locally',
      color: 'green'
    })

    isEditModalOpen.value = false
    await loadEvent()
  } catch (err: any) {
    toast.add({
      title: 'Error',
      description: err.data?.detail || 'Failed to update event',
      color: 'red'
    })
  } finally {
    editLoading.value = false
  }
}

const handlePushToSpond = async () => {
  pushing.value = true
  try {
    const { $api } = useNuxtApp()

    await $api(`/events/${eventId.value}/push-to-spond`, {
      method: 'POST'
    })

    toast.add({
      title: 'Success',
      description: 'Event pushed to Spond successfully',
      color: 'green'
    })

    await loadEvent()
  } catch (err: any) {
    toast.add({
      title: 'Error',
      description: err.data?.detail || 'Failed to push event to Spond',
      color: 'red'
    })
  } finally {
    pushing.value = false
  }
}

const responseStats = computed(() => {
  if (!event.value?.responses?.responses) {
    return { accepted: 0, declined: 0, unanswered: 0, total: 0 }
  }

  const responses = event.value.responses.responses
  return {
    accepted: responses.filter((r: any) => r.answer?.toLowerCase() === 'accepted').length,
    declined: responses.filter((r: any) => r.answer?.toLowerCase() === 'declined').length,
    unanswered: responses.filter((r: any) =>
      !r.answer || r.answer.toLowerCase() === 'unanswered'
    ).length,
    total: responses.length
  }
})

const filteredAttendees = (type: string) => {
  if (!event.value?.responses?.responses) return []

  let attendees = event.value.responses.responses

  // Filter by response type
  if (type !== 'all') {
    attendees = attendees.filter((r: any) => {
      const answer = r.answer?.toLowerCase() || 'unanswered'
      if (type === 'unanswered') {
        return !r.answer || answer === 'unanswered'
      }
      return answer === type
    })
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    attendees = attendees.filter((r: any) => {
      const name = `${r.profile?.firstName || ''} ${r.profile?.lastName || ''}`.toLowerCase()
      const email = r.profile?.email?.toLowerCase() || ''
      return name.includes(query) || email.includes(query)
    })
  }

  return attendees
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getInitials = (profile: any) => {
  if (!profile) return '?'
  const first = profile.firstName?.[0] || ''
  const last = profile.lastName?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const formatAnswer = (answer: string) => {
  if (!answer) return 'Unanswered'
  return answer.charAt(0).toUpperCase() + answer.slice(1).toLowerCase()
}

const getResponseColor = (answer: string) => {
  const ans = answer?.toLowerCase() || 'unanswered'
  if (ans === 'accepted') return 'green'
  if (ans === 'declined') return 'red'
  return 'gray'
}

const getEventTypeColor = (type: string) => {
  const typeMap: Record<string, string> = {
    'TRAINING': 'blue',
    'EVENT': 'purple',
    'MATCH': 'orange',
    'MEETING': 'cyan'
  }
  return typeMap[type?.toUpperCase()] || 'gray'
}
</script>
