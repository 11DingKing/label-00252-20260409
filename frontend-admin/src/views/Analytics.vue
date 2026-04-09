<template>
  <div class="analytics-page">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon success">
            <el-icon><Sunny /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(energyStats.total_generation) }}</div>
            <div class="stat-label">总发电量 <small>kWh</small></div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon warning">
            <el-icon><Lightning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(energyStats.total_consumption) }}</div>
            <div class="stat-label">总用电量 <small>kWh</small></div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon info">
            <el-icon><Download /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(energyStats.grid_import) }}</div>
            <div class="stat-label">购电量 <small>kWh</small></div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon primary">
            <el-icon><Upload /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(energyStats.grid_export) }}</div>
            <div class="stat-label">售电量 <small>kWh</small></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 中间区域：趋势图全宽 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>能源趋势</h3>
            <div class="header-actions">
              <el-select v-model="selectedMetric" size="small" style="width: 120px" @change="fetchTrendData">
                <el-option label="总发电" value="total_generation" />
                <el-option label="总负载" value="total_load" />
                <el-option label="光伏功率" value="pv_power" />
                <el-option label="风电功率" value="wind_power" />
                <el-option label="电网功率" value="grid_power" />
              </el-select>
              <el-radio-group v-model="period" size="small" @change="fetchData">
                <el-radio-button label="hour">时</el-radio-button>
                <el-radio-button label="day">日</el-radio-button>
                <el-radio-button label="week">周</el-radio-button>
                <el-radio-button label="month">月</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <v-chart :option="trendChartOption" style="height: 280px" autoresize />
        </div>
      </el-col>
    </el-row>
    
    <!-- 效率 + 构成 + 详细统计 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :xs="24" :lg="8">
        <div class="card" style="height: 100%">
          <div class="card-header">
            <h3>系统效率</h3>
          </div>
          <div class="efficiency-grid">
            <div class="efficiency-item">
              <div class="eff-value" :style="{ color: '#10B981' }">{{ formatPercent(efficiency.pv_efficiency) }}</div>
              <div class="eff-label">光伏效率</div>
            </div>
            <div class="efficiency-item">
              <div class="eff-value" :style="{ color: '#3B82F6' }">{{ formatPercent(efficiency.wind_efficiency) }}</div>
              <div class="eff-label">风电效率</div>
            </div>
            <div class="efficiency-item">
              <div class="eff-value" :style="{ color: '#F59E0B' }">{{ formatPercent(efficiency.battery_round_trip_efficiency) }}</div>
              <div class="eff-label">储能效率</div>
            </div>
            <div class="efficiency-item">
              <div class="eff-value" :style="{ color: '#10B981' }">{{ formatPercent(efficiency.renewable_utilization) }}</div>
              <div class="eff-label">可再生利用</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="8">
        <div class="card" style="height: 100%">
          <div class="card-header">
            <h3>能源构成</h3>
          </div>
          <v-chart :option="pieChartOption" style="height: 180px" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="8">
        <div class="card" style="height: 100%">
          <div class="card-header">
            <h3>详细统计</h3>
          </div>
          <div class="detail-list">
            <div class="detail-row">
              <span class="label">光伏发电</span>
              <span class="value">{{ formatNumber(energyStats.pv_generation) }} <small>kWh</small></span>
            </div>
            <div class="detail-row">
              <span class="label">风力发电</span>
              <span class="value">{{ formatNumber(energyStats.wind_generation) }} <small>kWh</small></span>
            </div>
            <div class="detail-row">
              <span class="label">储能充电</span>
              <span class="value">{{ formatNumber(energyStats.battery_charge) }} <small>kWh</small></span>
            </div>
            <div class="detail-row">
              <span class="label">储能放电</span>
              <span class="value">{{ formatNumber(energyStats.battery_discharge) }} <small>kWh</small></span>
            </div>
            <div class="detail-row">
              <span class="label">峰值负载</span>
              <span class="value">{{ formatNumber(energyStats.peak_load) }} <small>kW</small></span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { Sunny, Lightning, Download, Upload } from '@element-plus/icons-vue'
import api from '@/api'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const period = ref('day')
const selectedMetric = ref('total_generation')
const energyStats = ref({})
const efficiency = ref({})
const trendData = ref([])

