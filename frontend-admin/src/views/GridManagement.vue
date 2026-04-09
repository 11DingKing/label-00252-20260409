<template>
  <div class="grid-management">
    <el-row :gutter="24">
      <el-col :xs="24" :lg="16">
        <div class="card">
          <div class="card-header">
            <h3>电网状态</h3>
            <el-tag :type="gridData.is_connected ? 'success' : 'warning'" size="large">
              {{ gridData.mode === 'grid_connected' ? '并网运行' : '离网运行' }}
            </el-tag>
          </div>
          
          <el-row :gutter="24">
            <el-col :span="6">
              <div class="grid-stat">
                <div class="stat-icon" :class="gridData.power > 0 ? 'import' : 'export'">
                  <el-icon :size="32"><Connection /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ Math.abs(gridData.power || 0).toFixed(1) }}</div>
                  <div class="stat-label">{{ gridData.power > 0 ? '购电功率' : '售电功率' }} (kW)</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="grid-stat">
                <div class="stat-icon voltage">
                  <el-icon :size="32"><Odometer /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ (gridData.voltage || 380).toFixed(1) }}</div>
                  <div class="stat-label">电压 (V)</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="grid-stat">
                <div class="stat-icon frequency">
                  <el-icon :size="32"><Timer /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ (gridData.frequency || 50).toFixed(2) }}</div>
                  <div class="stat-label">频率 (Hz)</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="grid-stat">
                <div class="stat-icon phase">
                  <el-icon :size="32"><Compass /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ (gridData.phase_angle || 0).toFixed(1) }}</div>
                  <div class="stat-label">相角 (°)</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>电网功率趋势</h3>
          </div>
          <v-chart :option="chartOption" style="height: 300px" autoresize />
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>电压/频率稳定性</h3>
          </div>
          <el-row :gutter="24">
            <el-col :span="12">
              <v-chart :option="voltageGaugeOption" style="height: 200px" autoresize />
              <div class="gauge-label">电压稳定性</div>
            </el-col>
            <el-col :span="12">
              <v-chart :option="frequencyGaugeOption" style="height: 200px" autoresize />
              <div class="gauge-label">频率稳定性</div>
            </el-col>
          </el-row>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>运行模式</h3>
            <el-tag :type="currentMode === 'grid_connected' ? 'success' : 'warning'" size="small" effect="dark">
              {{ currentMode === 'grid_connected' ? '在线' : '独立' }}
            </el-tag>
          </div>
          <div class="mode-selector-enhanced">
            <div 
              class="mode-card" 
              :class="{ active: currentMode === 'grid_connected' }"
              @click="changeMode('grid_connected')"
            >
              <div class="mode-icon grid-connected">
                <el-icon :size="28"><Connection /></el-icon>
              </div>
              <div class="mode-info">
                <div class="mode-title">并网模式</div>
                <div class="mode-desc">与电网互联，可购售电</div>
              </div>
              <div class="mode-check" v-if="currentMode === 'grid_connected'">
                <el-icon :size="18"><Check /></el-icon>
              </div>
            </div>
            <div 
              class="mode-card" 
              :class="{ active: currentMode === 'islanded' }"
              @click="changeMode('islanded')"
            >
              <div class="mode-icon islanded">
                <el-icon :size="28"><SwitchButton /></el-icon>
              </div>
              <div class="mode-info">
                <div class="mode-title">离网模式</div>
                <div class="mode-desc">独立运行，依赖储能</div>
              </div>
              <div class="mode-check" v-if="currentMode === 'islanded'">
                <el-icon :size="18"><Check /></el-icon>
              </div>
            </div>
          </div>
          <transition name="fade">
            <div v-if="currentMode === 'islanded'" class="mode-warning">
              <el-icon :size="16"><Warning /></el-icon>
              <span>离网模式下系统将独立运行，请确保储能充足</span>
            </div>
          </transition>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>电网参数</h3>
          </div>
          <div class="params-list">
            <div class="param-item">
              <span class="param-label">最大购电</span>
              <span class="param-value">{{ gridData.max_import || 800 }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">最大售电</span>
              <span class="param-value">{{ gridData.max_export || 500 }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">额定电压</span>
              <span class="param-value">380 <small>V</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">额定频率</span>
              <span class="param-value">50 <small>Hz</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">电压容差</span>
              <span class="param-value">±5 <small>%</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">频率容差</span>
              <span class="param-value">±0.2 <small>Hz</small></span>
            </div>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>余电上网设置</h3>
          </div>
          <el-form label-width="100px" size="small">
            <el-form-item label="启用售电">
              <el-switch v-model="exportEnabled" />
            </el-form-item>
            <el-form-item label="最大售电">
              <el-input-number v-model="maxExport" :min="0" :max="1000" :disabled="!exportEnabled" />
              <span style="margin-left: 8px">kW</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveExportSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, GaugeChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { useRealtimeStore } from '@/stores/realtime'
import api from '@/api'

use([CanvasRenderer, LineChart, GaugeChart, GridComponent, TooltipComponent])

const realtimeStore = useRealtimeStore()
const history = computed(() => realtimeStore.history)
const gridData = computed(() => realtimeStore.gridData)

const currentMode = ref('grid_connected')
const exportEnabled = ref(true)
const maxExport = ref(500)

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: history.value.map((_, i) => i)
  },
  yAxis: { type: 'value', name: 'kW' },
  series: [{
    name: '电网功率',
    type: 'line',
    smooth: true,
    areaStyle: { 
      opacity: 0.3,
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#409EFF' },
          { offset: 1, color: '#fff' }
        ]
      }
    },
    data: history.value.map(h => h.grid_power || 0),
    itemStyle: { color: '#409EFF' }
  }]
}))

