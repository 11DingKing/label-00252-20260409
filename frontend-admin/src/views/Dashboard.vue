<template>
  <div class="dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card success">
          <div class="stat-content">
            <div class="stat-value">
              {{ formatPower(summary.total_generation) }}
            </div>
            <div class="stat-label">总发电功率 (kW)</div>
            <div class="stat-trend up">
              <el-icon><Top /></el-icon>
              <span>{{ renewablePercent }}% 可再生</span>
            </div>
          </div>
          <div class="stat-icon">
            <el-icon><Sunny /></el-icon>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card warning">
          <div class="stat-content">
            <div class="stat-value">{{ formatPower(summary.total_load) }}</div>
            <div class="stat-label">总负载功率 (kW)</div>
            <div class="stat-trend">
              <span>{{ loadCount }} 个负载在线</span>
            </div>
          </div>
          <div class="stat-icon">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div
          class="stat-card"
          :class="summary.grid_power > 0 ? 'info' : 'success'"
        >
          <div class="stat-content">
            <div class="stat-value">
              {{ formatPower(Math.abs(summary.grid_power || 0)) }}
            </div>
            <div class="stat-label">
              {{ summary.grid_power > 0 ? "购电功率" : "售电功率" }} (kW)
            </div>
            <div class="stat-trend" :class="summary.grid_power > 0 ? '' : 'up'">
              <el-icon v-if="summary.grid_power <= 0"><Top /></el-icon>
              <span>{{
                summary.grid_mode === "grid_connected" ? "并网运行" : "离网运行"
              }}</span>
            </div>
          </div>
          <div class="stat-icon">
            <el-icon><Connection /></el-icon>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card" :class="getBatterySocClass()">
          <div class="stat-content">
            <div class="stat-value">
              {{ formatPercent(summary.battery_soc) }}%
            </div>
            <div class="stat-label">储能 SOC</div>
            <div class="stat-trend">
              <span>{{ getBatteryStatus() }}</span>
            </div>
          </div>
          <div class="stat-icon">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="battery-bar">
            <div
              class="battery-level"
              :style="{ width: formatPercent(summary.battery_soc) + '%' }"
            ></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <div class="card">
          <div class="card-header">
            <h3>实时功率趋势</h3>
            <div class="chart-legend">
              <span class="legend-item generation"><i></i>发电</span>
              <span class="legend-item load"><i></i>负载</span>
              <span class="legend-item grid"><i></i>电网</span>
              <span class="legend-item battery"><i></i>储能</span>
            </div>
          </div>
          <v-chart
            :option="powerChartOption"
            style="height: 320px"
            autoresize
          />
        </div>
      </el-col>
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>能源构成</h3>
          </div>
          <div v-if="hasPieData" class="chart-container">
            <v-chart
              :option="pieChartOption"
              style="height: 320px"
              autoresize
            />
          </div>
          <div v-else class="no-data-placeholder">
            <el-icon :size="48"><DataLine /></el-icon>
            <span>暂无数据</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 子系统状态 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <div class="card system-card">
          <div class="card-header">
            <h3>光伏系统</h3>
            <span
              class="status-indicator"
              :class="summary.pv_power > 0 ? 'online' : 'offline'"
            >
              {{ summary.pv_power > 0 ? "发电中" : "停机" }}
            </span>
          </div>
          <div class="system-gauge">
            <v-chart :option="pvGaugeOption" style="height: 160px" autoresize />
            <div class="gauge-info">
              <div class="gauge-value">{{ formatPower(summary.pv_power) }}</div>
              <div class="gauge-unit">kW</div>
            </div>
          </div>
          <div class="system-stats">
            <div class="stat-row">
              <span>装机容量</span>
              <span>500 kW</span>
            </div>
            <div class="stat-row">
              <span>利用率</span>
              <span
                >{{ (((summary.pv_power || 0) / 500) * 100).toFixed(1) }}%</span
              >
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="card system-card">
          <div class="card-header">
            <h3>风力发电</h3>
            <span
              class="status-indicator"
              :class="summary.wind_power > 0 ? 'online' : 'offline'"
            >
              {{ summary.wind_power > 0 ? "发电中" : "停机" }}
            </span>
          </div>
          <div class="system-gauge">
            <v-chart
              :option="windGaugeOption"
              style="height: 160px"
              autoresize
            />
            <div class="gauge-info">
              <div class="gauge-value">
                {{ formatPower(summary.wind_power) }}
              </div>
              <div class="gauge-unit">kW</div>
            </div>
          </div>
          <div class="system-stats">
            <div class="stat-row">
              <span>装机容量</span>
              <span>300 kW</span>
            </div>
            <div class="stat-row">
              <span>利用率</span>
              <span
                >{{
                  (((summary.wind_power || 0) / 300) * 100).toFixed(1)
                }}%</span
              >
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="card system-card">
          <div class="card-header">
            <h3>储能系统</h3>
            <span class="status-indicator" :class="getBatteryStatusClass()">
              {{ getBatteryStatus() }}
            </span>
          </div>
          <div class="system-gauge">
            <v-chart
              :option="batteryGaugeOption"
              style="height: 160px"
              autoresize
            />
            <div class="gauge-info">
              <div class="gauge-value">
                {{ formatPercent(summary.battery_soc) }}
              </div>
              <div class="gauge-unit">%</div>
            </div>
          </div>
          <div class="system-stats">
            <div class="stat-row">
              <span>总容量</span>
              <span>1000 kWh</span>
            </div>
            <div class="stat-row">
              <span>当前功率</span>
              <span>{{ formatPower(summary.battery_power) }} kW</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 电网状态 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card grid-status-card">
          <div class="card-header">
            <h3>电网状态</h3>
            <el-tag
              :type="
                summary.grid_mode === 'grid_connected' ? 'success' : 'warning'
              "
              effect="dark"
            >
              {{
                summary.grid_mode === "grid_connected" ? "并网运行" : "离网运行"
              }}
            </el-tag>
          </div>
          <el-row :gutter="40">
            <el-col :xs="12" :md="6">
              <div class="grid-metric">
                <div class="metric-icon voltage">
                  <el-icon><Odometer /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-value">
                    {{ (summary.grid_voltage || 380).toFixed(1) }}
                  </div>
                  <div class="metric-label">电压 (V)</div>
                </div>
                <div class="metric-status" :class="getVoltageStatus()">
                  {{ getVoltageStatus() === "normal" ? "正常" : "异常" }}
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :md="6">
              <div class="grid-metric">
                <div class="metric-icon frequency">
                  <el-icon><Timer /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-value">
                    {{ (summary.grid_frequency || 50).toFixed(2) }}
                  </div>
                  <div class="metric-label">频率 (Hz)</div>
                </div>
                <div class="metric-status" :class="getFrequencyStatus()">
                  {{ getFrequencyStatus() === "normal" ? "正常" : "异常" }}
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :md="6">
              <div class="grid-metric">
                <div class="metric-icon renewable">
                  <el-icon><Sunny /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-value">
                    {{ formatPercent(summary.renewable_ratio) }}
                  </div>
                  <div class="metric-label">可再生占比 (%)</div>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :md="6">
              <div class="grid-metric">
                <div class="metric-icon self">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div class="metric-info">
                  <div class="metric-value">
                    {{ formatPercent(summary.self_sufficiency) }}
                  </div>
                  <div class="metric-label">自给率 (%)</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, PieChart, GaugeChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import { useRealtimeStore } from "@/stores/realtime";
