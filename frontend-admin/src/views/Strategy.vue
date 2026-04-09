<template>
  <div class="strategy-page">
    <el-row :gutter="24">
      <!-- 左侧：当前策略 + 策略列表 -->
      <el-col :xs="24" :lg="16">
        <!-- 当前策略卡片 -->
        <div class="card current-strategy-card" v-if="activeStrategy">
          <div class="strategy-header">
            <div class="strategy-info">
              <el-tag :type="getTypeColor(activeStrategy.strategy_type)" size="large" effect="dark">
                {{ getTypeText(activeStrategy.strategy_type) }}
              </el-tag>
              <span class="strategy-name">{{ activeStrategy.name }}</span>
              <el-tag type="success" size="small">运行中</el-tag>
            </div>
          </div>
          <div class="strategy-params">
            <div class="param-card" v-for="(value, key) in activeStrategy.parameters" :key="key">
              <div class="param-value">{{ formatParamValue(value) }}</div>
              <div class="param-label">{{ formatParamKey(key) }}</div>
            </div>
          </div>
        </div>

        <!-- 策略列表 -->
        <div class="card">
          <div class="card-header">
            <h3>控制策略</h3>
            <el-button type="primary" size="small" @click="openAddDialog">
              <el-icon><Plus /></el-icon> 新建策略
            </el-button>
          </div>
          
          <div class="enhanced-table scrollable">
            <el-table :data="strategies" stripe height="300">
              <el-table-column prop="name" label="策略名称" min-width="150" />
              <el-table-column prop="strategy_type" label="类型" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="getTypeColor(row.strategy_type)" size="small">
                    {{ getTypeText(row.strategy_type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_default" label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag 
                    :type="row.is_default ? 'success' : 'info'" 
                    size="small"
                    class="status-tag"
                  >
                    {{ row.is_default ? '运行中' : '未激活' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" align="center">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button 
                      v-if="row.is_default"
                      type="success" 
                      link 
                      size="small" 
                      disabled
                      class="action-btn"
                    >
                      当前
                    </el-button>
                    <el-button 
                      v-else
                      type="success" 
                      link 
                      size="small" 
                      class="action-btn"
                      @click="activateStrategy(row)"
                    >
                      激活
                    </el-button>
                    <el-button type="primary" link size="small" class="action-btn" @click="editStrategy(row)">编辑</el-button>
                    <el-button 
                      type="danger" 
                      link 
                      size="small" 
                      class="action-btn"
                      :disabled="row.is_default"
                      @click="deleteStrategy(row)"
                    >
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      
      <!-- 右侧：策略说明 -->
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>策略说明</h3>
          </div>
          <div class="strategy-desc-list">
            <div class="strategy-desc-item" v-for="item in strategyDescriptions" :key="item.type">
              <div class="desc-header">
                <el-tag :type="getTypeColor(item.type)" size="small">{{ item.name }}</el-tag>
              </div>
              <p class="desc-text">{{ item.description }}</p>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showAddDialog" :title="editingStrategy ? '编辑策略' : '新建策略'" width="500px">
      <el-form :model="strategyForm" label-width="80px" size="default">
        <el-form-item label="策略名称" required>
          <el-input v-model="strategyForm.name" placeholder="请输入策略名称" />
        </el-form-item>
        <el-form-item label="策略类型" required>
          <el-select v-model="strategyForm.strategy_type" style="width: 100%" @change="onTypeChange">
            <el-option label="经济优先" value="economic" />
            <el-option label="绿色优先" value="green" />
            <el-option label="稳定优先" value="stability" />
          </el-select>
        </el-form-item>
        
        <el-divider content-position="left">策略参数</el-divider>
        
        <template v-if="strategyForm.strategy_type === 'economic'">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="峰时电价">
                <el-input-number v-model="strategyForm.parameters.peak_price" :precision="2" :step="0.1" :min="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="谷时电价">
                <el-input-number v-model="strategyForm.parameters.valley_price" :precision="2" :step="0.1" :min="0" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="储能阈值">
            <div class="slider-row">
              <el-slider v-model="strategyForm.parameters.battery_threshold" :min="0" :max="100" style="flex: 1" />
              <span class="slider-value">{{ strategyForm.parameters.battery_threshold }}%</span>
            </div>
          </el-form-item>
        </template>
        
        <template v-if="strategyForm.strategy_type === 'green'">
          <el-form-item label="购电限制">
            <div class="slider-row">
              <el-slider v-model="strategyForm.parameters.grid_import_limit" :min="0" :max="100" style="flex: 1" />
              <span class="slider-value">{{ strategyForm.parameters.grid_import_limit }}%</span>
            </div>
          </el-form-item>
          <el-form-item label="储能备用">
            <div class="slider-row">
              <el-slider v-model="strategyForm.parameters.battery_reserve" :min="0" :max="50" style="flex: 1" />
              <span class="slider-value">{{ strategyForm.parameters.battery_reserve }}%</span>
            </div>
          </el-form-item>
          <el-form-item label="可再生优先">
            <el-switch v-model="strategyForm.parameters.renewable_priority" />
          </el-form-item>
        </template>
        
        <template v-if="strategyForm.strategy_type === 'stability'">
          <el-form-item label="电压容差">
            <div class="slider-row">
              <el-slider v-model="strategyForm.parameters.voltage_tolerance" :min="1" :max="10" style="flex: 1" />
              <span class="slider-value">{{ strategyForm.parameters.voltage_tolerance }}%</span>
            </div>
          </el-form-item>
          <el-form-item label="储能备用">
            <div class="slider-row">
              <el-slider v-model="strategyForm.parameters.battery_reserve" :min="0" :max="50" style="flex: 1" />
              <span class="slider-value">{{ strategyForm.parameters.battery_reserve }}%</span>
            </div>
          </el-form-item>
          <el-form-item label="负载切除">
            <el-switch v-model="strategyForm.parameters.load_shedding_enabled" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveStrategy">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const strategies = ref([])
const showAddDialog = ref(false)
const editingStrategy = ref(null)

const defaultParams = {
  economic: {
    peak_price: 1.2,
    valley_price: 0.4,
    battery_threshold: 30
  },
  green: {
    grid_import_limit: 20,
    battery_reserve: 20,
    renewable_priority: true
  },
  stability: {
    voltage_tolerance: 5,
    battery_reserve: 30,
    load_shedding_enabled: true
  }
}

const strategyForm = ref({
  name: '',
  strategy_type: 'economic',
  parameters: { ...defaultParams.economic }
})

const strategyDescriptions = [
  {
    type: 'economic',
    name: '经济优先',
    description: '根据电价时段优化储能充放电，在谷电时段充电，峰电时段放电，最大化经济效益。适合电价差异较大的场景。'
  },
  {
    type: 'green',
    name: '绿色优先',
    description: '最大化可再生能源利用率，限制电网购电比例，优先使用光伏和风电。适合追求碳中和目标的场景。'
  },
  {
    type: 'stability',
    name: '稳定优先',
    description: '优先保证电压和频率稳定，保持储能备用容量，必要时启用负载切除。适合对供电可靠性要求高的场景。'
  }
]

const activeStrategy = computed(() => strategies.value.find(s => s.is_default))

const typeMap = {
  economic: { text: '经济优先', color: 'success' },
  green: { text: '绿色优先', color: '' },
  stability: { text: '稳定优先', color: 'warning' }
}

function getTypeText(type) {
  return typeMap[type]?.text || type
}

function getTypeColor(type) {
  return typeMap[type]?.color || ''
}

function formatParamKey(key) {
  const keyMap = {
    peak_price: '峰时电价',
    valley_price: '谷时电价',
    flat_price: '平时电价',
    battery_threshold: '储能阈值',
    grid_import_limit: '购电限制',
    battery_reserve: '储能备用',
    voltage_tolerance: '电压容差',
    load_shedding_enabled: '负载切除',
    renewable_priority: '可再生优先',
    peak_hours: '峰时时段',
    valley_hours: '谷时时段'
  }
  return keyMap[key] || key
}

function formatParamValue(value) {
  if (typeof value === 'boolean') return value ? '启用' : '禁用'
  if (Array.isArray(value)) {
    // 格式化时段数组，如 [10,11,12] -> "10-12"
    if (value.length === 0) return '-'
    const sorted = [...value].sort((a, b) => a - b)
    const ranges = []
    let start = sorted[0]
    let end = sorted[0]
    for (let i = 1; i <= sorted.length; i++) {
      if (sorted[i] === end + 1) {
        end = sorted[i]
      } else {
        ranges.push(start === end ? `${start}` : `${start}-${end}`)
        start = sorted[i]
        end = sorted[i]
      }
    }
    return ranges.join(',') + '时'
  }
  if (typeof value === 'number') {
    if (value < 10) return value.toFixed(1)
    return value
  }
  return value
}

function onTypeChange(type) {
  strategyForm.value.parameters = { ...defaultParams[type] }
}

function openAddDialog() {
  editingStrategy.value = null
  strategyForm.value = {
    name: '',
    strategy_type: 'economic',
    parameters: { ...defaultParams.economic }
  }
  showAddDialog.value = true
}

async function fetchStrategies() {
  try {
    const response = await api.get('/api/strategies')
    if (response.data.success) {
      strategies.value = response.data.data
    }
  } catch (e) {
    console.error('Failed to fetch strategies:', e)
  }
}

function editStrategy(strategy) {
  editingStrategy.value = strategy
  strategyForm.value = {
    name: strategy.name,
    strategy_type: strategy.strategy_type,
    parameters: { ...strategy.parameters }
  }
  showAddDialog.value = true
}

async function saveStrategy() {
  if (!strategyForm.value.name) {
    ElMessage.warning('请输入策略名称')
    return
  }
  try {
    if (editingStrategy.value) {
      await api.put(`/api/strategies/${editingStrategy.value.id}`, strategyForm.value)
    } else {
      await api.post('/api/strategies', strategyForm.value)
    }
    ElMessage.success('保存成功')
    showAddDialog.value = false
    editingStrategy.value = null
    fetchStrategies()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function activateStrategy(strategy) {
  try {
    await api.post(`/api/strategies/${strategy.id}/activate`)
    ElMessage.success(`策略 "${strategy.name}" 已激活`)
    fetchStrategies()
  } catch (e) {
    ElMessage.error('激活失败')
  }
}

async function deleteStrategy(strategy) {
  try {
    await ElMessageBox.confirm('确定要删除该策略吗？', '提示', { type: 'warning' })
    await api.delete(`/api/strategies/${strategy.id}`)
    ElMessage.success('删除成功')
    fetchStrategies()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchStrategies()
})
</script>

<style lang="scss" scoped>
$success: #10B981;
$warning: #E6A23C;
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;
$border-color: rgba(255, 255, 255, 0.1);
$bg-card: #1E293B;

.slider-row {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  
  .slider-value {
    min-width: 50px;
    text-align: right;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    font-size: 14px;
    color: $text-primary;
  }
}

.current-strategy-card {
  margin-bottom: 24px;
  min-height: 160px;
  
  .strategy-header {
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color;
    margin-bottom: 16px;
    
    .strategy-info {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .strategy-name {
        font-size: 20px;
        font-weight: 600;
        color: $text-primary;
      }
    }
  }
  
  .strategy-params {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    
    .param-card {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 14px 16px;
      text-align: center;
      min-width: 80px;
      
      .param-value {
        font-size: 18px;
        font-weight: 700;
        color: $text-primary;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        margin-bottom: 6px;
      }
      
      .param-label {
        font-size: 12px;
        color: $text-secondary;
      }
    }
  }
}

.strategy-desc-list {
  .strategy-desc-item {
    padding: 16px 0;
    border-bottom: 1px solid $border-color;
    
    &:last-child {
      border-bottom: none;
    }
    
    .desc-header {
      margin-bottom: 8px;
    }
    
    .desc-text {
      font-size: 13px;
      color: $text-secondary;
      line-height: 1.6;
      margin: 0;
    }
  }
}

.unit {
  margin-left: 8px;
  color: $text-secondary;
  font-size: 14px;
}

// 固定表格行高，防止切换时跳动
:deep(.el-table) {
  .el-table__row {
    height: 60px;
    
    td {
      padding: 8px 0;
    }
  }
}

// 状态标签禁用动画，防止切换时文字重叠
.status-tag {
  transition: none !important;
  min-width: 56px;
  text-align: center;
}

// 操作按钮固定宽度，防止文字跳动
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: nowrap;
  
  .action-btn {
    min-width: 40px;
    text-align: center;
  }
}
</style>
