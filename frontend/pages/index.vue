<script setup>
// Redirect to dashboard if authenticated, otherwise login
const authStore = useAuthStore()

if (authStore.isAuthenticated) {
  navigateTo('/dashboard')
} else {
  navigateTo('/login')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <UIcon name="i-heroicons-arrow-path" class="animate-spin h-8 w-8" />
  </div>
</template>
