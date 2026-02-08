/**
 * CSV Export Composable
 * Provides functionality to export data to CSV format
 */

export const useCsvExport = () => {
  /**
   * Convert array of objects to CSV string
   */
  const arrayToCSV = (data: any[], headers: { key: string; label: string }[]): string => {
    if (data.length === 0) return ''

    // CSV header row
    const headerRow = headers.map(h => `"${h.label}"`).join(',')

    // CSV data rows
    const dataRows = data.map(row => {
      return headers.map(h => {
        const value = row[h.key]

        // Handle different data types
        if (value === null || value === undefined) {
          return '""'
        }

        // Format numbers
        if (typeof value === 'number') {
          return value.toString()
        }

        // Escape quotes and wrap in quotes
        const stringValue = String(value).replace(/"/g, '""')
        return `"${stringValue}"`
      }).join(',')
    })

    return [headerRow, ...dataRows].join('\n')
  }

  /**
   * Download CSV file
   */
  const downloadCSV = (csvContent: string, filename: string) => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')

    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', filename)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
  }

  /**
   * Export data to CSV file
   */
  const exportToCSV = (
    data: any[],
    headers: { key: string; label: string }[],
    filename: string
  ) => {
    const csvContent = arrayToCSV(data, headers)
    const csvFilename = filename.endsWith('.csv') ? filename : `${filename}.csv`
    downloadCSV(csvContent, csvFilename)
  }

  return {
    arrayToCSV,
    downloadCSV,
    exportToCSV
  }
}
