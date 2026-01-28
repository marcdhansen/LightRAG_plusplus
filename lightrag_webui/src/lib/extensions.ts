// This file is for importing libraries that have global side effects.
import katex from 'katex'

// Safely initialize extensions
export const initExtensions = async () => {
  try {
    // Ensure katex is available globally for extensions that might need it
    if (typeof window !== 'undefined') {
      ;(window as any).katex = katex
    }

    // Dynamic imports to prevent module evaluation crashes
    await import('katex/contrib/mhchem')
    await import('katex/contrib/copy-tex')
    console.log('Extensions initialized successfully')
  } catch (error) {
    console.error('Failed to initialize extensions:', error)
    // Don't crash the app if extensions fail
  }
}
