<template>
  <div class="pos-system">
    <div class="pos-header">
      <h2>收银台</h2>
      <div class="pos-info">
        <span>收银员: {{ authStore.user?.username }}</span>
        <span>时间: {{ currentTime }}</span>
      </div>
    </div>

    <el-row :gutter="20" class="pos-content">
      <!-- 商品选择区域 -->
      <el-col :span="14">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">商品选择</h3>
            <el-input
              v-model="searchQuery"
              placeholder="搜索商品名称、SKU或扫描条码"
              :prefix-icon="Search"
              clearable
              style="width: 300px"
              @keyup.enter="addProductBySearch"
            />
          </div>
          
          <div class="card-body">
            <div class="product-grid">
              <div
                v-for="product in filteredProducts"
                :key="product.product_id"
                class="product-card"
                :class="{ 'has-promotion': product.has_promotion }"
                @click="addProduct(product)"
              >
                <div class="product-name">{{ product.name }}</div>
                <div class="product-price">
                  <span v-if="product.has_promotion" class="original-price">¥{{ product.original_price }}</span>
                  <span class="current-price" :class="{ 'promotion-price': product.has_promotion }">
                    ¥{{ product.price.toFixed(2) }}
                  </span>
                  <span v-if="product.has_promotion" class="promotion-tag">促销</span>
                </div>
                <div class="product-stock">库存: {{ product.stock }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 购物车区域 -->
      <el-col :span="10">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">购物车</h3>
            <el-button type="danger" size="small" @click="clearCart">
              清空
            </el-button>
          </div>
          
          <div class="card-body">
            <div class="cart-items">
              <div
                v-for="(item, index) in cartItems"
                :key="index"
                class="cart-item"
              >
                <div class="item-info">
                  <div class="item-name">
                    {{ item.name }}
                    <span v-if="item.has_promotion" class="cart-promotion-tag">促销</span>
                  </div>
                  <div class="item-price">
                    <span v-if="item.has_promotion" class="original-price-small">¥{{ item.original_price }}</span>
                    ¥{{ item.price.toFixed(2) }}
                  </div>
                </div>
                <div class="item-controls">
                  <el-input-number
                    v-model="item.quantity"
                    :min="1"
                    :max="item.stock"
                    size="small"
                    @change="updateItemTotal(item)"
                  />
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="removeItem(index)"
                  />
                </div>
                <div class="item-total">¥{{ item.total.toFixed(2) }}</div>
              </div>
            </div>
            
            <div class="cart-summary">
              <div class="summary-row">
                <span>商品总数:</span>
                <span>{{ totalQuantity }}</span>
              </div>
              <div class="summary-row total">
                <span>总金额:</span>
                <span>¥{{ totalAmount.toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="cart-actions">
              <el-button
                type="primary"
                size="large"
                :disabled="cartItems.length === 0"
                @click="checkout"
                style="width: 100%"
              >
                结算
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import { Search, Delete } from '@element-plus/icons-vue'

interface Product {
  product_id: number
  name: string
  price: number
  original_price: number
  has_promotion: boolean
  stock: number
  sku?: string
}

interface CartItem {
  product_id: number
  name: string
  price: number
  original_price: number
  has_promotion: boolean
  quantity: number
  stock: number
  total: number
}

const authStore = useAuthStore()

const searchQuery = ref('')
const products = ref<Product[]>([])
const cartItems = ref<CartItem[]>([])
const currentTime = ref('')

let timeInterval: NodeJS.Timeout

const filteredProducts = computed(() => {
  if (!searchQuery.value) return products.value
  const query = searchQuery.value.toLowerCase()
  
  // 调试搜索逻辑
  const filtered = products.value.filter(product => {
    const nameMatch = product.name.toLowerCase().includes(query)
    const skuMatch = product.sku && product.sku.toLowerCase().includes(query)
    
    if (query.length > 0) {
      console.log(`搜索 "${query}":`, {
        产品: product.name,
        SKU: product.sku,
        名称匹配: nameMatch,
        SKU匹配: skuMatch,
        最终匹配: nameMatch || skuMatch
      })
    }
    
    return nameMatch || skuMatch
  })
  
  return filtered
})

const totalQuantity = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
})

const totalAmount = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + item.total, 0)
})

