<template>
  <div class="sale-management">
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">销售管理</h3>
        <el-button 
          v-if="hasPermission('pos_system', 'view')"
          type="primary" 
          :icon="Plus" 
          @click="$router.push('/pos')"
        >
          前往收银台
        </el-button>
      </div>
      <div class="card-body">
        <el-table :data="sales" v-loading="loading" stripe>
          <el-table-column prop="sale_id" label="ID" width="80" />
          <el-table-column prop="store_name" label="门店" width="120" />
          <el-table-column prop="cashier_name" label="收银员" width="120" />
          <el-table-column prop="total_amount" label="总金额" width="120">
            <template #default="{ row }">
              ¥{{ row.total_amount }}
            </template>
          </el-table-column>
          <el-table-column prop="sale_timestamp" label="销售时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.sale_timestamp) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                :icon="View"
                @click="showDetails(row)"
              >
                详情
              </el-button>
              <el-button 
                v-if="hasPermission('sales_management', 'delete')"
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

    <!-- 销售详情对话框 -->
    <el-dialog v-model="detailsVisible" title="销售详情" width="800px">
      <div v-if="selectedSale">
        <h4>基本信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="销售ID">{{ selectedSale.sale_id }}</el-descriptions-item>
          <el-descriptions-item label="门店">{{ selectedSale.store_name }}</el-descriptions-item>
          <el-descriptions-item label="收银员">{{ selectedSale.cashier_name || selectedSale.user_name }}</el-descriptions-item>
          <el-descriptions-item label="总金额">¥{{ selectedSale.total_amount }}</el-descriptions-item>
          <el-descriptions-item label="销售时间">{{ formatDate(selectedSale.sale_timestamp) }}</el-descriptions-item>
        </el-descriptions>
        
        <h4 style="margin-top: 20px;">商品明细</h4>
        <el-table :data="saleItems" stripe>
          <el-table-column prop="product_name" label="商品名称" min-width="150" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="unit_price" label="单价" width="100">
            <template #default="{ row }">
              ¥{{ row.unit_price }}
            </template>
          </el-table-column>
          <el-table-column prop="subtotal" label="小计" width="100">
            <template #default="{ row }">
              ¥{{ row.subtotal }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { Plus, View, Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { hasPermission } = authStore

interface Sale {
  sale_id: number
  store_name: string
  user_name: string
  cashier_name: string
  total_amount: number
  sale_date: string
  sale_timestamp: string
}

interface SaleItem {
  product_name: string
  quantity: number
  unit_price: number
  subtotal: number
}

const loading = ref(false)
const detailsVisible = ref(false)
const sales = ref<Sale[]>([])
const selectedSale = ref<Sale | null>(null)
const saleItems = ref<SaleItem[]>([])

const loadSales = async () => {
  loading.value = true
  try {
    const response = await api.get('/sales/')
    sales.value = response.data.sales || []
    
    // 调试：打印前几条数据的时间字段
    if (sales.value.length > 0) {
      console.log('🔍 销售数据调试:')
      sales.value.slice(0, 3).forEach((sale, index) => {
        console.log(`  记录 ${index + 1}:`, {
          sale_id: sale.sale_id,
          sale_date: sale.sale_date,
          sale_timestamp: sale.sale_timestamp,
          store_name: sale.store_name,
          user_name: sale.user_name,
          cashier_name: sale.cashier_name
        })
      })
    }
  } catch (error) {
    console.error('加载销售列表失败:', error)
    ElMessage.error('加载销售列表失败')
  } finally {
    loading.value = false
  }
}

const showDetails = async (sale: Sale) => {
  selectedSale.value = sale
  detailsVisible.value = true
  
  try {
    const response = await api.get(`/sales/${sale.sale_id}/items`)
    saleItems.value = response.data.items || []
  } catch (error) {
    ElMessage.error('加载销售详情失败')
  }
}

const handleDelete = async (sale: Sale) => {
  try {
    await ElMessageBox.confirm(`确定要删除销售记录 #${sale.sale_id} 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/sales/${sale.sale_id}`)
    ElMessage.success('销售记录删除成功')
    await loadSales()
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || '销售记录删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  try {
    // 尝试多种时间格式
    let date: Date
    
    // 如果是ISO 8601格式（包含T和时区信息）
    if (dateString.includes('T')) {
      date = new Date(dateString)
    } 
    // 如果是标准的 YYYY-MM-DD HH:mm:ss 格式
    else if (dateString.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
      date = new Date(dateString.replace(' ', 'T'))
    }
    // 其他格式
    else {
      date = new Date(dateString)
    }
    
    if (isNaN(date.getTime())) {
      console.warn('无效的日期格式:', dateString)
      return dateString // 返回原始字符串
    }
    
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  } catch (error) {
    console.error('日期格式化错误:', error, 'dateString:', dateString)
    return dateString || '-'
  }
}

onMounted(() => {
  loadSales()
})
</script>

<style scoped>
.sale-management {
  padding: 0;
}
</style> 