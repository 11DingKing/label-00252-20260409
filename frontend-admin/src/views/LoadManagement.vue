<template>
  <div class="load-management">
    <el-row :gutter="24">
      <el-col :xs="24" :lg="16">
        <div class="card">
          <div class="card-header">
            <h3>负载列表</h3>
            <el-button type="primary" size="small" @click="openAddDialog">
              <el-icon><Plus /></el-icon> 添加负载
            </el-button>
          </div>
          
          <div class="enhanced-table scrollable">
            <el-table :data="loadList" stripe height="400">
              <el-table-column prop="name" label="名称" min-width="120" />
              <el-table-column prop="load_type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag size="small">{{ getLoadTypeText(row.load_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="power" label="当前功率" width="120" align="right">
                <template #default="{ row }">
                  <span class="numeric-value">{{ row.power?.toFixed(1) || 0 }}</span>
                  <span class="unit">kW</span>
                </template>
              </el-table-column>
              <el-table-column prop="rated_power" label="额定功率" width="120" align="right">
                <template #default="{ row }">
                  <span class="numeric-value">{{ row.rated_power }}</span>
                  <span class="unit">kW</span>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="160">
                <template #default="{ row }">
                  <el-rate v-model="row.priority" disabled :max="5" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" align="center">
                <template #default="{ row }">
                  <div style="display: flex; justify-content: center; gap: 8px;">
                    <el-button type="primary" link size="small" @click="editLoad(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deleteLoad(row)">删除</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>负载功率趋势</h3>
          </div>
          <v-chart :option="chartOption" style="height: 300px" autoresize />
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>负载统计</h3>
          </div>
          <div class="params-list">
            <div class="param-item">
              <span class="param-label">总负载</span>
              <span class="param-value">{{ totalLoad.toFixed(1) }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">额定总功率</span>
              <span class="param-value">{{ totalRated }} <small>kW</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">负载率</span>
              <span class="param-value highlight">{{ loadFactor.toFixed(1) }} <small>%</small></span>
            </div>
            <div class="param-item">
              <span class="param-label">在线负载</span>
              <span class="param-value">{{ onlineCount }} / {{ loadList.length }}</span>
            </div>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>负载分布</h3>
          </div>
          <v-chart :option="pieOption" style="height: 250px" autoresize />
        </div>
        
        <div class="card">
          <div class="card-header">
            <h3>负载管理策略</h3>
          </div>
          <el-form label-width="80px" size="small">
            <el-form-item label="切负载">
              <el-switch v-model="loadShedding" />
              <span style="margin-left: 8px; color: #909399">自动切除低优先级负载</span>
            </el-form-item>
            <el-form-item label="功率限制">
              <el-input-number v-model="powerLimit" :min="0" :max="2000" />
              <span style="margin-left: 8px">kW</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveLoadStrategy">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showAddDialog" :title="editingLoad ? '编辑负载' : '添加负载'" width="500px">
      <el-form :model="loadForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="loadForm.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="loadForm.load_type" style="width: 100%">
            <el-option label="办公负载" value="office" />
            <el-option label="生产负载" value="production" />
            <el-option label="照明负载" value="lighting" />
            <el-option label="空调系统" value="hvac" />
            <el-option label="充电桩" value="ev_charger" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="额定功率" required>
          <el-input-number v-model="loadForm.rated_power" :min="0" :max="1000" />
          <span style="margin-left: 8px">kW</span>
        </el-form-item>
        <el-form-item label="优先级">
          <el-rate v-model="loadForm.priority" :max="5" />
          <span style="margin-left: 8px; color: #909399">1最高，5最低</span>
        </el-form-item>
        <el-form-item label="可控制">
          <el-switch v-model="loadForm.is_controllable" />
          <span style="margin-left: 8px; color: #909399">允许远程开关控制</span>
        </el-form-item>
        <el-form-item label="默认开启">
          <el-switch v-model="loadForm.is_active" />
          <span style="margin-left: 8px; color: #909399">负载初始状态</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveLoad">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRealtimeStore } from '@/stores/realtime'
import api from '@/api'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const realtimeStore = useRealtimeStore()
const history = computed(() => realtimeStore.history)

const loadList = ref([])
const showAddDialog = ref(false)
const editingLoad = ref(null)
const loadShedding = ref(true)
const powerLimit = ref(1200)

const loadForm = ref({
  name: '',
  load_type: 'office',
  rated_power: 100,
  priority: 3,
  is_controllable: true,
  is_active: true
})

const loadTypeMap = {
  office: '办公负载',
  production: '生产负载',
  lighting: '照明负载',
  hvac: '空调系统',
  ev_charger: '充电桩',
  other: '其他'
}

function getLoadTypeText(type) {
  return loadTypeMap[type] || type
}

const totalLoad = computed(() => loadList.value.reduce((sum, l) => sum + (l.is_on ? (l.power || 0) : 0), 0))
const totalRated = computed(() => loadList.value.reduce((sum, l) => sum + (l.rated_power || 0), 0))
const loadFactor = computed(() => totalRated.value > 0 ? (totalLoad.value / totalRated.value) * 100 : 0)
const onlineCount = computed(() => loadList.value.filter(l => l.is_on).length)

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
    name: '总负载',
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.3 },
    data: history.value.map(h => h.total_load || 0),
    itemStyle: { color: '#E6A23C' }
  }]
}))

