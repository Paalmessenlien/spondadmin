/**
 * Category Store
 * Manages event categories state
 */
import { defineStore } from 'pinia'

interface PatternRule {
  type: 'contains' | 'starts_with' | 'ends_with' | 'regex'
  value: string
  case_insensitive: boolean
}

interface Category {
  id: number
  name: string
  description?: string
  color: string
  icon: string
  pattern_rules: {
    patterns: PatternRule[]
  }
  priority: number
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

interface CategoryDistribution {
  category_id: number
  category_name: string
  color: string
  icon: string
  event_count: number
  percentage: number
}

export const useCategoryStore = defineStore('category', {
  state: () => ({
    categories: [] as Category[],
    selectedCategories: [] as number[],
    loading: false,
    error: null as string | null,
  }),

  getters: {
    activeCategories: (state) => state.categories.filter(c => c.is_active),

    categoriesById: (state) => {
      return Object.fromEntries(state.categories.map(c => [c.id, c]))
    },

    categoryColors: (state) => {
      return Object.fromEntries(state.categories.map(c => [c.id, c.color]))
    },

    categoryNames: (state) => {
      return Object.fromEntries(state.categories.map(c => [c.id, c.name]))
    },

    defaultCategory: (state) => state.categories.find(c => c.is_default),

    sortedCategories: (state) => {
      return [...state.categories].sort((a, b) => a.priority - b.priority)
    },
  },

  actions: {
    async fetchCategories(activeOnly: boolean = true) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        this.categories = await api.getCategories(activeOnly)
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch categories'
        console.error('Failed to fetch categories:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchCategory(id: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const category = await api.getCategory(id)

        // Update or add to categories list
        const index = this.categories.findIndex(c => c.id === id)
        if (index !== -1) {
          this.categories[index] = category
        } else {
          this.categories.push(category)
        }

        return category
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch category'
        console.error('Failed to fetch category:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async createCategory(data: Partial<Category>) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const newCategory = await api.createCategory(data)
        this.categories.push(newCategory)
        return newCategory
      } catch (error: any) {
        this.error = error.message || 'Failed to create category'
        console.error('Failed to create category:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateCategory(id: number, data: Partial<Category>) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const updatedCategory = await api.updateCategory(id, data)

        // Update in list
        const index = this.categories.findIndex(c => c.id === id)
        if (index !== -1) {
          this.categories[index] = updatedCategory
        }

        return updatedCategory
      } catch (error: any) {
        this.error = error.message || 'Failed to update category'
        console.error('Failed to update category:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteCategory(id: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        await api.deleteCategory(id)

        // Remove from list
        this.categories = this.categories.filter(c => c.id !== id)
      } catch (error: any) {
        this.error = error.message || 'Failed to delete category'
        console.error('Failed to delete category:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async bulkCategorizeEvents(payload: { event_ids?: number[], force_recategorize?: boolean }) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const result = await api.bulkCategorizeEvents(payload)
        return result
      } catch (error: any) {
        this.error = error.message || 'Failed to categorize events'
        console.error('Failed to categorize events:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchCategoryStatistics(params: Record<string, any> = {}) {
      this.loading = true
      this.error = null

      try {
        const api = useApi()
        const stats = await api.getCategoryStatistics(params)
        return stats as CategoryDistribution[]
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch category statistics'
        console.error('Failed to fetch category statistics:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    setSelectedCategories(categoryIds: number[]) {
      this.selectedCategories = categoryIds
    },

    toggleCategorySelection(categoryId: number) {
      const index = this.selectedCategories.indexOf(categoryId)
      if (index !== -1) {
        this.selectedCategories.splice(index, 1)
      } else {
        this.selectedCategories.push(categoryId)
      }
    },

    clearSelectedCategories() {
      this.selectedCategories = []
    },

    getCategoryById(id: number): Category | undefined {
      return this.categories.find(c => c.id === id)
    },

    getCategoryColor(id: number): string {
      return this.categories.find(c => c.id === id)?.color || '#6B7280'
    },

    getCategoryName(id: number): string {
      return this.categories.find(c => c.id === id)?.name || 'Unknown'
    },
  },
})
