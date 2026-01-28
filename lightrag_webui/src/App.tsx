import { useState, useCallback, useEffect, useRef } from 'react'
import ThemeProvider from '@/components/ThemeProvider'
import TabVisibilityProvider from '@/contexts/TabVisibilityProvider'
import ApiKeyAlert from '@/components/ApiKeyAlert'
import StatusIndicator from '@/components/status/StatusIndicator'
import { SiteInfo, webuiPrefix } from '@/lib/constants'
import { useBackendState, useAuthStore } from '@/stores/state'
import { useSettingsStore } from '@/stores/settings'
import { getAuthStatus } from '@/api/lightrag'
import SiteHeader from '@/features/SiteHeader'
import { InvalidApiKeyError, RequireApiKeError } from '@/api/lightrag'
import { ZapIcon } from 'lucide-react'

import GraphViewer from '@/features/GraphViewer'
import DocumentManager from '@/features/DocumentManager'
import RetrievalTesting from '@/features/RetrievalTesting'
import ApiSite from '@/features/ApiSite'
import AceReview from '@/features/AceReview'

import { Tabs, TabsContent } from '@/components/ui/Tabs'

function App() {
  const message = useBackendState.use.message()
  const enableHealthCheck = useSettingsStore.use.enableHealthCheck()
  const currentTab = useSettingsStore.use.currentTab()
  const [apiKeyAlertOpen, setApiKeyAlertOpen] = useState(false)
  const [initializing, setInitializing] = useState(true) // Add initializing state
  const versionCheckRef = useRef(false) // Prevent duplicate calls in Vite dev mode
  const healthCheckInitializedRef = useRef(false) // Prevent duplicate health checks in Vite dev mode

  const handleApiKeyAlertOpenChange = useCallback((open: boolean) => {
    setApiKeyAlertOpen(open)
    if (!open) {
      useBackendState.getState().clear()
    }
  }, [])

  // Track component mount status with useRef
  const isMountedRef = useRef(true)

  // Set up mount/unmount status tracking
  useEffect(() => {
    isMountedRef.current = true

    // Handle page reload/unload
    const handleBeforeUnload = () => {
      isMountedRef.current = false
    }

    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      isMountedRef.current = false
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [])

  // Health check - can be disabled
  useEffect(() => {
    // Health check function
    const performHealthCheck = async () => {
      try {
        // Only perform health check if component is still mounted
        if (isMountedRef.current) {
          await useBackendState.getState().check()
        }
      } catch (error) {
        console.error('Health check error:', error)
      }
    }

    // Set health check function in the store
    useBackendState.getState().setHealthCheckFunction(performHealthCheck)

    if (!enableHealthCheck || apiKeyAlertOpen) {
      useBackendState.getState().clearHealthCheckTimer()
      return
    }

    // On first mount or when enableHealthCheck becomes true and apiKeyAlertOpen is false,
    // perform an immediate health check and start the timer
    if (!healthCheckInitializedRef.current) {
      healthCheckInitializedRef.current = true
    }

    // Start/reset the health check timer using the store
    useBackendState.getState().resetHealthCheckTimer()

    // Component unmount cleanup
    return () => {
      useBackendState.getState().clearHealthCheckTimer()
    }
  }, [enableHealthCheck, apiKeyAlertOpen])

  // Version check - independent and executed only once
  useEffect(() => {
    const checkVersion = async () => {
      // Prevent duplicate calls in Vite dev mode
      if (versionCheckRef.current) return
      versionCheckRef.current = true

      try {
        console.log('App initialization: checking version and auth status')
        const token = localStorage.getItem('LIGHTRAG-API-TOKEN')
        const status = await getAuthStatus()

        if (isMountedRef.current) {
          // Robust handle for login and version info
          if (!status.auth_configured && status.access_token) {
            // Guest mode / Auto-login
            useAuthStore.getState().login(
              status.access_token,
              true, // Guest mode
              status.core_version,
              status.api_version,
              status.webui_title || null,
              status.webui_description || null
            )
          } else if (token) {
            // Re-validate or update existing session
            const isGuestMode =
              status.auth_mode === 'disabled' || useAuthStore.getState().isGuestMode
            useAuthStore
              .getState()
              .login(
                token,
                isGuestMode,
                status.core_version,
                status.api_version,
                status.webui_title || null,
                status.webui_description || null
              )
          } else {
            // Fallback: just set version info
            useAuthStore
              .getState()
              .setVersion(status.core_version || null, status.api_version || null)
            if (status.webui_title || status.webui_description) {
              useAuthStore
                .getState()
                .setCustomTitle(status.webui_title || null, status.webui_description || null)
            }
          }

          // Set flag to indicate version info has been checked
          sessionStorage.setItem('VERSION_CHECKED_FROM_LOGIN', 'true')
        }
      } catch (error) {
        console.error('Critical initialization error caught in App:', error)
        // We catch here to allow the app to finish loading if possible,
        // or let the ErrorBoundary handle it if we re-throw.
        if (error instanceof InvalidApiKeyError || error instanceof RequireApiKeError) {
          console.log('Auth required/invalid - keeping initializing=false to show Login or alert')
        } else {
          // Re-throw so ErrorBoundary can catch truly unexpected boot crashes
          throw error
        }
      } finally {
        if (isMountedRef.current) {
          setInitializing(false)
        }
      }
    }

    checkVersion()
  }, [])

  const handleTabChange = useCallback(
    (tab: string) => useSettingsStore.getState().setCurrentTab(tab as any),
    []
  )

  useEffect(() => {
    if (message) {
      if (message.includes(InvalidApiKeyError) || message.includes(RequireApiKeError)) {
        setApiKeyAlertOpen(true)
      }
    }
  }, [message])

  return (
    <ThemeProvider>
      <TabVisibilityProvider>
        {initializing ? (
          // Loading state while initializing with simplified header
          <div className="flex h-screen w-screen flex-col">
            {/* Simplified header during initialization */}
            <header className="border-border/40 bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 flex h-10 w-full border-b px-4 backdrop-blur">
              <div className="flex w-auto min-w-[200px] items-center">
                <a href={webuiPrefix} className="flex items-center gap-2">
                  <ZapIcon className="size-4 text-emerald-400" aria-hidden="true" />
                  <span className="font-bold md:inline-block">{SiteInfo.name}</span>
                </a>
              </div>
              <div className="flex h-10 flex-1 items-center justify-center"></div>
              <nav className="flex w-[200px] items-center justify-end"></nav>
            </header>

            {/* Loading indicator */}
            <div className="flex flex-1 items-center justify-center">
              <div className="text-center">
                <div className="border-primary mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-4 border-t-transparent"></div>
                <p>Initializing...</p>
              </div>
            </div>
          </div>
        ) : (
          // Main content after initialization
          <main className="flex h-screen w-screen overflow-hidden">
            <Tabs
              value={currentTab}
              className="!m-0 flex grow flex-col overflow-hidden !p-0"
              onValueChange={handleTabChange}
            >
              <SiteHeader />
              <div className="relative grow">
                <TabsContent
                  value="documents"
                  className="absolute top-0 right-0 bottom-0 left-0 overflow-auto"
                >
                  <DocumentManager />
                </TabsContent>
                <TabsContent
                  value="knowledge-graph"
                  className="absolute top-0 right-0 bottom-0 left-0 overflow-hidden"
                >
                  <GraphViewer />
                </TabsContent>
                <TabsContent
                  value="retrieval"
                  className="absolute top-0 right-0 bottom-0 left-0 overflow-hidden"
                >
                  <RetrievalTesting />
                </TabsContent>
                <TabsContent
                  value="api"
                  className="absolute top-0 right-0 bottom-0 left-0 overflow-hidden"
                >
                  <ApiSite />
                </TabsContent>
                <TabsContent
                  value="ace-review"
                  className="absolute top-0 right-0 bottom-0 left-0 overflow-auto"
                >
                  <AceReview />
                </TabsContent>
              </div>
            </Tabs>
            {enableHealthCheck && <StatusIndicator />}
            <ApiKeyAlert open={apiKeyAlertOpen} onOpenChange={handleApiKeyAlertOpenChange} />
          </main>
        )}
      </TabVisibilityProvider>
    </ThemeProvider>
  )
}

export default App