const pieOption = computed(() => {
  const typeData = {}
  loadList.value.forEach(l => {
    if (l.is_on) {
      const type = getLoadTypeText(l.load_type)
      typeData[type] = (typeData[type] || 0) + (l.power || 0)
    }
  })
  
  return {
    tooltip: { 
      trigger: 'item',
      formatter: '{b}: {c} kW ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: {
        color: '#F8FAFC',
        fontSize: 13
      }
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['35%', '50%'],
      label: {
        show: false
      },
      labelLine: {
        show: false
      },
      data: Object.entries(typeData).map(([name, value]) => ({ name, value: value.toFixed(1) }))
    }]
  }
})

async function fetchLoadData() {
  try {
    // Fetch all loads (including inactive ones)
    const loadsResponse = await api.get('/api/loads')
    if (!loadsResponse.data.success) return
    
    const allLoads = loadsResponse.data.data
    
    // Fetch realtime data for active loads
    const realtimeResponse = await api.get('/api/loads/realtime')
    const realtimeMap = {}
    if (realtimeResponse.data.success) {
      realtimeResponse.data.data.forEach(item => {
        realtimeMap[item.load_id] = item
      })
    }
    
    // Merge data: use realtime data if available, otherwise use base load data
    loadList.value = allLoads.map(load => {
      const realtime = realtimeMap[load.id]
      if (realtime) {
        return realtime
      }
      // For inactive loads, return basic info with zero power
      return {
        load_id: load.id,
        name: load.name,
        load_type: load.load_type,
        power: 0,
        voltage: 380,
        current: 0,
        power_factor: 0.95,
        rated_power: load.rated_power,
        priority: load.priority,
        is_on: false,
        is_controllable: load.is_controllable,
        is_active: load.is_active,
        utilization: 0
      }
    })
  } catch (e) {
    console.error('Failed to fetch load data:', e)
  }
}

async function fetchLoadStrategy() {
  try {
    const response = await api.get('/api/loads/strategy')
    if (response.data.success) {
      const data = response.data.data
      loadShedding.value = data.load_shedding ?? true
      powerLimit.value = data.power_limit ?? 1200
    }
  } catch (e) {
    console.error('Failed to fetch load strategy:', e)
  }
}

async function saveLoadStrategy() {
  try {
    await api.post('/api/loads/strategy', {
      load_shedding: loadShedding.value,
      power_limit: powerLimit.value
    })
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function toggleLoad(load) {
  try {
    await api.post(`/api/loads/${load.load_id}/control`, { is_on: load.is_on })
    ElMessage.success(load.is_on ? '负载已开启' : '负载已关闭')
  } catch (e) {
    load.is_on = !load.is_on
    ElMessage.error('操作失败')
  }
}

function editLoad(load) {
  editingLoad.value = load
  loadForm.value = {
    name: load.name,
    load_type: load.load_type,
    rated_power: load.rated_power,
    priority: load.priority,
    is_controllable: Boolean(load.is_controllable),
    is_active: Boolean(load.is_active)
  }
  showAddDialog.value = true
}

function openAddDialog() {
  editingLoad.value = null
  loadForm.value = {
    name: '',
    load_type: 'office',
    rated_power: 100,
    priority: 3,
    is_controllable: true,
    is_active: true
  }
  showAddDialog.value = true
}

async function saveLoad() {
  try {
    if (editingLoad.value) {
      await api.put(`/api/loads/${editingLoad.value.load_id}`, loadForm.value)
    } else {
      await api.post('/api/loads', loadForm.value)
    }
    ElMessage.success('保存成功')
    showAddDialog.value = false
    editingLoad.value = null
    loadForm.value = {
      name: '',
      load_type: 'office',
      rated_power: 100,
      priority: 3,
      is_controllable: true,
      is_active: true
    }
    fetchLoadData()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function deleteLoad(load) {
  try {
    await ElMessageBox.confirm('确定要删除该负载吗？', '提示', { type: 'warning' })
    await api.delete(`/api/loads/${load.load_id}`)
    ElMessage.success('删除成功')
    fetchLoadData()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchLoadData()
  fetchLoadStrategy()
  setInterval(fetchLoadData, 5000)
})
</script>


<style lang="scss" scoped>
$warning: #E6A23C;
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);

.load-management {
  .numeric-value {
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: #F8FAFC;
  }
  
  .unit {
    font-size: 12px;
    color: #64748B;
    margin-left: 4px;
  }
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
