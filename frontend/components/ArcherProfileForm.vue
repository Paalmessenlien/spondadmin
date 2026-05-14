<template>
  <div class="space-y-6">
    <div v-if="loading" class="flex justify-center py-8">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin h-6 w-6 text-gray-400" />
    </div>

    <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UFormGroup label="Bow Type">
          <USelectMenu
            v-model="form.bow_type"
            :items="bowTypes"
            placeholder="Select bow type"
          />
        </UFormGroup>

        <UFormGroup label="Division">
          <USelectMenu
            v-model="form.division"
            :items="divisions"
            placeholder="Select division"
          />
        </UFormGroup>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UFormGroup label="Skill Level">
          <USelectMenu
            v-model="form.skill_level"
            :items="skillLevels"
            placeholder="Select skill level"
          />
        </UFormGroup>

        <UFormGroup label="Club Join Date">
          <DateInputISO v-model="form.club_join_date" />
        </UFormGroup>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UFormGroup label="Archery GB Number">
          <UInput v-model="form.archery_gb_number" placeholder="e.g., 123456" />
        </UFormGroup>

        <UFormGroup label="Current Classification">
          <USelectMenu
            v-model="form.current_classification"
            :items="classifications"
            placeholder="Select classification"
          />
        </UFormGroup>
      </div>

      <UFormGroup label="Current Handicap">
        <UInput v-model.number="form.current_handicap" type="number" min="0" max="150" placeholder="0-150" />
      </UFormGroup>

      <UFormGroup label="Notes">
        <UTextarea v-model="form.notes" :rows="3" placeholder="Additional notes..." />
      </UFormGroup>

      <div class="flex gap-2">
        <UButton :loading="saving" @click="handleSave">
          {{ hasProfile ? 'Update Profile' : 'Create Profile' }}
        </UButton>
        <UButton
          v-if="hasProfile"
          color="red"
          variant="soft"
          :loading="deleting"
          @click="handleDelete"
        >
          Delete Profile
        </UButton>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  memberId: number
}>()

const emit = defineEmits<{
  saved: []
}>()

const api = useApi()
const toast = useToast()

const loading = ref(true)
const saving = ref(false)
const deleting = ref(false)
const hasProfile = ref(false)

const form = ref({
  bow_type: null as string | null,
  division: null as string | null,
  skill_level: null as string | null,
  club_join_date: null as string | null,
  archery_gb_number: null as string | null,
  current_classification: null as string | null,
  current_handicap: null as number | null,
  notes: null as string | null,
})

const bowTypes = ['Recurve', 'Compound', 'Barebow', 'Longbow', 'Traditional', 'Crossbow']
const divisions = ['Senior', 'Junior', 'Under 18', 'Under 15', 'Under 12', '50+', '60+', '70+']
const skillLevels = ['Beginner', 'Intermediate', 'Advanced', 'Elite']
const classifications = [
  'Archer 3rd Class',
  'Archer 2nd Class',
  'Archer 1st Class',
  'Bowman 3rd Class',
  'Bowman 2nd Class',
  'Bowman 1st Class',
  'Bowman',
  'Master Bowman',
  'Grand Master Bowman',
  'Elite Master Bowman',
]

onMounted(async () => {
  try {
    const profile = await api.getArcherProfile(props.memberId)
    if (profile) {
      hasProfile.value = true
      Object.assign(form.value, profile)
    }
  } catch {
    // No profile exists yet - that's fine
  } finally {
    loading.value = false
  }
})

const handleSave = async () => {
  saving.value = true
  try {
    await api.saveArcherProfile(props.memberId, form.value)
    hasProfile.value = true
    toast.add({ title: 'Success', description: 'Archery profile saved', color: 'green' })
    emit('saved')
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message || 'Failed to save profile', color: 'red' })
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!confirm('Delete this archery profile?')) return
  deleting.value = true
  try {
    await api.deleteArcherProfile(props.memberId)
    hasProfile.value = false
    form.value = {
      bow_type: null,
      division: null,
      skill_level: null,
      club_join_date: null,
      archery_gb_number: null,
      current_classification: null,
      current_handicap: null,
      notes: null,
    }
    toast.add({ title: 'Success', description: 'Archery profile deleted', color: 'green' })
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message || 'Failed to delete profile', color: 'red' })
  } finally {
    deleting.value = false
  }
}
</script>
