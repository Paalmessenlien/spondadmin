<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h2 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
            Spond Admin
          </h2>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Sign in to your account
          </p>
        </div>
      </template>

      <div
        v-if="route.query.error === 'no_admin'"
        class="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 p-3 border border-red-200 dark:border-red-800"
      >
        <div class="flex items-start">
          <UIcon name="i-heroicons-exclamation-circle" class="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
          <div class="ml-2 text-sm text-red-700 dark:text-red-300">
            Your sign-in succeeded but no admin account is linked to that email. Please ask an existing admin to invite you.
          </div>
        </div>
      </div>

      <ClientOnly>
        <UButton
          block
          size="lg"
          :loading="redirecting || !isLoaded"
          @click="goToSignIn"
        >
          {{ isLoaded ? 'Continue to sign in' : 'Loading…' }}
        </UButton>

        <p class="mt-4 text-center text-xs text-gray-500 dark:text-gray-400">
          You'll be redirected to a secure Clerk page where you can sign in with email, Google, or a magic link.
        </p>
      </ClientOnly>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: [] })

const route = useRoute()
const clerk = useClerk()
const { isSignedIn, isLoaded } = useAuth()
const redirecting = ref(false)

const goToSignIn = async () => {
  if (!clerk.value) return
  redirecting.value = true
  try {
    await clerk.value.redirectToSignIn({
      signInForceRedirectUrl: `${window.location.origin}/dashboard`,
    })
  } catch (e) {
    console.error('redirectToSignIn failed', e)
    redirecting.value = false
  }
}

// Already signed in (e.g. came back from Clerk's hosted page) — go straight to dashboard.
watchEffect(() => {
  if (isLoaded.value && isSignedIn.value) {
    navigateTo('/dashboard')
  }
})
</script>
