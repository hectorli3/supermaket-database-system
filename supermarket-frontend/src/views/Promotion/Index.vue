<template>
  <div class="promotion-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">促销管理</h3>
        <el-button 
          v-if="hasPermission('promotion_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          新增促销
        </el-button>
      </div>
      <div class="card-body">
        <el-table :data="promotions" v-loading="loading" stripe>
          <el-table-column prop="promotion_id" label="ID" width="80" />
          <el-table-column prop="name" label="促销名称" min-width="150" />
          <el-table-column label="折扣率" width="100">
            <template #default="{ row }">
              <span v-if="row.discount_type === 'percentage'">
                {{ row.discount_value }}%
              </span>
              <span v-else>
                ¥{{ row.discount_value }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="开始时间" width="120">
            <template #default="{ row }">
              {{ formatDate(row.start_date) }}
            </template>
          </el-table-column>
          <el-table-column label="结束时间" width="120">
            <template #default="{ row }">
              {{ formatDate(row.end_date) }}
            </template>
          </el-table-column>
          <el-table-column label="参与商品" min-width="200">
            <template #default="{ row }">
              <el-tag 
                v-for="product in row.products.slice(0, 3)" 
                :key="product.product_id"
                size="small"
                style="margin-right: 5px;"
              >
                {{ product.name }}
              </el-tag>
              <span v-if="row.products.length > 3" class="more-products">
                +{{ row.products.length - 3 }}个
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button 
                v-if="hasPermission('promotion_management', 'edit')"
                type="primary" 
                size="small" 
                :icon="Edit" 
                @click="showEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="hasPermission('promotion_management', 'delete')"
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑促销' : '新增促销'" width="700px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="促销名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入促销名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入促销描述" />
        </el-form-item>
        <el-form-item label="折扣类型" prop="discount_type">
          <el-select v-model="form.discount_type" placeholder="请选择折扣类型" style="width: 100%">
            <el-option label="百分比折扣" value="percentage" />
            <el-option label="固定金额" value="fixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="折扣值" prop="discount_value">
          <el-input-number 
            v-model="form.discount_value" 
            :min="0" 
            :max="form.discount_type === 'percentage' ? 100 : 9999" 
            :step="form.discount_type === 'percentage' ? 1 : 0.01" 
            :precision="form.discount_type === 'percentage' ? 0 : 2" 
            style="width: 100%" 
          />
          <span style="margin-left: 8px; color: #666;">
            {{ form.discount_type === 'percentage' ? '%' : '元' }}
          </span>
        </el-form-item>
        <el-form-item label="开始时间" prop="start_date">
          <el-date-picker 
            v-model="form.start_date" 
            type="date" 
            placeholder="选择开始日期" 
            style="width: 100%" 
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_date">
          <el-date-picker 
            v-model="form.end_date" 
            type="date" 
            placeholder="选择结束日期" 
            style="width: 100%" 
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="参与商品" prop="product_ids">
          <el-select
            v-model="form.product_ids"
            multiple
            filterable
            placeholder="请选择参与促销的商品"
            style="width: 100%"
            @focus="loadProducts"
          >
            <el-option
              v-for="product in products"
              :key="product.product_id"
              :label="`${product.name} (${product.sku})`"
              :value="product.product_id"
            />
          </el-select>
          <div style="margin-top: 5px; color: #666; font-size: 12px;">
            已选择 {{ form.product_ids.length }} 个商品
          </div>
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

interface Promotion {
  promotion_id: number
  name: string
  description: string
  discount_type: 'percentage' | 'fixed'
  discount_value: number
  start_date: string
  end_date: string
  status: 'pending' | 'active' | 'expired' | 'inactive'
  products: Array<{ product_id: number; name: string }>
}

interface Product {
  product_id: number
  name: string
  sku: string
  category_name?: string
  supplier_name?: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const promotions = ref<Promotion[]>([])
const products = ref<Product[]>([])

const form = ref({
  promotion_id: 0,
  name: '',
  description: '',
  discount_type: 'percentage' as 'percentage' | 'fixed',
  discount_value: 0,
  start_date: '',
  end_date: '',
  product_ids: [] as number[]
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入促销名称', trigger: 'blur' },
    { min: 2, max: 100, message: '促销名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  discount_type: [
    { required: true, message: '请选择折扣类型', trigger: 'change' }
  ],
  discount_value: [
    { required: true, message: '请输入折扣值', trigger: 'blur' }
  ],
  start_date: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  end_date: [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ],
  product_ids: [
    { required: true, message: '请选择参与促销的商品', trigger: 'change' }
  ]
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'pending': return 'warning'
    case 'expired': return 'info'
    default: return 'danger'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '进行中'
    case 'pending': return '未开始'
    case 'expired': return '已过期'
    default: return '停用'
  }
}

const loadPromotions = async () => {
  loading.value = true
  try {
    const response = await api.get('/promotions/')
    promotions.value = response.data.promotions || []
  } catch (error) {
    ElMessage.error('加载促销列表失败')
  } finally {
    loading.value = false
  }
}

const loadProducts = async () => {
  if (products.value.length > 0) return // 避免重复加载
  
  try {
    const response = await api.get('/products/')
    products.value = response.data.products || []
  } catch (error) {
    ElMessage.error('加载商品列表失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  form.value = { 
    promotion_id: 0, 
    name: '', 
    description: '',
    discount_type: 'percentage', 
    discount_value: 0, 
    start_date: '', 
    end_date: '',
    product_ids: []
  }
}

const showEditDialog = (promotion: Promotion) => {
  isEdit.value = true
  dialogVisible.value = true
  form.value = { 
    promotion_id: promotion.promotion_id,
    name: promotion.name,
    description: promotion.description,
    discount_type: promotion.discount_type,
    discount_value: promotion.discount_value,
    start_date: promotion.start_date,
    end_date: promotion.end_date,
    product_ids: promotion.products.map(p => p.product_id)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await api.put(`/promotions/${form.value.promotion_id}`, form.value)
          ElMessage.success('促销更新成功')
        } else {
          await api.post('/promotions/', form.value)
          ElMessage.success('促销创建成功')
        }
        dialogVisible.value = false
        await loadPromotions()
      } catch (error: any) {
        const errorMsg = error.response?.data?.message || (isEdit.value ? '促销更新失败' : '促销创建失败')
        ElMessage.error(errorMsg)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (promotion: Promotion) => {
  try {
    await ElMessageBox.confirm(`确定要删除促销 "${promotion.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/promotions/${promotion.promotion_id}`)
    ElMessage.success('促销删除成功')
    await loadPromotions()
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || '促销删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

onMounted(() => {
  loadPromotions()
})
</script>

<style scoped>
.promotion-management {
  padding: 0;
}

.more-products {
  color: #666;
  font-size: 12px;
}
</style> 