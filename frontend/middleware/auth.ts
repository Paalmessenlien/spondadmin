export default defineNuxtRouteMiddleware(async (to, from) => {
  // Only run on client side
  if (import.meta.server) {
    return
  }

  const authStore = useAuthStore()

  // Initialize auth from localStorage if not already initialized
  if (!authStore.token) {
    await authStore.initAuth()
  }

  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
})
