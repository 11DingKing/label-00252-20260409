<template>
  <div class="layout-container">
    <aside class="layout-aside" :class="{ collapsed: isCollapsed }">
      <div class="logo">
        <el-icon :size="28"><Cpu /></el-icon>
        <span v-show="!isCollapsed">微网控制系统</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapsed"
        background-color="#1F2D3D"
        text-color="#BFCBD9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>系统概览</span>
        </el-menu-item>
        <el-menu-item index="/topology">
          <el-icon><Share /></el-icon>
          <span>系统拓扑</span>
        </el-menu-item>
        <el-sub-menu index="energy">
          <template #title>
            <el-icon><Lightning /></el-icon>
            <span>能源系统</span>
          </template>
          <el-menu-item index="/pv">光伏系统</el-menu-item>
          <el-menu-item index="/wind">风力发电</el-menu-item>
          <el-menu-item index="/battery">储能系统</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/load">
          <el-icon><OfficeBuilding /></el-icon>
          <span>负载管理</span>
        </el-menu-item>
        <el-menu-item index="/grid">
          <el-icon><Connection /></el-icon>
          <span>电网管理</span>
        </el-menu-item>
        <el-menu-item index="/strategy">
          <el-icon><Setting /></el-icon>
          <span>控制策略</span>
        </el-menu-item>
        <el-menu-item index="/alarm">
          <el-icon><Bell /></el-icon>
          <span>告警管理</span>
        </el-menu-item>
        <el-menu-item index="/analytics">
          <el-icon><TrendCharts /></el-icon>
          <span>数据分析</span>
        </el-menu-item>
        <el-sub-menu index="system" v-if="userStore.isAdmin">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/users">用户管理</el-menu-item>
          <el-menu-item index="/logs">操作日志</el-menu-item>
          <el-menu-item index="/settings">系统设置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </aside>
    
    <main class="layout-main">
      <header class="layout-header">
        <div class="header-left">
          <el-button :icon="isCollapsed ? 'Expand' : 'Fold'" text @click="toggleCollapse" />
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag :type="realtimeStore.connected ? 'success' : 'danger'" size="small">
            {{ realtimeStore.connected ? '已连接' : '未连接' }}
          </el-tag>
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :icon="UserFilled" />
              <span>{{ userStore.user?.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <div class="layout-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useRealtimeStore } from '@/stores/realtime'
import { useWebSocket } from '@/composables/useWebSocket'
import api from '@/api'

const router = useRouter()
const userStore = useUserStore()
const realtimeStore = useRealtimeStore()
const { connect } = useWebSocket()

const isCollapsed = ref(false)

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  }
}

onMounted(() => {
  // WebSocket connection handled by useWebSocket
})
</script>

<style lang="scss" scoped>
$primary-color: #00D4AA;
$bg-dark-1: #0A0E17;
$bg-dark-2: #111827;
$border-color: rgba(255, 255, 255, 0.1);
$text-primary: #F8FAFC;
$text-secondary: #94A3B8;

.layout-container {
  height: 100vh;
  display: flex;
  background: $bg-dark-1;
}

.layout-aside {
  width: 260px;
  background: linear-gradient(180deg, $bg-dark-2 0%, $bg-dark-1 100%);
  border-right: 1px solid $border-color;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  
  &.collapsed {
    width: 72px;
    
    .logo span { display: none; }
  }
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid $border-color;
  
  :deep(.el-icon) {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, $primary-color, #6C5CE7);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: 0 0 20px rgba(0, 212, 170, 0.3);
  }
  
  span {
    font-size: 16px;
    font-weight: 700;
    background: linear-gradient(90deg, $text-primary, $primary-color);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 0.5px;
  }
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: $bg-dark-1;
}

.layout-header {
  height: 64px;
  background: rgba($bg-dark-2, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid $border-color;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  
  :deep(.el-button) {
    color: $text-secondary;
    
    &:hover {
      color: $primary-color;
    }
  }
  
  :deep(.el-breadcrumb) {
    .el-breadcrumb__item {
      .el-breadcrumb__inner {
        color: $text-secondary;
        
        &:hover {
          color: $primary-color;
        }
      }
      
      .el-breadcrumb__separator {
        color: rgba(255, 255, 255, 0.3);
      }
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  
  :deep(.el-button) {
    color: $text-secondary;
    
    &:hover {
      color: $primary-color;
    }
  }
  
  :deep(.el-tag) {
    border: none;
    font-weight: 500;
    
    &.el-tag--success {
      background: rgba(0, 184, 148, 0.15);
      color: #00B894;
    }
    
    &.el-tag--danger {
      background: rgba(255, 118, 117, 0.15);
      color: #FF7675;
    }
  }
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  
  :deep(.el-avatar) {
    background: linear-gradient(135deg, $primary-color, #6C5CE7);
  }
  
  span {
    color: $text-secondary;
    font-size: 14px;
  }
}

.layout-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: linear-gradient(135deg, $bg-dark-1 0%, rgba($bg-dark-2, 0.5) 100%);
}

:deep(.el-menu) {
  background: transparent !important;
  border-right: none !important;
  padding: 8px;
  
  .el-menu-item,
  .el-sub-menu__title {
    height: 48px;
    line-height: 48px;
    margin: 4px 0;
    border-radius: 12px;
    color: $text-secondary !important;
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba($primary-color, 0.1) !important;
      color: $primary-color !important;
    }
    
    .el-icon {
      font-size: 20px;
      margin-right: 12px;
    }
  }
  
  .el-menu-item.is-active {
    background: linear-gradient(90deg, rgba($primary-color, 0.2), transparent) !important;
    color: $primary-color !important;
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 24px;
      background: $primary-color;
      border-radius: 0 2px 2px 0;
      box-shadow: 0 0 20px rgba(0, 212, 170, 0.3);
    }
  }
  
  .el-sub-menu {
    .el-menu-item {
      padding-left: 56px !important;
      height: 44px;
      line-height: 44px;
    }
  }
}

@media (max-width: 768px) {
  .layout-aside {
    position: fixed;
    z-index: 1000;
    height: 100%;
    transform: translateX(-100%);
    
    &.show {
      transform: translateX(0);
    }
  }
  
  .layout-content {
    padding: 16px;
  }
}
</style>
