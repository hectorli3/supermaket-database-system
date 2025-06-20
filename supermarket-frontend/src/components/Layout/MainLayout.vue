<template>
  <div class="layout-container">
    <!-- 顶部导航 -->
    <el-header class="layout-header" height="60px">
      <div class="header-content">
        <div class="header-left">
          <el-button
            :icon="collapsed ? Expand : Fold"
            @click="toggleSidebar"
            text
            size="large"
          />
          <h1 class="system-title">超市管理系统</h1>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ authStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <!-- 主体内容 -->
    <el-container class="layout-main">
      <!-- 侧边栏 -->
      <el-aside :width="collapsed ? '64px' : '200px'" class="layout-sidebar">
        <el-menu
          :default-active="$route.path"
          :collapse="collapsed"
          :unique-opened="true"
          router
          background-color="#001529"
          text-color="#fff"
          active-text-color="#ffffff"
        >
          <template v-for="route in menuRoutes" :key="route.path">
            <el-menu-item
              v-if="canAccessRoute(route)"
              :index="route.path"
            >
              <el-icon>
                <component :is="route.meta?.icon" />
              </el-icon>
              <template #title>{{ route.meta?.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>

      <!-- 内容区域 -->
      <el-main class="layout-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Fold,
  Expand,
  UserFilled,
  ArrowDown,
  User,
  Setting,
  SwitchButton,
  House
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const collapsed = ref(false)

// 菜单路由
const menuRoutes = computed(() => {
  return router.getRoutes()
    .filter(route => route.meta?.title && route.path !== '/')
    .sort((a, b) => {
      const order = {
        '/home': 1,
        '/stores': 2,
        '/users': 3,
        '/categories': 4,
        '/suppliers': 5,
        '/products': 6,
        '/inventory': 7,
        '/promotions': 8,
        '/sales': 9,
        '/pos': 10,
        '/permissions': 11
      }
      return (order[a.path] || 999) - (order[b.path] || 999)
    })
})

const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
      authStore.logout()
      router.push('/login')
  }
}

const canAccessRoute = (route: any) => {
  // 路由与功能代码的映射
  const routeFeatureMap: Record<string, string> = {
    '/stores': 'store_management',
    '/users': 'user_management',
    '/categories': 'category_management',
    '/suppliers': 'supplier_management',
    '/products': 'product_management',
    '/inventory': 'inventory_management',
    '/promotions': 'promotion_management',
    '/sales': 'sales_management',
    '/pos': 'pos_system',
    '/permissions': 'permission_management'
  }
  
  const featureCode = routeFeatureMap[route.path]
  if (!featureCode) return true // 未映射的路由默认允许访问
  
  return authStore.hasPermission(featureCode, 'view')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  z-index: 1000;
  padding: 0;
}

.header-content {
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.system-title {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f5f5;
}

.username {
  font-size: 14px;
  color: #262626;
}

.layout-main {
  flex: 1;
  overflow: hidden;
}

.layout-sidebar {
  background: #001529;
  transition: width 0.3s;
}

.layout-content {
  background: #f0f2f5;
  overflow-y: auto;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
}

:deep(.el-menu-item.is-active) {
  background-color: #1890ff !important;
}

@media (max-width: 768px) {
  .system-title {
    display: none;
  }
  
  .layout-sidebar {
    position: fixed;
    left: -200px;
    top: 60px;
    height: calc(100vh - 60px);
    z-index: 1001;
    transition: left 0.3s;
  }
  
  .layout-sidebar.mobile-open {
    left: 0;
  }
}
</style> 