import { DataLine } from "@element-plus/icons-vue";
import api from "@/api";

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GaugeChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
]);

const realtimeStore = useRealtimeStore();
const summary = computed(() => realtimeStore.summary);
const history = computed(() => realtimeStore.history);

const thresholds = ref({
  voltage: {
    nominal: 380,
    tolerance: 0.05,
    min: 361,
    max: 399,
  },
  frequency: {
    nominal: 50,
    tolerance: 0.004,
    min: 49.8,
    max: 50.2,
  },
});

const loadCount = computed(
  () => Object.values(realtimeStore.loadData).filter((l) => l.is_on).length,
);
const renewablePercent = computed(() =>
  formatPercent(summary.value.renewable_ratio),
);

const hasPieData = computed(() => {
  const pv = summary.value.pv_power || 0;
  const wind = summary.value.wind_power || 0;
  const grid = Math.max(0, summary.value.grid_power || 0);
  return pv > 0 || wind > 0 || grid > 0;
});

async function fetchThresholds() {
  try {
    const response = await api.get("/api/config/thresholds");
    if (response.data && response.data.data) {
      thresholds.value = response.data.data;
    }
  } catch (error) {
    console.error("Failed to fetch thresholds:", error);
  }
}

function formatPower(value) {
  return (value || 0).toFixed(1);
}

