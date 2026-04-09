<template>
  <div class="settings-page">
    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>系统参数</h3>
          </div>
          
          <el-form label-width="120px">
            <el-form-item v-for="config in configs" :key="config.config_key" :label="config.description || config.config_key">
              <template v-if="config.config_type === 'bool'">
                <el-switch v-model="config.config_value" @change="updateConfig(config)" />
              </template>
              <template v-else-if="config.config_type === 'int' || config.config_type === 'float'">
                <el-input-number 
                  v-model.number="config.config_value" 
                  :precision="config.config_type === 'float' ? 2 : 0"
                  @change="updateConfig(config)"
                />
              </template>
              <template v-else>
                <el-input v-model="config.config_value" @blur="updateConfig(config)" />
              </template>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>仿真设置</h3>
          </div>
          
          <el-form label-width="120px">
            <el-form-item label="仿真速度">
              <el-slider v-model="simSpeed" :min="0.1" :max="10" :step="0.1" :format-tooltip="v => v + 'x'" />
            </el-form-item>
            <el-form-item label="数据保留">
              <el-input-number v-model="dataRetention" :min="1" :max="365" />
              <span style="margin-left: 8px">天</span>
            </el-form-item>
          </el-form>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>系统信息</h3>
          </div>
          
          <div class="params-list">
            <div class="param-item">
              <span class="param-label">系统名称</span>
              <span class="param-value">微网控制系统</span>
            </div>
            <div class="param-item">
              <span class="param-label">版本</span>
              <span class="param-value">1.0.0</span>
            </div>
            <div class="param-item">
              <span class="param-label">后端状态</span>
              <span class="param-value"><el-tag type="success" size="small">运行中</el-tag></span>
            </div>
            <div class="param-item">
              <span class="param-label">数据库状态</span>
              <span class="param-value"><el-tag type="success" size="small">已连接</el-tag></span>
            </div>
            <div class="param-item">
              <span class="param-label">WebSocket</span>
              <span class="param-value">
                <el-tag :type="wsConnected ? 'success' : 'danger'" size="small">
                  {{ wsConnected ? '已连接' : '未连接' }}
                </el-tag>
              </span>
            </div>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>配置变更历史</h3>
          </div>
          
          <el-table :data="configHistory" size="small" max-height="300">
            <el-table-column prop="config_key" label="配置项" width="120" />
            <el-table-column prop="old_value" label="原值" width="80" />
            <el-table-column prop="new_value" label="新值" width="80" />
            <el-table-column prop="changed_at" label="时间">
              <template #default="{ row }">
                {{ formatTime(row.changed_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useRealtimeStore } from '@/stores/realtime'
import api from '@/api'

const realtimeStore = useRealtimeStore()
const wsConnected = computed(() => realtimeStore.connected)

const configs = ref([])
const configHistory = ref([])
const simSpeed = ref(1.0)
const dataRetention = ref(30)

function formatTime(time) {
  return dayjs(time).format('MM-DD HH:mm')
}

async function fetchConfigs() {
  try {
    const response = await api.get('/api/config')
    if (response.data.success) {
      configs.value = response.data.data.map(c => ({
        ...c,
        config_value: parseConfigValue(c.config_value, c.config_type)
      }))
    }
  } catch (e) {
    console.error('Failed to fetch configs:', e)
  }
}

async function fetchConfigHistory() {
  try {
    const response = await api.get('/api/config/history', { params: { page_size: 10 } })
    if (response.data.success) {
      configHistory.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch config history:', e)
  }
}

function parseConfigValue(value, type) {
  if (type === 'int') return parseInt(value)
  if (type === 'float') return parseFloat(value)
  if (type === 'bool') return value === 'true'
  return value
}

async function updateConfig(config) {
  try {
    await api.put(`/api/config/${config.config_key}`, {
      config_value: String(config.config_value)
    })
    ElMessage.success('配置已更新')
    fetchConfigHistory()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

onMounted(() => {
  fetchConfigs()
  fetchConfigHistory()
})
</script>


<style lang="scss" scoped>
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);

// 参数列表样式
.params-list {
  .param-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid $border-color;
    
    &:last-child {
      border-bottom: none;
    }
    
    .param-label {
      font-size: 14px;
      color: $text-secondary;
    }
    
    .param-value {
      font-size: 16px;
      font-weight: 600;
      color: $text-primary;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    }
  }
}
</style>
