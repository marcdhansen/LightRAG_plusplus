import { test, expect } from '@playwright/test'

test.describe('ACE Review Visualization', () => {
  test.beforeEach(async ({ page }) => {
    // Set a fake token in localStorage to bypass client-side auth checks
    await page.addInitScript(() => {
      localStorage.setItem('LIGHTRAG-API-TOKEN', 'fake-token')
    })

    // Debugging logs
    page.on('console', (msg) => console.log('PAGE LOG:', msg.text()))
    page.on('pageerror', (exception) => console.log('PAGE ERROR:', exception))
    page.on('requestfailed', (request) =>
      console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText)
    )
  })

  test('should display visualizer when eyeball icon is clicked', async ({ page }) => {
    // Mock the repairs API response
    await page.route('**/ace/repairs/pending', async (route) => {
      const json = [
        {
          id: 'test-repair-1',
          action: 'delete_entity',
          name: 'Test Entity',
          created_at: '2026-01-27T12:00:00Z'
        }
      ]
      await route.fulfill({ json })
    })

    // Mock the graph query API response for the strict match
    await page.route('**/graphs?*', async (route) => {
      const json = {
        nodes: [
          {
            id: 'Test Entity',
            labels: ['Test Entity'],
            properties: { name: 'Test Entity' },
            color: '#ff0000'
          }
        ],
        edges: []
      }
      await route.fulfill({ json })
    })

    // Mock auth status to confirm valid token
    await page.route('**/auth-status', async (route) => {
      await route.fulfill({
        json: {
          auth_configured: true,
          access_token: 'fake-token'
        }
      })
    })

    await page.goto('/')

    // Wait for App to load
    await expect(page.getByText('LightRAG_gemini')).toBeVisible()

    // Click on ACE Review tab explicitily
    await page.getByText('ACE Review').click()

    // Verify the component header is visible
    await expect(page.getByText('ACE Repair Review')).toBeVisible()

    // Wait for the repair card by test ID
    await expect(page.getByTestId('repair-card')).toBeVisible({ timeout: 10000 })

    // Verify Title text content (exact match)
    await expect(page.getByText('Delete Entity', { exact: true })).toBeVisible()

    // Click the Visualize button (inside the card)
    await page.getByRole('button', { name: 'Visualize' }).click()

    // Verify the dialog opens
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText('Inspect Repair Impact')).toBeVisible()

    // Verify canvas is present (GraphViewer loaded) - check first canvas
    await expect(page.locator('canvas').first()).toBeVisible()

    // Verify minimal mode checks
    // Check that View Logs button is NOT present
    await expect(page.getByRole('button', { name: 'View Logs' })).not.toBeVisible()
  })
})
