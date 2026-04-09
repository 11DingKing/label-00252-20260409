<template>
  <div class="users-page">
    <div class="card main-card">
      <div class="card-header">
        <h3>用户管理</h3>
        <el-button type="primary" size="small" @click="openAddDialog">
          <el-icon><Plus /></el-icon> 添加用户
        </el-button>
      </div>
      
      <div class="enhanced-table scrollable" style="flex: 1;">
          <el-table :data="users" stripe style="height: 100%">
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="role" label="角色" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              <span class="time-value">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" link size="small" @click="editUser(row)">编辑</el-button>
                <el-button type="warning" link size="small" @click="resetPassword(row)">重置密码</el-button>
                <el-button 
                  type="danger" 
                  link 
                  size="small" 
                  :disabled="row.username === 'admin'"
                  @click="deleteUser(row)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="fetchUsers"
      />
    </div>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showAddDialog" :title="editingUser ? '编辑用户' : '添加用户'" width="500px">
      <el-form :model="userForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="操作员" value="operator" />
            <el-option label="访客" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- Reset Password Dialog -->
    <el-dialog v-model="showPasswordDialog" title="重置密码" width="400px">
      <el-form :model="passwordForm" label-width="100px">
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmResetPassword">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import api from '@/api'

const users = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showAddDialog = ref(false)
const showPasswordDialog = ref(false)
const editingUser = ref(null)
const formRef = ref()

const userForm = ref({
  username: '',
  password: '',
  role: 'operator',
  is_active: true
})

const passwordForm = ref({
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

function getRoleType(role) {
  if (role === 'admin') return 'danger'
  if (role === 'operator') return ''
  return 'info'
}

function getRoleText(role) {
  if (role === 'admin') return '管理员'
  if (role === 'operator') return '操作员'
  return '访客'
}

function formatTime(time) {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

async function fetchUsers() {
  try {
    const response = await api.get('/api/users', {
      params: { page: currentPage.value, page_size: pageSize.value }
    })
    if (response.data.success) {
      users.value = response.data.data
      total.value = response.data.total
    }
  } catch (e) {
    console.error('Failed to fetch users:', e)
  }
}

function editUser(user) {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    password: '',
    role: user.role,
    is_active: user.is_active
  }
  showAddDialog.value = true
}

function openAddDialog() {
  editingUser.value = null
  userForm.value = {
    username: '',
    password: '',
    role: 'operator',
    is_active: true
  }
  showAddDialog.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      await api.put(`/api/users/${editingUser.value.id}`, {
        role: userForm.value.role,
        is_active: userForm.value.is_active
      })
    } else {
      await formRef.value.validate()
      await api.post('/api/users', {
        username: userForm.value.username,
        password: userForm.value.password,
        role: userForm.value.role,
        is_active: userForm.value.is_active
      })
    }
    ElMessage.success('保存成功')
    showAddDialog.value = false
    editingUser.value = null
    // 重置表单
    userForm.value = {
      username: '',
      password: '',
      role: 'operator',
      is_active: true
    }
    fetchUsers()
  } catch (e) {
    if (e !== false) {
      const msg = e.response?.data?.detail || '保存失败'
      ElMessage.error(msg)
    }
  }
}

function resetPassword(user) {
  editingUser.value = user
  passwordForm.value.password = ''
  showPasswordDialog.value = true
}

async function confirmResetPassword() {
  try {
    await api.put(`/api/users/${editingUser.value.id}`, {
      password: passwordForm.value.password
    })
    ElMessage.success('密码已重置')
    showPasswordDialog.value = false
  } catch (e) {
    ElMessage.error('重置失败')
  }
}

async function deleteUser(user) {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？', '提示', { type: 'warning' })
    await api.delete(`/api/users/${user.id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style lang="scss" scoped>
.users-page {
  height: 100%;
  min-height: calc(100vh - 112px);
  
  .main-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    
    .enhanced-table {
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }
  }
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: nowrap;
}

:deep(.el-table) {
  .el-table__row {
    height: 48px;
    
    td {
      padding: 8px 0;
    }
  }
}
</style>
