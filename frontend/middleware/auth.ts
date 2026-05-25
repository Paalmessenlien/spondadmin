export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const { isSignedIn, isLoaded, getToken } = useAuth()

  // Wait for Clerk to initialize so we don't race the page render.
  if (!isLoaded.value) {
    await new Promise<void>((resolve) => {
      const stop = watch(isLoaded, (loaded) => {
        if (loaded) {
          stop()
          resolve()
        }
      })
    })
  }

  if (!isSignedIn.value) {
    if (to.path !== '/login' && !to.path.startsWith('/login/')) {
      return navigateTo('/login')
    }
    return
  }

  const authStore = useAuthStore()
  if (!authStore.user) {
    // Fetch the local admin row directly. Bypassing useApi avoids the
    // Pinia/composable resolution gotchas (useAuth in here returns
    // *computed refs*, so getToken must be unwrapped with .value).
    const token = await getToken.value()
    if (!token) {
      return navigateTo('/login?error=no_token')
    }

    const config = useRuntimeConfig()
    try {
      const me = await $fetch<any>('/auth/me', {
        baseURL: config.public.apiBase,
        headers: { Authorization: `Bearer ${token}` },
      })
      authStore.user = me
      authStore.restoreSelectionsFromStorage()
    } catch {
      return navigateTo('/login?error=no_admin')
    }
  }

  if (!authStore.user) {
    return navigateTo('/login?error=no_admin')
  }
})