function formatPercent(value) {
  return ((value || 0) * 100).toFixed(1);
}

function formatTime(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

function getBatteryStatus() {
  const power = summary.value.battery_power || 0;
  if (power > 5) return "放电中";
  if (power < -5) return "充电中";
  return "待机";
}

function getBatteryStatusClass() {
  const power = summary.value.battery_power || 0;
  if (power > 5) return "warning";
  if (power < -5) return "online";
  return "offline";
}

function getBatterySocClass() {
  const soc = summary.value.battery_soc || 0.5;
  if (soc < 0.2) return "danger";
  if (soc < 0.5) return "warning";
  return "success";
}

function getVoltageStatus() {
  const v = summary.value.grid_voltage || thresholds.value.voltage.nominal;
  const { min, max } = thresholds.value.voltage;
  return v >= min && v <= max ? "normal" : "warning";
}

function getFrequencyStatus() {
  const f = summary.value.grid_frequency || thresholds.value.frequency.nominal;
  const { min, max } = thresholds.value.frequency;
  return f >= min && f <= max ? "normal" : "warning";
}

const chartColors = {
  generation: "#00D4AA",
  load: "#FDCB6E",
  grid: "#74B9FF",
  battery: "#A29BFE",
};

const powerChartOption = computed(() => ({
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(30, 41, 59, 0.95)",
    borderColor: "rgba(255,255,255,0.1)",
    textStyle: { color: "#F8FAFC" },
  },
  grid: {
    left: "3%",
    right: "4%",
    bottom: "3%",
    top: "10%",
    containLabel: true,
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: history.value.map((h) => formatTime(h.timestamp)),
    axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } },
    axisLabel: { color: "#64748B" },
  },
  yAxis: {
    type: "value",
    name: "kW",
    nameTextStyle: { color: "#64748B" },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
    axisLabel: { color: "#64748B" },
  },
  series: [
    {
      name: "发电",
      type: "line",
      smooth: true,
      symbol: "none",
      data: history.value.map((h) => h.total_generation || 0),
      lineStyle: { width: 2, color: chartColors.generation },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(0,212,170,0.3)" },
            { offset: 1, color: "rgba(0,212,170,0)" },
          ],
        },
      },
    },
    {
      name: "负载",
      type: "line",
      smooth: true,
      symbol: "none",
      data: history.value.map((h) => h.total_load || 0),
      lineStyle: { width: 2, color: chartColors.load },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(253,203,110,0.3)" },
            { offset: 1, color: "rgba(253,203,110,0)" },
          ],
        },
      },
    },
    {
      name: "电网",
      type: "line",
      smooth: true,
      symbol: "none",
      data: history.value.map((h) => h.grid_power || 0),
      lineStyle: { width: 2, color: chartColors.grid },
    },
    {
      name: "储能",
      type: "line",
      smooth: true,
      symbol: "none",
      data: history.value.map((h) => h.battery_power || 0),
      lineStyle: { width: 2, color: chartColors.battery, type: "dashed" },
    },
  ],
}));

const pieChartOption = computed(() => ({
  tooltip: {
    trigger: "item",
    backgroundColor: "rgba(30, 41, 59, 0.95)",
    borderColor: "rgba(255,255,255,0.1)",
    textStyle: { color: "#F8FAFC" },
  },
  legend: {
    bottom: "5%",
    textStyle: { color: "#94A3B8" },
  },
  series: [
    {
      type: "pie",
      radius: ["45%", "70%"],
      center: ["50%", "45%"],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 8, borderColor: "#1E293B", borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: "bold",
          color: "#F8FAFC",
        },
        itemStyle: { shadowBlur: 20, shadowColor: "rgba(0,0,0,0.5)" },
      },
      data: [
        {
          value: summary.value.pv_power || 0,
          name: "光伏",
          itemStyle: { color: "#00D4AA" },
        },
        {
          value: summary.value.wind_power || 0,
          name: "风电",
          itemStyle: { color: "#74B9FF" },
        },
        {
          value: Math.max(0, summary.value.grid_power || 0),
          name: "电网",
          itemStyle: { color: "#A29BFE" },
        },
      ],
    },
  ],
}));

