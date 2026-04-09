<template>
  <div class="battery-system">
    <!-- 第一排：储能监控 + 系统参数 + 调度策略 -->
    <el-row :gutter="24" class="equal-height-row">
      <el-col :xs="24" :lg="10">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>储能系统监控</h3>
          </div>
          
          <div class="battery-list">
            <div class="battery-card" v-for="battery in batteryList" :key="battery.battery_id">
              <div class="battery-header">
                <el-icon :size="20" :color="getBatteryColor(battery)"><Coin /></el-icon>
                <span>{{ battery.name }}</span>
                <el-tag :type="getStatusType(battery.status)" size="small">
                  {{ getStatusText(battery.status) }}
                </el-tag>
              </div>
              
              <div class="battery-content">
                <div class="battery-visual">
                  <div class="battery-body">
                    <div class="battery-level" :style="{ height: (battery.soc * 100) + '%', background: getBatteryColor(battery) }"></div>
                  </div>
                </div>
                
                <div class="battery-stats">
                  <div class="stat-item">
                    <span class="label">SOC</span>
                    <span class="value">{{ (battery.soc * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">功率</span>
                    <span class="value">{{ battery.power?.toFixed(1) || 0 }} kW</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">电压</span>
                    <span class="value">{{ battery.voltage?.toFixed(1) || 400 }} V</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">温度</span>
                    <span class="value">{{ battery.temperature?.toFixed(1) || 25 }} °C</span>
                  </div>
                </div>
              </div>
              
              <div class="battery-controls">
                <el-button-group size="small">
                  <el-button 
                    :type="battery.status === 'charging' ? 'success' : 'default'"
                    :class="{ active: battery.status === 'charging' }"
                    @click="controlBattery(battery, 'charge')"
                  >充电</el-button>
                  <el-button 
                    :type="battery.status === 'idle' ? 'info' : 'default'"
                    :class="{ active: battery.status === 'idle' }"
                    @click="controlBattery(battery, 'stop')"
                  >停止</el-button>
                  <el-button 
                    :type="battery.status === 'discharging' ? 'warning' : 'default'"
                    :class="{ active: battery.status === 'discharging' }"
                    @click="controlBattery(battery, 'discharge')"
                  >放电</el-button>
                </el-button-group>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="7">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>系统参数</h3>
          </div>
          <div class="params-list">
            <div class="param-item">
              <span class="param-label">总容量</span>
              <span class="param-value">{{ totalCapacity }} <small>kWh</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">可用能量</span>
              <span class="param-value highlight">{{ availableEnergy.toFixed(1) }} <small>kWh</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">当前功率</span>
              <span class="param-value">{{ totalPower.toFixed(1) }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">平均SOC</span>
              <span class="param-value">{{ (avgSoc * 100).toFixed(1) }} <small>%</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">充放电效率</span>
              <span class="param-value">95 <small>%</small></span>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="7">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>调度策略</h3>
          </div>
          <div class="schedule-form">
            <div class="form-item">
              <label>运行模式</label>
              <el-select v-model="scheduleMode" size="small" style="width: 100%" @change="onModeChange">
                <el-option label="自动调度" value="auto" />
                <el-option label="手动控制" value="manual" />
                <el-option label="削峰填谷" value="peak_shaving" />
              </el-select>
            </div>
            <div class="form-item">
              <label>SOC下限 ({{ socMin }}%)</label>
              <el-slider v-model="socMin" :min="0" :max="50" :show-tooltip="false" />
            </div>
            <div class="form-item">
              <label>SOC上限 ({{ socMax }}%)</label>
              <el-slider v-model="socMax" :min="50" :max="100" :show-tooltip="false" />
            </div>
            <el-button type="primary" size="small" @click="saveSchedule" :loading="saving" style="width: 100%">保存设置</el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二排：SOC趋势 -->
    <el-row :gutter="24">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>SOC趋势</h3>
          </div>
          <v-chart :option="chartOption" style="height: 280px" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { useRealtimeStore } from '@/stores/realtime'
import api from '@/api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const realtimeStore = useRealtimeStore()
const history = computed(() => realtimeStore.history)

const batteryList = ref([])
const batterySystems = ref([]) // 存储完整的电池系统配置
const scheduleMode = ref('auto')
const socMin = ref(10)
const socMax = ref(90)
const saving = ref(false)

const totalCapacity = computed(() => batteryList.value.reduce((sum, b) => sum + (b.capacity_kwh || 0), 0))
const totalPower = computed(() => batteryList.value.reduce((sum, b) => sum + (b.power || 0), 0))
const availableEnergy = computed(() => batteryList.value.reduce((sum, b) => sum + (b.available_energy || 0), 0))
const avgSoc = computed(() => {
  if (batteryList.value.length === 0) return 0
  return batteryList.value.reduce((sum, b) => sum + (b.soc || 0), 0) / batteryList.value.length
})

function getBatteryColor(battery) {
  if (battery.soc < 0.2) return '#F56C6C'
  if (battery.soc < 0.5) return '#E6A23C'
  return '#67C23A'
}

function getStatusType(status) {
  if (status === 'charging') return 'success'
  if (status === 'discharging') return 'warning'
  return 'info'
}

function getStatusText(status) {
  if (status === 'charging') return '充电中'
  if (status === 'discharging') return '放电中'
  return '待机'
}

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: {
    data: ['SOC'],
    textStyle: { color: '#F8FAFC' }
  },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: history.value.map((_, i) => i),
    axisLabel: { color: '#94A3B8' },
    axisLine: { lineStyle: { color: '#334155' } }
  },
  yAxis: { 
    type: 'value', 
    name: '%', 
    min: 0, 
    max: 100,
    nameTextStyle: { color: '#94A3B8' },
    axisLabel: { color: '#94A3B8' },
    axisLine: { lineStyle: { color: '#334155' } },
    splitLine: { lineStyle: { color: '#334155' } }
  },
  series: [{
    name: 'SOC',
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.3 },
    data: history.value.map(h => (h.battery_soc || 0.5) * 100),
    itemStyle: { color: '#E6A23C' }
  }]
}))

