<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const { canManageSystem } = usePermissions()
if (!canManageSystem.value) navigateTo('/dashboard')

const route = useRoute()
const router = useRouter()
const categoryStore = useCategoryStore()
const toast = useToast()

const categoryId = computed(() => parseInt(route.params.id as string))
const category = ref<any>(null)
const formData = ref({
  name: '',
  description: '',
  color: '#3B82F6',
  icon: 'i-heroicons-tag',
  pattern_rules: { patterns: [] },
  priority: 100,
  is_active: true
})

onMounted(async () => {
  category.value = await categoryStore.fetchCategory(categoryId.value)
  Object.assign(formData.value, category.value)
})

const handleSubmit = async () => {
  try {
    await categoryStore.updateCategory(categoryId.value, formData.value)
    toast.add({ title: 'Success', description: 'Category updated', color: 'green' })
    router.push('/dashboard/settings/categories')
  } catch (error: any) {
    toast.add({ title: 'Error', description: error.message, color: 'red' })
  }
}
</script>

<template>
  <div class="p-6">
    <Breadcrumb :items="[
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Settings', to: '/dashboard/settings' },
      { label: 'Categories', to: '/dashboard/settings/categories' },
      { label: category?.name || 'Edit' }
    ]" />

    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Edit Category</h1>

      <UCard v-if="category">
        <div class="space-y-6">
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Name" required>
              <UInput v-model="formData.name" />
            </UFormGroup>
            <UFormGroup label="Priority">
              <UInput v-model.number="formData.priority" type="number" />
            </UFormGroup>
          </div>

          <UFormGroup label="Description">
            <UTextarea v-model="formData.description" :rows="2" />
          </UFormGroup>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Color">
              <UInput v-model="formData.color" type="color" />
            </UFormGroup>
            <UFormGroup label="Icon">
              <UInput v-model="formData.icon" placeholder="i-heroicons-tag" />
            </UFormGroup>
          </div>

          <UFormGroup label="Pattern Rules">
            <PatternRuleBuilder v-model="formData.pattern_rules" />
          </UFormGroup>

          <UCheckbox v-model="formData.is_active" label="Active" />

          <div class="flex gap-2">
            <UButton @click="handleSubmit">Save Changes</UButton>
            <UButton to="/dashboard/settings/categories" color="gray" variant="soft">Cancel</UButton>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
