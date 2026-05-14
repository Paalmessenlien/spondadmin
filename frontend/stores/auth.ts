/**
 * Authentication Store
 * Manages user authentication state
 */
import { defineStore } from 'pinia'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  role: 'admin' | 'editor' | 'viewer'
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    user: null as User | null,
    loading: false,
    selectedGroupId: null as string | null,
    // Active training plan — mirror of selectedGroupId. Persists across
    // sessions in localStorage. Set null = no plan picked yet.
    selectedPlanId: null as number | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isLoading: (state) => state.loading,
    hasSelectedGroup: (state) => !!state.selectedGroupId,
    hasSelectedPlan: (state) => state.selectedPlanId !== null,
    isAdmin: (state) => state.user?.role === 'admin',
    canEdit: (state) => ['admin', 'editor'].includes(state.user?.role ?? ''),
    canManageSystem: (state) => state.user?.role === 'admin',
  },

  actions: {
    async login(username: string, password: string) {
      this.loading = true
      try {
        const api = useApi()
        const response = await api.login(username, password)

        this.token = response.access_token

        // Store token in localStorage for persistence
        if (import.meta.client) {
          localStorage.setItem('auth_token', response.access_token)
        }

        // Fetch user data
        await this.fetchUser()

        return true
      } catch (error) {
        console.error('Login failed:', error)
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchUser() {
      try {
        const api = useApi()
        this.user = await api.getCurrentUser()
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.selectedGroupId = null
      this.selectedPlanId = null

      if (import.meta.client) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('selected_group_id')
        localStorage.removeItem('selected_plan_id')
      }

      navigateTo('/login')
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

    async initAuth() {
      // Try to restore token and selected group / plan from localStorage
      if (import.meta.client) {
        const token = localStorage.getItem('auth_token')
        if (token) {
          this.token = token
          await this.fetchUser()
        }

        const selectedGroupId = localStorage.getItem('selected_group_id')
        if (selectedGroupId) {
          this.selectedGroupId = selectedGroupId
        }

        const selectedPlanId = localStorage.getItem('selected_plan_id')
        if (selectedPlanId) {
          const n = parseInt(selectedPlanId, 10)
          if (Number.isFinite(n)) this.selectedPlanId = n
        }
      }
    },
  },
})