const voltageGaugeOption = computed(() => {
  const voltage = gridData.value.voltage || 380
  const deviation = Math.abs(voltage - 380) / 380 * 100
  
  return {
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 10,
      progress: { show: true, width: 18 },
      axisLine: { lineStyle: { width: 18 } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      detail: { 
        valueAnimation: true, 
        formatter: '{value}%',
        fontSize: 20,
        offsetCenter: [0, '20%']
      },
      data: [{ value: deviation.toFixed(2) }],
      itemStyle: { color: deviation < 5 ? '#67C23A' : '#F56C6C' }
    }]
  }
})

const frequencyGaugeOption = computed(() => {
  const frequency = gridData.value.frequency || 50
  const deviation = Math.abs(frequency - 50) / 50 * 100
  
  return {
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 1,
      progress: { show: true, width: 18 },
      axisLine: { lineStyle: { width: 18 } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      detail: { 
        valueAnimation: true, 
        formatter: '{value}%',
        fontSize: 20,
        offsetCenter: [0, '20%']
      },
      data: [{ value: deviation.toFixed(3) }],
      itemStyle: { color: deviation < 0.4 ? '#67C23A' : '#F56C6C' }
    }]
  }
})

async function changeMode(mode) {
  if (mode === currentMode.value) return
  
  const previousMode = currentMode.value
  currentMode.value = mode
  
  try {
    await api.post('/api/grid/mode', { mode })
    ElMessage.success(`已切换至${mode === 'grid_connected' ? '并网' : '离网'}模式`)
  } catch (e) {
    ElMessage.error('模式切换失败')
    currentMode.value = previousMode
  }
}

async function saveExportSettings() {
  try {
    await api.post('/api/grid/export', {
      max_export: maxExport.value,
      enabled: exportEnabled.value
    })
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function fetchGridStatus() {
  try {
    const response = await api.get('/api/grid/status')
    if (response.data.success) {
      const data = response.data.data
      currentMode.value = data.mode
      maxExport.value = data.max_export || 500
      exportEnabled.value = data.connection_type !== 'import_only'
    }
  } catch (e) {
    console.error('Failed to fetch grid status:', e)
  }
}

onMounted(() => {
  fetchGridStatus()
})
</script>

<style lang="scss" scoped>
$warning: #FDCB6E;
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);

.grid-stat {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(31, 41, 55, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  
  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    
    &.import { background: linear-gradient(135deg, #FF7675, #E6A23C); }
    &.export { background: linear-gradient(135deg, #00B894, #00D4AA); }
    &.voltage { background: linear-gradient(135deg, #74B9FF, #409EFF); }
    &.frequency { background: linear-gradient(135deg, #FDCB6E, #F7BA2A); }
    &.phase { background: linear-gradient(135deg, #64748B, #94A3B8); }
  }
  
  .stat-info {
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #F8FAFC;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      font-variant-numeric: tabular-nums;
    }
    .stat-label {
      font-size: 12px;
      color: #94A3B8;
    }
  }
}

// 运行模式选择器增强样式
.mode-selector-enhanced {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
  
  .mode-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px;
    background: rgba(31, 41, 55, 0.5);
    border: 2px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.25s ease;
    position: relative;
    
    &:hover {
      background: rgba(31, 41, 55, 0.8);
      border-color: rgba(255, 255, 255, 0.15);
      transform: translateY(-1px);
    }
    
    &.active {
      background: rgba(64, 158, 255, 0.12);
      border-color: #409EFF;
      box-shadow: 0 0 20px rgba(64, 158, 255, 0.15);
      
      .mode-icon {
        transform: scale(1.05);
      }
    }
    
    .mode-icon {
      width: 52px;
      height: 52px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      flex-shrink: 0;
      transition: transform 0.25s ease;
      
      &.grid-connected {
        background: linear-gradient(135deg, #00B894, #00D4AA);
        box-shadow: 0 4px 12px rgba(0, 184, 148, 0.3);
      }
      
      &.islanded {
        background: linear-gradient(135deg, #FDCB6E, #F39C12);
        box-shadow: 0 4px 12px rgba(253, 203, 110, 0.3);
      }
    }
    
    .mode-info {
      flex: 1;
      
      .mode-title {
        font-size: 16px;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 4px;
      }
      
      .mode-desc {
        font-size: 12px;
        color: #94A3B8;
      }
    }
    
    .mode-check {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #409EFF;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      animation: checkPop 0.3s ease;
    }
  }
}

.mode-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: rgba(253, 203, 110, 0.1);
  border: 1px solid rgba(253, 203, 110, 0.3);
  border-radius: 8px;
  margin-top: 12px;
  font-size: 13px;
  color: #FDCB6E;
  
  .el-icon {
    flex-shrink: 0;
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@keyframes checkPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.gauge-label {
  text-align: center;
  font-size: 14px;
  color: #94A3B8;
  margin-top: -20px;
}

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
</style>
