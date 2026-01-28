import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRouter from './AppRouter'
import './i18n.ts'
import 'katex/dist/katex.min.css'
import { initExtensions } from '@/lib/extensions'

const initApp = async () => {
  try {
    await initExtensions()
  } catch (e) {
    console.error('Extension initialization failed', e)
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <AppRouter />
    </StrictMode>
  )
}

initApp()
