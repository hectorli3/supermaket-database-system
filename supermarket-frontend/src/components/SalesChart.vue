<template>
  <div class="sales-chart">
    <div class="chart-header">
      <div class="chart-title-section">
        <h3 class="chart-title">近5天销售趋势</h3>
        <span class="chart-subtitle" v-if="chartSubtitle">{{ chartSubtitle }}</span>
      </div>
      <el-button 
        type="primary" 
        size="small" 
        :icon="Refresh" 
        @click="refreshChart"
        :loading="loading"
      >
        刷新
      </el-button>
    </div>
    <div 
      ref="chartRef" 
      class="chart-container"
      v-loading="loading"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

interface SalesTrendData {
  date: string
  label: string
  value: number
  percentage: number
}

const chartRef = ref<HTMLDivElement>()
const loading = ref(false)
const chartSubtitle = ref('')
const authStore = useAuthStore()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  // 初始化空图表
  const option = {
    title: {
      text: '销售额 (¥)',
      left: 'left',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal',
        color: '#666'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50,50,50,0.9)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#fff'
      },
      formatter: function(params: any) {
        const data = params[0]
        return `${data.name}<br/>销售额: ¥${data.value.toLocaleString()}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [],
      axisLine: {
        lineStyle: {
          color: '#e1e6f0'
        }
      },
      axisLabel: {
        color: '#666'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#666',
        formatter: (value: number) => `¥${value.toLocaleString()}`
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: '#409EFF',
          width: 3
        },
        itemStyle: {
          color: '#409EFF',
          borderColor: '#fff',
          borderWidth: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(64, 158, 255, 0.3)'
            },
            {
              offset: 1,
              color: 'rgba(64, 158, 255, 0.1)'
            }
          ])
        },
        data: []
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const loadSalesData = async () => {
  loading.value = true
  try {
    const response = await api.get('/dashboard/stats')
    
    // 根据用户角色设置图表副标题
    const userRole = authStore.user?.role
    if (userRole === 'system_admin') {
      chartSubtitle.value = '(全部门店数据)'
    } else {
      chartSubtitle.value = '(本门店数据)'
    }
    
    const salesTrend = response.data.salesTrend || []
    
    // 只取最近5天的数据
    const last5Days = salesTrend.slice(-5)
    
    if (chartInstance && last5Days.length > 0) {
      const dates = last5Days.map((item: SalesTrendData) => item.label)
      const values = last5Days.map((item: SalesTrendData) => item.value)
      
      chartInstance.setOption({
        xAxis: {
          data: dates
        },
        series: [
          {
            data: values
          }
        ]
      })
    }
  } catch (error) {
    console.error('加载销售数据失败:', error)
    ElMessage.error('加载销售趋势数据失败')
  } finally {
    loading.value = false
  }
}

const refreshChart = () => {
  loadSalesData()
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(async () => {
  await nextTick()
  initChart()
  loadSalesData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.sales-chart {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.chart-title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chart-subtitle {
  font-size: 12px;
  color: #666;
  font-weight: normal;
}

.chart-container {
  width: 100%;
  height: 300px;
  min-height: 300px;
}
</style> 