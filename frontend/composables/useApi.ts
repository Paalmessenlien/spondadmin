/**
 * API Client Composable
 * Handles all HTTP requests to the backend API
 *
 * Note: For data fetching in components, prefer using useFetch or useAsyncData directly.
 * This composable is mainly for imperative operations (sync, mutations, invitations).
 * Sign-in itself is owned by Clerk — see pages/login/index.vue.
 */

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: any
  headers?: Record<string, string>
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const { getToken } = useAuth()
  const clerk = useClerk()

  // Helper to inject group_id from auth store into params
  const withGroupFilter = (params: Record<string, any> = {}): Record<string, any> => {
    if (authStore.selectedGroupId && !params.group_id) {
      return { ...params, group_id: authStore.selectedGroupId }
    }
    return params
  }

  const handleUnauthorized = async () => {
    authStore.clearLocalState()
    try {
      if (clerk.value) await clerk.value.signOut()
    } catch { /* ignore */ }
    navigateTo('/login')
  }

  const makeRequest = async <T>(endpoint: string, options: ApiOptions = {}): Promise<T> => {
    const { method = 'GET', body, headers = {} } = options

    const token = await getToken.value()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return await $fetch<T>(endpoint, {
      baseURL: config.public.apiBase,
      method,
      body,
      headers,
      onResponseError({ response }) {
        if (response.status === 401) {
          handleUnauthorized()
        }
      },
    })
  }

  const getCurrentUser = async () => {
    return makeRequest('/auth/me')
  }

  const inviteAdmin = async (payload: { email: string; full_name?: string; role: string }) => {
    return makeRequest('/auth/invite', { method: 'POST', body: payload })
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

  // Legacy local-account create. Clerk-based onboarding uses ``inviteAdmin``
  // above; this is kept only for one transition release and will be removed
  // alongside the /auth/register backend route in the cleanup task.
  const createAdmin = async (data: any) => {
    return makeRequest<any>('/auth/invite', {
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

  const analyzeAllExternalEvents = async () => {
    // Returns the full URL for SSE streaming - caller handles EventSource.
    // Token is fetched fresh from Clerk because EventSource has no headers,
    // so the caller has to append it to the URL or use a fetch stream.
    const token = await getToken.value()
    return { url: `${config.public.apiBase}/external-events/analyze-all`, token }
  }

  const stopExternalEventAnalysis = async (taskId: string) => {
    return makeRequest(`/external-events/analyze-stop/${taskId}`, { method: 'POST' })
  }

  // Heuristic link suggestions (Spond events / competitions) for an external event.
  const getExternalEventLinkSuggestions = async (id: number) => {
    return makeRequest(`/external-events/${id}/link-suggestions`)
  }

  // Confirm/clear the link. Only keys included in `body` are changed
  // (pass an explicit null to clear that side).
  const setExternalEventLink = async (
    id: number,
    body: { event_id?: number | null; competition_id?: number | null },
  ) => {
    return makeRequest(`/external-events/${id}/link`, {
      method: 'POST',
      body,
    })
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
    // Argless call → backwards-compatible. Pass {plan_id} to scope.
    return makeRequest<{ items: any[]; total: number }>('/training/session-types')
  }

  const getTrainingSessionTypesForPlan = async (planId: number) => {
    return makeRequest<{ items: any[]; total: number }>(
      `/training/session-types?plan_id=${planId}`
    )
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

  // Training: plans (the period container for session types)
  const getTrainingPlans = async () => {
    return makeRequest<{ items: any[]; total: number }>('/training/plans')
  }

  // Aggregated training statistics for the plans Statistics tab.
  // params: { plan_id?, start_date?, end_date?, period? ('month'|'week') }
  const getTrainingStatistics = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '') as any
    ).toString()
    return makeRequest(`/training/statistics?${query}`)
  }

  const createTrainingPlan = async (body: any) => {
    return makeRequest<any>('/training/plans', { method: 'POST', body })
  }

  const updateTrainingPlan = async (id: number, body: any) => {
    return makeRequest<any>(`/training/plans/${id}`, { method: 'PATCH', body })
  }

  const deleteTrainingPlan = async (id: number) => {
    return makeRequest(`/training/plans/${id}`, { method: 'DELETE' })
  }

  // Returns a Blob of the rendered PDF — call URL.createObjectURL on it
  // or pipe through an <a download> anchor. Doesn't go through makeRequest
  // because $fetch with responseType:'blob' is the cleanest path and
  // we don't want the JSON-parsing assumption getting in the way.
  const exportTrainingPlanPdf = async (id: number): Promise<Blob> => {
    const headers: Record<string, string> = {}
    const token = await getToken.value()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return await $fetch<Blob>(`/training/plans/${id}/export.pdf`, {
      baseURL: config.public.apiBase,
      method: 'GET',
      headers,
      responseType: 'blob',
      onResponseError({ response }) {
        if (response.status === 401) {
          handleUnauthorized()
        }
      },
    })
  }

  // Training: import xlsx (multipart upload). Always goes into a specific
  // plan now — dedup is (plan_id, name)-scoped on the backend.
  const importTrainingXlsx = async (planId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const headers: Record<string, string> = {}
    const token = await getToken.value()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return $fetch<any>(`/training/plans/${planId}/import`, {
      baseURL: config.public.apiBase,
      method: 'POST',
      body: formData,
      headers,
      onResponseError({ response }) {
        if (response.status === 401) {
          handleUnauthorized()
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

  // Expenses (utlegg)
  const getExpenses = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null) as any
    ).toString()
    return makeRequest(`/expenses/?${query}`)
  }

  const getExpense = async (id: number) => makeRequest(`/expenses/${id}`)

  const createExpense = async (body: Record<string, any>) =>
    makeRequest('/expenses/', { method: 'POST', body })

  const updateExpense = async (id: number, body: Record<string, any>) =>
    makeRequest(`/expenses/${id}`, { method: 'PATCH', body })

  const deleteExpense = async (id: number) =>
    makeRequest(`/expenses/${id}`, { method: 'DELETE' })

  const submitExpense = async (id: number) =>
    makeRequest(`/expenses/${id}/submit`, { method: 'POST' })

  const reviewExpense = async (id: number, action: string, note?: string) =>
    makeRequest(`/expenses/${id}/review`, { method: 'POST', body: { action, note } })

  // Receipt upload (multipart). Returns the attachment incl. ai_suggestions.
  const uploadExpenseAttachment = async (id: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const headers: Record<string, string> = {}
    const token = await getToken.value()
    if (token) headers['Authorization'] = `Bearer ${token}`
    return $fetch<any>(`/expenses/${id}/attachments`, {
      baseURL: config.public.apiBase,
      method: 'POST',
      body: formData,
      headers,
      onResponseError({ response }) {
        if (response.status === 401) handleUnauthorized()
      },
    })
  }

  const deleteExpenseAttachment = async (id: number, attachmentId: number) =>
    makeRequest(`/expenses/${id}/attachments/${attachmentId}`, { method: 'DELETE' })

  // CSV export (kasserer/admin). Returns a Blob for download.
  const exportExpensesCsv = async (params: Record<string, any> = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null) as any
    ).toString()
    const headers: Record<string, string> = {}
    const token = await getToken.value()
    if (token) headers['Authorization'] = `Bearer ${token}`
    return $fetch<Blob>(`/expenses/export.csv?${query}`, {
      baseURL: config.public.apiBase,
      headers,
      responseType: 'blob',
    })
  }

  return {
    // Auth
    getCurrentUser,
    inviteAdmin,
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
    getExternalEventLinkSuggestions,
    setExternalEventLink,
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
    getTrainingSessionTypesForPlan,
    createTrainingSessionType,
    updateTrainingSessionType,
    deleteTrainingSessionType,
    getTrainingPlans,
    getTrainingStatistics,
    createTrainingPlan,
    updateTrainingPlan,
    deleteTrainingPlan,
    exportTrainingPlanPdf,
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
    // Expenses (utlegg)
    getExpenses,
    getExpense,
    createExpense,
    updateExpense,
    deleteExpense,
    submitExpense,
    reviewExpense,
    uploadExpenseAttachment,
    deleteExpenseAttachment,
    exportExpensesCsv,
  }
}
