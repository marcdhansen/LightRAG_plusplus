import { test, expect } from '@playwright/test'

test.describe('Graph Visualizer', () => {
    test.beforeEach(async ({ page }) => {
        await page.addInitScript(() => {
            localStorage.setItem('LIGHTRAG-API-TOKEN', 'fake-token')
        })

        // Mock auth status
        await page.route('**/auth-status', async (route) => {
            await route.fulfill({
                json: {
                    auth_configured: true,
                    access_token: 'fake-token'
                }
            })
        })

        // Mock health check
        await page.route('**/health', async (route) => {
            await route.fulfill({
                json: {
                    status: 'healthy',
                    working_directory: '',
                    input_directory: '',
                    configuration: {},
                    pipeline_busy: false
                }
            })
        })

        // Mock documents paginated
        await page.route('**/documents/paginated*', async (route) => {
            await route.fulfill({
                json: {
                    documents: [],
                    pagination: { page: 1, page_size: 10, total_count: 0, total_pages: 0 },
                    status_counts: {}
                }
            })
        })

        // Mock graph query API
        await page.route('**/graphs?*', async (route) => {
            await route.fulfill({
                json: {
                    nodes: [
                        { id: 'Entity1', labels: ['Entity'], properties: { entity_type: 'Entity' } },
                        { id: 'Entity2', labels: ['Entity'], properties: { entity_type: 'Entity' } }
                    ],
                    edges: [
                        {
                            id: 'Edge1',
                            source: 'Entity1',
                            target: 'Entity2',
                            type: 'RELATED',
                            properties: {}
                        }
                    ]
                }
            })
        })

        // Mock popular labels
        await page.route('**/graph/label/popular?*', async (route) => {
            await route.fulfill({ json: ['Entity1', 'Entity2'] })
        })
    })

    test('should display graph and allow interaction', async ({ page }) => {
        await page.goto('/')

        // Wait for App to load
        await expect(page.getByText('LightRAG_gemini')).toBeVisible()

        // Click on Knowledge Graph tab
        await page.getByText('Knowledge Graph').click()

        // Wait for canvas to be visible
        await expect(page.locator('canvas').first()).toBeVisible()

        // Check SettingsDisplay
        await expect(page.getByText('D: 3')).toBeVisible()
        await expect(page.getByText('Max: 1000')).toBeVisible()

        // Click on Legend button
        const legendBtn = page.locator('button[aria-label="Toggle Legend"]')
        await expect(legendBtn).toBeVisible()
        await legendBtn.click()
    })
})
