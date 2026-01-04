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

  // Helper to inject group_id from auth store into params
  const withGroupFilter = (params: Record<string, any> = {}): Record<string, any> => {
    if (authStore.selectedGroupId && !params.group_id) {
      return { ...params, group_id: authStore.selectedGroupId }
    }
    return params
  }

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
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/events/?${query}`)
  }

  const syncEvents = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/events/sync?${query}`, { method: 'POST' })
  }

  const getEventStats = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/events/stats?${query}`)
  }

  const getEvent = async (id: number) => {
    return makeRequest(`/events/${id}`)
  }

  const createEvent = async (data: any) => {
    return makeRequest<any>('/events/', {
      method: 'POST',
      body: data,
    })
  }

  const updateEvent = async (id: number, data: any) => {
    return makeRequest<any>(`/events/${id}`, {
      method: 'PUT',
      body: data,
    })
  }

  const pushEventToSpond = async (id: number) => {
    return makeRequest<any>(`/events/${id}/push-to-spond`, {
      method: 'POST',
    })
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
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/members/?${query}`)
  }

  const syncMembers = async () => {
    return makeRequest('/members/sync', { method: 'POST' })
  }

  const getMemberStats = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/members/stats?${query}`)
  }

  const getMember = async (id: number) => {
    return makeRequest(`/members/${id}`)
  }

  // Analytics
  const getAnalyticsSummary = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/summary?${query}`)
  }

  const getAttendanceTrends = async (period: string = 'month', params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter({ ...params, period })
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/attendance-trends?${query}`)
  }

  const getResponseRates = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/response-rates?${query}`)
  }

  const getEventTypeDistribution = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/event-types?${query}`)
  }

  const getMemberParticipation = async (limit: number = 10, params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter({ ...params, limit: limit.toString() })
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/member-participation?${query}`)
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
    createEvent,
    updateEvent,
    pushEventToSpond,
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
