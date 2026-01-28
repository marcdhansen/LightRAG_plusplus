import axios from 'axios'
import { backendBaseUrl } from '@/lib/constants'
import { LightragStatus } from './types'

// Axios instance
export const axiosInstance = axios.create({
  baseURL: backendBaseUrl,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Get the current API token from localStorage without importing the store
 */
const getAuthToken = () => {
  return localStorage.getItem('LIGHTRAG-API-TOKEN')
}

/**
 * Get the current API key from localStorage settings without importing the store
 */
const getApiKey = () => {
  try {
    const settingsStr = localStorage.getItem('settings-storage')
    if (settingsStr) {
      const settings = JSON.parse(settingsStr)
      return settings.state?.apiKey || null
    }
  } catch (e) {
    // console.error('Failed to get API key from storage', e)
  }
  return null
}

// Request Interceptor: add auth headers
axiosInstance.interceptors.request.use((config) => {
  // Skip interceptor if requested
  if (config.headers['X-Skip-Interceptor']) {
    delete config.headers['X-Skip-Interceptor']
    return config
  }

  const token = getAuthToken()
  const apiKey = getApiKey()

  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

/**
 * Basic health check that doesn't depend on other high-level logic
 */
export const checkHealth = async (): Promise<
  LightragStatus | { status: 'error'; message: string }
> => {
  try {
    const response = await axiosInstance.get('/health')
    return response.data
  } catch (error: any) {
    return {
      status: 'error',
      message: error.message || 'Unknown health check error'
    }
  }
}
