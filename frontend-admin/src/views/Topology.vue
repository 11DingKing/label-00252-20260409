<template>
  <div class="topology-page">
    <div class="card topology-card">
      <div class="card-header">
        <h3>系统拓扑图</h3>
        <el-tag :type="realtimeStore.connected ? 'success' : 'danger'" size="small">
          {{ realtimeStore.connected ? '实时更新中' : '连接断开' }}
        </el-tag>
      </div>
      
      <div class="topology-wrapper">
        <VueFlow 
          :nodes="nodes" 
          :edges="edges"
          :default-viewport="{ x: 0, y: 0, zoom: 1 }"
          :nodes-draggable="false"
          :nodes-connectable="false"
          :elements-selectable="false"
          :zoom-on-scroll="false"
          :pan-on-scroll="false"
          :pan-on-drag="false"
          fit-view-on-init
        >
          <Background :gap="20" :size="1" pattern-color="rgba(255,255,255,0.03)" />
          
          <template #node-grid="{ data }">
            <div class="custom-node grid-node" :class="{ active: data.active }">
              <div class="node-label">{{ data.label }}</div>
              <div class="node-value">{{ data.value }}<span class="unit">{{ data.unit }}</span></div>
              <div class="node-status" :class="data.statusClass">{{ data.status }}</div>
              <div class="node-indicator" :class="{ active: data.active }"></div>
            </div>
          </template>

          <template #node-source="{ data }">
            <div class="custom-node source-node" :class="{ active: data.active, [data.type]: true }">
              <div class="node-label">{{ data.label }}</div>
              <div class="node-value">{{ data.value }}<span class="unit">{{ data.unit }}</span></div>
              <div v-if="data.status" class="node-status" :class="data.statusClass">{{ data.status }}</div>
            </div>
          </template>

          <template #node-load="{ data }">
            <div class="custom-node load-node" :class="{ active: data.active, warning: data.warning }">
              <div class="node-label">{{ data.label }}</div>
              <div class="node-value">{{ data.value }}<span class="unit">{{ data.unit }}</span></div>
              <div v-if="data.warning" class="impact-badge">冲击负载</div>
            </div>
          </template>
        </VueFlow>

        <!-- 能量流动指示 -->
        <div class="energy-flow-indicator">
          <div class="flow-item generation">
            <span>↑ 发电 {{ formatPower(summary.total_generation) }} kW</span>
          </div>
          <div class="flow-item consumption">
            <span>↓ 用电 {{ formatPower(summary.total_load) }} kW</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 实时数据面板 -->
    <el-row :gutter="24" style="margin-top: 24px">
      <el-col :xs="24" :md="8">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">电网参数</span>
            <el-tag :type="summary.grid_mode === 'grid_connected' ? 'success' : 'warning'" size="small">
              {{ summary.grid_mode === 'grid_connected' ? '并网' : '离网' }}
            </el-tag>
          </div>
          <div class="stat-grid">
            <div class="stat-item">
              <span class="label">电压</span>
              <span class="value">{{ (summary.grid_voltage || 380).toFixed(1) }}<small>V</small></span>
            </div>
            <div class="stat-item">
              <span class="label">频率</span>
              <span class="value">{{ (summary.grid_frequency || 50).toFixed(2) }}<small>Hz</small></span>
            </div>
            <div class="stat-item">
              <span class="label">功率</span>
              <span class="value">{{ formatPower(summary.grid_power) }}<small>kW</small></span>
            </div>
            <div class="stat-item">
              <span class="label">功率因数</span>
              <span class="value">0.95</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">发电统计</span>
            <el-tag type="success" size="small">{{ formatPercent(summary.renewable_ratio) }}% 清洁</el-tag>
          </div>
          <div class="stat-grid">
            <div class="stat-item">
              <span class="label">光伏功率</span>
              <span class="value green">{{ formatPower(summary.pv_power) }}<small>kW</small></span>
            </div>
            <div class="stat-item">
              <span class="label">风电功率</span>
              <span class="value green">{{ formatPower(summary.wind_power) }}<small>kW</small></span>
            </div>
            <div class="stat-item">
              <span class="label">总发电</span>
              <span class="value">{{ formatPower(summary.total_generation) }}<small>kW</small></span>
            </div>
            <div class="stat-item">
              <span class="label">储能功率</span>
              <span class="value">{{ formatPower(summary.battery_power) }}<small>kW</small></span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">负载统计</span>
            <el-tag :type="summary.battery_power > 0 ? 'warning' : summary.battery_power < 0 ? 'success' : 'info'" size="small">
              {{ getBatteryStatus() }}
            </el-tag>
          </div>
          <div class="stat-grid">
            <div class="stat-item">
              <span class="label">总负载</span>
              <span class="value orange">{{ formatPower(summary.total_load) }}<small>kW</small></span>
            </div>
            <div class="stat-item">
              <span class="label">储能SOC</span>
              <span class="value">{{ formatPercent(summary.battery_soc) }}<small>%</small></span>
            </div>
            <div class="stat-item">
              <span class="label">自给率</span>
              <span class="value green">{{ formatPercent(summary.self_sufficiency) }}<small>%</small></span>
            </div>
            <div class="stat-item">
              <span class="label">峰值负载</span>
              <span class="value">{{ formatPower(summary.total_load * 1.2) }}<small>kW</small></span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { useRealtimeStore } from '@/stores/realtime'

