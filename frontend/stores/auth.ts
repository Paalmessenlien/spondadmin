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
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    user: null as User | null,
    loading: false,
    selectedGroupId: null as string | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isLoading: (state) => state.loading,
    hasSelectedGroup: (state) => !!state.selectedGroupId,
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

      if (import.meta.client) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('selected_group_id')
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

    async initAuth() {
      // Try to restore token and selected group from localStorage
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
      }
    },
  },
})
