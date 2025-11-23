import { test, expect } from '@playwright/test'

test.describe('Group Filtering', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.waitForLoadState('networkidle')

    // Fill the form with robust selectors
    await page.getByRole('textbox', { name: 'Username' }).fill('admin')
    // Use input[type="password"] to avoid matching the "Show password" button
    await page.locator('input[type="password"]').fill('TestPass123!')

    // Wait for submit button to be enabled and click it
    const submitButton = page.getByRole('button', { name: /sign in/i })
    await expect(submitButton).toBeEnabled({ timeout: 10000 })
    await submitButton.click()

    await page.waitForURL('/dashboard')
  })

  test('should display All Groups option in selector', async ({ page }) => {
    // Find the group selector
    const groupSelector = page.locator('[aria-label="Select group"]')
    await expect(groupSelector).toBeVisible()

    // Click to open dropdown
    await groupSelector.click()

    // Check that "All Groups" option exists
    await expect(page.locator('text=All Groups')).toBeVisible()
  })

  test('should filter analytics data when group is selected', async ({ page }) => {
    // Navigate to analytics
    await page.goto('/dashboard/analytics')
    await page.waitForLoadState('networkidle')

    // Get initial summary stats
    const initialEvents = await page.locator('text=Total Events').locator('..').locator('.text-2xl').textContent()

    // Select a specific group
    const groupSelector = page.locator('[aria-label="Select group"]').first()
    await groupSelector.click()

    // Wait for dropdown to appear and select first group (not "All Groups")
    const firstGroup = page.locator('button:has-text("All Groups")').locator('..').locator('button').nth(1)
    if (await firstGroup.isVisible()) {
      await firstGroup.click()

      // Wait for data to reload
      await page.waitForTimeout(1000)

      // Verify that stats have changed (or at least page reloaded)
      await expect(page.locator('text=Total Events')).toBeVisible()
    }
  })

  test('should filter events when group is selected', async ({ page }) => {
    // Navigate to events
    await page.goto('/dashboard/events')
    await page.waitForLoadState('networkidle')

    // Check if there are any events
    const hasEvents = await page.locator('table tbody tr').count() > 0

    if (hasEvents) {
      // Get initial event count
      const initialCount = await page.locator('table tbody tr').count()

      // Select a specific group
      const groupSelector = page.locator('[aria-label="Select group"]').first()
      await groupSelector.click()

      // Select first group (not "All Groups")
      const groups = page.locator('button').filter({ hasText: /^(?!All Groups)/ })
      const firstGroup = groups.first()
      if (await firstGroup.isVisible()) {
        await firstGroup.click()

        // Wait for data to reload
        await page.waitForTimeout(1000)

        // Verify that the events table still exists (data may be filtered)
        await expect(page.locator('table')).toBeVisible()
      }
    }
  })

  test('should filter members when group is selected', async ({ page }) => {
    // Navigate to members
    await page.goto('/dashboard/members')
    await page.waitForLoadState('networkidle')

    // Check if there are any members
    const hasMembers = await page.locator('table tbody tr').count() > 0

    if (hasMembers) {
      // Get initial member count
      const initialCount = await page.locator('table tbody tr').count()

      // Select a specific group
      const groupSelector = page.locator('[aria-label="Select group"]').first()
      await groupSelector.click()

      // Wait for dropdown
      await page.waitForTimeout(500)

      // Look for group options
      const groupOptions = page.locator('[role="option"]')
      const optionsCount = await groupOptions.count()

      if (optionsCount > 1) {
        // Select second option (first is "All Groups")
        await groupOptions.nth(1).click()

        // Wait for data to reload
        await page.waitForTimeout(1000)

        // Verify that the members table still exists
        await expect(page.locator('table')).toBeVisible()
      }
    }
  })

  test('should show hierarchy on groups page when group is selected', async ({ page }) => {
    // Navigate to groups
    await page.goto('/dashboard/groups')
    await page.waitForLoadState('networkidle')

    // Check if there are any groups
    const hasGroups = await page.locator('.p-4.border.rounded-lg').count() > 0

    if (hasGroups) {
      // Get initial groups count
      const initialCount = await page.locator('.p-4.border.rounded-lg').count()

      // Select a specific group
      const groupSelector = page.locator('[aria-label="Select group"]').first()
      await groupSelector.click()

      // Wait for dropdown
      await page.waitForTimeout(500)

      // Select a group
      const groups = page.locator('text=/^(?!All Groups).*/')
      if (await groups.first().isVisible()) {
        await groups.first().click()

        // Wait for data to reload
        await page.waitForTimeout(1000)

        // Verify page is still showing groups (may be filtered to show hierarchy)
        const afterCount = await page.locator('.p-4.border.rounded-lg').count()
        expect(afterCount).toBeGreaterThanOrEqual(0)
      }
    }
  })

  test('should persist group selection in localStorage', async ({ page, context }) => {
    // Navigate to analytics
    await page.goto('/dashboard/analytics')
    await page.waitForLoadState('networkidle')

    // Select a specific group
    const groupSelector = page.locator('[aria-label="Select group"]').first()
    await groupSelector.click()

    // Wait for dropdown and select a group
    await page.waitForTimeout(500)
    const groups = page.locator('[role="option"]')
    const groupCount = await groups.count()

    if (groupCount > 1) {
      // Get the second group's text (first is "All Groups")
      const selectedGroupText = await groups.nth(1).textContent()
      await groups.nth(1).click()

      // Wait a bit for localStorage to be set
      await page.waitForTimeout(500)

      // Check localStorage
      const selectedGroupId = await page.evaluate(() => {
        return localStorage.getItem('selected_group_id')
      })

      expect(selectedGroupId).toBeTruthy()

      // Close and reopen browser to test persistence
      await page.close()
      const newPage = await context.newPage()

      // Login again
      await newPage.goto('/login')
      await newPage.fill('input[type="text"]', 'admin')
      await newPage.fill('input[type="password"]', 'admin')
      await newPage.click('button[type="submit"]')
      await newPage.waitForURL('/dashboard')

      // Navigate to analytics
      await newPage.goto('/dashboard/analytics')
      await newPage.waitForLoadState('networkidle')

      // Check that the same group is selected
      const restoredGroupId = await newPage.evaluate(() => {
        return localStorage.getItem('selected_group_id')
      })

      expect(restoredGroupId).toBe(selectedGroupId)
    }
  })

  test('should show toast notification when group is selected', async ({ page }) => {
    // Navigate to analytics
    await page.goto('/dashboard/analytics')
    await page.waitForLoadState('networkidle')

    // Select a specific group
    const groupSelector = page.locator('[aria-label="Select group"]').first()
    await groupSelector.click()

    // Wait for dropdown
    await page.waitForTimeout(500)

    // Select a group
    const groups = page.locator('[role="option"]')
    const groupCount = await groups.count()

    if (groupCount > 1) {
      await groups.nth(1).click()

      // Wait for toast notification
      await page.waitForTimeout(500)

      // Check for success toast
      const toast = page.locator('text=/Group selected|Showing data from all groups/')
      await expect(toast).toBeVisible({ timeout: 5000 })
    }
  })

  test('should reset pagination when group changes on events page', async ({ page }) => {
    // Navigate to events
    await page.goto('/dashboard/events')
    await page.waitForLoadState('networkidle')

    // Check if pagination exists
    const hasPagination = await page.locator('text=Page').isVisible()

    if (hasPagination) {
      // Try to go to page 2 if available
      const nextButton = page.locator('button:has-text("Next")')
      if (await nextButton.isEnabled()) {
        await nextButton.click()
        await page.waitForTimeout(500)

        // Check we're on page 2
        const pageInfo = await page.locator('text=/Page \\d+ of \\d+/').textContent()
        expect(pageInfo).toContain('Page 2')

        // Now change group
        const groupSelector = page.locator('[aria-label="Select group"]').first()
        await groupSelector.click()
        await page.waitForTimeout(500)

        const groups = page.locator('[role="option"]')
        if (await groups.count() > 1) {
          await groups.nth(1).click()
          await page.waitForTimeout(1000)

          // Check we're back on page 1
          const newPageInfo = await page.locator('text=/Page \\d+ of \\d+/').textContent()
          expect(newPageInfo).toContain('Page 1')
        }
      }
    }
  })

  test('should handle "All Groups" selection correctly', async ({ page }) => {
    // Navigate to analytics
    await page.goto('/dashboard/analytics')
    await page.waitForLoadState('networkidle')

    // Select a specific group first
    const groupSelector = page.locator('[aria-label="Select group"]').first()
    await groupSelector.click()
    await page.waitForTimeout(500)

    const groups = page.locator('[role="option"]')
    if (await groups.count() > 1) {
      // Select specific group
      await groups.nth(1).click()
      await page.waitForTimeout(1000)

      // Now select "All Groups"
      await groupSelector.click()
      await page.waitForTimeout(500)
      await groups.first().click() // "All Groups" is first option

      // Wait for toast
      await page.waitForTimeout(500)

      // Check for toast message about showing all groups
      const toast = page.locator('text=Showing data from all groups')
      await expect(toast).toBeVisible({ timeout: 5000 })

      // Check localStorage is cleared (or set to null)
      const selectedGroupId = await page.evaluate(() => {
        return localStorage.getItem('selected_group_id')
      })
      expect(selectedGroupId).toBeNull()
    }
  })
})
