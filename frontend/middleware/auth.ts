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

  // Module gate. The backend is the real enforcement point (it 403s data
  // requests); this just keeps users out of pages they can't use, matching
  // the sidebar. Maps the first path segment under /dashboard to a module.
  // Ordered so the fallback landing prefers Dashboard, then the sidebar order.
  const MODULE_ROUTES: Array<{ module: string; route: string }> = [
    { module: 'dashboard', route: '/dashboard' },
    { module: 'members', route: '/dashboard/members' },
    { module: 'events', route: '/dashboard/events' },
    { module: 'training', route: '/dashboard/training' },
    { module: 'competitions', route: '/dashboard/competitions' },
    { module: 'scores', route: '/dashboard/scores' },
    { module: 'expenses', route: '/dashboard/expenses' },
    { module: 'projects', route: '/dashboard/projects' },
    { module: 'forms', route: '/dashboard/forms' },
    { module: 'reports', route: '/dashboard/reports' },
    { module: 'analytics', route: '/dashboard/analytics' },
    { module: 'settings', route: '/dashboard/settings' },
  ]

  const moduleForPath = (path: string): string | null => {
    if (path === '/dashboard' || path === '/dashboard/') return 'dashboard'
    const seg = path.replace(/^\/dashboard\/?/, '').split('/')[0]
    return MODULE_ROUTES.find(m => m.route === `/dashboard/${seg}`)?.module ?? null
  }

  const requiredModule = moduleForPath(to.path)
  if (requiredModule && !authStore.canAccessModule(requiredModule)) {
    // Redirect to the first module they *can* reach. If none (or that
    // target is where they already are), fall through and let the page's
    // own empty/permission state render — never redirect in a loop.
    const landing = MODULE_ROUTES.find(m => authStore.canAccessModule(m.module))
    if (landing && landing.route !== to.path) {
      return navigateTo(landing.route)
    }
  }
})
