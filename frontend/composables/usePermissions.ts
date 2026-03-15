export const usePermissions = () => {
  const authStore = useAuthStore()

  return {
    canEdit: computed(() => authStore.canEdit),
    canManageSystem: computed(() => authStore.canManageSystem),
    isAdmin: computed(() => authStore.isAdmin),
    role: computed(() => authStore.user?.role ?? 'viewer'),
  }
}
