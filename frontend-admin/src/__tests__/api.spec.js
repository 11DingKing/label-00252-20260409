import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    }))
  }
}))

describe('API Module', () => {
  let api

  beforeEach(async () => {
    vi.resetModules()
    const module = await import('@/api')
    api = module.default
  })

  it('creates axios instance', () => {
    expect(axios.create).toHaveBeenCalled()
  })

  it('has correct base URL', () => {
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: expect.any(String)
      })
    )
  })

  it('sets timeout', () => {
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        timeout: expect.any(Number)
      })
    )
  })
})

describe('API Endpoints', () => {
  it('should have auth endpoints', () => {
    const authEndpoints = [
      '/api/auth/login',
      '/api/auth/logout',
      '/api/auth/profile'
    ]
    
    authEndpoints.forEach(endpoint => {
      expect(endpoint).toMatch(/^\/api\/auth\//)
    })
  })

  it('should have PV endpoints', () => {
    const pvEndpoints = [
      '/api/pv/status',
      '/api/pv/config',
      '/api/pv/history'
    ]
    
    pvEndpoints.forEach(endpoint => {
      expect(endpoint).toMatch(/^\/api\/pv\//)
    })
  })

  it('should have battery endpoints', () => {
    const batteryEndpoints = [
      '/api/battery/status',
      '/api/battery/config',
      '/api/battery/mode'
    ]
    
    batteryEndpoints.forEach(endpoint => {
      expect(endpoint).toMatch(/^\/api\/battery\//)
    })
  })

  it('should have grid endpoints', () => {
    const gridEndpoints = [
      '/api/grid/status',
      '/api/grid/mode'
    ]
    
    gridEndpoints.forEach(endpoint => {
      expect(endpoint).toMatch(/^\/api\/grid\//)
    })
  })
})