async function fetchBatteryData() {
  try {
    const response = await api.get('/api/battery/realtime')
    if (response.data.success) {
      batteryList.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch battery data:', e)
  }
}

async function fetchBatterySystems() {
  try {
    const response = await api.get('/api/battery/systems')
    if (response.data.success) {
      batterySystems.value = response.data.data
      // 从第一个电池系统加载 SOC 限制设置
      if (batterySystems.value.length > 0) {
        const firstSystem = batterySystems.value[0]
        socMin.value = Math.round((firstSystem.min_soc || 0.1) * 100)
        socMax.value = Math.round((firstSystem.max_soc || 0.9) * 100)
      }
    }
  } catch (e) {
    console.error('Failed to fetch battery systems:', e)
  }
}

async function controlBattery(battery, action) {
  try {
    let endpoint = ''
    let power = 100
    const batteryId = battery.battery_id
    
    if (action === 'charge') {
      endpoint = `/api/battery/systems/${batteryId}/charge`
      battery.status = 'charging'
    } else if (action === 'discharge') {
      endpoint = `/api/battery/systems/${batteryId}/discharge`
      battery.status = 'discharging'
    } else {
      power = 0
      endpoint = `/api/battery/systems/${batteryId}/charge`
      battery.status = 'idle'
    }
    
    await api.post(endpoint, { power })
    // 切换到手动模式
    scheduleMode.value = 'manual'
    ElMessage.success('指令发送成功')
  } catch (e) {
    ElMessage.error('指令发送失败')
    // 失败时刷新数据恢复状态
    fetchBatteryData()
  }
}

async function onModeChange(mode) {
  if (mode === 'auto') {
    // 切换回自动模式，通知后端
    try {
      for (const battery of batteryList.value) {
        await api.post(`/api/battery/systems/${battery.battery_id}/auto`)
      }
      ElMessage.success('已切换到自动调度模式')
    } catch (e) {
      console.error('Failed to switch to auto mode:', e)
    }
  }
}

async function saveSchedule() {
  if (batterySystems.value.length === 0) {
    ElMessage.warning('没有可配置的储能系统')
    return
  }
  
  saving.value = true
  try {
    // 更新所有电池系统的 SOC 限制
    const minSocValue = socMin.value / 100
    const maxSocValue = socMax.value / 100
    
    for (const system of batterySystems.value) {
      await api.put(`/api/battery/systems/${system.id}`, {
        min_soc: minSocValue,
        max_soc: maxSocValue
      })
    }
    
    ElMessage.success('调度策略已保存')
  } catch (e) {
    console.error('Failed to save schedule:', e)
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchBatteryData()
  fetchBatterySystems()
  setInterval(fetchBatteryData, 5000)
})
</script>

<style lang="scss" scoped>
$primary: #00D4AA;
$success: #67C23A;
$warning: #E6A23C;
$danger: #F56C6C;
$info: #409EFF;
$bg-card: #1E293B;
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);

