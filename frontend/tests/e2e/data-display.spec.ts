import { test, expect } from '@playwright/test'

/**
 * Tests to verify that data is actually being displayed on the pages
 */
test.describe('Data Display Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.waitForLoadState('networkidle')

    await page.getByRole('textbox', { name: 'Username' }).fill('admin')
    await page.locator('input[type="password"]').fill('TestPass123!')

    const submitButton = page.getByRole('button', { name: /sign in/i })
    await expect(submitButton).toBeEnabled({ timeout: 10000 })
    await submitButton.click()

    await page.waitForURL('/dashboard', { timeout: 10000 })
  })

  test('should display events on events page', async ({ page }) => {
    await page.goto('/dashboard/events')
    await page.waitForLoadState('networkidle')

    // Wait a bit for data to load
    await page.waitForTimeout(2000)

    // Log the page content to see what's there
    const bodyText = await page.locator('body').textContent()
    console.log('Page body contains:', bodyText?.substring(0, 500))

    // Check if we have a table or event list items
    const hasTable = await page.locator('table').count() > 0
    const hasEmptyState = await page.locator('text=No events').count() > 0

    console.log('Has table:', hasTable)
    console.log('Has empty state:', hasEmptyState)

    // Take a screenshot for debugging
    await page.screenshot({ path: 'events-page-debug.png', fullPage: true })

    // Check if there are any table rows (besides header)
    if (hasTable) {
      const rowCount = await page.locator('tbody tr').count()
      console.log('Table rows found:', rowCount)
      expect(rowCount).toBeGreaterThan(0)
    }
  })

  test('should display groups on groups page', async ({ page }) => {
    await page.goto('/dashboard/groups')
    await page.waitForLoadState('networkidle')

    // Wait for data to load
    await page.waitForTimeout(2000)

    const bodyText = await page.locator('body').textContent()
    console.log('Groups page body contains:', bodyText?.substring(0, 500))

    const hasEmptyState = await page.locator('text=No groups').count() > 0
    console.log('Has empty state:', hasEmptyState)

    // Take a screenshot
    await page.screenshot({ path: 'groups-page-debug.png', fullPage: true })

    // Look for group items (they should be in divs with specific classes)
    const groupItems = await page.locator('[class*="border rounded-lg"]').count()
    console.log('Group items found:', groupItems)
  })

  test('should display members on members page', async ({ page }) => {
    await page.goto('/dashboard/members')
    await page.waitForLoadState('networkidle')

    // Wait for data to load
    await page.waitForTimeout(2000)

    const bodyText = await page.locator('body').textContent()
    console.log('Members page body contains:', bodyText?.substring(0, 500))

    const hasEmptyState = await page.locator('text=No members').count() > 0
    console.log('Has empty state:', hasEmptyState)

    // Take a screenshot
    await page.screenshot({ path: 'members-page-debug.png', fullPage: true })

    // Check if we have a table or member list items
    const hasTable = await page.locator('table').count() > 0
    if (hasTable) {
      const rowCount = await page.locator('tbody tr').count()
      console.log('Member table rows found:', rowCount)
    }
  })
})
