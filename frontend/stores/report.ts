/**
 * Report Store
 * Manages saved reports state
 */
import { defineStore } from 'pinia'

interface DateRange {
  start: string
  end: string
}

interface ReportConfiguration {
  date_range?: DateRange
  group_ids?: string[]
  category_ids?: number[]
  metrics?: string[]
  chart_types?: string[]
  comparison_period?: string
}

interface Report {
  id: number
  name: string
  description?: string
  report_type: string
  configuration: ReportConfiguration
  is_public: boolean
  is_favorite: boolean
  created_by: number
  last_generated_at?: string
  created_at: string
  updated_at: string
}

interface ReportData {
  report_id: number
  report_name: string
  report_type: string
  generated_at: string
  configuration: ReportConfiguration
  data: Record<string, any>
}

export const useReportStore = defineStore('report', {
  state: () => ({
    reports: [] as Report[],
    currentReport: null as Report | null,
    reportData: null as ReportData | null,
    loading: false,
    error: null as string | null,
    filters: {
      show_public: true,
      show_favorites: false,
      report_type: null as string | null,
    },
  }),

  getters: {
    favoriteReports: (state) => state.reports.filter(r => r.is_favorite),

    publicReports: (state) => state.reports.filter(r => r.is_public),

    myReports: (state) => {
      const authStore = useAuthStore()
      return state.reports.filter(r => r.created_by === authStore.user?.id)
    },

    reportsByType: (state) => {
      const grouped: Record<string, Report[]> = {}
      state.reports.forEach(report => {
        if (!grouped[report.report_type]) {
          grouped[report.report_type] = []
        }
        grouped[report.report_type].push(report)
      })
      return grouped
    },

    recentReports: (state) => {
      return [...state.reports]
        .sort((a, b) => {
          const aDate = a.last_generated_at || a.created_at
          const bDate = b.last_generated_at || b.created_at
          return new Date(bDate).getTime() - new Date(aDate).getTime()
        })
        .slice(0, 5)
    },
  },

  actions: {
    async fetchReports(filters: Record<string, any> = {}) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const queryFilters = {
          show_public: filters.show_public ?? this.filters.show_public,
          show_favorites: filters.show_favorites ?? this.filters.show_favorites,
          report_type: filters.report_type ?? this.filters.report_type,
        }

        // Remove null/undefined values
        const cleanFilters = Object.fromEntries(
          Object.entries(queryFilters).filter(([_, v]) => v != null)
        )

        this.reports = await api.getReports(cleanFilters)
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch reports'
        console.error('Failed to fetch reports:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchReport(id: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const report = await api.getReport(id)
        this.currentReport = report

        // Update in list if exists
        const index = this.reports.findIndex(r => r.id === id)
        if (index !== -1) {
          this.reports[index] = report
        } else {
          this.reports.push(report)
        }

        return report
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch report'
        console.error('Failed to fetch report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async createReport(data: Partial<Report>) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const newReport = await api.createReport(data)
        this.reports.push(newReport)
        this.currentReport = newReport
        return newReport
      } catch (error: any) {
        this.error = error.message || 'Failed to create report'
        console.error('Failed to create report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateReport(id: number, data: Partial<Report>) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const updatedReport = await api.updateReport(id, data)

        // Update in list
        const index = this.reports.findIndex(r => r.id === id)
        if (index !== -1) {
          this.reports[index] = updatedReport
        }

        // Update current report if it's the one being updated
        if (this.currentReport?.id === id) {
          this.currentReport = updatedReport
        }

        return updatedReport
      } catch (error: any) {
        this.error = error.message || 'Failed to update report'
        console.error('Failed to update report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteReport(id: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        await api.deleteReport(id)

        // Remove from list
        this.reports = this.reports.filter(r => r.id !== id)

        // Clear current report if it's the deleted one
        if (this.currentReport?.id === id) {
          this.currentReport = null
          this.reportData = null
        }
      } catch (error: any) {
        this.error = error.message || 'Failed to delete report'
        console.error('Failed to delete report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async generateReport(id: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const data = await api.generateReport(id)
        this.reportData = data

        // Update last_generated_at in the report
        const index = this.reports.findIndex(r => r.id === id)
        if (index !== -1) {
          this.reports[index].last_generated_at = data.generated_at
        }

        return data
      } catch (error: any) {
        this.error = error.message || 'Failed to generate report'
        console.error('Failed to generate report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async exportReport(id: number, format: string = 'csv') {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const url = await api.exportReport(id, format)

        // Trigger download
        if (import.meta.client) {
          const authStore = useAuthStore()
          const link = document.createElement('a')
          link.href = url + `&token=${authStore.token}`
          link.download = `report_${id}.${format}`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        }
      } catch (error: any) {
        this.error = error.message || 'Failed to export report'
        console.error('Failed to export report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async toggleFavorite(id: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const updatedReport = await api.toggleReportFavorite(id)

        // Update in list
        const index = this.reports.findIndex(r => r.id === id)
        if (index !== -1) {
          this.reports[index] = updatedReport
        }

        // Update current report if it's the one being updated
        if (this.currentReport?.id === id) {
          this.currentReport = updatedReport
        }

        return updatedReport
      } catch (error: any) {
        this.error = error.message || 'Failed to toggle favorite'
        console.error('Failed to toggle favorite:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    setCurrentReport(report: Report | null) {
      this.currentReport = report
    },

    clearReportData() {
      this.reportData = null
    },

    updateFilters(filters: Partial<typeof this.filters>) {
      this.filters = { ...this.filters, ...filters }
    },
  },
})
