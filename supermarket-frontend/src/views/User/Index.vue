<template>
  <div class="user-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">用户管理</h3>
        <el-button 
          v-if="hasPermission('user_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          新增用户
        </el-button>
      </div>
      <div class="card-body">
        <el-table :data="users" v-loading="loading" stripe>
          <el-table-column prop="user_id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="role" label="角色" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="store_name" label="所属门店" width="150">
            <template #default="{ row }">
              {{ row.role === 'admin' ? '总部' : (row.store_name || '未分配') }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button 
                v-if="hasPermission('user_management', 'edit')"
                size="small" 
                type="primary" 
                :icon="Edit"
                @click="editUser(row)"
                :disabled="!canEditUser(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="hasPermission('user_management', 'delete')"
                size="small" 
                type="danger" 
                :icon="Delete"
                @click="deleteUser(row)" 
                :disabled="!canDeleteUser(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 新增/编辑用户对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
      @close="resetForm"
    >
      <el-form :model="userForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="password" v-if="isEdit">
          <el-input v-model="userForm.password" type="password" placeholder="留空则不修改密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option 
              v-for="option in availableRoles" 
              :key="option.value"
              :label="option.label" 
              :value="option.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属门店" prop="store_id">
          <el-select 
            v-model="userForm.store_id" 
            placeholder="请选择门店" 
            style="width: 100%" 
            clearable
            :disabled="userForm.role === 'admin'"
          >
            <el-option
              v-for="store in availableStores"
              :key="store.store_id"
              :label="store.name"
              :value="store.store_id"
            />
          </el-select>
          <div v-if="userForm.role === 'admin'" style="margin-top: 5px; color: #909399; font-size: 12px;">
            系统管理员自动分配到总部
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import { formatDate } from '@/utils/date'

interface User {
  user_id: number
  username: string
  role: string
  store_id?: number
  store_name?: string
  created_at: string
  updated_at: string
}

interface Store {
  store_id: number
  name: string
}

const authStore = useAuthStore()
const { hasPermission } = authStore

const loading = ref(false)
const submitting = ref(false)
const users = ref<User[]>([])
const stores = ref<Store[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const userForm = ref({
  user_id: 0,
  username: '',
  password: '',
  role: '',
  store_id: null as number | null
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const currentUserId = computed(() => {
  return authStore.user?.user_id
})

const dialogTitle = computed(() => {
  return isEdit.value ? '编辑用户' : '新增用户'
})

const availableRoles = computed(() => {
  const currentUserRole = authStore.user?.role
  
  if (currentUserRole === 'system_admin') {
    // 系统管理员可以创建所有角色
    return [
      { label: '系统管理员', value: 'admin' },
      { label: '门店经理', value: 'manager' },
      { label: '收银员', value: 'cashier' }
    ]
  } else if (currentUserRole === 'store_manager') {
    // 门店经理只能创建收银员
    return [
      { label: '收银员', value: 'cashier' }
    ]
  } else {
    // 收银员不能创建用户（这个情况不应该出现，因为前端已经隐藏了按钮）
    return []
  }
})

const availableStores = computed(() => {
  const currentUserRole = authStore.user?.role
  const currentUserStoreId = authStore.user?.store_id
  
  if (currentUserRole === 'system_admin') {
    // 系统管理员可以选择所有门店
    return stores.value
  } else if (currentUserRole === 'store_manager') {
    // 门店经理只能选择自己的门店
    return stores.value.filter(store => store.store_id === currentUserStoreId)
  } else {
    // 收银员不能创建用户
    return []
  }
})

const canEditUser = (user: User) => {
  const currentUserRole = authStore.user?.role
  const currentUserStoreId = authStore.user?.store_id
  const currentUserId = authStore.user?.user_id
  
  if (currentUserRole === 'system_admin') {
    // 系统管理员可以编辑所有用户
    return true
  } else if (currentUserRole === 'store_manager') {
    // 门店经理不能编辑系统管理员
    if (user.role === 'admin') {
      return false
    }
    // 门店经理只能编辑自己门店的用户或自己
    return user.store_id === currentUserStoreId || user.user_id === currentUserId
  } else {
    // 收银员只能编辑自己
    return user.user_id === currentUserId
  }
}

const canDeleteUser = (user: User) => {
  const currentUserRole = authStore.user?.role
  const currentUserStoreId = authStore.user?.store_id
  const currentUserId = authStore.user?.user_id
  
  // 不能删除自己
  if (user.user_id === currentUserId) {
    return false
  }
  
  if (currentUserRole === 'system_admin') {
    // 系统管理员可以删除除自己外的所有用户
    return true
  } else if (currentUserRole === 'store_manager') {
    // 门店经理不能删除系统管理员和其他门店经理
    if (user.role === 'admin' || user.role === 'manager') {
      return false
    }
    // 门店经理只能删除自己门店的收银员
    return user.store_id === currentUserStoreId && user.role === 'cashier'
  } else {
    // 收银员不能删除任何用户
    return false
  }
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await api.get('/users/')
    users.value = response.data.users || []
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const loadStores = async () => {
  try {
    const response = await api.get('/stores/')
    stores.value = response.data.stores || []
  } catch (error) {
    console.error('加载门店列表失败:', error)
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

const editUser = (user: User) => {
  isEdit.value = true
  dialogVisible.value = true
  userForm.value = {
    user_id: user.user_id,
    username: user.username,
    password: '',
    role: user.role,
    store_id: user.store_id || null
  }
}

const resetForm = () => {
  userForm.value = {
    user_id: 0,
    username: '',
    password: '',
    role: '',
    store_id: null
  }
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const formData = { ...userForm.value }
    
    // 如果是编辑且密码为空，则不发送密码字段
    if (isEdit.value && !formData.password) {
      delete formData.password
    }
    
    if (isEdit.value) {
      await api.put(`/users/${formData.user_id}`, formData)
      ElMessage.success('用户更新成功')
    } else {
      await api.post('/users/', formData)
      ElMessage.success('用户创建成功')
    }
    
    dialogVisible.value = false
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const deleteUser = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/users/${user.user_id}`)
    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const getRoleType = (role: string) => {
  const types = {
    'admin': 'danger',
    'manager': 'warning',
    'cashier': 'success'
  }
  return types[role] || 'info'
}

const getRoleText = (role: string) => {
  const texts = {
    'admin': '系统管理员',
    'manager': '门店经理',
    'cashier': '收银员'
  }
  return texts[role] || role
}

// 监听角色变化，如果选择admin则自动设置为总店
watch(() => userForm.value.role, (newRole) => {
  if (newRole === 'admin') {
    // 查找总店ID（假设总店名称为"总店"）
    const headquarter = stores.value.find(store => store.name === '总店')
    if (headquarter) {
      userForm.value.store_id = headquarter.store_id
    }
  }
})

onMounted(() => {
  loadUsers()
  loadStores()
})
</script>

<style scoped>
.user-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
</style> 