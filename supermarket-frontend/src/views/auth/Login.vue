<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="login-title">超市管理系统</h1>
        <p class="login-subtitle">欢迎登录</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
        
        <div class="login-footer">
          <el-link type="primary" @click="$router.push('/register')">
            还没有账号？立即注册
          </el-link>
        </div>
      </el-form>
      
      <!-- 演示账号 -->
      <div class="demo-accounts">
        <h3>演示账号</h3>
        <div class="demo-account-list">
          <div class="demo-account" @click="fillDemoAccount('admin')">
            <strong>系统管理员</strong>
            <span>admin / admin123</span>
          </div>
          <div class="demo-account" @click="fillDemoAccount('manager')">
            <strong>门店经理</strong>
            <span>manager / manager123</span>
          </div>
          <div class="demo-account" @click="fillDemoAccount('cashier')">
            <strong>收银员</strong>
            <span>cashier / cashier123</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await authStore.login(loginForm)
        if (success) {
          router.push('/home')
        }
      } finally {
        loading.value = false
      }
    }
  })
}

const fillDemoAccount = (type: string) => {
  switch (type) {
    case 'admin':
      loginForm.username = 'admin'
      loginForm.password = 'admin123'
      break
    case 'manager':
      loginForm.username = 'manager'
      loginForm.password = 'manager123'
      break
    case 'cashier':
      loginForm.username = 'cashier'
      loginForm.password = 'cashier123'
      break
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.login-box {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  color: #1890ff;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
}

.login-footer {
  text-align: center;
}

.demo-accounts {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.demo-accounts h3 {
  font-size: 16px;
  color: #333;
  margin: 0 0 16px 0;
  text-align: center;
}

.demo-account-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.demo-account {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.demo-account:hover {
  background: #e3f2fd;
  transform: translateY(-1px);
}

.demo-account strong {
  color: #333;
  font-size: 14px;
}

.demo-account span {
  color: #666;
  font-size: 12px;
  font-family: monospace;
}

@media (max-width: 480px) {
  .login-box {
    padding: 24px;
    margin: 0 12px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .demo-account {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style> 