<template>
  <div class="category-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">商品分类管理</h3>
        <el-button 
          v-if="hasPermission('category_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          新增分类
        </el-button>
      </div>
      
      <div class="card-body">
        <el-table :data="categories" v-loading="loading" stripe>
          <el-table-column prop="category_id" label="ID" width="80" />
          <el-table-column prop="name" label="分类名称" min-width="200" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button 
                v-if="hasPermission('category_management', 'edit')"
                type="primary" 
                size="small" 
                :icon="Edit" 
                @click="showEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="hasPermission('category_management', 'delete')"
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑分类' : '新增分类'" width="400px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
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
import { formatDate } from '@/utils/date'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { hasPermission } = authStore

interface Category {
  category_id: number
  name: string
  created_at: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const categories = ref<Category[]>([])

const form = ref({
  category_id: 0,
  name: ''
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 2, max: 50, message: '分类名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const loadCategories = async () => {
  loading.value = true
  try {
    const response = await api.get('/categories/')
    categories.value = response.data.categories || []
  } catch (error) {
    ElMessage.error('加载分类列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  form.value = { category_id: 0, name: '' }
}

const showEditDialog = (category: Category) => {
  isEdit.value = true
  dialogVisible.value = true
  form.value = { ...category }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await api.put(`/categories/${form.value.category_id}`, form.value)
          ElMessage.success('分类更新成功')
        } else {
          await api.post('/categories/', form.value)
          ElMessage.success('分类创建成功')
        }
        dialogVisible.value = false
        await loadCategories()
      } catch (error: any) {
        const errorMsg = error.response?.data?.message || (isEdit.value ? '分类更新失败' : '分类创建失败')
        ElMessage.error(errorMsg)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (category: Category) => {
  try {
    await ElMessageBox.confirm(`确定要删除分类 "${category.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/categories/${category.category_id}`)
    ElMessage.success('分类删除成功')
    await loadCategories()
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || '分类删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.category-management {
  padding: 0;
}
</style> 