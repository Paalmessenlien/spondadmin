/**
 * Authentication store.
 *
 * Identity (sign-in/sign-out, token issuance, refresh) is owned by
 * Clerk via @clerk/nuxt — use ``useAuth()`` / ``useUser()`` /
 * ``useClerk()`` for those. This store holds the *local* admin row
 * (role, is_active, selected group/plan) loaded from
 * ``GET /auth/me`` after the user has signed in to Clerk.
 */
import { defineStore } from 'pinia'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  role: 'admin' | 'editor' | 'viewer' | 'kasserer'
  clerk_user_id?: string | null
  // Raw per-user allow-list: null = not customised (uses role defaults).
  modules?: string[] | null
  // Resolved set the user can actually reach — what nav/pages gate on.
  effective_modules?: string[]
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    loading: false,
    selectedGroupId: null as string | null,
    // Active training plan. Persists across sessions in localStorage.
    selectedPlanId: null as number | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    isLoading: (state) => state.loading,
    hasSelectedGroup: (state) => !!state.selectedGroupId,
    hasSelectedPlan: (state) => state.selectedPlanId !== null,
    isAdmin: (state) => state.user?.role === 'admin',
    canEdit: (state) => ['admin', 'editor'].includes(state.user?.role ?? ''),
    canManageSystem: (state) => state.user?.role === 'admin',
    // Treasurer: may review/approve/mark-paid expense reimbursements.
    isKasserer: (state) => state.user?.role === 'kasserer',
    // Anyone who can act on the expense review queue.
    canReviewExpenses: (state) => ['admin', 'kasserer'].includes(state.user?.role ?? ''),
    // Module allow-list check. Admins implicitly reach everything; the
    // backend resolves that into effective_modules, so we just test
    // membership. Returns a predicate: canAccessModule('members').
    canAccessModule: (state) => (moduleKey: string): boolean => {
      if (state.user?.role === 'admin' || state.user?.is_superuser) return true
      return (state.user?.effective_modules ?? []).includes(moduleKey)
    },
  },

  actions: {
    async fetchUser() {
      this.loading = true
      try {
        const api = useApi()
        this.user = await api.getCurrentUser() as User
        return this.user
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.user = null
        return null
      } finally {
        this.loading = false
      }
    },

    clearLocalState() {
      this.user = null
      this.selectedGroupId = null
      this.selectedPlanId = null
      if (import.meta.client) {
        localStorage.removeItem('selected_group_id')
        localStorage.removeItem('selected_plan_id')
      }
    },

    setSelectedGroup(groupId: string | null) {
      this.selectedGroupId = groupId
      if (import.meta.client) {
        if (groupId) {
          localStorage.setItem('selected_group_id', groupId)
        } else {
          localStorage.removeItem('selected_group_id')
        }
      }
    },

    setSelectedPlan(planId: number | null) {
      this.selectedPlanId = planId
      if (import.meta.client) {
        if (planId !== null) {
          localStorage.setItem('selected_plan_id', String(planId))
        } else {
          localStorage.removeItem('selected_plan_id')
        }
      }
    },

    restoreSelectionsFromStorage() {
      if (!import.meta.client) return
      const selectedGroupId = localStorage.getItem('selected_group_id')
      if (selectedGroupId) this.selectedGroupId = selectedGroupId
      const selectedPlanId = localStorage.getItem('selected_plan_id')
      if (selectedPlanId) {
        const n = parseInt(selectedPlanId, 10)
        if (Number.isFinite(n)) this.selectedPlanId = n
      }
    },
  },
})
