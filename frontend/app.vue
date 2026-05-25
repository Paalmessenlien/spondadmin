<template>
  <div>
    <UToaster />
    <NuxtLayout>
      <NuxtPage :key="$route.fullPath" />
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
// Auth init (session loading) is owned by @clerk/nuxt; per-route fetch
// of the local admin row happens in middleware/auth.ts.
</script>
