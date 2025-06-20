import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/Register.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/components/Layout/MainLayout.vue'),
      meta: { requiresAuth: true },
      redirect: '/home',
      children: [
        {
          path: '/home',
          name: 'Home',
          component: () => import('@/views/Home/Index.vue'),
          meta: { title: '首页', icon: 'House' }
        },
        {
          path: '/stores',
          name: 'Stores',
          component: () => import('@/views/Store/Index.vue'),
          meta: { title: '门店管理', icon: 'Shop', roles: ['system_admin', 'store_manager'] }
        },
        {
          path: '/users',
          name: 'Users',
          component: () => import('@/views/User/Index.vue'),
          meta: { title: '用户管理', icon: 'User', roles: ['system_admin', 'store_manager'] }
        },
        {
          path: '/categories',
          name: 'Categories',
          component: () => import('@/views/Category/Index.vue'),
          meta: { title: '商品分类', icon: 'Menu', roles: ['system_admin', 'store_manager'] }
        },
        {
          path: '/suppliers',
          name: 'Suppliers',
          component: () => import('@/views/Supplier/Index.vue'),
          meta: { title: '供应商管理', icon: 'OfficeBuilding', roles: ['system_admin', 'store_manager'] }
        },
        {
          path: '/products',
          name: 'Products',
          component: () => import('@/views/Product/Index.vue'),
          meta: { title: '商品管理', icon: 'Goods', roles: ['system_admin', 'store_manager'] }
        },
        {
          path: '/inventory',
          name: 'Inventory',
          component: () => import('@/views/Inventory/Index.vue'),
          meta: { title: '库存管理', icon: 'Box' }
        },
        {
          path: '/promotions',
          name: 'Promotions',
          component: () => import('@/views/Promotion/Index.vue'),
          meta: { title: '促销管理', icon: 'Present', roles: ['system_admin', 'store_manager'] }
        },
        {
          path: '/sales',
          name: 'Sales',
          component: () => import('@/views/Sale/Index.vue'),
          meta: { title: '销售管理', icon: 'ShoppingCart' }
        },
        {
          path: '/pos',
          name: 'POS',
          component: () => import('@/views/Sale/POS.vue'),
          meta: { title: '收银台', icon: 'CreditCard', roles: ['cashier', 'store_manager'] }
        },
        {
          path: '/permissions',
          name: 'Permissions',
          component: () => import('@/views/Permission/Index.vue'),
          meta: { title: '权限管理', icon: 'Lock', roles: ['system_admin'] }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/404.vue')
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 如果已登录访问登录页，重定向到首页
  if (authStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next('/home')
    return
  }
  
  // 确保权限已加载
  if (authStore.isAuthenticated && authStore.permissions.length === 0) {
    await authStore.loadUserPermissions()
  }
  
  // 检查动态权限
  if (authStore.isAuthenticated) {
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
    
    const featureCode = routeFeatureMap[to.path]
    if (featureCode && !authStore.hasPermission(featureCode, 'view')) {
      ElMessage.error('您没有权限访问此页面')
      next('/home')
      return
    }
  }
  
  next()
})

export default router 