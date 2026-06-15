<template>
  <div class="flex flex-col items-center justify-center py-24 gap-3">
    <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8 text-gray-400" />
    <p class="text-gray-500">Oppretter skjema…</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const toast = useToast()

onMounted(async () => {
  try {
    const form: any = await api.createForm({ title: 'Nytt skjema' })
    await navigateTo(`/dashboard/forms/${form.id}/edit`, { replace: true })
  } catch (err: any) {
    toast.add({ title: 'Kunne ikke opprette skjema', description: err?.data?.detail || 'Ukjent feil', color: 'error' })
    navigateTo('/dashboard/forms')
  }
})
</script>
