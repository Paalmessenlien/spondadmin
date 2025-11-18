<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '#ui/types'

definePageMeta({
  middleware: 'auth',
  layout: 'dashboard'
})

const { $api } = useNuxtApp()
const toast = useToast()
const router = useRouter()

// Form schema
const schema = z.object({
  heading: z.string().min(3, 'Heading must be at least 3 characters'),
  description: z.string().optional(),
  event_type: z.enum(['EVENT', 'RECURRING', 'AVAILABILITY']),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string().min(1, 'End time is required'),
  location_address: z.string().optional(),
  location_latitude: z.number().optional(),
  location_longitude: z.number().optional(),
  max_accepted: z.number().min(0).default(0),
  cancelled: z.boolean().default(false),
  hidden: z.boolean().default(false),
  sync_to_spond: z.boolean().default(false)
})

type Schema = z.output<typeof schema>

// Form state
const loading = ref(false)
const state = reactive<Schema>({
  heading: '',
  description: '',
  event_type: 'EVENT',
  start_time: '',
  end_time: '',
  location_address: '',
  max_accepted: 0,
  cancelled: false,
  hidden: false,
  sync_to_spond: false
})

// Event type options
const eventTypeOptions = [
  { value: 'EVENT', label: 'Event' },
  { value: 'RECURRING', label: 'Recurring' },
  { value: 'AVAILABILITY', label: 'Availability' }
]

// Set default date/time (tomorrow at 10:00)
onMounted(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(10, 0, 0, 0)

  const tomorrowEnd = new Date(tomorrow)
  tomorrowEnd.setHours(12, 0, 0, 0)

  state.start_time = tomorrow.toISOString().slice(0, 16)
  state.end_time = tomorrowEnd.toISOString().slice(0, 16)
})

async function onSubmit(event: FormSubmitEvent<Schema>) {
  loading.value = true

  try {
    const response = await $api('/events', {
      method: 'POST',
      body: {
        ...event.data,
        start_time: new Date(event.data.start_time).toISOString(),
        end_time: new Date(event.data.end_time).toISOString()
      }
    })

    toast.add({
      title: 'Event created',
      description: event.data.sync_to_spond
        ? 'Event created and synced to Spond'
        : 'Event created locally',
      color: 'green'
    })

    // Navigate to the event detail page
    router.push(`/dashboard/events/${response.id}`)
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.data?.detail || 'Failed to create event',
      color: 'red'
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
        <NuxtLink to="/dashboard/events" class="hover:text-gray-700 dark:hover:text-gray-200">
          Events
        </NuxtLink>
        <UIcon name="i-heroicons-chevron-right" class="w-4 h-4" />
        <span>Create Event</span>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Create New Event
      </h1>
    </div>

    <!-- Form -->
    <UCard>
      <UForm :schema="schema" :state="state" @submit="onSubmit" class="space-y-6">
        <!-- Basic Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Basic Information
          </h3>

          <UFormGroup label="Event Title" name="heading" required>
            <UInput
              v-model="state.heading"
              placeholder="e.g. Training Session"
              :disabled="loading"
            />
          </UFormGroup>

          <UFormGroup label="Description" name="description">
            <UTextarea
              v-model="state.description"
              placeholder="Event description..."
              :rows="3"
              :disabled="loading"
            />
          </UFormGroup>

          <UFormGroup label="Event Type" name="event_type" required>
            <USelectMenu
              v-model="state.event_type"
              :options="eventTypeOptions"
              value-attribute="value"
              option-attribute="label"
              :disabled="loading"
            />
          </UFormGroup>
        </div>

        <!-- Date and Time -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Date & Time
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <UFormGroup label="Start Time" name="start_time" required>
              <UInput
                v-model="state.start_time"
                type="datetime-local"
                :disabled="loading"
              />
            </UFormGroup>

            <UFormGroup label="End Time" name="end_time" required>
              <UInput
                v-model="state.end_time"
                type="datetime-local"
                :disabled="loading"
              />
            </UFormGroup>
          </div>
        </div>

        <!-- Location -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Location
          </h3>

          <UFormGroup label="Address" name="location_address">
            <UInput
              v-model="state.location_address"
              placeholder="e.g. Main Stadium, 123 Street"
              :disabled="loading"
            />
          </UFormGroup>
        </div>

        <!-- Settings -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Settings
          </h3>

          <UFormGroup label="Maximum Participants" name="max_accepted">
            <UInput
              v-model.number="state.max_accepted"
              type="number"
              min="0"
              placeholder="0 = unlimited"
              :disabled="loading"
            />
          </UFormGroup>

          <UFormGroup name="cancelled">
            <UCheckbox
              v-model="state.cancelled"
              label="Mark as cancelled"
              :disabled="loading"
            />
          </UFormGroup>

          <UFormGroup name="hidden">
            <UCheckbox
              v-model="state.hidden"
              label="Hide event"
              :disabled="loading"
            />
          </UFormGroup>

          <UFormGroup name="sync_to_spond">
            <UCheckbox
              v-model="state.sync_to_spond"
              label="Sync to Spond immediately"
              :disabled="loading"
            />
            <template #help>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                If unchecked, event will be created locally only. You can sync it to Spond later.
              </p>
            </template>
          </UFormGroup>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-4">
          <UButton
            type="submit"
            color="primary"
            :loading="loading"
            :disabled="loading"
          >
            <UIcon name="i-heroicons-plus" class="w-4 h-4 mr-2" />
            Create Event
          </UButton>

          <UButton
            color="gray"
            variant="ghost"
            :to="'/dashboard/events'"
            :disabled="loading"
          >
            Cancel
          </UButton>
        </div>
      </UForm>
    </UCard>
  </div>
</template>