const gaugeBaseOption = {
  series: [
    {
      type: "gauge",
      startAngle: 200,
      endAngle: -20,
      pointer: { show: false },
      progress: { show: true, width: 12, roundCap: true },
      axisLine: {
        lineStyle: { width: 12, color: [[1, "rgba(255,255,255,0.1)"]] },
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: { show: false },
    },
  ],
};

const pvGaugeOption = computed(() => ({
  ...gaugeBaseOption,
  series: [
    {
      ...gaugeBaseOption.series[0],
      min: 0,
      max: 500,
      data: [{ value: summary.value.pv_power || 0 }],
      progress: {
        ...gaugeBaseOption.series[0].progress,
        itemStyle: { color: "#00D4AA" },
      },
    },
  ],
}));

const windGaugeOption = computed(() => ({
  ...gaugeBaseOption,
  series: [
    {
      ...gaugeBaseOption.series[0],
      min: 0,
      max: 300,
      data: [{ value: summary.value.wind_power || 0 }],
      progress: {
        ...gaugeBaseOption.series[0].progress,
        itemStyle: { color: "#74B9FF" },
      },
    },
  ],
}));

const batteryGaugeOption = computed(() => ({
  ...gaugeBaseOption,
  series: [
    {
      ...gaugeBaseOption.series[0],
      min: 0,
      max: 100,
      data: [{ value: (summary.value.battery_soc || 0.5) * 100 }],
      progress: {
        ...gaugeBaseOption.series[0].progress,
        itemStyle: { color: "#FDCB6E" },
      },
    },
  ],
}));

onMounted(() => {
  fetchThresholds();
});
</script>

<style lang="scss" scoped>
.dashboard {
  animation: fadeIn 0.5s ease;
}

.stats-row {
  margin-bottom: 20px;

  .el-col {
    margin-bottom: 20px;
  }
}

.stat-card {
  position: relative;

  .stat-content {
    position: relative;
    z-index: 1;
  }

  .battery-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 0 0 16px 16px;
    overflow: hidden;

    .battery-level {
      height: 100%;
      background: linear-gradient(90deg, #fdcb6e, #00d4aa);
      transition: width 0.5s ease;
    }
  }
}

.chart-legend {
  display: flex;
  gap: 16px;

  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #94a3b8;

    i {
      width: 12px;
      height: 3px;
      border-radius: 2px;
    }

    &.generation i {
      background: #00d4aa;
    }
    &.load i {
      background: #fdcb6e;
    }
    &.grid i {
      background: #74b9ff;
    }
    &.battery i {
      background: #a29bfe;
      border-style: dashed;
    }
  }
}

.chart-container {
  position: relative;
}

.no-data-placeholder {
  height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #64748b;

  .el-icon {
    opacity: 0.5;
  }

  span {
    font-size: 14px;
    color: #94a3b8;
  }
}

.system-card {
  .system-gauge {
    position: relative;
    display: flex;
    justify-content: center;

    .gauge-info {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;

      .gauge-value {
        font-size: 28px;
        font-weight: 700;
        color: #f8fafc;
      }

      .gauge-unit {
        font-size: 12px;
        color: #64748b;
      }
    }
  }

  .system-stats {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);

    .stat-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      font-size: 13px;

      span:first-child {
        color: #64748b;
      }
      span:last-child {
        color: #f8fafc;
        font-weight: 500;
      }
    }
  }
}

.grid-status-card {
  .grid-metric {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);

    .metric-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;

      &.voltage {
        background: rgba(116, 185, 255, 0.15);
        color: #74b9ff;
      }
      &.frequency {
        background: rgba(253, 203, 110, 0.15);
        color: #fdcb6e;
      }
      &.renewable {
        background: rgba(0, 212, 170, 0.15);
        color: #00d4aa;
      }
      &.self {
        background: rgba(162, 155, 254, 0.15);
        color: #a29bfe;
      }
    }

    .metric-info {
      flex: 1;

      .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #f8fafc;
      }

      .metric-label {
        font-size: 12px;
        color: #64748b;
      }
    }

    .metric-status {
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;

      &.normal {
        background: rgba(0, 184, 148, 0.15);
        color: #00b894;
      }

      &.warning {
        background: rgba(255, 118, 117, 0.15);
        color: #ff7675;
      }
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
