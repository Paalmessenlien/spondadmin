/**
 * API Client Composable
 * Handles all HTTP requests to the backend API
 *
 * Note: For data fetching in components, prefer using useFetch or useAsyncData directly.
 * This composable is mainly for imperative operations (login, sync, mutations).
 */

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: any
  headers?: Record<string, string>
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  const makeRequest = async <T>(endpoint: string, options: ApiOptions = {}): Promise<T> => {
    const { method = 'GET', body, headers = {} } = options

    // Add auth token if available
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    try {
      const response = await $fetch<T>(endpoint, {
        baseURL: config.public.apiBase,
        method,
        body, // $fetch automatically handles JSON stringification
        headers,
        onResponseError({ response }) {
          // Handle 401 unauthorized
          if (response.status === 401) {
            authStore.logout()
            navigateTo('/login')
          }
        },
      })

      return response
    } catch (error) {
      throw error
    }
  }

  // Authentication
  const login = async (username: string, password: string) => {
    const response = await makeRequest<{ access_token: string; token_type: string }>(
      '/auth/login',
      {
        method: 'POST',
        body: { username, password },
      }
    )
    return response
  }

  const getCurrentUser = async () => {
    return makeRequest('/auth/me')
  }

  // Events
  const getEvents = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/events/?${query}`)
  }

  const syncEvents = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/events/sync?${query}`, { method: 'POST' })
  }

  const getEventStats = async () => {
    return makeRequest('/events/stats')
  }

  const getEvent = async (id: number) => {
    return makeRequest(`/events/${id}`)
  }

  // Groups
  const getGroups = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/groups/?${query}`)
  }

  const syncGroups = async () => {
    return makeRequest('/groups/sync', { method: 'POST' })
  }

  const getGroupStats = async () => {
    return makeRequest('/groups/stats')
  }

  const getGroup = async (id: number) => {
    return makeRequest(`/groups/${id}`)
  }

  // Members
  const getMembers = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/members/?${query}`)
  }

  const syncMembers = async () => {
    return makeRequest('/members/sync', { method: 'POST' })
  }

  const getMemberStats = async () => {
    return makeRequest('/members/stats')
  }

  const getMember = async (id: number) => {
    return makeRequest(`/members/${id}`)
  }

  // Analytics
  const getAnalyticsSummary = async () => {
    return makeRequest('/analytics/summary')
  }

  const getAttendanceTrends = async (period: string = 'month') => {
    return makeRequest(`/analytics/attendance-trends?period=${period}`)
  }

  const getResponseRates = async () => {
    return makeRequest('/analytics/response-rates')
  }

  const getEventTypeDistribution = async () => {
    return makeRequest('/analytics/event-types')
  }

  const getMemberParticipation = async (limit: number = 10) => {
    return makeRequest(`/analytics/member-participation?limit=${limit}`)
  }

  return {
    // Auth
    login,
    getCurrentUser,
    // Events
    getEvents,
    syncEvents,
    getEventStats,
    getEvent,
    // Groups
    getGroups,
    syncGroups,
    getGroupStats,
    getGroup,
    // Members
    getMembers,
    syncMembers,
    getMemberStats,
    getMember,
    // Analytics
    getAnalyticsSummary,
    getAttendanceTrends,
    getResponseRates,
    getEventTypeDistribution,
    getMemberParticipation,
  }
}
