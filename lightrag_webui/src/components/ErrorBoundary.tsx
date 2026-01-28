import React, { Component, ErrorInfo, ReactNode } from 'react'
import Button from '@/components/ui/Button'
import { AlertCircle, RefreshCcw, Trash2 } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)
  }

  private handleReset = () => {
    try {
      localStorage.clear()
      sessionStorage.clear()
      window.location.href = window.location.pathname // Reload to root
    } catch (e) {
      console.error('Failed to clear storage:', e)
      window.location.reload()
    }
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="bg-background text-foreground flex min-h-screen w-full flex-col items-center justify-center p-4">
          <div className="border-destructive/30 bg-card animate-in fade-in zoom-in w-full max-w-md rounded-xl border-2 p-8 shadow-2xl duration-300">
            <div className="mb-6 flex flex-col items-center text-center">
              <div className="bg-destructive/10 text-destructive mb-4 rounded-full p-3">
                <AlertCircle size={48} />
              </div>
              <h1 className="text-2xl font-bold tracking-tight">Something went wrong</h1>
              <p className="text-muted-foreground mt-2">
                The application encountered an unexpected error and could not continue.
              </p>
            </div>

            <div className="bg-muted/50 mb-8 max-h-32 overflow-auto rounded-lg border p-4 font-mono text-xs">
              <p className="text-destructive mb-1 font-bold">{this.state.error?.name}:</p>
              <p className="opacity-80">{this.state.error?.message}</p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Button
                variant="outline"
                onClick={this.handleReload}
                className="flex items-center justify-center gap-2"
              >
                <RefreshCcw size={16} />
                Try Reloading
              </Button>
              <Button
                variant="destructive"
                onClick={this.handleReset}
                className="flex items-center justify-center gap-2"
              >
                <Trash2 size={16} />
                Reset & Reload
              </Button>
            </div>

            <p className="text-muted-foreground mt-6 text-center text-[10px] tracking-widest uppercase opacity-50">
              Resetting will clear your local settings and history
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
