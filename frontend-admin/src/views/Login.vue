<template>
  <div class="login-page">
    <!-- 背景动画 -->
    <div class="bg-animation">
      <div class="grid-lines"></div>
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>
    
    <div class="login-container">
      <!-- 左侧品牌区 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo-wrapper">
            <div class="logo-icon">
              <el-icon :size="48"><Cpu /></el-icon>
            </div>
            <div class="logo-glow"></div>
          </div>
          <h1>微网控制系统</h1>
          <p class="subtitle">Industrial Park Microgrid Control System</p>
          
          <div class="features">
            <div class="feature-item">
              <el-icon><Sunny /></el-icon>
              <span>光伏发电监控</span>
            </div>
            <div class="feature-item">
              <el-icon><Coin /></el-icon>
              <span>储能系统管理</span>
            </div>
            <div class="feature-item">
              <el-icon><Connection /></el-icon>
              <span>智能电网调度</span>
            </div>
            <div class="feature-item">
              <el-icon><DataAnalysis /></el-icon>
              <span>实时数据分析</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-wrapper">
          <div class="form-header">
            <h2>欢迎回来</h2>
            <p>请登录您的账户以继续</p>
          </div>
          
          <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleLogin"
                class="login-btn"
              >
                <span v-if="!loading">登 录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="form-footer">
            <div class="divider">
              <span>测试账号</span>
            </div>
            <div class="test-accounts">
              <div class="account-item" @click="fillAccount('admin', 'admin123')">
                <el-icon><UserFilled /></el-icon>
                <span>管理员: admin / admin123</span>
              </div>
              <div class="account-item" @click="fillAccount('operator', 'operator123')">
                <el-icon><User /></el-icon>
                <span>操作员: operator / operator123</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function fillAccount(username, password) {
  form.username = username
  form.password = password
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    const result = await userStore.login(form.username, form.password)
    if (result.success) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(result.message || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0A0E17 0%, #111827 50%, #0A0E17 100%);
  position: relative;
  overflow: hidden;
}

.bg-animation {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  
  .grid-lines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(rgba(0, 212, 170, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 212, 170, 0.03) 1px, transparent 1px);
    background-size: 60px 60px;
  }
  
  .glow-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.4;
    animation: float 8s ease-in-out infinite;
    
    &.orb-1 {
      width: 400px;
      height: 400px;
      background: radial-gradient(circle, rgba(0, 212, 170, 0.3), transparent);
      top: -100px;
      left: -100px;
      animation-delay: 0s;
    }
    
    &.orb-2 {
      width: 300px;
      height: 300px;
      background: radial-gradient(circle, rgba(108, 92, 231, 0.3), transparent);
      bottom: -50px;
      right: -50px;
      animation-delay: -3s;
    }
    
    &.orb-3 {
      width: 200px;
      height: 200px;
      background: radial-gradient(circle, rgba(116, 185, 255, 0.2), transparent);
      top: 50%;
      left: 50%;
      animation-delay: -5s;
    }
  }
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.login-container {
  display: flex;
  width: 900px;
  max-width: 95vw;
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.brand-section {
  flex: 1;
  padding: 48px;
  background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(108, 92, 231, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  
  @media (max-width: 768px) {
    display: none;
  }
}

.brand-content {
  text-align: center;
  
  .logo-wrapper {
    position: relative;
    display: inline-block;
    margin-bottom: 24px;
    
    .logo-icon {
      width: 80px;
      height: 80px;
      background: linear-gradient(135deg, #00D4AA, #6C5CE7);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      box-shadow: 0 0 40px rgba(0, 212, 170, 0.4);
    }
    
    .logo-glow {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 120px;
      height: 120px;
      background: radial-gradient(circle, rgba(0, 212, 170, 0.3), transparent);
      border-radius: 50%;
      animation: pulse 3s ease-in-out infinite;
    }
  }
  
  h1 {
    font-size: 28px;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 8px;
    background: linear-gradient(90deg, #F8FAFC, #00D4AA);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .subtitle {
    font-size: 13px;
    color: #94A3B8;
    letter-spacing: 1px;
    margin-bottom: 40px;
  }
  
  .features {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    text-align: left;
    
    .feature-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      transition: all 0.3s ease;
      
      &:hover {
        background: rgba(0, 212, 170, 0.1);
        border-color: rgba(0, 212, 170, 0.2);
        transform: translateX(4px);
      }
      
      .el-icon {
        font-size: 20px;
        color: #00D4AA;
      }
      
      span {
        font-size: 13px;
        color: #94A3B8;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.8; transform: translate(-50%, -50%) scale(1.1); }
}

.form-section {
  flex: 1;
  padding: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-wrapper {
  width: 100%;
  max-width: 360px;
  
  .form-header {
    margin-bottom: 32px;
    
    h2 {
      font-size: 24px;
      font-weight: 700;
      color: #F8FAFC;
      margin-bottom: 8px;
    }
    
    p {
      font-size: 14px;
      color: #64748B;
    }
  }
  
  :deep(.el-form-item) {
    margin-bottom: 20px;
  }
  
  :deep(.el-input__wrapper) {
    background: rgba(31, 41, 55, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 4px 16px;
    box-shadow: none !important;
    transition: all 0.3s ease;
    
    &:hover, &.is-focus {
      border-color: #00D4AA !important;
      box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1) !important;
    }
    
    .el-input__inner {
      color: #F8FAFC !important;
      font-size: 15px;
      
      &::placeholder {
        color: #64748B !important;
      }
    }
    
    .el-input__prefix {
      color: #64748B;
    }
  }
  
  .login-btn {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 12px;
    background: linear-gradient(135deg, #00D4AA, #00B894);
    border: none;
    transition: all 0.3s ease;
    
    &:hover {
      background: linear-gradient(135deg, #33DDBB, #00D4AA);
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 212, 170, 0.4);
    }
    
    &:active {
      transform: translateY(0);
    }
  }
  
  .form-footer {
    margin-top: 32px;
    
    .divider {
      display: flex;
      align-items: center;
      margin-bottom: 20px;
      
      &::before, &::after {
        content: '';
        flex: 1;
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
      }
      
      span {
        padding: 0 16px;
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 1px;
      }
    }
    
    .test-accounts {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .account-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(0, 212, 170, 0.1);
          border-color: rgba(0, 212, 170, 0.2);
        }
        
        .el-icon {
          font-size: 18px;
          color: #00D4AA;
        }
        
        span {
          font-size: 13px;
          color: #94A3B8;
        }
      }
    }
  }
}
</style>
