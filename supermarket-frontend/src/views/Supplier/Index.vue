<template>
  <div class="supplier-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">供应商管理</h3>
        <el-button 
          v-if="hasPermission('supplier_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          新增供应商
        </el-button>
      </div>
      
      <div class="card-body">
        <el-table :data="suppliers" v-loading="loading" stripe>
          <el-table-column prop="supplier_id" label="ID" width="80" />
          <el-table-column prop="name" label="供应商名称" min-width="150" />
          <el-table-column prop="contact_info" label="联系方式" min-width="150" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button 
                v-if="hasPermission('supplier_management', 'edit')"
                type="primary" 
                size="small" 
                :icon="Edit" 
                @click="showEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="hasPermission('supplier_management', 'delete')"
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑供应商' : '新增供应商'" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="供应商名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="联系方式" prop="contact_info">
          <el-input v-model="form.contact_info" placeholder="请输入联系方式" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { hasPermission } = authStore

interface Supplier {
  supplier_id: number
  name: string
  contact_info: string
  created_at: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const suppliers = ref<Supplier[]>([])

const form = ref({
  supplier_id: 0,
  name: '',
  contact_info: ''
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入供应商名称', trigger: 'blur' },
    { min: 2, max: 100, message: '供应商名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  contact_info: [
    { required: true, message: '请输入联系方式', trigger: 'blur' },
    { min: 5, max: 100, message: '联系方式长度在 5 到 100 个字符', trigger: 'blur' }
  ]
}

const loadSuppliers = async () => {
  loading.value = true
  try {
    const response = await api.get('/suppliers/')
    suppliers.value = response.data.suppliers || []
  } catch (error) {
    ElMessage.error('加载供应商列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  form.value = { supplier_id: 0, name: '', contact_info: '' }
}

const showEditDialog = (supplier: Supplier) => {
  isEdit.value = true
  dialogVisible.value = true
  form.value = { ...supplier }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await api.put(`/suppliers/${form.value.supplier_id}`, form.value)
          ElMessage.success('供应商更新成功')
        } else {
          await api.post('/suppliers/', form.value)
          ElMessage.success('供应商创建成功')
        }
        dialogVisible.value = false
        await loadSuppliers()
      } catch (error: any) {
        const errorMsg = error.response?.data?.message || (isEdit.value ? '供应商更新失败' : '供应商创建失败')
        ElMessage.error(errorMsg)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (supplier: Supplier) => {
  try {
    await ElMessageBox.confirm(`确定要删除供应商 "${supplier.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/suppliers/${supplier.supplier_id}`)
    ElMessage.success('供应商删除成功')
    await loadSuppliers()
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || '供应商删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  loadSuppliers()
})
</script>

<style scoped>
.supplier-management {
  padding: 0;
}
</style> 