const loadProducts = async () => {
  try {
    const response = await api.get('/inventory/')
    const inventory = response.data.inventory || []
    
    products.value = inventory.map((item: any) => ({
      product_id: item.product_id,
      name: item.product_name,
      price: parseFloat(item.price),
      original_price: parseFloat(item.original_price || item.price),
      has_promotion: item.has_promotion || false,
      stock: item.quantity,
      sku: item.product_sku || ''
    }))
    
    // 调试SKU数据
    console.log('前3个商品的SKU数据:', products.value.slice(0, 3).map(p => ({
      name: p.name,
      sku: p.sku,
      raw_sku: inventory.find((item: any) => item.product_id === p.product_id)?.product_sku
    })))
  } catch (error) {
    ElMessage.error('加载商品失败')
  }
}

const addProduct = (product: Product) => {
  if (product.stock <= 0) {
    ElMessage.warning('商品库存不足')
    return
  }

  const existingItem = cartItems.value.find(item => item.product_id === product.product_id)
  
  if (existingItem) {
    if (existingItem.quantity < product.stock) {
      existingItem.quantity++
      updateItemTotal(existingItem)
    } else {
      ElMessage.warning('库存不足')
    }
  } else {
    cartItems.value.push({
      product_id: product.product_id,
      name: product.name,
      price: product.price,
      original_price: product.original_price,
      has_promotion: product.has_promotion,
      quantity: 1,
      stock: product.stock,
      total: product.price
    })
  }
}

const addProductBySearch = () => {
  const query = searchQuery.value.toLowerCase()
  const product = filteredProducts.value.find(p => 
    p.name.toLowerCase() === query ||
    (p.sku && p.sku.toLowerCase() === query)
  )
  
  if (product) {
    addProduct(product)
    searchQuery.value = ''
  } else {
    ElMessage.warning('未找到商品')
  }
}

const updateItemTotal = (item: CartItem) => {
  item.total = item.price * item.quantity
}

const removeItem = (index: number) => {
  cartItems.value.splice(index, 1)
}

const clearCart = () => {
  cartItems.value = []
}

const checkout = async () => {
  if (cartItems.value.length === 0) {
    ElMessage.warning('购物车为空')
    return
  }

  try {
    // 获取当前用户的门店ID，如果没有则默认为1
    const userStoreId = authStore.user?.store_id || 1
    
    const saleData = {
      store_id: userStoreId,
      items: cartItems.value.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.price
      }))
    }

    await api.post('/sales/', saleData)
    ElMessage.success('结算成功')
    clearCart()
    await loadProducts() // 重新加载库存
  } catch (error) {
    ElMessage.error('结算失败')
  }
}

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

onMounted(() => {
  loadProducts()
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.pos-system {
  padding: 0;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.pos-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.pos-header h2 {
  margin: 0;
  color: #1890ff;
}

.pos-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #666;
}

.pos-content {
  flex: 1;
  overflow: hidden;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.product-card {
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.product-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.product-card.has-promotion {
  border-color: #ff4d4f;
  background: linear-gradient(135deg, #fff2f0 0%, #ffffff 100%);
}

.product-card.has-promotion:hover {
  border-color: #ff4d4f;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.3);
}

.product-name {
  font-weight: 500;
  margin-bottom: 8px;
}

.product-price {
  color: #f56565;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.original-price {
  font-size: 14px;
  color: #999;
  text-decoration: line-through;
  font-weight: normal;
}

.current-price.promotion-price {
  color: #ff4d4f;
}

.promotion-tag {
  background: #ff4d4f;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: normal;
}

.product-stock {
  color: #666;
  font-size: 12px;
}

.cart-items {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.cart-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.item-price {
  color: #666;
  font-size: 14px;
}

.item-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 16px;
}

.item-total {
  font-weight: bold;
  color: #f56565;
  min-width: 80px;
  text-align: right;
}

.cart-summary {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
  margin-bottom: 20px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.summary-row.total {
  font-size: 18px;
  font-weight: bold;
  color: #f56565;
}

.cart-actions {
  margin-top: 20px;
}

.cart-promotion-tag {
  background: #ff4d4f;
  color: white;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 2px;
  margin-left: 8px;
}

.original-price-small {
  font-size: 12px;
  color: #999;
  text-decoration: line-through;
  margin-right: 4px;
}

@media (max-width: 1200px) {
  .product-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}

@media (max-width: 768px) {
  .pos-content .el-col {
    margin-bottom: 20px;
  }
  
  .product-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
  
  .cart-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .item-controls {
    margin: 0;
  }
}
</style> 