const realtimeStore = useRealtimeStore()
const summary = computed(() => realtimeStore.summary)
const loadData = computed(() => realtimeStore.loadData)

function formatPower(value) {
  return (value || 0).toFixed(1)
}

function formatPercent(value) {
  return ((value || 0) * 100).toFixed(1)
}

function getBatteryStatus() {
  const power = summary.value.battery_power || 0
  if (power > 0) return '放电中'
  if (power < 0) return '充电中'
  return '待机'
}

function getBatteryStatusClass() {
  const power = summary.value.battery_power || 0
  if (power > 0) return 'discharging'
  if (power < 0) return 'charging'
  return 'standby'
}

function getLoadPower(type) {
  let total = 0
  for (const load of Object.values(loadData.value)) {
    if (load.load_type === type && load.is_on) {
      total += load.power || 0
    }
  }
  return total.toFixed(1)
}

// 节点定义 - 均匀分布
const nodes = computed(() => [
  // 电网节点 - 顶部中央
  {
    id: 'grid',
    type: 'grid',
    position: { x: 330, y: 30 },
    data: {
      label: '电网',
      value: formatPower(summary.value.grid_power),
      unit: 'kW',
      status: summary.value.grid_mode === 'grid_connected' ? '并网运行' : '离网运行',
      statusClass: summary.value.grid_mode,
      active: summary.value.grid_mode === 'grid_connected'
    }
  },
  // 发电侧节点 - 均匀分布
  {
    id: 'pv',
    type: 'source',
    position: { x: 100, y: 180 },
    data: {
      label: '光伏系统',
      value: formatPower(summary.value.pv_power),
      unit: 'kW',
      type: 'pv',
      active: summary.value.pv_power > 0
    }
  },
  {
    id: 'wind',
    type: 'source',
    position: { x: 330, y: 180 },
    data: {
      label: '风力发电',
      value: formatPower(summary.value.wind_power),
      unit: 'kW',
      type: 'wind',
      active: summary.value.wind_power > 0
    }
  },
  {
    id: 'battery',
    type: 'source',
    position: { x: 560, y: 180 },
    data: {
      label: '储能系统',
      value: formatPercent(summary.value.battery_soc),
      unit: '%',
      type: 'battery',
      status: getBatteryStatus(),
      statusClass: getBatteryStatusClass(),
      active: summary.value.battery_power !== 0
    }
  },
  // 负载节点 - 均匀分布
  {
    id: 'office',
    type: 'load',
    position: { x: 100, y: 360 },
    data: {
      label: '办公负载',
      value: getLoadPower('office'),
      unit: 'kW',
      active: parseFloat(getLoadPower('office')) > 0
    }
  },
  {
    id: 'production',
    type: 'load',
    position: { x: 330, y: 360 },
    data: {
      label: '生产负载',
      value: getLoadPower('production'),
      unit: 'kW',
      active: parseFloat(getLoadPower('production')) > 0
    }
  },
  {
    id: 'ev',
    type: 'load',
    position: { x: 560, y: 360 },
    data: {
      label: '充电桩',
      value: getLoadPower('ev_charger'),
      unit: 'kW',
      active: parseFloat(getLoadPower('ev_charger')) > 0,
      warning: parseFloat(getLoadPower('ev_charger')) > 50
    }
  }
])

// 连线定义
const edges = computed(() => [
  // 电网到母线
  { id: 'grid-bus', source: 'grid', target: 'pv', type: 'smoothstep', animated: true, style: { stroke: '#00D4AA', strokeWidth: 2 } },
  { id: 'grid-wind', source: 'grid', target: 'wind', type: 'smoothstep', animated: true, style: { stroke: '#00D4AA', strokeWidth: 2 } },
  { id: 'grid-battery', source: 'grid', target: 'battery', type: 'smoothstep', animated: true, style: { stroke: '#00D4AA', strokeWidth: 2 } },
  // 发电侧到负载
  { id: 'pv-office', source: 'pv', target: 'office', type: 'smoothstep', animated: summary.value.pv_power > 0, style: { stroke: '#00B894', strokeWidth: 2 } },
  { id: 'wind-production', source: 'wind', target: 'production', type: 'smoothstep', animated: summary.value.wind_power > 0, style: { stroke: '#74B9FF', strokeWidth: 2 } },
  { id: 'battery-ev', source: 'battery', target: 'ev', type: 'smoothstep', animated: summary.value.battery_power !== 0, style: { stroke: '#FDCB6E', strokeWidth: 2 } }
])
</script>

