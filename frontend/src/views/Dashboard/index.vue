<template>
  <div class="dashboard">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>今日概览</span>
          <el-date-picker
            v-model="date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
            size="small"
          />
        </div>
      </template>

      <div v-loading="loading" class="stats-container">
        <!-- 大盘指数 -->
        <el-card class="stat-card" shadow="hover">
          <template #header>
            <span>大盘指数</span>
          </template>
          <div class="index-list">
            <div
              v-for="index in mainIndices"
              :key="index.index_code"
              class="index-item"
            >
              <div class="index-name">{{ index.index_name }}</div>
              <div class="index-price">{{ formatPrice(index.close_price) }}</div>
              <div
                class="index-change"
                :class="{
                  'positive': (index.change_percent || 0) > 0,
                  'negative': (index.change_percent || 0) < 0,
                }"
              >
                {{ formatPercent(index.change_percent) }}
              </div>
            </div>
          </div>
        </el-card>

        <!-- 统计数据 -->
        <div class="stats-grid">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-label">涨停个股</div>
              <div class="stat-value highlight">{{ stats.ztPoolCount }}</div>
            </div>
          </el-card>

          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-label">跌停个股</div>
              <div class="stat-value negative">{{ stats.ztPoolDownCount }}</div>
            </div>
          </el-card>

          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-label">上涨板块</div>
              <div class="stat-value positive">{{ stats.sectorStats.riseCount }}</div>
            </div>
          </el-card>

          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-label">下跌板块</div>
              <div class="stat-value negative">{{ stats.sectorStats.fallCount }}</div>
            </div>
          </el-card>
        </div>

      </div>

    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  User,
  DataLine,
  Grid,
  Money,
} from '@element-plus/icons-vue'
import { dashboardApi } from '@/api/dashboard'
import { formatPercent, formatPrice } from '@/utils/format'
import { filterMainIndices } from '@/utils/indexFilter'
import dayjs from 'dayjs'

const router = useRouter()

const date = ref(dayjs().format('YYYY-MM-DD'))
const loading = ref(false)
const indexData = ref<any[]>([])
const stats = ref({
  ztPoolCount: 0,
  ztPoolDownCount: 0,
  sectorStats: {
    riseCount: 0,
    fallCount: 0,
    totalCount: 0,
  },
})

// 过滤后的主要指数数据
const mainIndices = computed(() => filterMainIndices(indexData.value))

const fetchData = async () => {
  loading.value = true
  try {
    const data = await dashboardApi.getStats(date.value)
    indexData.value = data.indexData
    stats.value = {
      ztPoolCount: data.ztPoolCount,
      ztPoolDownCount: data.ztPoolDownCount,
      sectorStats: data.sectorStats,
    }
  } catch (error) {
    ElMessage.error('获取数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleDateChange = () => {
  fetchData()
}

const goToPage = (path: string) => {
  router.push(path)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-container {
  margin-bottom: 20px;
}

.index-list {
  display: flex;
  flex-wrap: nowrap;
  gap: 12px;
  overflow-x: auto;
}

.index-item {
  flex: 0 0 auto;
  min-width: 120px;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  white-space: nowrap;
}

.index-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.index-price {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}

.index-change {
  font-size: 14px;
}

.index-change.positive {
  color: #f56c6c;
}

.index-change.negative {
  color: #67c23a;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  text-align: center;
  padding: 20px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-value.highlight {
  color: #409eff;
}

.stat-value.positive {
  color: #f56c6c;
}

.stat-value.negative {
  color: #67c23a;
}

.quick-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.quick-actions h3 {
  margin-bottom: 16px;
  color: #303133;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>

