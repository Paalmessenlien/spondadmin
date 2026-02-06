/**
 * Composable for managing table state (sorting, filtering, pagination)
 * Provides a reusable pattern for interactive data tables
 */
export function useTableState<T extends Record<string, any>>(
  filteredData: Ref<T[]>,
  defaultSortField: keyof T,
  defaultSortDesc = true
) {
  const sortField = ref<keyof T>(defaultSortField)
  const sortDesc = ref(defaultSortDesc)
  const searchQuery = ref('')
  const pageSize = ref(20)
  const currentPage = ref(0)

  const sortedData = computed(() => {
    const result = [...filteredData.value]
    result.sort((a, b) => {
      const aVal = a[sortField.value]
      const bVal = b[sortField.value]

      // Handle null/undefined values
      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1

      // Compare values
      const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0
      return sortDesc.value ? -comparison : comparison
    })
    return result
  })

  const paginatedData = computed(() => {
    const start = currentPage.value * pageSize.value
    const end = start + pageSize.value
    return sortedData.value.slice(start, end)
  })

  const totalPages = computed(() =>
    Math.ceil(sortedData.value.length / pageSize.value)
  )

  const toggleSort = (field: keyof T) => {
    if (sortField.value === field) {
      sortDesc.value = !sortDesc.value
    } else {
      sortField.value = field
      sortDesc.value = true
    }
    currentPage.value = 0 // Reset to first page
  }

  const nextPage = () => {
    if (currentPage.value < totalPages.value - 1) {
      currentPage.value++
    }
  }

  const prevPage = () => {
    if (currentPage.value > 0) {
      currentPage.value--
    }
  }

  // Watch pageSize changes to reset to first page
  watch(pageSize, () => {
    currentPage.value = 0
  })

  return {
    sortField,
    sortDesc,
    pageSize,
    currentPage,
    sortedData,
    paginatedData,
    totalPages,
    toggleSort,
    nextPage,
    prevPage
  }
}
