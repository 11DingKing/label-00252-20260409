import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import Dashboard from '../views/Dashboard.vue'

// Mock API
vi.mock('@/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: {
        success: true,
        data: {
          pv: { power_output: 85.5, status: 'running' },
          wind: { power_output: 45.2, status: 'running' },
          battery: { soc: 75, power: 20, mode: 'charging' },
          load: { total_load: 120.5 },
          grid: { mode: 'connected', exchange: -10.2 }
        }
      }
    })
  }
}))

// Mock realtime store
vi.mock('@/stores/realtime', () => ({
  useRealtimeStore: () => ({
    data: {
      pv: { power_output: 85.5 },
      wind: { power_output: 45.2 },
      battery: { soc: 75 },
      load: { total_load: 120.5 },
      grid: { mode: 'connected' }
    },
    connected: true
  })
}))

describe('Dashboard.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders dashboard page', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: ['router-link']
      }
    })
    
    expect(wrapper.find('.dashboard-page').exists()).toBe(true)
  })

  it('displays stat cards', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: ['router-link']
      }
    })
    
    const statCards = wrapper.findAll('.stat-card')
    expect(statCards.length).toBeGreaterThan(0)
  })

  it('shows system status section', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: ['router-link']
      }
    })
    
    expect(wrapper.find('.system-status').exists()).toBe(true)
  })

  it('displays power flow visualization', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: ['router-link']
      }
    })
    
    expect(wrapper.find('.power-flow').exists()).toBe(true)
  })

  it('shows charts section', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: ['router-link']
      }
    })
    
    expect(wrapper.find('.charts-section').exists()).toBe(true)
  })
})
