<template>
  <div class="wind-system">
    <!-- 第一排：风力监控 + 系统参数 + 风况信息 -->
    <el-row :gutter="24" class="equal-height-row">
      <el-col :xs="24" :lg="10">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>风力发电监控</h3>
          </div>
          
          <div class="wind-list">
            <div class="wind-card" v-for="wind in windList" :key="wind.wind_id">
              <div class="wind-header">
                <el-icon :size="20" color="#409EFF" class="rotating"><Refresh /></el-icon>
                <span>{{ wind.name }}</span>
              </div>
              <div class="wind-stats">
                <div class="stat-item">
                  <span class="label">输出功率</span>
                  <span class="value">{{ wind.power_output?.toFixed(1) || 0 }} kW</span>
                </div>
                <div class="stat-item">
                  <span class="label">风速</span>
                  <span class="value">{{ wind.wind_speed?.toFixed(1) || 0 }} m/s</span>
                </div>
                <div class="stat-item">
                  <span class="label">风向</span>
                  <span class="value">{{ wind.wind_direction?.toFixed(0) || 0 }}°</span>
                </div>
                <div class="stat-item">
                  <span class="label">转速</span>
                  <span class="value">{{ wind.rotor_speed?.toFixed(1) || 0 }} rpm</span>
                </div>
              </div>
              <el-progress 
                :percentage="Math.round((wind.utilization || 0) * 100)" 
                :stroke-width="6"
                :color="'#409EFF'"
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
              <span class="param-label">切入风速</span>
              <span class="param-value">3.0 <small>m/s</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">额定风速</span>
              <span class="param-value">12.0 <small>m/s</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">切出风速</span>
              <span class="param-value">25.0 <small>m/s</small></span>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="7">
        <div class="card card-fixed-height">
          <div class="card-header">
            <h3>风况信息</h3>
          </div>
          <div class="gauge-container">
            <div class="gauge-item">
              <v-chart :option="windDirectionOption" style="height: 160px" autoresize />
            </div>
            <div class="gauge-item">
              <v-chart :option="windSpeedOption" style="height: 160px" autoresize />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二排：发电功率趋势 -->
    <el-row :gutter="24">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>发电功率趋势</h3>
          </div>
          <v-chart :option="chartOption" style="height: 280px" autoresize />
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
import { useRealtimeStore } from '@/stores/realtime'
import api from '@/api'

use([CanvasRenderer, LineChart, GaugeChart, GridComponent, TooltipComponent])

const realtimeStore = useRealtimeStore()
const history = computed(() => realtimeStore.history)

const windList = ref([])

const totalCapacity = computed(() => windList.value.reduce((sum, w) => sum + (w.capacity_kw || 0), 0))
const totalPower = computed(() => windList.value.reduce((sum, w) => sum + (w.power_output || 0), 0))
const avgWindSpeed = computed(() => {
  if (windList.value.length === 0) return 0
  return windList.value.reduce((sum, w) => sum + (w.wind_speed || 0), 0) / windList.value.length
})
const avgWindDirection = computed(() => {
  if (windList.value.length === 0) return 0
  return windList.value.reduce((sum, w) => sum + (w.wind_direction || 0), 0) / windList.value.length
})

// 风向仪表盘
const windDirectionOption = computed(() => ({
  series: [{
    type: 'gauge',
    startAngle: 90,
    endAngle: -270,
    min: 0,
    max: 360,
    splitNumber: 8,
    radius: '75%',
    center: ['50%', '45%'],
    axisLine: {
      lineStyle: {
        width: 6,
        color: [[1, 'rgba(64, 158, 255, 0.3)']]
      }
    },
    axisTick: { show: false },
    splitLine: {
      length: 10,
      lineStyle: { width: 2, color: '#409EFF' }
    },
    axisLabel: {
      distance: 14,
      fontSize: 12,
      fontWeight: 'bold',
      color: '#F8FAFC',
      formatter: (value) => {
        const labels = { 0: 'N', 90: 'E', 180: 'S', 270: 'W' }
        return labels[value] || ''
      }
    },
    pointer: {
      icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
      length: '55%',
      width: 12,
      offsetCenter: [0, '-10%'],
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#F56C6C' },
            { offset: 0.5, color: '#F56C6C' },
            { offset: 0.5, color: '#409EFF' },
            { offset: 1, color: '#409EFF' }
          ]
        }
      }
    },
    anchor: {
      show: true,
      size: 14,
      itemStyle: { color: '#409EFF', borderWidth: 2, borderColor: '#1E293B' }
    },
    title: { show: false },
    detail: {
      offsetCenter: [0, '95%'],
      fontSize: 14,
      fontWeight: 'bold',
      color: '#94A3B8',
      formatter: (value) => `${value}° 风向`
    },
    data: [{ value: avgWindDirection.value.toFixed(0) }]
  }]
}))

// 风速仪表盘
const windSpeedOption = computed(() => ({
  series: [{
    type: 'gauge',
    radius: '75%',
    center: ['50%', '45%'],
    startAngle: 200,
    endAngle: -20,
    min: 0,
    max: 30,
    splitNumber: 6,
    axisLine: {
      lineStyle: {
        width: 12,
        color: [
          [0.1, '#67C23A'],
          [0.4, '#409EFF'],
          [0.7, '#E6A23C'],
          [1, '#F56C6C']
        ]
      }
    },
    axisTick: {
      length: 4,
      lineStyle: { color: 'auto', width: 1 }
    },
    splitLine: {
      length: 10,
      lineStyle: { color: 'auto', width: 2 }
    },
    axisLabel: {
      distance: 16,
      fontSize: 10,
      color: '#94A3B8'
    },
    pointer: {
      length: '50%',
      width: 5,
      itemStyle: { color: '#F8FAFC' }
    },
    anchor: {
      show: true,
      size: 10,
      itemStyle: { color: '#F8FAFC' }
    },
    title: { show: false },
    detail: {
      offsetCenter: [0, '95%'],
      fontSize: 14,
      fontWeight: 'bold',
      color: '#94A3B8',
      formatter: (value) => `${value} m/s 风速`
    },
    data: [{ value: avgWindSpeed.value.toFixed(1) }]
  }]
}))

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: {
    data: ['风电功率'],
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
    name: '风电功率',
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.3 },
    data: history.value.map(h => h.wind_power || 0),
    itemStyle: { color: '#409EFF' }
  }]
}))

async function fetchWindData() {
  try {
    const response = await api.get('/api/wind/realtime')
    if (response.data.success) {
      windList.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch wind data:', e)
  }
}

onMounted(() => {
  fetchWindData()
  setInterval(fetchWindData, 5000)
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

.card-fixed-height {
  min-height: 320px;
}

// 风力卡片列表
.wind-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.wind-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid $border-color;
  border-radius: 10px;
  padding: 16px 20px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: $info;
    box-shadow: 0 2px 12px rgba($info, 0.15);
  }
  
  .wind-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
    
    span {
      font-weight: 600;
      font-size: 14px;
      color: $text-primary;
    }
    
    .rotating {
      animation: rotate 2s linear infinite;
    }
  }
  
  .wind-stats {
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
        color: $info;
      }
    }
  }
}

// 仪表盘容器
.gauge-container {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  align-content: center;
  padding: 16px 0;
  
  .gauge-item {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
