/**
 * API Client Composable
 * Handles all HTTP requests to the backend API
 *
 * Note: For data fetching in components, prefer using useFetch or useAsyncData directly.
 * This composable is mainly for imperative operations (login, sync, mutations).
 */

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
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

  // Categories
  const getCategories = async (activeOnly: boolean = true) => {
    const query = new URLSearchParams({ active_only: activeOnly.toString() }).toString()
    return makeRequest(`/categories/?${query}`)
  }

  const getCategory = async (id: number) => {
    return makeRequest(`/categories/${id}`)
  }

  const createCategory = async (data: any) => {
    return makeRequest('/categories/', {
      method: 'POST',
      body: data,
    })
  }

  const updateCategory = async (id: number, data: any) => {
    return makeRequest(`/categories/${id}`, {
      method: 'PUT',
      body: data,
    })
  }

  const deleteCategory = async (id: number) => {
    return makeRequest(`/categories/${id}`, {
      method: 'DELETE',
    })
  }

  const duplicateCategory = async (id: number) => {
    return makeRequest(`/categories/${id}/duplicate`, {
      method: 'POST',
    })
  }

  const bulkCategorizeEvents = async (payload: { event_ids?: number[], force_recategorize?: boolean }) => {
    return makeRequest('/categories/bulk-categorize', {
      method: 'POST',
      body: payload,
    })
  }

  const getCategoryStatistics = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/categories/statistics/distribution?${query}`)
  }

  // Reports
  const getReports = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/reports/?${query}`)
  }

  const getReport = async (id: number) => {
    return makeRequest(`/reports/${id}`)
  }

  const createReport = async (data: any) => {
    return makeRequest('/reports/', {
      method: 'POST',
      body: data,
    })
  }

  const updateReport = async (id: number, data: any) => {
    return makeRequest(`/reports/${id}`, {
      method: 'PUT',
      body: data,
    })
  }

  const deleteReport = async (id: number) => {
    return makeRequest(`/reports/${id}`, {
      method: 'DELETE',
    })
  }

  const generateReport = async (id: number) => {
    return makeRequest(`/reports/${id}/generate`, {
      method: 'POST',
    })
  }

  const exportReport = async (id: number, format: string = 'csv') => {
    const query = new URLSearchParams({ format }).toString()
    // Return the full URL for download
    return `${config.public.apiBase}/reports/${id}/export?${query}`
  }

  const toggleReportFavorite = async (id: number) => {
    return makeRequest(`/reports/${id}/favorite`, {
      method: 'POST',
    })
  }

  // Category Analytics
  const getCategoryDistribution = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/categories/distribution?${query}`)
  }

  const getCategoryAttendanceComparison = async (params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/categories/attendance?${query}`)
  }

  const getCategoryTrends = async (period: string = 'month', params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter({ ...params, period })
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/categories/trends?${query}`)
  }

  const getCategoryResponseRates = async (categoryId: number, params: Record<string, any> = {}) => {
    const filteredParams = withGroupFilter(params)
    const query = new URLSearchParams(filteredParams).toString()
    return makeRequest(`/analytics/categories/${categoryId}/response-rates?${query}`)
  }

  // Scores & Records
  const getScoresSummary = async () => {
    return makeRequest('/scores/summary')
  }

  const getResults = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/scores/results?${query}`)
  }

  const getResultById = async (id: number) => {
    return makeRequest(`/scores/results/${id}`)
  }

  const getCompetitions = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/scores/competitions?${query}`)
  }

  const getCompetition = async (id: number) => {
    return makeRequest(`/scores/competitions/${id}`)
  }

  const getRecords = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/scores/records?${query}`)
  }

  const getRecordFilters = async () => {
    return makeRequest('/scores/records/filters')
  }

  const getStatistics = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/scores/statistics?${query}`)
  }

  const getMemberResults = async (spondId: string) => {
    return makeRequest(`/scores/members/${spondId}/results`)
  }

  const getMemberStatistics = async (spondId: string) => {
    return makeRequest(`/scores/members/${spondId}/statistics`)
  }

  const getMemberRecords = async (spondId: string) => {
    return makeRequest(`/scores/members/${spondId}/records`)
  }

  // Scraper
  const triggerScrape = async (data: { type: string; archer_id?: string; mode?: string }) => {
    return makeRequest('/scraper/run', { method: 'POST', body: data })
  }

  const getScrapeStatus = async () => {
    return makeRequest('/scraper/status')
  }

  const getScrapeLogs = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/scraper/logs?${query}`)
  }

  const getScrapingConfig = async () => {
    return makeRequest('/scraper/config')
  }

  const updateScrapingConfig = async (data: any) => {
    return makeRequest('/scraper/config', { method: 'PUT', body: data })
  }

  const getUnmatchedArchers = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/scraper/unmatched?${query}`)
  }

  const matchArcher = async (data: { bueskyting_id: string; spond_id: string }) => {
    return makeRequest('/scraper/match', { method: 'POST', body: data })
  }

  const dismissUnmatched = async (id: number) => {
    return makeRequest(`/scraper/dismiss/${id}`, { method: 'POST' })
  }

  const runAutoMatch = async () => {
    return makeRequest('/scraper/auto-match', { method: 'POST' })
  }

  // Admin Users
  const getAdmins = async () => {
    return makeRequest<any[]>('/auth/admins')
  }

  const getAdmin = async (id: number) => {
    return makeRequest<any>(`/auth/admins/${id}`)
  }

  const createAdmin = async (data: any) => {
    return makeRequest<any>('/auth/register', {
      method: 'POST',
      body: data,
    })
  }

  const updateAdmin = async (id: number, data: any) => {
    return makeRequest<any>(`/auth/admins/${id}`, {
      method: 'PUT',
      body: data,
    })
  }

  const deleteAdmin = async (id: number) => {
    return makeRequest(`/auth/admins/${id}`, {
      method: 'DELETE',
    })
  }

  // Backups
  const getBackups = async () => {
    return makeRequest('/backups/')
  }

  const createBackup = async (data: any = {}) => {
    return makeRequest('/backups/', { method: 'POST', body: data })
  }

  const getBackup = async (id: number) => {
    return makeRequest(`/backups/${id}`)
  }

  const restoreBackup = async (id: number) => {
    return makeRequest(`/backups/${id}/restore`, { method: 'POST' })
  }

  const uploadBackupToCdn = async (id: number) => {
    return makeRequest(`/backups/${id}/upload-cdn`, { method: 'POST' })
  }

  const deleteBackup = async (id: number) => {
    return makeRequest(`/backups/${id}`, { method: 'DELETE' })
  }

  // Migrations
  const getMigrationStatus = async () => {
    return makeRequest('/migrations/status')
  }

  const getMigrationHistory = async () => {
    return makeRequest('/migrations/history')
  }

  const runMigrations = async () => {
    return makeRequest('/migrations/run', { method: 'POST' })
  }

  // Archer Profiles
  const getArcherProfile = async (memberId: number) => {
    return makeRequest(`/members/${memberId}/archery-profile`)
  }

  const saveArcherProfile = async (memberId: number, data: any) => {
    return makeRequest(`/members/${memberId}/archery-profile`, {
      method: 'PUT',
      body: data,
    })
  }

  const deleteArcherProfile = async (memberId: number) => {
    return makeRequest(`/members/${memberId}/archery-profile`, {
      method: 'DELETE',
    })
  }

  // External Events
  const getExternalEvents = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(params).toString()
    return makeRequest(`/external-events/?${query}`)
  }

  const getExternalEvent = async (id: number) => {
    return makeRequest(`/external-events/${id}`)
  }

  const scrapeExternalEvents = async () => {
    return makeRequest('/external-events/scrape', { method: 'POST' })
  }

  const analyzeExternalEvent = async (id: number) => {
    return makeRequest(`/external-events/${id}/analyze`, { method: 'POST' })
  }

  const analyzeAllExternalEvents = () => {
    // Returns the full URL for SSE streaming - caller handles EventSource
    const token = authStore.token
    return { url: `${config.public.apiBase}/external-events/analyze-all`, token }
  }

  const stopExternalEventAnalysis = async (taskId: string) => {
    return makeRequest(`/external-events/analyze-stop/${taskId}`, { method: 'POST' })
  }

  // Training: shifts
  const getTrainingShifts = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).reduce((acc, [k, v]) => {
        if (v !== undefined && v !== null && v !== '') acc[k] = String(v)
        return acc
      }, {} as Record<string, string>)
    ).toString()
    return makeRequest<{ items: any[]; total: number }>(`/training/shifts${query ? `?${query}` : ''}`)
  }

  const getTrainingShift = async (id: number) => {
    return makeRequest<any>(`/training/shifts/${id}`)
  }

  const createTrainingShift = async (body: any) => {
    return makeRequest<any>('/training/shifts', { method: 'POST', body })
  }

  const updateTrainingShift = async (id: number, body: any) => {
    return makeRequest<any>(`/training/shifts/${id}`, { method: 'PATCH', body })
  }

  const deleteTrainingShift = async (id: number) => {
    return makeRequest(`/training/shifts/${id}`, { method: 'DELETE' })
  }

  const publishTrainingShift = async (id: number) => {
    return makeRequest<any>(`/training/shifts/${id}/publish`, { method: 'POST' })
  }

  // Training: session types
  const getTrainingSessionTypes = async () => {
    return makeRequest<{ items: any[]; total: number }>('/training/session-types')
  }

  const createTrainingSessionType = async (body: any) => {
    return makeRequest<any>('/training/session-types', { method: 'POST', body })
  }

  const updateTrainingSessionType = async (id: number, body: any) => {
    return makeRequest<any>(`/training/session-types/${id}`, { method: 'PATCH', body })
  }

  const deleteTrainingSessionType = async (id: number) => {
    return makeRequest(`/training/session-types/${id}`, { method: 'DELETE' })
  }

  // Training: aliases
  const getTrainingAliases = async () => {
    return makeRequest<{ items: any[]; total: number }>('/training/aliases')
  }

  const createTrainingAlias = async (body: any) => {
    return makeRequest<any>('/training/aliases', { method: 'POST', body })
  }

  const updateTrainingAlias = async (id: number, body: any) => {
    return makeRequest<any>(`/training/aliases/${id}`, { method: 'PATCH', body })
  }

  const deleteTrainingAlias = async (id: number) => {
    return makeRequest(`/training/aliases/${id}`, { method: 'DELETE' })
  }

  // Training: leader groups
  const getLeaderGroups = async () => {
    return makeRequest<{ items: any[]; total: number }>('/training/leader-groups')
  }

  const createLeaderGroup = async (body: any) => {
    return makeRequest<any>('/training/leader-groups', { method: 'POST', body })
  }

  const updateLeaderGroup = async (id: number, body: any) => {
    return makeRequest<any>(`/training/leader-groups/${id}`, { method: 'PATCH', body })
  }

  const deleteLeaderGroup = async (id: number) => {
    return makeRequest(`/training/leader-groups/${id}`, { method: 'DELETE' })
  }

  const setLeaderGroupMembers = async (id: number, memberIds: number[]) => {
    return makeRequest<any>(`/training/leader-groups/${id}/members`, {
      method: 'PUT',
      body: { member_ids: memberIds },
    })
  }

  // Training: import xlsx (multipart upload)
  const importTrainingXlsx = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const headers: Record<string, string> = {}
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    return $fetch<any>('/training/import', {
      baseURL: config.public.apiBase,
      method: 'POST',
      body: formData,
      headers,
      onResponseError({ response }) {
        if (response.status === 401) {
          authStore.logout()
          navigateTo('/login')
        }
      },
    })
  }

  // AI Providers
  const getAIProviders = async () => {
    return makeRequest('/ai/providers')
  }

  const getAIProvider = async (provider: string) => {
    return makeRequest(`/ai/providers/${provider}`)
  }

  const updateAIProvider = async (provider: string, data: any) => {
    return makeRequest(`/ai/providers/${provider}`, { method: 'PUT', body: data })
  }

  const testAIProvider = async (provider: string) => {
    return makeRequest(`/ai/providers/${provider}/test`, { method: 'POST' })
  }

  const getAIModels = async (provider: string) => {
    return makeRequest(`/ai/models/${provider}`)
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
    // Categories
    getCategories,
    getCategory,
    createCategory,
    updateCategory,
    deleteCategory,
    duplicateCategory,
    bulkCategorizeEvents,
    getCategoryStatistics,
    // Reports
    getReports,
    getReport,
    createReport,
    updateReport,
    deleteReport,
    generateReport,
    exportReport,
    toggleReportFavorite,
    // Category Analytics
    getCategoryDistribution,
    getCategoryAttendanceComparison,
    getCategoryTrends,
    getCategoryResponseRates,
    // Scores & Records
    getScoresSummary,
    getResults,
    getResultById,
    getCompetitions,
    getCompetition,
    getRecords,
    getRecordFilters,
    getStatistics,
    getMemberResults,
    getMemberStatistics,
    getMemberRecords,
    // Scraper
    triggerScrape,
    getScrapeStatus,
    getScrapeLogs,
    getScrapingConfig,
    updateScrapingConfig,
    getUnmatchedArchers,
    matchArcher,
    dismissUnmatched,
    runAutoMatch,
    // Admin Users
    getAdmins,
    getAdmin,
    createAdmin,
    updateAdmin,
    deleteAdmin,
    // Backups
    getBackups,
    createBackup,
    getBackup,
    restoreBackup,
    uploadBackupToCdn,
    deleteBackup,
    // Migrations
    getMigrationStatus,
    getMigrationHistory,
    runMigrations,
    // Archer Profiles
    getArcherProfile,
    saveArcherProfile,
    deleteArcherProfile,
    // External Events
    getExternalEvents,
    getExternalEvent,
    scrapeExternalEvents,
    analyzeExternalEvent,
    analyzeAllExternalEvents,
    stopExternalEventAnalysis,
    // AI Providers
    getAIProviders,
    getAIProvider,
    updateAIProvider,
    testAIProvider,
    getAIModels,
    // Training
    getTrainingShifts,
    getTrainingShift,
    createTrainingShift,
    updateTrainingShift,
    deleteTrainingShift,
    publishTrainingShift,
    getTrainingSessionTypes,
    createTrainingSessionType,
    updateTrainingSessionType,
    deleteTrainingSessionType,
    getTrainingAliases,
    createTrainingAlias,
    updateTrainingAlias,
    deleteTrainingAlias,
    getLeaderGroups,
    createLeaderGroup,
    updateLeaderGroup,
    deleteLeaderGroup,
    setLeaderGroupMembers,
    importTrainingXlsx,
  }
}
