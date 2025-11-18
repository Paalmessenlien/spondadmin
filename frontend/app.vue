<template>
  <div>
    <UToaster />
    <NuxtLayout>
      <NuxtPage :key="$route.fullPath" />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()
const route = useRoute()

// Initialize auth on mount
onMounted(() => {
  authStore.initAuth()
})
</script>
