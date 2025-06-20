<template>
  <div class="store-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">门店管理</h3>
        <el-button 
          v-if="hasPermission('store_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          新增门店
        </el-button>
      </div>
      
      <div class="card-body">
        <div class="table-toolbar">
          <div class="table-toolbar-left">
            <el-input
              v-model="searchQuery"
              placeholder="搜索门店名称或地址"
              :prefix-icon="Search"
              clearable
              style="width: 300px"
            />
          </div>
          <div class="table-toolbar-right">
            <el-button :icon="Refresh" @click="loadStores">刷新</el-button>
          </div>
        </div>

        <el-table :data="filteredStores" v-loading="loading" stripe>
          <el-table-column prop="store_id" label="ID" width="80" />
          <el-table-column prop="name" label="门店名称" min-width="150" />
          <el-table-column prop="address" label="地址" min-width="200" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button 
                v-if="hasPermission('store_management', 'edit')"
                type="primary" 
                size="small" 
                :icon="Edit" 
                @click="showEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="hasPermission('store_management', 'delete')"
                type="danger" 
                size="small" 
                :icon="Delete" 
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑门店' : '新增门店'" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="门店名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入门店名称" />
        </el-form-item>
        <el-form-item label="门店地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入门店地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { Plus, Search, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { formatDate } from '@/utils/date'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { hasPermission } = authStore

interface Store {
  store_id: number
  name: string
  address: string
  created_at: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const stores = ref<Store[]>([])
const searchQuery = ref('')

const form = ref({
  store_id: 0,
  name: '',
  address: ''
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入门店名称', trigger: 'blur' },
    { min: 2, max: 100, message: '门店名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  address: [
    { required: true, message: '请输入门店地址', trigger: 'blur' },
    { min: 5, max: 200, message: '门店地址长度在 5 到 200 个字符', trigger: 'blur' }
  ]
}

const filteredStores = computed(() => {
  if (!searchQuery.value) return stores.value
  const query = searchQuery.value.toLowerCase()
  return stores.value.filter(store =>
    store.name.toLowerCase().includes(query) ||
    store.address.toLowerCase().includes(query)
  )
})

const loadStores = async () => {
  loading.value = true
  try {
    const response = await api.get('/stores/')
    stores.value = response.data.stores || []
  } catch (error) {
    ElMessage.error('加载门店列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

const showEditDialog = (store: Store) => {
  isEdit.value = true
  dialogVisible.value = true
  form.value = { ...store }
}

const resetForm = () => {
  form.value = { store_id: 0, name: '', address: '' }
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await api.put(`/stores/${form.value.store_id}`, form.value)
          ElMessage.success('门店更新成功')
        } else {
          await api.post('/stores/', form.value)
          ElMessage.success('门店创建成功')
        }
        dialogVisible.value = false
        await loadStores()
      } catch (error: any) {
        const errorMsg = error.response?.data?.message || (isEdit.value ? '门店更新失败' : '门店创建失败')
        ElMessage.error(errorMsg)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (store: Store) => {
  try {
    await ElMessageBox.confirm(`确定要删除门店 "${store.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/stores/${store.store_id}`)
    ElMessage.success('门店删除成功')
    await loadStores()
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || '门店删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

onMounted(() => {
  loadStores()
})
</script>

<style scoped>
.store-management {
  padding: 0;
}
</style> 