import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import { useRealtimeStore } from '@/stores/realtime'

// Mock API
vi.mock('@/api', () => ({
  default: {
    post: vi.fn().mockResolvedValue({
      data: {
        success: true,
        data: {
          access_token: 'test-token',
          user: {
            id: 1,
            username: 'admin',
            role: 'admin'
          }
        }
      }
    }),
    get: vi.fn().mockResolvedValue({
      data: {
        success: true,
        data: {}
      }
    })
  }
}))

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('initializes with null user', () => {
    const store = useUserStore()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })

  it('login sets user and token', async () => {
    const store = useUserStore()
    const result = await store.login('admin', 'admin123')
    
    expect(result.success).toBe(true)
    expect(store.user).toBeDefined()
    expect(store.token).toBe('test-token')
  })

  it('logout clears user and token', async () => {
    const store = useUserStore()
    await store.login('admin', 'admin123')
    
    store.logout()
    
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })

  it('isLoggedIn returns correct state', async () => {
    const store = useUserStore()
    expect(store.isLoggedIn).toBe(false)
    
    await store.login('admin', 'admin123')
    expect(store.isLoggedIn).toBe(true)
  })

  it('isAdmin returns correct state', async () => {
    const store = useUserStore()
    await store.login('admin', 'admin123')
    
    expect(store.isAdmin).toBe(true)
  })
})

describe('Realtime Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default state', () => {
    const store = useRealtimeStore()
    expect(store.connected).toBe(false)
    expect(store.data).toBeDefined()
  })

  it('setConnected updates connection state', () => {
    const store = useRealtimeStore()
    store.setConnected(true)
    expect(store.connected).toBe(true)
  })

  it('updateData updates store data', () => {
    const store = useRealtimeStore()
    const testData = {
      pv: { power_output: 100 },
      battery: { soc: 80 }
    }
    
    store.updateData(testData)
    
    expect(store.data.pv.power_output).toBe(100)
    expect(store.data.battery.soc).toBe(80)
  })
})
