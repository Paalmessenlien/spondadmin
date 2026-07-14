export const usePermissions = () => {
  const authStore = useAuthStore()

  return {
    canEdit: computed(() => authStore.canEdit),
    canManageSystem: computed(() => authStore.canManageSystem),
    isAdmin: computed(() => authStore.isAdmin),
    isKasserer: computed(() => authStore.isKasserer),
    canReviewExpenses: computed(() => authStore.canReviewExpenses),
    role: computed(() => authStore.user?.role ?? 'viewer'),
    // Predicate: canAccessModule('members'). Backed by the resolved
    // effective_modules from the backend (admins always pass).
    canAccessModule: (moduleKey: string) => authStore.canAccessModule(moduleKey),
  }
}