// 等高行
.equal-height-row {
  display: flex;
  flex-wrap: wrap;
  
  > [class*="el-col"] {
    display: flex;
    margin-bottom: 24px;
    
    > .card {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
  }
}

.card-fixed-height {
  min-height: 320px;
}

// 储能卡片列表
.battery-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.battery-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid $border-color;
  border-radius: 10px;
  padding: 16px 20px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: $warning;
    box-shadow: 0 2px 12px rgba($warning, 0.15);
  }
  
  .battery-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    
    span {
      font-weight: 600;
      font-size: 14px;
      color: $text-primary;
      flex: 1;
    }
  }
  
  .battery-content {
    display: flex;
    gap: 20px;
    margin-bottom: 12px;
  }
  
  .battery-visual {
    .battery-body {
      width: 40px;
      height: 70px;
      border: 2px solid $text-secondary;
      border-radius: 4px;
      position: relative;
      overflow: hidden;
      
      &::before {
        content: '';
        position: absolute;
        top: -6px;
        left: 50%;
        transform: translateX(-50%);
        width: 16px;
        height: 4px;
        background: $text-secondary;
        border-radius: 2px 2px 0 0;
      }
      
      .battery-level {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        transition: height 0.5s ease;
      }
    }
  }
  
  .battery-stats {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    
    .stat-item {
      .label {
        display: block;
        font-size: 11px;
        color: $text-secondary;
        margin-bottom: 2px;
      }
      .value {
        font-size: 15px;
        font-weight: 700;
        color: $text-primary;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      }
    }
  }
  
  .battery-controls {
    text-align: center;
    
    :deep(.el-button-group) {
      .el-button {
        background: rgba(255, 255, 255, 0.1);
        border-color: $border-color;
        color: $text-primary;
        
        &:hover {
          background: rgba(255, 255, 255, 0.2);
          border-color: $primary;
          color: $primary;
        }
        
        &.active {
          font-weight: 600;
        }
        
        &.el-button--success {
          background: rgba($success, 0.2);
          border-color: $success;
          color: $success;
        }
        
        &.el-button--warning {
          background: rgba($warning, 0.2);
          border-color: $warning;
          color: $warning;
        }
        
        &.el-button--info {
          background: rgba($info, 0.2);
          border-color: $info;
          color: $info;
        }
      }
    }
  }
}

// 系统参数列表
.params-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  
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
      font-size: 18px;
      font-weight: 700;
      color: $text-primary;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      
      small {
        font-size: 12px;
        font-weight: 400;
        color: $text-secondary;
        margin-left: 4px;
      }
      
      &.highlight {
        color: $warning;
      }
    }
  }
}

// 调度策略表单
.schedule-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  
  .form-item {
    label {
      display: block;
      font-size: 13px;
      color: $text-secondary;
      margin-bottom: 8px;
    }
  }
  
  :deep(.el-slider) {
    .el-slider__runway {
      background-color: rgba(255, 255, 255, 0.1);
    }
  }
}
</style>
