<template>
  <div class="inventory-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">库存管理</h3>
        <el-button 
          v-if="hasPermission('inventory_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          库存调整
        </el-button>
      </div>
      
      <div class="card-body">
        <el-table :data="inventory" v-loading="loading" stripe>
          <el-table-column prop="inventory_id" label="ID" width="80" />
          <el-table-column prop="product_name" label="商品名称" min-width="150" />
          <el-table-column prop="store_name" label="门店" width="120" />
          <el-table-column prop="quantity" label="库存数量" width="100">
            <template #default="{ row }">
              <el-tag :type="getQuantityType(row.quantity)">{{ row.quantity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="单价" width="100">
            <template #default="{ row }">
              ¥{{ row.price }}
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button 
                v-if="hasPermission('inventory_management', 'edit')"
                type="primary" 
                size="small" 
                :icon="Edit" 
                @click="showEditDialog(row)"
              >
                调整
              </el-button>
              <el-button 
                v-if="hasPermission('inventory_management', 'delete')"
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

    <el-dialog v-model="dialogVisible" title="库存调整" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="门店" prop="store_id">
          <el-select v-model="form.store_id" placeholder="请选择门店" style="width: 100%">
            <el-option v-for="store in stores" :key="store.store_id" :label="store.name" :value="store.store_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品" prop="product_id">
          <el-select v-model="form.product_id" placeholder="请选择商品" style="width: 100%">
            <el-option v-for="product in products" :key="product.product_id" :label="product.name" :value="product.product_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="单价" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
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

interface InventoryItem {
  inventory_id: number
  product_name: string
  store_name: string
  quantity: number
  price: number
  updated_at: string
  store_id: number
  product_id: number
  original_price?: number
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const inventory = ref<InventoryItem[]>([])
const stores = ref([])
const products = ref([])

const form = ref({
  store_id: null,
  product_id: null,
  quantity: 0,
  price: 0
})

const formRules: FormRules = {
  store_id: [{ required: true, message: '请选择门店', trigger: 'change' }],
  product_id: [{ required: true, message: '请选择商品', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

const loadInventory = async () => {
  loading.value = true
  try {
    const response = await api.get('/inventory/')
    inventory.value = response.data.inventory || []
  } catch (error) {
    ElMessage.error('加载库存列表失败')
  } finally {
    loading.value = false
  }
}

const loadStores = async () => {
  try {
    const response = await api.get('/stores/')
    stores.value = response.data.stores || []
  } catch (error) {
    console.error('加载门店失败')
  }
}

const loadProducts = async () => {
  try {
    const response = await api.get('/products/')
    products.value = response.data.products || []
  } catch (error) {
    console.error('加载商品失败')
  }
}

const showAddDialog = () => {
  dialogVisible.value = true
  form.value = { store_id: null, product_id: null, quantity: 0, price: 0 }
}

const showEditDialog = (item: InventoryItem) => {
  dialogVisible.value = true
  form.value = {
    store_id: item.store_id,
    product_id: item.product_id,
    quantity: item.quantity,
    price: item.original_price || item.price
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await api.post('/inventory/', form.value)
        ElMessage.success('库存调整成功')
        dialogVisible.value = false
        form.value = { store_id: null, product_id: null, quantity: 0, price: 0 }
        await loadInventory()
      } catch (error: any) {
        console.error('库存调整失败:', error)
        const errorMessage = error.response?.data?.message || '库存调整失败，请检查网络连接'
        ElMessage.error(errorMessage)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (item: InventoryItem) => {
  try {
    await ElMessageBox.confirm(`确定要删除商品 "${item.product_name}" 在门店 "${item.store_name}" 的库存记录吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/inventory/${item.inventory_id}`)
    ElMessage.success('库存记录删除成功')
    await loadInventory()
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || '库存记录删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

const getQuantityType = (quantity: number) => {
  if (quantity <= 10) return 'danger'
  if (quantity <= 50) return 'warning'
  return 'success'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(async () => {
  await Promise.all([loadInventory(), loadStores(), loadProducts()])
})
</script>

<style scoped>
.inventory-management {
  padding: 0;
}
</style> 