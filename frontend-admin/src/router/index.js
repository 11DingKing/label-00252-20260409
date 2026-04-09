import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '系统概览' }
      },
      {
        path: 'topology',
        name: 'Topology',
        component: () => import('@/views/Topology.vue'),
        meta: { title: '系统拓扑' }
      },
      {
        path: 'pv',
        name: 'PVSystem',
        component: () => import('@/views/PVSystem.vue'),
        meta: { title: '光伏系统' }
      },
      {
        path: 'wind',
        name: 'WindSystem',
        component: () => import('@/views/WindSystem.vue'),
        meta: { title: '风力发电' }
      },
      {
        path: 'battery',
        name: 'BatterySystem',
        component: () => import('@/views/BatterySystem.vue'),
        meta: { title: '储能系统' }
      },
      {
        path: 'load',
        name: 'LoadManagement',
        component: () => import('@/views/LoadManagement.vue'),
        meta: { title: '负载管理' }
      },
      {
        path: 'grid',
        name: 'GridManagement',
        component: () => import('@/views/GridManagement.vue'),
        meta: { title: '电网管理' }
      },
      {
        path: 'strategy',
        name: 'Strategy',
        component: () => import('@/views/Strategy.vue'),
        meta: { title: '控制策略' }
      },
      {
        path: 'alarm',
        name: 'Alarm',
        component: () => import('@/views/Alarm.vue'),
        meta: { title: '告警管理' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { title: '数据分析' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '操作日志', requiresAdmin: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth !== false && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router
