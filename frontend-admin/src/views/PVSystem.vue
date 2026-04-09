<template>
  <div class="pv-system">
    <!-- 第一排：光伏监控 + 系统参数 + 环境参数 -->
    <el-row :gutter="24" class="equal-height-row">
      <el-col :xs="24" :lg="10">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>光伏系统监控</h3>
            <el-button type="primary" size="small" @click="openConfigDialog">
              <el-icon><Setting /></el-icon> 配置
            </el-button>
          </div>
          
          <div class="pv-list">
            <div class="pv-card" v-for="pv in pvList" :key="pv.pv_id">
              <div class="pv-header">
                <el-icon :size="20" color="#67C23A"><Sunny /></el-icon>
                <span>{{ pv.name }}</span>
              </div>
              <div class="pv-stats">
                <div class="stat-item">
                  <span class="label">输出功率</span>
                  <span class="value">{{ pv.power_output?.toFixed(1) || 0 }} kW</span>
                </div>
                <div class="stat-item">
                  <span class="label">光照强度</span>
                  <span class="value">{{ pv.irradiance?.toFixed(0) || 0 }} W/m²</span>
                </div>
                <div class="stat-item">
                  <span class="label">环境温度</span>
                  <span class="value">{{ pv.temperature?.toFixed(1) || 25 }} °C</span>
                </div>
                <div class="stat-item">
                  <span class="label">利用率</span>
                  <span class="value">{{ ((pv.utilization || 0) * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <el-progress 
                :percentage="Math.round((pv.utilization || 0) * 100)" 
                :stroke-width="6"
                :color="'#67C23A'"
                :show-text="false"
              />
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
              <span class="param-label">装机容量</span>
              <span class="param-value">{{ totalCapacity }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">当前功率</span>
              <span class="param-value highlight">{{ totalPower.toFixed(1) }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">转换效率</span>
              <span class="param-value">{{ avgEfficiency }} <small>%</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">面板面积</span>
              <span class="param-value">{{ totalArea }} <small>m²</small></span>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="7">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>环境参数</h3>
          </div>
          <div class="env-params">
            <div class="env-item sun">
              <div class="env-icon">
                <el-icon :size="32"><Sunny /></el-icon>
              </div>
              <div class="env-value">{{ avgIrradiance.toFixed(0) }}</div>
              <div class="env-label">光照强度 (W/m²)</div>
            </div>
            <div class="env-item temp">
              <div class="env-icon">
                <el-icon :size="32"><Cloudy /></el-icon>
              </div>
              <div class="env-value">{{ avgTemperature.toFixed(1) }}</div>
              <div class="env-label">环境温度 (°C)</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二排：发电功率趋势 -->
    <el-row :gutter="24" style="margin-top: 24px">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>发电功率趋势</h3>
          </div>
          <v-chart :option="chartOption" style="height: 280px" autoresize />
        </div>
      </el-col>
    </el-row>
    <!-- Config Dialog -->
    <el-dialog v-model="showConfigDialog" title="光伏系统配置" width="500px">
      <el-form :model="configForm" label-width="100px">
        <el-form-item label="系统名称">
          <el-input v-model="configForm.name" />
        </el-form-item>
        <el-form-item label="装机容量">
          <el-input-number v-model="configForm.capacity_kw" :min="0" :max="10000" />
          <span style="margin-left: 8px">kW</span>
        </el-form-item>
        <el-form-item label="转换效率">
          <el-slider v-model="configForm.efficiency" :min="0" :max="100" :format-tooltip="v => v + '%'" />
        </el-form-item>
        <el-form-item label="面板面积">
          <el-input-number v-model="configForm.panel_area" :min="0" :max="100000" />
          <span style="margin-left: 8px">m²</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { useRealtimeStore } from '@/stores/realtime'
import api from '@/api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const realtimeStore = useRealtimeStore()
const pvData = computed(() => realtimeStore.pvData)
const history = computed(() => realtimeStore.history)

const pvList = ref([])
const showConfigDialog = ref(false)
const configForm = ref({
  name: '',
  capacity_kw: 500,
  efficiency: 18,
  panel_area: 2800
})

function openConfigDialog() {
  if (pvList.value.length > 0) {
    const pv = pvList.value[0]
    configForm.value = {
      name: pv.name || '',
      capacity_kw: pv.capacity_kw || 500,
      efficiency: (pv.efficiency || 0.18) * 100,
      panel_area: pv.panel_area || 2800
    }
  }
  showConfigDialog.value = true
}

const totalCapacity = computed(() => pvList.value.reduce((sum, pv) => sum + (pv.capacity_kw || 0), 0))
const totalPower = computed(() => pvList.value.reduce((sum, pv) => sum + (pv.power_output || 0), 0))
const totalArea = computed(() => pvList.value.reduce((sum, pv) => sum + (pv.panel_area || 0), 0))
const avgEfficiency = computed(() => {
  if (pvList.value.length === 0) return 0
  return (pvList.value.reduce((sum, pv) => sum + (pv.efficiency || 0), 0) / pvList.value.length * 100).toFixed(1)
})
const avgIrradiance = computed(() => {
  if (pvList.value.length === 0) return 0
  return pvList.value.reduce((sum, pv) => sum + (pv.irradiance || 0), 0) / pvList.value.length
})
const avgTemperature = computed(() => {
  if (pvList.value.length === 0) return 25
  return pvList.value.reduce((sum, pv) => sum + (pv.temperature || 25), 0) / pvList.value.length
})

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { 
    data: ['光伏功率'],
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
    name: 'kW',
    nameTextStyle: { color: '#94A3B8' },
    axisLabel: { color: '#94A3B8' },
    axisLine: { lineStyle: { color: '#334155' } },
    splitLine: { lineStyle: { color: '#334155' } }
  },
  series: [{
    name: '光伏功率',
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.3 },
    data: history.value.map(h => h.pv_power || 0),
    itemStyle: { color: '#67C23A' }
  }]
}))

async function fetchPVData() {
  try {
    const response = await api.get('/api/pv/realtime')
    if (response.data.success) {
      pvList.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch PV data:', e)
  }
}

async function saveConfig() {
  try {
    if (pvList.value.length > 0) {
      // 更新第一个光伏系统的配置
      const systemId = pvList.value[0].pv_id
      await api.put(`/api/pv/systems/${systemId}`, {
        name: configForm.value.name,
        capacity_kw: configForm.value.capacity_kw,
        efficiency: configForm.value.efficiency / 100,
        panel_area: configForm.value.panel_area
      })
    } else {
      // 创建新的光伏系统
      await api.post('/api/pv/systems', {
        name: configForm.value.name || '光伏系统1',
        capacity_kw: configForm.value.capacity_kw,
        efficiency: configForm.value.efficiency / 100,
        panel_area: configForm.value.panel_area
      })
    }
    ElMessage.success('配置保存成功')
    showConfigDialog.value = false
    fetchPVData()
  } catch (e) {
    console.error('Save config error:', e)
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(() => {
  fetchPVData()
  setInterval(fetchPVData, 5000)
})
</script>

<style lang="scss" scoped>
$primary: #00D4AA;
$success: #67C23A;
$warning: #E6A23C;
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

// 固定高度卡片
.card-fixed-height {
  min-height: 280px;
}

// 光伏卡片列表
.pv-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.pv-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid $border-color;
  border-radius: 10px;
  padding: 16px 20px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: $success;
    box-shadow: 0 2px 12px rgba($success, 0.15);
  }
  
  .pv-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
    
    span {
      font-weight: 600;
      font-size: 14px;
      color: $text-primary;
    }
  }
  
  .pv-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 14px;
    
    .stat-item {
      .label {
        display: block;
        font-size: 11px;
        color: $text-secondary;
        margin-bottom: 4px;
      }
      .value {
        font-size: 16px;
        font-weight: 700;
        color: $text-primary;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      }
    }
  }

  :deep(.el-progress) {
    .el-progress-bar__outer {
      background-color: rgba(255, 255, 255, 0.1);
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
    padding: 14px 0;
    border-bottom: 1px solid $border-color;
    
    &:last-child {
      border-bottom: none;
    }
    
    .param-label {
      font-size: 14px;
      color: $text-secondary;
    }
    
    .param-value {
      font-size: 20px;
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
        color: $success;
      }
    }
  }
}

// 环境参数
.env-params {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-content: center;
  padding: 10px 0;
  
  .env-item {
    text-align: center;
    padding: 28px 16px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    border: 1px solid $border-color;
    
    .env-icon {
      width: 56px;
      height: 56px;
      margin: 0 auto 14px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    &.sun .env-icon {
      background: rgba($warning, 0.15);
      color: $warning;
    }
    
    &.temp .env-icon {
      background: rgba($info, 0.15);
      color: $info;
    }
    
    .env-value {
      font-size: 32px;
      font-weight: 700;
      color: $text-primary;
      margin-bottom: 6px;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    }
    
    .env-label {
      font-size: 12px;
      color: $text-secondary;
    }
  }
}
</style>
