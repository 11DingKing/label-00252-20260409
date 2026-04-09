import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import Login from '../views/Login.vue'

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
    { path: '/login', name: 'login', component: Login }
  ]
})

// Mock user store
vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    login: vi.fn().mockResolvedValue({ success: true }),
    user: null,
    isLoggedIn: false
  })
}))

describe('Login.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders login form', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router, ElementPlus, createPinia()]
      }
    })
    
    expect(wrapper.find('.login-page').exists()).toBe(true)
    expect(wrapper.find('.form-section').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('欢迎回来')
  })

  it('displays brand section', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router, ElementPlus, createPinia()]
      }
    })
    
    expect(wrapper.find('.brand-section').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toBe('微网控制系统')
  })

  it('shows test accounts', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router, ElementPlus, createPinia()]
      }
    })
    
    const accounts = wrapper.findAll('.account-item')
    expect(accounts.length).toBe(2)
    expect(accounts[0].text()).toContain('admin')
    expect(accounts[1].text()).toContain('operator')
  })

  it('fills account on click', async () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router, ElementPlus, createPinia()]
      }
    })
    
    const adminAccount = wrapper.findAll('.account-item')[0]
    await adminAccount.trigger('click')
    
    // Check that form values are updated
    expect(wrapper.vm.form.username).toBe('admin')
    expect(wrapper.vm.form.password).toBe('admin123')
  })

  it('validates required fields', async () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router, ElementPlus, createPinia()]
      }
    })
    
    // Try to submit empty form
    const loginBtn = wrapper.find('.login-btn')
    await loginBtn.trigger('click')
    
    // Form should not submit with empty fields
    expect(wrapper.vm.loading).toBe(false)
  })

  it('shows loading state during login', async () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router, ElementPlus, createPinia()]
      }
    })
    
    // Fill form
    wrapper.vm.form.username = 'admin'
    wrapper.vm.form.password = 'admin123'
    wrapper.vm.loading = true
    
    await wrapper.vm.$nextTick()
    
    const loginBtn = wrapper.find('.login-btn')
    expect(loginBtn.text()).toContain('登录中')
  })
})