function formatNumber(val) {
  if (!val && val !== 0) return '0'
  return val.toFixed(1)
}

function formatPercent(val) {
  if (!val && val !== 0) return '0%'
  return (val * 100).toFixed(1) + '%'
}

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 20, bottom: 30 },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trendData.value.map((_, i) => i),
    axisLine: { lineStyle: { color: '#334155' } },
    axisLabel: { color: '#94A3B8' }
  },
  yAxis: { 
    type: 'value', 
    name: 'kW',
    nameTextStyle: { color: '#94A3B8' },
    axisLine: { show: false },
    axisLabel: { color: '#94A3B8' },
    splitLine: { lineStyle: { color: '#334155' } }
  },
  series: [{
    name: selectedMetric.value,
    type: 'line',
    smooth: true,
    symbol: 'none',
    areaStyle: { 
      opacity: 0.3,
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#10B981' },
          { offset: 1, color: 'transparent' }
        ]
      }
    },
    lineStyle: { color: '#10B981', width: 2 },
    data: trendData.value.map(d => d.value)
  }]
}))

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} kWh ({d}%)' },
  legend: { 
    bottom: 0,
    textStyle: { color: '#94A3B8', fontSize: 12 }
  },
  series: [{
    type: 'pie',
    radius: ['40%', '65%'],
    center: ['50%', '45%'],
    label: { show: false },
    data: [
      { value: energyStats.value.pv_generation || 0, name: '光伏', itemStyle: { color: '#10B981' } },
      { value: energyStats.value.wind_generation || 0, name: '风电', itemStyle: { color: '#3B82F6' } },
      { value: energyStats.value.grid_import || 0, name: '电网', itemStyle: { color: '#64748B' } }
    ]
  }]
}))

async function fetchData() {
  await Promise.all([
    fetchEnergyStats(),
    fetchEfficiency(),
    fetchTrendData()
  ])
}

async function fetchEnergyStats() {
  try {
    const response = await api.get('/api/analytics/energy', { params: { period: period.value } })
    if (response.data.success) {
      energyStats.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch energy stats:', e)
  }
}

async function fetchEfficiency() {
  try {
    const response = await api.get('/api/analytics/efficiency')
    if (response.data.success) {
      efficiency.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch efficiency:', e)
  }
}

async function fetchTrendData() {
  try {
    const response = await api.get(`/api/analytics/trends/${selectedMetric.value}`, { params: { points: 60 } })
    if (response.data.success) {
      trendData.value = response.data.data.data
    }
  } catch (e) {
    console.error('Failed to fetch trend data:', e)
  }
}

onMounted(() => {
  fetchData()
  setInterval(fetchData, 30000)
})
</script>

<style lang="scss" scoped>
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);
$success: #10B981;
$warning: #F59E0B;
$info: #3B82F6;
$primary: #6366F1;

.stats-row {
  .stat-card {
    background: #1E293B;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      
      &.success { background: rgba($success, 0.15); color: $success; }
      &.warning { background: rgba($warning, 0.15); color: $warning; }
      &.info { background: rgba($info, 0.15); color: $info; }
      &.primary { background: rgba($primary, 0.15); color: $primary; }
    }
    
    .stat-content {
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: $text-primary;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      }
      
      .stat-label {
        font-size: 13px;
        color: $text-secondary;
        margin-top: 4px;
        
        small {
          font-size: 11px;
          opacity: 0.7;
        }
      }
    }
  }
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.efficiency-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  
  .efficiency-item {
    text-align: center;
    padding: 12px 8px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    
    .eff-value {
      font-size: 20px;
      font-weight: 700;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    }
    
    .eff-label {
      font-size: 12px;
      color: $text-secondary;
      margin-top: 4px;
    }
  }
}

.detail-list {
  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid $border-color;
    
    &:last-child {
      border-bottom: none;
    }
    
    .label {
      font-size: 13px;
      color: $text-secondary;
    }
    
    .value {
      font-size: 15px;
      font-weight: 600;
      color: $text-primary;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      
      small {
        font-size: 11px;
        font-weight: 400;
        color: $text-secondary;
      }
    }
  }
}
</style>
