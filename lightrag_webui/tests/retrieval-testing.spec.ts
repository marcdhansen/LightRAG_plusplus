import { test, expect } from '@playwright/test'

test.describe('Retrieval Testing', () => {
    test.beforeEach(async ({ page }) => {
        // Set a fake token in localStorage to bypass client-side auth checks
        await page.addInitScript(() => {
            localStorage.setItem('LIGHTRAG-API-TOKEN', 'fake-token')
        })

        // Debugging logs
        page.on('console', (msg) => console.log('PAGE LOG:', msg.text()))
        page.on('pageerror', (exception) => console.log('PAGE ERROR:', exception))
        page.on('request', (request) =>
            console.log('REQUEST:', request.method(), request.url())
        )
        page.on('response', (response) =>
            console.log('RESPONSE:', response.status(), response.url())
        )
        page.on('requestfailed', (request) =>
            console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText)
        )

        // Mock auth status to confirm valid token
        await page.route('**/auth-status', async (route) => {
            await route.fulfill({
                json: {
                    auth_configured: true,
                    access_token: 'fake-token'
                }
            })
        })

        // Mock graph query API response (used by labels/popular search)
        await page.route('**/graph/label/popular?*', async (route) => {
            await route.fulfill({ json: ['Entity1', 'Entity2'] })
        })
    })

    test('should perform a successful retrieval query', async ({ page }) => {
        // Mock the query API response (non-streaming)
        await page.route('**/query', async (route) => {
            const json = {
                response: 'This is a test response from the assistant.',
                references: [
                    {
                        reference_id: 'doc-1',
                        file_path: 'test_documents/doc1.txt',
                        content: ['This is some source content.'],
                        score: 0.9
                    }
                ]
            }
            await route.fulfill({ json })
        })

        // Mock the query API response (streaming)
        await page.route('**/query/stream', async (route) => {
            const chunks = [
                JSON.stringify({ response: 'This is a test response ' }),
                JSON.stringify({ response: 'from the assistant.' }),
                JSON.stringify({
                    references: [
                        {
                            reference_id: 'doc-1',
                            file_path: 'test_documents/doc1.txt',
                            content: ['This is some source content.'],
                            score: 0.9
                        }
                    ]
                })
            ]
            await route.fulfill({
                contentType: 'application/x-ndjson',
                body: chunks.join('\n') + '\n'
            })
        })

        await page.goto('/')

        // Wait for App to load
        await expect(page.getByText('LightRAG_gemini')).toBeVisible()

        // Click on Retrieval tab (exact match to avoid confusion with other text)
        await page.getByText('Retrieval', { exact: true }).click()

        // Verify the start prompt is visible
        await expect(page.getByText('Start a retrieval by typing your query below')).toBeVisible()

        // Optional: test with streaming enabled (default)
        const input = page.locator('#query-input')
        await input.fill('What is LightRAG? (streaming)')
        await page.getByRole('button', { name: 'Send' }).click()
        await expect(page.getByText('This is a test response from the assistant.')).toBeVisible()

        // Clear for next part
        await page.getByRole('button', { name: 'Clear' }).click()

        // Disable streaming for non-streaming test
        await page.getByLabel('Stream Response').uncheck()

        // Type a query
        await input.fill('What is LightRAG? (non-streaming)')

        // Click Send
        await page.getByRole('button', { name: 'Send' }).click()

        // Verify assistant message appears
        await expect(page.getByText('This is a test response from the assistant.')).toBeVisible()

        // Verify references are visible
        await expect(page.getByText('Sources:')).toBeVisible()
        await expect(page.getByText('doc1.txt')).toBeVisible()

        // Test Clear button
        await page.getByRole('button', { name: 'Clear' }).click()

        // Verify messages are cleared
        await expect(page.getByText('This is a test response from the assistant.')).not.toBeVisible()
        await expect(page.getByText('Start a retrieval by typing your query below')).toBeVisible()
    })
})
