<template>
  <div class="product-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">商品管理</h3>
        <el-button 
          v-if="hasPermission('product_management', 'create')"
          type="primary" 
          :icon="Plus" 
          @click="showAddDialog"
        >
          新增商品
        </el-button>
      </div>
      
      <div class="card-body">
        <!-- 销售趋势图 -->
        <div v-if="hasPermission('sales_management', 'view')" class="chart-section">
          <SalesChart />
        </div>
        
        <!-- 搜索和筛选 -->
        <div class="table-toolbar">
          <div class="table-toolbar-left">
            <el-input
              v-model="searchQuery"
              placeholder="搜索商品名称或SKU"
              :prefix-icon="Search"
              clearable
              style="width: 300px"
              @input="handleSearch"
            />
            <el-select
              v-model="selectedCategory"
              placeholder="选择分类"
              clearable
              style="width: 150px"
              @change="handleCategoryFilter"
            >
              <el-option
                v-for="category in categories"
                :key="category.category_id"
                :label="category.name"
                :value="category.category_id"
              />
            </el-select>
          </div>
          
          <div class="table-toolbar-right">
            <el-button :icon="Refresh" @click="loadProducts">刷新</el-button>
          </div>
        </div>

        <!-- 商品表格 -->
        <el-table
          :data="filteredProducts"
          v-loading="loading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="product_id" label="ID" width="80" />
          <el-table-column prop="name" label="商品名称" min-width="150" />
          <el-table-column prop="sku" label="SKU" width="120" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category_name" label="分类" width="120" />
          <el-table-column prop="supplier_name" label="供应商" width="150" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="hasPermission('product_management', 'edit')"
                type="primary"
                size="small"
                :icon="Edit"
                @click="showEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button
                v-if="hasPermission('product_management', 'delete')"
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

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalProducts"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑商品' : '新增商品'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入商品名称" />
        </el-form-item>
        
        <el-form-item label="SKU" prop="sku">
          <el-input v-model="form.sku" placeholder="请输入商品SKU" />
        </el-form-item>
        
        <el-form-item label="商品描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入商品描述"
          />
        </el-form-item>
        
        <el-form-item label="商品分类" prop="category_id">
          <el-select
            v-model="form.category_id"
            placeholder="请选择商品分类"
            style="width: 100%"
          >
            <el-option
              v-for="category in categories"
              :key="category.category_id"
              :label="category.name"
              :value="category.category_id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="供应商" prop="supplier_id">
          <el-select
            v-model="form.supplier_id"
            placeholder="请选择供应商"
            style="width: 100%"
          >
            <el-option
              v-for="supplier in suppliers"
              :key="supplier.supplier_id"
              :label="supplier.name"
              :value="supplier.supplier_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import {
  Plus,
  Search,
  Refresh,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import SalesChart from '@/components/SalesChart.vue'

const authStore = useAuthStore()
const { hasPermission } = authStore

interface Product {
  product_id: number
  name: string
  sku: string
  description: string
  category_id: number
  category_name?: string
  supplier_id: number
  supplier_name?: string
  created_at: string
}

interface Category {
  category_id: number
  name: string
}

interface Supplier {
  supplier_id: number
  name: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const suppliers = ref<Supplier[]>([])

const searchQuery = ref('')
const selectedCategory = ref<number | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)

const form = ref({
  product_id: 0,
  name: '',
  sku: '',
  description: '',
  category_id: null as number | null,
  supplier_id: null as number | null
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' },
    { min: 2, max: 100, message: '商品名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  sku: [
    { required: true, message: '请输入商品SKU', trigger: 'blur' },
    { min: 3, max: 50, message: 'SKU长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ],
  category_id: [
    { required: true, message: '请选择商品分类', trigger: 'change' }
  ],
  supplier_id: [
    { required: true, message: '请选择供应商', trigger: 'change' }
  ]
}

// 计算属性
const filteredProducts = computed(() => {
  let result = products.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(product =>
      product.name.toLowerCase().includes(query) ||
      product.sku.toLowerCase().includes(query)
    )
  }

  // 分类过滤
  if (selectedCategory.value) {
    result = result.filter(product => product.category_id === selectedCategory.value)
  }

  return result
})

const totalProducts = computed(() => filteredProducts.value.length)

// 方法
const loadProducts = async () => {
  loading.value = true
  try {
    const response = await api.get('/products/')
    products.value = response.data.products || []
  } catch (error) {
    ElMessage.error('加载商品列表失败')
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const response = await api.get('/categories/')
    categories.value = response.data.categories || []
  } catch (error) {
    ElMessage.error('加载分类列表失败')
  }
}

const loadSuppliers = async () => {
  try {
    const response = await api.get('/suppliers/')
    suppliers.value = response.data.suppliers || []
  } catch (error) {
    ElMessage.error('加载供应商列表失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

const showEditDialog = (product: Product) => {
  isEdit.value = true
  dialogVisible.value = true
  form.value = {
    product_id: product.product_id,
    name: product.name,
    sku: product.sku,
    description: product.description,
    category_id: product.category_id,
    supplier_id: product.supplier_id
  }
}

const resetForm = () => {
  form.value = {
    product_id: 0,
    name: '',
    sku: '',
    description: '',
    category_id: null,
    supplier_id: null
  }
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await api.put(`/products/${form.value.product_id}`, form.value)
          ElMessage.success('商品更新成功')
        } else {
          await api.post('/products/', form.value)
          ElMessage.success('商品创建成功')
        }
        dialogVisible.value = false
        await loadProducts()
      } catch (error) {
        ElMessage.error(isEdit.value ? '商品更新失败' : '商品创建失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (product: Product) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除商品 "${product.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/products/${product.product_id}`)
    ElMessage.success('商品删除成功')
    await loadProducts()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('商品删除失败')
    }
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleCategoryFilter = () => {
  currentPage.value = 1
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(async () => {
  await Promise.all([
    loadProducts(),
    loadCategories(),
    loadSuppliers()
  ])
})
</script>

<style scoped>
.product-management {
  padding: 0;
}

.chart-section {
  margin-bottom: 24px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  text-align: right;
}

@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    gap: 12px;
  }
  
  .table-toolbar-left {
    flex-direction: column;
    align-items: stretch;
  }
  
  .table-toolbar-left .el-input,
  .table-toolbar-left .el-select {
    width: 100% !important;
  }
}
</style> 