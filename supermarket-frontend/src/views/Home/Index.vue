<template>
  <div class="home-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">欢迎使用超市管理系统</h1>
        <p class="welcome-subtitle">高效管理您的超市业务，让经营更简单</p>
        <div class="user-info">
          <span class="user-greeting">您好，{{ authStore.user?.username }}！</span>
          <span class="role-badge" :class="roleClass">{{ roleText }}</span>
        </div>
      </div>
      <div class="welcome-image">
        <div class="image-placeholder">
          <div class="store-icon">🏪</div>
        </div>
      </div>
    </div>

    <!-- 快速操作区域 -->
    <div class="quick-actions">
      <h2 class="section-title">快速操作</h2>
      <div class="action-grid">
        <div 
          v-for="action in availableActions" 
          :key="action.name"
          class="action-card"
          @click="navigateTo(action.path)"
        >
          <div class="action-icon" :style="{ backgroundColor: action.color }">
            {{ action.icon }}
          </div>
          <h3 class="action-title">{{ action.name }}</h3>
          <p class="action-description">{{ action.description }}</p>
        </div>
      </div>
    </div>

    <!-- 销售趋势图 -->
    <div class="sales-trend-section" v-if="showSalesChart">
      <h2 class="section-title">销售趋势</h2>
      <SalesChart />
    </div>

    <!-- 系统信息区域 -->
    <div class="system-info">
      <h2 class="section-title">系统信息</h2>
      <div class="info-grid">
        <div class="info-card">
          <h4>当前时间</h4>
          <p>{{ currentTime }}</p>
        </div>
        <div class="info-card">
          <h4>您的角色</h4>
          <p>{{ roleText }}</p>
        </div>
        <div class="info-card">
          <h4>系统版本</h4>
          <p>v1.0.0</p>
        </div>
        <div class="info-card">
          <h4>在线状态</h4>
          <p class="status-online">● 正常运行</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import SalesChart from '@/components/SalesChart.vue'

const router = useRouter()
const authStore = useAuthStore()

const currentTime = ref('')

// 控制销售图表显示 - 有销售管理权限的用户可以看到
const showSalesChart = computed(() => {
  return authStore.hasPermission('sales_management', 'view')
})

// 角色映射
const roleText = computed(() => {
  const roleMap = {
    'system_admin': '系统管理员',
    'store_manager': '门店经理', 
    'cashier': '收银员',
    'admin': '系统管理员',
    'manager': '门店经理'
  }
  return roleMap[authStore.user?.role] || '未知角色'
})

const roleClass = computed(() => {
  const roleClassMap = {
    'system_admin': 'role-admin',
    'store_manager': 'role-manager',
    'cashier': 'role-cashier',
    'admin': 'role-admin',
    'manager': 'role-manager'
  }
  return roleClassMap[authStore.user?.role] || 'role-default'
})

// 根据用户权限显示不同的快速操作
const availableActions = computed(() => {
  const allActions = [
    {
      name: '门店管理',
      description: '管理门店信息和设置',
      icon: '🏪',
      color: '#1890ff',
      path: '/stores',
      featureCode: 'store_management'
    },
    {
      name: '用户管理',
      description: '管理系统用户和权限',
      icon: '👥',
      color: '#52c41a',
      path: '/users',
      featureCode: 'user_management'
    },
    {
      name: '商品分类',
      description: '管理商品分类信息',
      icon: '📂',
      color: '#faad14',
      path: '/categories',
      featureCode: 'category_management'
    },
    {
      name: '供应商管理',
      description: '管理供应商信息',
      icon: '🏭',
      color: '#722ed1',
      path: '/suppliers',
      featureCode: 'supplier_management'
    },
    {
      name: '商品管理',
      description: '管理商品信息和规格',
      icon: '📦',
      color: '#eb2f96',
      path: '/products',
      featureCode: 'product_management'
    },
    {
      name: '库存管理',
      description: '查看和管理商品库存',
      icon: '📊',
      color: '#13c2c2',
      path: '/inventory',
      featureCode: 'inventory_management'
    },
    {
      name: '促销管理',
      description: '设置和管理促销活动',
      icon: '🎁',
      color: '#f5222d',
      path: '/promotions',
      featureCode: 'promotion_management'
    },
    {
      name: '销售管理',
      description: '查看销售记录和统计',
      icon: '💰',
      color: '#fa8c16',
      path: '/sales',
      featureCode: 'sales_management'
    },
    {
      name: '收银台',
      description: '进行商品销售操作',
      icon: '💳',
      color: '#2f54eb',
      path: '/pos',
      featureCode: 'pos_system'
    },
    {
      name: '权限管理',
      description: '管理角色和权限配置',
      icon: '🔐',
      color: '#fa541c',
      path: '/permissions',
      featureCode: 'permission_management'
    }
  ]

  // 使用动态权限过滤可用操作
  return allActions.filter(action => 
    authStore.hasPermission(action.featureCode, 'view')
  )
})

const navigateTo = (path: string) => {
  router.push(path)
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

let timeInterval: number

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.home-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 12px;
  margin-bottom: 32px;
  min-height: 200px;
}

.welcome-content {
  flex: 1;
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 12px 0;
  line-height: 1.2;
}

.welcome-subtitle {
  font-size: 18px;
  margin: 0 0 24px 0;
  opacity: 0.9;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-greeting {
  font-size: 16px;
  font-weight: 500;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.role-admin {
  background: rgba(245, 34, 45, 0.2);
  border: 1px solid rgba(245, 34, 45, 0.4);
}

.role-manager {
  background: rgba(82, 196, 26, 0.2);
  border: 1px solid rgba(82, 196, 26, 0.4);
}

.role-cashier {
  background: rgba(24, 144, 255, 0.2);
  border: 1px solid rgba(24, 144, 255, 0.4);
}

.role-default {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.welcome-image {
  flex-shrink: 0;
  margin-left: 40px;
}

.image-placeholder {
  width: 120px;
  height: 120px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.store-icon {
  font-size: 48px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 24px 0;
}

.quick-actions {
  margin-bottom: 32px;
}

.sales-trend-section {
  margin-bottom: 32px;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.action-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 16px;
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 8px 0;
}

.action-description {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
  line-height: 1.5;
}

.system-info {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.info-card {
  text-align: center;
  padding: 20px;
  background: #fafafa;
  border-radius: 6px;
}

.info-card h4 {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.info-card p {
  font-size: 16px;
  color: #262626;
  margin: 0;
  font-weight: 600;
}

.status-online {
  color: #52c41a !important;
}

@media (max-width: 768px) {
  .welcome-section {
    flex-direction: column;
    text-align: center;
    padding: 24px;
  }
  
  .welcome-image {
    margin: 24px 0 0 0;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .action-grid {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 