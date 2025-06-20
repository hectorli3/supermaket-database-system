import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

export interface User {
  user_id: number
  username: string
  role: 'system_admin' | 'store_manager' | 'cashier'
  store_id?: number
  created_at: string
}

export interface Permission {
  feature_code: string
  feature_name: string
  module: string
  can_view: boolean
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const permissions = ref<Permission[]>([])
  
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  
  const login = async (credentials: { username: string; password: string }) => {
    try {
      const response = await api.post('/auth/login', credentials)
      const { access_token, user: userData } = response.data
      
      token.value = access_token
      user.value = userData
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      // 登录后获取用户权限
      await loadUserPermissions()
      
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '登录失败')
      return false
    }
  }
  
  const register = async (userData: {
    username: string
    password: string
    role: string
    store_id?: number
  }) => {
    try {
      await api.post('/auth/register', userData)
      ElMessage.success('注册成功，请登录')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '注册失败')
      return false
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    permissions.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('permissions')
    ElMessage.success('已退出登录')
  }
  
  const checkAuth = async () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    const savedPermissions = localStorage.getItem('permissions')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
        if (savedPermissions) {
          permissions.value = JSON.parse(savedPermissions)
        } else {
          // 如果没有缓存的权限，重新获取
          await loadUserPermissions()
        }
      } catch {
        logout()
      }
    }
  }
  
  const loadUserPermissions = async () => {
    if (!user.value) return
    
    try {
      const response = await api.get(`/permissions/user/${user.value.user_id}`)
      permissions.value = response.data.permissions || []
      localStorage.setItem('permissions', JSON.stringify(permissions.value))
    } catch (error) {
      console.error('获取用户权限失败:', error)
      permissions.value = []
    }
  }
  
  const hasRole = (roles: string[]) => {
    return user.value ? roles.includes(user.value.role) : false
  }
  
  // 检查是否有特定功能的权限
  const hasPermission = (featureCode: string, action: 'view' | 'create' | 'edit' | 'delete' = 'view') => {
    const permission = permissions.value.find(p => p.feature_code === featureCode)
    if (!permission) return false
    
    switch (action) {
      case 'view':
        return permission.can_view
      case 'create':
        return permission.can_create
      case 'edit':
        return permission.can_edit
      case 'delete':
        return permission.can_delete
      default:
        return false
    }
  }
  
  // 检查是否可以访问某个模块
  const canAccessModule = (moduleCode: string) => {
    return permissions.value.some(p => p.module === moduleCode && p.can_view)
  }
  
  const isAdmin = computed(() => user.value?.role === 'system_admin')
  const isManager = computed(() => user.value?.role === 'store_manager')
  const isCashier = computed(() => user.value?.role === 'cashier')
  
  return {
    user,
    token,
    permissions,
    isAuthenticated,
    login,
    register,
    logout,
    checkAuth,
    loadUserPermissions,
    hasRole,
    hasPermission,
    canAccessModule,
    isAdmin,
    isManager,
    isCashier
  }
}) 