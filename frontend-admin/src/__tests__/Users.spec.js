import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'
import Users from '@/views/Users.vue'

// Mock ElMessage and ElMessageBox
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

// Mock API module
vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Users.vue', () => {
  let wrapper
  let api

  const mockUsers = [
    {
      id: 1,
      username: 'admin',
      role: 'admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      username: 'operator',
      role: 'operator',
      is_active: true,
      created_at: '2024-01-02T00:00:00Z'
    }
  ]

  beforeEach(async () => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    
    // Import mocked api
    const apiModule = await import('@/api')
    api = apiModule.default
    
    // Default mock responses
    api.get.mockResolvedValue({
      data: {
        success: true,
        data: mockUsers,
        total: 2
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  const createWrapper = () => {
    return mount(Users, {
      global: {
        plugins: [ElementPlus],
        stubs: {
          teleport: true
        }
      }
    })
  }

  describe('用户列表', () => {
    it('应该在挂载时获取用户列表', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(api.get).toHaveBeenCalledWith('/api/users', {
        params: { page: 1, page_size: 20 }
      })
    })

    it('应该正确显示用户数据', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const table = wrapper.find('.el-table')
      expect(table.exists()).toBe(true)
    })

    it('应该正确显示角色标签', async () => {
      wrapper = createWrapper()
      await flushPromises()

      // 验证角色文本转换
      const vm = wrapper.vm
      expect(vm.getRoleText('admin')).toBe('管理员')
      expect(vm.getRoleText('operator')).toBe('操作员')
      expect(vm.getRoleText('viewer')).toBe('访客')
    })

    it('应该正确显示角色标签类型', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const vm = wrapper.vm
      expect(vm.getRoleType('admin')).toBe('danger')
      expect(vm.getRoleType('operator')).toBe('')
      expect(vm.getRoleType('viewer')).toBe('info')
    })
  })

  describe('添加用户', () => {
    it('应该成功创建新用户', async () => {
      api.post.mockResolvedValue({
        data: {
          success: true,
          data: {
            id: 3,
            username: 'newuser',
            role: 'operator',
            is_active: true
          }
        }
      })

      wrapper = createWrapper()
      await flushPromises()

      // 设置表单数据
      wrapper.vm.userForm = {
        username: 'newuser',
        password: 'password123',
        role: 'operator',
        is_active: true
      }
      wrapper.vm.editingUser = null
      wrapper.vm.formRef = { validate: vi.fn().mockResolvedValue(true) }

      await wrapper.vm.saveUser()
      await flushPromises()

      expect(api.post).toHaveBeenCalledWith('/api/users', {
        username: 'newuser',
        password: 'password123',
        role: 'operator',
        is_active: true
      })
      expect(ElMessage.success).toHaveBeenCalledWith('保存成功')
    })

    it('应该在用户名已存在时显示错误', async () => {
      api.post.mockRejectedValue({
        response: {
          data: {
            detail: 'Username already exists'
          }
        }
      })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.userForm = {
        username: 'admin',
        password: 'password123',
        role: 'operator',
        is_active: true
      }
      wrapper.vm.editingUser = null
      wrapper.vm.formRef = { validate: vi.fn().mockResolvedValue(true) }

      await wrapper.vm.saveUser()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('Username already exists')
    })

    it('应该验证密码最小长度', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const rules = wrapper.vm.rules
      const passwordRule = rules.password.find(r => r.min)
      
      expect(passwordRule).toBeDefined()
      expect(passwordRule.min).toBe(6)
      expect(passwordRule.message).toBe('密码至少6个字符')
    })

    it('应该验证用户名长度', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const rules = wrapper.vm.rules
      const usernameRule = rules.username.find(r => r.min)
      
      expect(usernameRule).toBeDefined()
      expect(usernameRule.min).toBe(3)
      expect(usernameRule.max).toBe(50)
    })
  })

  describe('编辑用户', () => {
    it('应该正确加载用户数据到表单', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const user = mockUsers[1]
      wrapper.vm.editUser(user)

      expect(wrapper.vm.editingUser).toEqual(user)
      expect(wrapper.vm.userForm.username).toBe(user.username)
      expect(wrapper.vm.userForm.role).toBe(user.role)
      expect(wrapper.vm.userForm.is_active).toBe(user.is_active)
      expect(wrapper.vm.showAddDialog).toBe(true)
    })

    it('应该成功更新用户', async () => {
      api.put.mockResolvedValue({
        data: {
          success: true,
          data: {
            id: 2,
            username: 'operator',
            role: 'viewer',
            is_active: false
          }
        }
      })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editingUser = { id: 2 }
      wrapper.vm.userForm = {
        username: 'operator',
        password: '',
        role: 'viewer',
        is_active: false
      }

      await wrapper.vm.saveUser()
      await flushPromises()

      expect(api.put).toHaveBeenCalledWith('/api/users/2', {
        role: 'viewer',
        is_active: false
      })
      expect(ElMessage.success).toHaveBeenCalledWith('保存成功')
    })
  })

  describe('删除用户', () => {
    it('应该在确认后删除用户', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      api.delete.mockResolvedValue({
        data: { success: true }
      })

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteUser({ id: 2, username: 'operator' })
      await flushPromises()

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除该用户吗？',
        '提示',
        { type: 'warning' }
      )
      expect(api.delete).toHaveBeenCalledWith('/api/users/2')
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('应该在取消时不删除用户', async () => {
      ElMessageBox.confirm.mockRejectedValue('cancel')

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteUser({ id: 2, username: 'operator' })
      await flushPromises()

      expect(api.delete).not.toHaveBeenCalled()
    })

    it('应该在删除失败时显示错误', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      api.delete.mockRejectedValue(new Error('Delete failed'))

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteUser({ id: 2, username: 'operator' })
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
    })
  })

  describe('重置密码', () => {
    it('应该打开重置密码对话框', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const user = mockUsers[1]
      wrapper.vm.resetPassword(user)

      expect(wrapper.vm.editingUser).toEqual(user)
      expect(wrapper.vm.showPasswordDialog).toBe(true)
      expect(wrapper.vm.passwordForm.password).toBe('')
    })

    it('应该成功重置密码', async () => {
      api.put.mockResolvedValue({
        data: { success: true }
      })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editingUser = { id: 2 }
      wrapper.vm.passwordForm.password = 'newpassword123'

      await wrapper.vm.confirmResetPassword()
      await flushPromises()

      expect(api.put).toHaveBeenCalledWith('/api/users/2', {
        password: 'newpassword123'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('密码已重置')
      expect(wrapper.vm.showPasswordDialog).toBe(false)
    })

    it('应该在重置失败时显示错误', async () => {
      api.put.mockRejectedValue(new Error('Reset failed'))

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editingUser = { id: 2 }
      wrapper.vm.passwordForm.password = 'newpassword123'

      await wrapper.vm.confirmResetPassword()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('重置失败')
    })
  })

  describe('时间格式化', () => {
    it('应该正确格式化时间', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const formatted = wrapper.vm.formatTime('2024-01-15T10:30:00Z')
      expect(formatted).toMatch(/2024-01-15/)
    })
  })
})