<style lang="scss" scoped>
$primary: #00D4AA;
$success: #00B894;
$warning: #FDCB6E;
$danger: #FF7675;
$info: #74B9FF;
$bg-card: #1E293B;
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);

.topology-page {
  .topology-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .topology-wrapper {
    position: relative;
    height: 520px;
    background: linear-gradient(180deg, rgba(10, 14, 23, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
    border-radius: 12px;
    overflow: hidden;
  }

  // 自定义节点样式 - 统一大小
  :deep(.custom-node) {
    background: rgba($bg-card, 0.95);
    border: 2px solid $border-color;
    border-radius: 12px;
    padding: 16px;
    width: 140px;
    height: 100px;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    &.active {
      border-color: $success;
      box-shadow: 0 0 20px rgba($success, 0.2);
    }

    &.warning {
      border-color: $danger;
      box-shadow: 0 0 20px rgba($danger, 0.2);
    }

    .node-label {
      font-size: 12px;
      color: $text-secondary;
      margin-bottom: 6px;
    }

    .node-value {
      font-size: 26px;
      font-weight: 700;
      color: $text-primary;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      font-variant-numeric: tabular-nums;
      line-height: 1.2;

      .unit {
        font-size: 13px;
        font-weight: 400;
        color: $text-secondary;
        margin-left: 3px;
      }
    }

    .node-status {
      font-size: 10px;
      margin-top: 6px;
      padding: 2px 8px;
      border-radius: 8px;
      display: inline-block;

      &.grid_connected { background: rgba($success, 0.15); color: $success; }
      &.island { background: rgba($warning, 0.15); color: $warning; }
      &.charging { background: rgba($success, 0.15); color: $success; }
      &.discharging { background: rgba($warning, 0.15); color: $warning; }
      &.standby { background: rgba($text-secondary, 0.15); color: $text-secondary; }
    }

    .node-indicator {
      position: absolute;
      top: -4px;
      right: -4px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: $text-secondary;
      border: 2px solid $bg-card;

      &.active {
        background: $success;
        animation: pulse 2s infinite;
      }
    }

    .impact-badge {
      position: absolute;
      top: -8px;
      right: -8px;
      background: $danger;
      color: white;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 10px;
      animation: blink 1s infinite;
    }
  }

  :deep(.grid-node) {
    border-color: $primary;
  }

  :deep(.source-node) {
    &.pv.active { border-color: #FFD93D; box-shadow: 0 0 20px rgba(#FFD93D, 0.2); }
    &.wind.active { border-color: $info; box-shadow: 0 0 20px rgba($info, 0.2); }
    &.battery.active { border-color: $success; box-shadow: 0 0 20px rgba($success, 0.2); }
  }

  :deep(.load-node) {
    &.active { border-color: $warning; box-shadow: 0 0 15px rgba($warning, 0.15); }
    &.warning { border-color: $danger; box-shadow: 0 0 20px rgba($danger, 0.3); }
  }

  // Vue Flow 样式覆盖
  :deep(.vue-flow__edge-path) {
    stroke-width: 2;
  }

  :deep(.vue-flow__edge.animated path) {
    stroke-dasharray: 5;
    animation: dash 0.5s linear infinite;
  }

  // 能量流动指示器
  .energy-flow-indicator {
    position: absolute;
    top: 16px;
    right: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 10;

    .flow-item {
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 500;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;

      &.generation { background: rgba($success, 0.15); color: $success; }
      &.consumption { background: rgba($warning, 0.15); color: $warning; }
    }
  }

  // 统计卡片
  .stat-card {
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 24px;
    background: rgba($bg-card, 0.8);
    border: 1px solid $border-color;

    .stat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid $border-color;
    }

    .stat-label {
      font-size: 14px;
      font-weight: 600;
      color: $text-primary;
    }

    .stat-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .stat-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .label {
        font-size: 11px;
        color: $text-secondary;
        text-transform: uppercase;
      }

      .value {
        font-size: 18px;
        font-weight: 700;
        color: $text-primary;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        font-variant-numeric: tabular-nums;

        small { font-size: 12px; font-weight: 400; color: $text-secondary; margin-left: 2px; }
        &.green { color: $success; }
        &.orange { color: $warning; }
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba($success, 0.4); }
  50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba($success, 0); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes dash {
  to { stroke-dashoffset: -10; }
}
</style>
