<template>
  <div class="logs-page">
    <div class="card main-card">
      <div class="card-header">
        <h3>操作日志</h3>
        <div class="filter-group">
          <el-select v-model="filterModule" placeholder="模块" clearable style="width: 120px">
            <el-option label="认证" value="auth" />
            <el-option label="用户" value="user" />
            <el-option label="光伏" value="pv" />
            <el-option label="风电" value="wind" />
            <el-option label="储能" value="battery" />
            <el-option label="负载" value="load" />
            <el-option label="电网" value="grid" />
            <el-option label="策略" value="strategy" />
            <el-option label="告警" value="alarm" />
            <el-option label="配置" value="config" />
          </el-select>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
            @change="fetchLogs"
          />
          <el-button type="primary" @click="fetchLogs">查询</el-button>
        </div>
      </div>
      
      <div class="enhanced-table scrollable" style="flex: 1;">
        <el-table :data="logs" stripe style="height: 100%">
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column prop="action" label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getActionType(row.action)" size="small">
                {{ getActionText(row.action) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="100" align="center">
            <template #default="{ row }">
              <span class="module-text">{{ getModuleText(row.module) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
          <el-table-column prop="ip_address" label="IP地址" width="140">
            <template #default="{ row }">
              <span class="ip-value">{{ row.ip_address }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">
              <span class="time-value">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[20, 50, 100]"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="fetchLogs"
        @size-change="fetchLogs"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import api from '@/api'

const logs = ref([])
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const filterModule = ref('')
const dateRange = ref([])

const actionMap = {
  login: { text: '登录', type: 'success' },
  logout: { text: '登出', type: 'info' },
  create: { text: '创建', type: 'success' },
  update: { text: '更新', type: 'warning' },
  delete: { text: '删除', type: 'danger' },
  control: { text: '控制', type: '' },
  config: { text: '配置', type: 'warning' },
  activate: { text: '激活', type: 'success' },
  acknowledge: { text: '确认', type: '' },
  change_password: { text: '改密', type: 'warning' }
}

const moduleMap = {
  auth: '认证',
  user: '用户',
  pv: '光伏',
  wind: '风电',
  battery: '储能',
  load: '负载',
  grid: '电网',
  strategy: '策略',
  alarm: '告警',
  config: '配置'
}

function getActionType(action) {
  return actionMap[action]?.type || ''
}

function getActionText(action) {
  return actionMap[action]?.text || action
}

function getModuleText(module) {
  return moduleMap[module] || module
}

function formatTime(time) {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

async function fetchLogs() {
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterModule.value) params.module = filterModule.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dayjs(dateRange.value[0]).format('YYYY-MM-DD')
      params.end_time = dayjs(dateRange.value[1]).format('YYYY-MM-DD')
    }
    
    const response = await api.get('/api/logs/operation', { params })
    if (response.data.success) {
      logs.value = response.data.data
      total.value = response.data.total
    }
  } catch (e) {
    console.error('Failed to fetch logs:', e)
  }
}

onMounted(() => {
  fetchLogs()
})
</script>

<style lang="scss" scoped>
.logs-page {
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

.filter-group {
  display: flex;
  gap: 8px;
  align-items: center;
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
