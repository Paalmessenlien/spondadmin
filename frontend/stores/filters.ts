/**
 * Filters Store
 * Manages global filtering state across the application
 */
import { defineStore } from 'pinia'

export const useFiltersStore = defineStore('filters', {
  state: () => ({
    selectedGroupId: null as string | null, // null = "All Groups"
  }),

  getters: {
    hasSelectedGroup: (state) => state.selectedGroupId !== null,
    isAllGroups: (state) => state.selectedGroupId === null,
  },

  actions: {
    setSelectedGroup(groupId: string | null) {
      this.selectedGroupId = groupId

      // Persist to localStorage
      if (import.meta.client) {
        if (groupId) {
          localStorage.setItem('selected_group_id', groupId)
        } else {
          localStorage.removeItem('selected_group_id')
        }
      }
    },

    clearSelectedGroup() {
      this.setSelectedGroup(null)
    },

    initFilters() {
      // Restore selected group from localStorage
      if (import.meta.client) {
        const selectedGroupId = localStorage.getItem('selected_group_id')
        if (selectedGroupId) {
          this.selectedGroupId = selectedGroupId
        }
      }
    },
  },
})
