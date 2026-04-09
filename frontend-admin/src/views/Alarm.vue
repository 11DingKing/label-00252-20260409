<template>
  <div class="alarm-page">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card danger">
          <div class="stat-value">{{ alarmStats.critical }}</div>
          <div class="stat-label">严重告警</div>
          <div class="stat-icon"><el-icon><WarningFilled /></el-icon></div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card warning">
          <div class="stat-value">{{ alarmStats.warning }}</div>
          <div class="stat-label">警告</div>
          <div class="stat-icon"><el-icon><Warning /></el-icon></div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card info">
          <div class="stat-value">{{ alarmStats.info }}</div>
          <div class="stat-label">信息</div>
          <div class="stat-icon"><el-icon><InfoFilled /></el-icon></div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card success">
          <div class="stat-value">{{ alarmStats.cleared }}</div>
          <div class="stat-label">今日已清除</div>
          <div class="stat-icon"><el-icon><CircleCheckFilled /></el-icon></div>
        </div>
      </el-col>
    </el-row>

    <!-- 活动告警 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>活动告警</h3>
            <el-button type="primary" size="small" :disabled="activeAlarms.length === 0" @click="acknowledgeAll">
              全部确认
            </el-button>
          </div>
          
          <div class="alarm-list" v-if="activeAlarms.length > 0">
            <div 
              v-for="alarm in activeAlarms" 
              :key="alarm.id" 
              class="alarm-item"
              :class="alarm.severity"
            >
              <div class="alarm-indicator"></div>
              <div class="alarm-content">
                <div class="alarm-header">
                  <span class="alarm-code">{{ alarm.alarm_code }}</span>
                  <el-tag :type="getSeverityType(alarm.severity)" size="small" effect="dark">
                    {{ getSeverityText(alarm.severity) }}
                  </el-tag>
                  <el-tag v-if="alarm.status === 'triggered'" type="danger" size="small">待处理</el-tag>
                  <el-tag v-else type="warning" size="small">已确认</el-tag>
                </div>
                <div class="alarm-name">{{ alarm.alarm_name }}</div>
                <div class="alarm-meta">
                  <span class="module">{{ getModuleText(alarm.module) }}</span>
                  <span class="time">{{ formatTime(alarm.triggered_at) }}</span>
                </div>
              </div>
              <div class="alarm-actions">
                <el-button 
                  type="primary" 
                  size="small"
                  :disabled="alarm.status !== 'triggered'"
                  @click="acknowledgeAlarm(alarm)"
                >
                  确认
                </el-button>
              </div>
            </div>
          </div>
          
          <el-empty v-else description="系统运行正常，暂无告警" :image-size="80" />
        </div>
      </el-col>
    </el-row>
    
    <!-- 告警历史 + 统计 + 规则 -->
    <el-row :gutter="16" style="margin-top: 16px" class="bottom-row">
      <el-col :xs="24" :lg="16">
        <div class="card history-card">
          <div class="card-header">
            <h3>告警历史</h3>
          </div>
          
          <div class="enhanced-table scrollable" style="flex: 1;">
            <el-table :data="alarmHistory" stripe style="height: 100%">
              <el-table-column prop="alarm_code" label="代码" width="90" align="center">
                <template #default="{ row }">
                  <span class="code-text">{{ row.alarm_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="alarm_name" label="告警名称" min-width="120" />
              <el-table-column prop="module" label="模块" width="80" align="center">
                <template #default="{ row }">
                  <span>{{ getModuleText(row.module) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="severity" label="级别" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="getSeverityType(row.severity)" size="small">
                    {{ getSeverityText(row.severity) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90" align="center">
                <template #default="{ row }">
                  <div class="status-cell">
                    <span :class="['status-dot', row.status]"></span>
                    <span>{{ getStatusText(row.status) }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="triggered_at" label="触发时间" width="140">
                <template #default="{ row }">
                  <span class="time-text">{{ formatTime(row.triggered_at) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            size="small"
            style="margin-top: 12px; justify-content: flex-end"
            @current-change="fetchAlarmHistory"
          />
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="8" class="right-col">
        <!-- 告警趋势 -->
        <div class="card trend-card">
          <div class="card-header">
            <h3>告警趋势</h3>
          </div>
          <v-chart :option="trendOption" style="height: 180px" autoresize />
        </div>
        
        <!-- 告警规则 -->
        <div class="card rules-card">
          <div class="card-header">
            <h3>告警规则</h3>
            <el-button type="primary" size="small" @click="showRuleDialog = true">
              <el-icon><Plus /></el-icon> 添加
            </el-button>
          </div>
          <div class="rule-list">
            <div v-for="rule in alarmRules" :key="rule.id" class="rule-item">
              <div class="rule-info">
                <span class="rule-name">{{ rule.alarm_name }}</span>
                <el-tag :type="getSeverityType(rule.severity)" size="small">
                  {{ getSeverityText(rule.severity) }}
                </el-tag>
              </div>
              <el-switch v-model="rule.is_active" size="small" @change="toggleRule(rule)" />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Rule Dialog -->
    <el-dialog v-model="showRuleDialog" title="告警规则" width="480px">
      <el-form :model="ruleForm" label-width="80px" size="default">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="告警代码" required>
              <el-input v-model="ruleForm.alarm_code" placeholder="如: ALM001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="级别" required>
              <el-select v-model="ruleForm.severity" style="width: 100%">
                <el-option label="信息" value="info" />
                <el-option label="警告" value="warning" />
                <el-option label="严重" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="告警名称" required>
          <el-input v-model="ruleForm.alarm_name" placeholder="请输入告警名称" />
        </el-form-item>
        <el-form-item label="模块" required>
          <el-select v-model="ruleForm.module" style="width: 100%">
            <el-option label="光伏系统" value="pv" />
            <el-option label="风电系统" value="wind" />
            <el-option label="储能系统" value="battery" />
            <el-option label="负载管理" value="load" />
            <el-option label="电网连接" value="grid" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发条件" required>
          <el-input v-model="ruleForm.condition_expr" placeholder="如: voltage > 400" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { WarningFilled, Warning, InfoFilled, CircleCheckFilled, Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import api from '@/api'
import { useRealtimeStore } from '@/stores/realtime'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const realtimeStore = useRealtimeStore()
const activeAlarms = ref([])
const alarmHistory = ref([])
const alarmRules = ref([])
const currentPage = ref(1)
const pageSize = ref(15)
const total = ref(0)
const filterSeverity = ref('')
const filterModule = ref('')
const showRuleDialog = ref(false)

const ruleForm = ref({
  alarm_code: '',
  alarm_name: '',
  severity: 'warning',
  module: 'grid',
  condition_expr: ''
})

const alarmStats = computed(() => {
  const stats = { critical: 0, warning: 0, info: 0, cleared: 0 }
  // 只统计待处理(triggered)状态的告警
  activeAlarms.value.filter(a => a.status === 'triggered').forEach(a => {
    stats[a.severity] = (stats[a.severity] || 0) + 1
  })
  // 今日已确认数量
  stats.cleared = activeAlarms.value.filter(a => a.status === 'acknowledged').length
  return stats
})

// 模拟告警趋势数据
const trendOption = computed(() => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const data = Array.from({ length: 24 }, () => Math.floor(Math.random() * 5))
  
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: hours,
      axisLabel: { 
        color: '#94A3B8', 
        fontSize: 10,
        interval: 5
      },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94A3B8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#F59E0B', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(245, 158, 11, 0.3)' },
            { offset: 1, color: 'transparent' }
          ]
        }
      }
    }]
  }
})

function getSeverityType(severity) {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

function getSeverityText(severity) {
  if (severity === 'critical') return '严重'
  if (severity === 'warning') return '警告'
  return '信息'
}

function getStatusText(status) {
  if (status === 'triggered') return '触发'
  if (status === 'acknowledged') return '已确认'
  return '已清除'
}

function getModuleText(module) {
  const map = { pv: '光伏', wind: '风电', battery: '储能', load: '负载', grid: '电网' }
  return map[module] || module
}

function formatTime(time) {
  return dayjs(time).format('MM-DD HH:mm:ss')
}

async function fetchActiveAlarms() {
  try {
    const response = await api.get('/api/alarms/active')
    if (response.data.success) {
      activeAlarms.value = response.data.data
      // 更新全局告警计数
      const triggeredCount = response.data.data.filter(a => a.status === 'triggered').length
      realtimeStore.setActiveAlarmCount(triggeredCount)
    }
  } catch (e) {
    console.error('Failed to fetch active alarms:', e)
  }
}

async function fetchAlarmHistory() {
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (filterModule.value) params.module = filterModule.value
    
    const response = await api.get('/api/alarms/history', { params })
    if (response.data.success) {
      alarmHistory.value = response.data.data
      total.value = response.data.total
    }
  } catch (e) {
    console.error('Failed to fetch alarm history:', e)
  }
}

async function fetchAlarmRules() {
  try {
    const response = await api.get('/api/alarms')
    if (response.data.success) {
      alarmRules.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch alarm rules:', e)
  }
}

async function acknowledgeAlarm(alarm) {
  try {
    await api.post(`/api/alarms/${alarm.id}/acknowledge`, {})
    ElMessage.success('告警已确认')
    fetchActiveAlarms()
    fetchAlarmHistory()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function acknowledgeAll() {
  try {
    for (const alarm of activeAlarms.value.filter(a => a.status === 'triggered')) {
      await api.post(`/api/alarms/${alarm.id}/acknowledge`, {})
    }
    ElMessage.success('所有告警已确认')
    fetchActiveAlarms()
    fetchAlarmHistory()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function toggleRule(rule) {
  try {
    await api.put(`/api/alarms/${rule.id}`, { is_active: rule.is_active })
    ElMessage.success(rule.is_active ? '规则已启用' : '规则已禁用')
  } catch (e) {
    rule.is_active = !rule.is_active
    ElMessage.error('操作失败')
  }
}

async function saveRule() {
  try {
    await api.post('/api/alarms', ruleForm.value)
    ElMessage.success('规则已保存')
    showRuleDialog.value = false
    fetchAlarmRules()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  fetchActiveAlarms()
  fetchAlarmHistory()
  fetchAlarmRules()
  setInterval(fetchActiveAlarms, 10000)
})
</script>

<style lang="scss" scoped>
$danger: #EF4444;
$warning: #F59E0B;
$info: #3B82F6;
$success: #10B981;
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);

.stats-row {
  .stat-card {
    background: #1E293B;
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    
    .stat-value {
      font-size: 32px;
      font-weight: 700;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      color: $text-primary;
    }
    
    .stat-label {
      font-size: 13px;
      color: $text-secondary;
      margin-top: 4px;
    }
    
    .stat-icon {
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 40px;
      opacity: 0.15;
    }
    
    &.danger { 
      border-left: 4px solid $danger;
      .stat-icon { color: $danger; }
    }
    &.warning { 
      border-left: 4px solid $warning;
      .stat-icon { color: $warning; }
    }
    &.info { 
      border-left: 4px solid $info;
      .stat-icon { color: $info; }
    }
    &.success { 
      border-left: 4px solid $success;
      .stat-icon { color: $success; }
    }
  }
}

.alarm-badge {
  margin-left: 8px;
}

.alarm-list {
  max-height: 280px;
  overflow-y: auto;
  
  .alarm-item {
    display: flex;
    align-items: center;
    padding: 14px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    background: rgba(255, 255, 255, 0.03);
    
    &.critical {
      .alarm-indicator { background: $danger; }
    }
    &.warning {
      .alarm-indicator { background: $warning; }
    }
    &.info {
      .alarm-indicator { background: $info; }
    }
    
    .alarm-indicator {
      width: 4px;
      height: 40px;
      border-radius: 2px;
      margin-right: 16px;
    }
    
    .alarm-content {
      flex: 1;
      
      .alarm-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
        
        .alarm-code {
          font-family: 'SF Mono', monospace;
          font-size: 13px;
          color: $text-secondary;
        }
      }
      
      .alarm-name {
        font-size: 15px;
        font-weight: 500;
        color: $text-primary;
        margin-bottom: 4px;
      }
      
      .alarm-meta {
        font-size: 12px;
        color: $text-secondary;
        
        .module {
          margin-right: 16px;
        }
      }
    }
  }
}

.filter-group {
  display: flex;
  gap: 8px;
}

.code-text {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: $text-secondary;
}

.time-text {
  font-size: 12px;
  color: $text-secondary;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
  
  &.triggered { background: $danger; }
  &.acknowledged { background: $warning; }
  &.cleared { background: $success; }
}

.status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}

// 固定表格行高
:deep(.el-table) {
  .el-table__header th {
    white-space: nowrap;
  }
  
  .el-table__row {
    height: 48px;
    
    td {
      padding: 6px 0;
    }
  }
}

.rule-list {
  .rule-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid $border-color;
    
    &:last-child {
      border-bottom: none;
    }
    
    .rule-info {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .rule-name {
        font-size: 14px;
        color: $text-primary;
      }
    }
  }
}

.alarm-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 112px);
}

.bottom-row {
  flex: 1;
  
  .history-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 450px;
  }
  
  .right-col {
    display: flex;
    flex-direction: column;
    gap: 16px;
    
    .trend-card {
      flex-shrink: 0;
    }
    
    .rules-card {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
      
      .rule-list {
        flex: 1;
        overflow-y: auto;
      }
    }
  }
}
</style>
