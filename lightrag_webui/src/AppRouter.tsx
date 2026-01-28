// import '@/lib/extensions'; // Moved to main.tsx
import { HashRouter as Router, Routes, Route, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuthStore } from '@/stores/state'
import { navigationService } from '@/services/navigation'
import { Toaster } from 'sonner'
import App from './App'
import LoginPage from '@/features/LoginPage'
import ThemeProvider from '@/components/ThemeProvider'
import ErrorBoundary from '@/components/ErrorBoundary'
import { ZapIcon } from 'lucide-react'
import { SiteInfo, webuiPrefix } from '@/lib/constants'

const AppContent = () => {
  const [initializing, setInitializing] = useState(true)
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  // Set navigate function for navigation service
  useEffect(() => {
    navigationService.setNavigate(navigate)
  }, [navigate])

  // Token validity check
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('LIGHTRAG-API-TOKEN')

        if (token && isAuthenticated) {
          setInitializing(false)
          return
        }

        if (!token) {
          useAuthStore.getState().logout()
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        if (!isAuthenticated) {
          useAuthStore.getState().logout()
        }
      } finally {
        setInitializing(false)
      }
    }

    checkAuth()

    return () => {}
  }, [isAuthenticated])

  // Redirect effect for protected routes
  useEffect(() => {
    if (!initializing && !isAuthenticated) {
      const currentPath = window.location.hash.slice(1)
      if (currentPath !== '/login') {
        console.log('Not authenticated, redirecting to login')
        navigate('/login')
      }
    }
  }, [initializing, isAuthenticated, navigate])

  // Show loading indicator while initializing
  if (initializing) {
    return (
      <div className="bg-background flex h-screen w-screen flex-col">
        <header className="border-border/40 bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 flex h-10 w-full border-b px-4 backdrop-blur">
          <div className="flex w-auto min-w-[200px] items-center">
            <a href={webuiPrefix} className="flex items-center gap-2">
              <ZapIcon className="size-4 text-emerald-400" aria-hidden="true" />
              <span className="font-bold md:inline-block">{SiteInfo.name}</span>
            </a>
          </div>
        </header>
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <div className="border-primary mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-4 border-t-transparent"></div>
            <p className="text-muted-foreground font-mono text-sm">Verifying authentication...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={isAuthenticated ? <App /> : null} />
    </Routes>
  )
}

const AppRouter = () => {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <Router>
          <AppContent />
          <Toaster position="bottom-center" theme="system" closeButton richColors />
        </Router>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default AppRouter
