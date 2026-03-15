<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'dashboard' })
navigateTo('/dashboard/settings/categories', { redirectCode: 301 })
</script>

<template>
  <div class="p-6 text-center text-gray-500">
    Redirecting to Settings...
  </div>
</template>
