<template>
  <div class="permission-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">权限管理</h3>
        <div class="card-actions">
          <el-button type="success" :icon="Refresh" @click="loadData">
            刷新数据
          </el-button>
        </div>
      </div>
      
      <div class="card-body">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 角色权限配置 -->
          <el-tab-pane label="角色权限配置" name="roles">
            <div class="role-permissions">
              <div class="role-selector">
                <el-select
                  v-model="selectedRole"
                  placeholder="选择角色"
                  @change="handleRoleChange"
                  style="width: 200px; margin-bottom: 20px;"
                >
                  <el-option
                    v-for="role in availableRoles"
                    :key="role.value"
                    :label="role.label"
                    :value="role.value"
                  />
                </el-select>
              </div>

              <div v-if="selectedRole && rolePermissions[selectedRole]" class="permissions-table">
                <el-table
                  :data="groupedPermissions"
                  v-loading="loading"
                  stripe
                  border
                  style="width: 100%"
                >
                  <el-table-column prop="module" label="模块" width="120" />
                  <el-table-column prop="feature_name" label="功能名称" min-width="150" />
                  <el-table-column prop="description" label="功能描述" min-width="200" show-overflow-tooltip />
                  
                  <el-table-column label="查看" width="80" align="center">
                    <template #default="{ row }">
                      <el-switch
                        v-model="row.can_view"
                        @change="updatePermission(row, 'can_view', $event)"
                        :disabled="isSystemAdminPermission(row)"
                      />
                    </template>
                  </el-table-column>
                  
                  <el-table-column label="创建" width="80" align="center">
                    <template #default="{ row }">
                      <el-switch
                        v-model="row.can_create"
                        @change="updatePermission(row, 'can_create', $event)"
                        :disabled="isSystemAdminPermission(row)"
                      />
                    </template>
                  </el-table-column>
                  
                  <el-table-column label="编辑" width="80" align="center">
                    <template #default="{ row }">
                      <el-switch
                        v-model="row.can_edit"
                        @change="updatePermission(row, 'can_edit', $event)"
                        :disabled="isSystemAdminPermission(row)"
                      />
                    </template>
                  </el-table-column>
                  
                  <el-table-column label="删除" width="80" align="center">
                    <template #default="{ row }">
                      <el-switch
                        v-model="row.can_delete"
                        @change="updatePermission(row, 'can_delete', $event)"
                        :disabled="isSystemAdminPermission(row)"
                      />
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>

          <!-- 系统功能管理 -->
          <el-tab-pane label="系统功能" name="features">
            <el-table
              :data="features"
              v-loading="loading"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="feature_id" label="ID" width="80" />
              <el-table-column prop="module" label="模块" width="120" />
              <el-table-column prop="feature_name" label="功能名称" min-width="150" />
              <el-table-column prop="feature_code" label="功能代码" min-width="150" />
              <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'danger'">
                    {{ row.is_active ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 权限预览 -->
          <el-tab-pane label="权限预览" name="preview">
            <div class="permission-preview">
              <div class="preview-controls">
                <el-select
                  v-model="previewRole"
                  placeholder="选择角色预览权限"
                  @change="loadPreviewPermissions"
                  style="width: 200px; margin-bottom: 20px;"
                >
                  <el-option
                    v-for="role in availableRoles"
                    :key="role.value"
                    :label="role.label"
                    :value="role.value"
                  />
                </el-select>
              </div>

              <div v-if="previewPermissions.length > 0" class="preview-content">
                <div
                  v-for="module in groupedPreview"
                  :key="module.name"
                  class="module-section"
                >
                  <h4 class="module-title">{{ getModuleName(module.name) }}</h4>
                  <div class="feature-grid">
                    <div
                      v-for="feature in module.features"
                      :key="feature.feature_code"
                      class="feature-card"
                    >
                      <div class="feature-header">
                        <strong>{{ feature.feature_name }}</strong>
                      </div>
                      <div class="feature-permissions">
                        <el-tag
                          v-if="feature.can_view"
                          type="success"
                          size="small"
                          effect="plain"
                        >
                          查看
                        </el-tag>
                        <el-tag
                          v-if="feature.can_create"
                          type="primary"
                          size="small"
                          effect="plain"
                        >
                          创建
                        </el-tag>
                        <el-tag
                          v-if="feature.can_edit"
                          type="warning"
                          size="small"
                          effect="plain"
                        >
                          编辑
                        </el-tag>
                        <el-tag
                          v-if="feature.can_delete"
                          type="danger"
                          size="small"
                          effect="plain"
                        >
                          删除
                        </el-tag>
                        <el-tag
                          v-if="!feature.can_view && !feature.can_create && !feature.can_edit && !feature.can_delete"
                          type="info"
                          size="small"
                          effect="plain"
                        >
                          无权限
                        </el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { Refresh } from '@element-plus/icons-vue'

interface SystemFeature {
  feature_id: number
  feature_code: string
  feature_name: string
  description: string
  module: string
  is_active: boolean
}

interface RolePermission {
  feature_id: number
  feature_code: string
  feature_name: string
  module: string
  can_view: boolean
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
}

interface UserPermission {
  feature_code: string
  feature_name: string
  module: string
  can_view: boolean
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
}

// 响应式数据
const activeTab = ref('roles')
const loading = ref(false)
const features = ref<SystemFeature[]>([])
const rolePermissions = ref<Record<string, RolePermission[]>>({})
const selectedRole = ref('')
const previewRole = ref('')
const previewPermissions = ref<UserPermission[]>([])

// 可用角色
const availableRoles = [
  { label: '系统管理员', value: 'system_admin' },
  { label: '门店经理', value: 'store_manager' },
  { label: '收银员', value: 'cashier' }
]

// 模块名称映射
const moduleNames: Record<string, string> = {
  user: '用户管理',
  store: '门店管理',
  category: '分类管理',
  supplier: '供应商管理',
  product: '商品管理',
  inventory: '库存管理',
  promotion: '促销管理',
  sales: '销售管理',
  pos: '收银系统',
  permission: '权限管理'
}

// 计算属性
const groupedPermissions = computed(() => {
  if (!selectedRole.value || !rolePermissions.value[selectedRole.value]) {
    return []
  }
  
  let permissions = rolePermissions.value[selectedRole.value]
  
  // 如果不是系统管理员，则过滤掉权限管理功能
  if (selectedRole.value !== 'system_admin') {
    permissions = permissions.filter(perm => perm.feature_code !== 'permission_management')
  }
  
  return permissions.map(perm => {
    // 查找对应的功能描述
    const feature = features.value.find(f => f.feature_id === perm.feature_id)
    return {
      ...perm,
      description: feature?.description || ''
    }
  })
})

const groupedPreview = computed(() => {
  const groups: Record<string, UserPermission[]> = {}
  
  previewPermissions.value.forEach(perm => {
    if (!groups[perm.module]) {
      groups[perm.module] = []
    }
    groups[perm.module].push(perm)
  })
  
  return Object.keys(groups).map(module => ({
    name: module,
    features: groups[module]
  }))
})

// 方法
const loadData = async () => {
  await Promise.all([
    loadFeatures(),
    loadRolePermissions()
  ])
}

const loadFeatures = async () => {
  loading.value = true
  try {
    const response = await api.get('/permissions/features')
    features.value = response.data.features || []
  } catch (error) {
    ElMessage.error('加载系统功能失败')
  } finally {
    loading.value = false
  }
}

const loadRolePermissions = async () => {
  loading.value = true
  try {
    const response = await api.get('/permissions/roles')
    rolePermissions.value = response.data.role_permissions || {}
    
    // 默认选择第一个角色
    if (!selectedRole.value && availableRoles.length > 0) {
      selectedRole.value = availableRoles[0].value
    }
  } catch (error) {
    ElMessage.error('加载角色权限失败')
  } finally {
    loading.value = false
  }
}

const handleRoleChange = () => {
  // 角色切换时的处理逻辑
}

const updatePermission = async (row: RolePermission, field: string, value: boolean) => {
  try {
    const permissionData = {
      can_view: row.can_view,
      can_create: row.can_create,
      can_edit: row.can_edit,
      can_delete: row.can_delete
    }
    
    // 更新对应字段
    permissionData[field as keyof typeof permissionData] = value
    
    await api.put(`/permissions/roles/${selectedRole.value}/features/${row.feature_id}`, permissionData)
    
    ElMessage.success('权限更新成功')
  } catch (error: any) {
    // 恢复原值
    row[field as keyof RolePermission] = !value as any
    ElMessage.error(error.response?.data?.message || '权限更新失败')
  }
}

const isSystemAdminPermission = (row: RolePermission) => {
  return selectedRole.value === 'system_admin' && row.feature_code === 'permission_management'
}

const loadPreviewPermissions = async () => {
  if (!previewRole.value) return
  
  try {
    // 这里我们使用角色权限数据来模拟用户权限
    let permissions = rolePermissions.value[previewRole.value] || []
    
    // 如果不是系统管理员，则过滤掉权限管理功能
    if (previewRole.value !== 'system_admin') {
      permissions = permissions.filter(perm => perm.feature_code !== 'permission_management')
    }
    
    previewPermissions.value = permissions.map(perm => ({
      feature_code: perm.feature_code,
      feature_name: perm.feature_name,
      module: perm.module,
      can_view: perm.can_view,
      can_create: perm.can_create,
      can_edit: perm.can_edit,
      can_delete: perm.can_delete
    }))
  } catch (error) {
    ElMessage.error('加载权限预览失败')
  }
}

const getModuleName = (module: string) => {
  return moduleNames[module] || module
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.permission-management {
  padding: 0;
}

.role-permissions {
  padding: 0;
}

.role-selector {
  margin-bottom: 20px;
}

.permissions-table {
  margin-top: 20px;
}

.permission-preview {
  padding: 0;
}

.preview-controls {
  margin-bottom: 20px;
}

.module-section {
  margin-bottom: 30px;
}

.module-title {
  color: #409eff;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.feature-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  background: #f9f9f9;
}

.feature-header {
  margin-bottom: 10px;
  font-size: 14px;
}

.feature-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.feature-permissions .el-tag {
  margin: 2px;
}

@media (max-width: 768px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }
  
  .role-selector {
    width: 100%;
  }
  
  .role-selector .el-select {
    width: 100% !important;
  }
}
</style> 