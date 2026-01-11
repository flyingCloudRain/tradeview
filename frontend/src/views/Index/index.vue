<template>
  <div class="index-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>大盘指数</span>
          <div class="header-actions">
            <el-switch
              v-model="showAll"
              active-text="显示全部"
              inactive-text="主要指数"
              @change="handleDateChange"
            />
            <el-date-picker
              v-model="date"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleDateChange"
              size="small"
            />
            <el-input
              v-model="indexCode"
              placeholder="按代码筛选"
              size="small"
              clearable
              style="width: 180px"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" size="small" :loading="loading" @click="handleSearch">查询</el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="index-container">
        <el-row :gutter="16" class="summary-row">
          <el-col
            v-for="index in summaryIndices"
            :key="index.index_code"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <el-card class="index-card" shadow="hover">
              <div class="index-name">{{ index.index_name }}</div>
              <div class="index-code">{{ index.index_code }}</div>
              <div class="index-price">{{ formatPrice(index.close_price) }}</div>
              <div
                class="index-change"
                :class="{
                  positive: (index.change_percent || 0) > 0,
                  negative: (index.change_percent || 0) < 0,
                }"
              >
                {{ formatPercent(index.change_percent) }}
              </div>
              <div class="index-volume" v-if="index.volume">
                成交量: {{ formatVolume(index.volume) }}
                <span v-if="index.volume_change_percent !== null && index.volume_change_percent !== undefined" 
                      :class="{
                        'volume-change': true,
                        'positive': index.volume_change_percent > 0,
                        'negative': index.volume_change_percent < 0,
                      }">
                  ({{ index.volume_change_percent > 0 ? '+' : '' }}{{ formatPercent(index.volume_change_percent) }})
                </span>
              </div>
              <div class="index-amount" v-if="index.amount">
                成交额: {{ formatAmount(index.amount) }}
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-table :data="tableData" stripe border style="margin-top: 12px">
          <el-table-column prop="index_code" label="代码" width="120" />
          <el-table-column prop="index_name" label="名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="close_price" label="收盘价" width="120" align="right">
            <template #default="{ row }">{{ formatPrice(row.close_price) }}</template>
          </el-table-column>
          <el-table-column prop="change_percent" label="涨跌幅" width="110" align="right" sortable>
            <template #default="{ row }">
              <span
                :class="{
                  positive: (row.change_percent || 0) > 0,
                  negative: (row.change_percent || 0) < 0,
                }"
              >
                {{ formatPercent(row.change_percent) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="volume" label="成交量" width="200" align="right">
            <template #default="{ row }">
              <div>
                <div>{{ formatVolume(row.volume) }}</div>
                <div v-if="row.volume_change_percent !== null && row.volume_change_percent !== undefined" 
                     :class="{
                       'volume-change': true,
                       'positive': row.volume_change_percent > 0,
                       'negative': row.volume_change_percent < 0,
                     }"
                     style="font-size: 12px; margin-top: 4px;">
                  {{ row.volume_change_percent > 0 ? '+' : '' }}{{ formatPercent(row.volume_change_percent) }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="成交额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { indexApi } from '@/api/index'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'
import { filterMainIndices } from '@/utils/indexFilter'
import dayjs from 'dayjs'

const date = ref(dayjs().format('YYYY-MM-DD'))
const loading = ref(false)
const indexData = ref<any[]>([])
const showAll = ref(false) // 是否显示所有指数
const indexCode = ref('')

// 主要/全部指数列表
const summaryIndices = computed(() => (showAll.value ? indexData.value : filterMainIndices(indexData.value)))
const tableData = computed(() => {
  if (indexCode.value) {
    const kw = indexCode.value.trim()
    return indexData.value.filter(
      (item: any) => item.index_code?.includes(kw) || item.index_name?.includes(kw),
    )
  }
  return indexData.value
})

const formatVolume = (volume: number | undefined) => {
  if (!volume) return '-'
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = { date: date.value }
    if (indexCode.value) params.index_code = indexCode.value.trim()
    indexData.value = await indexApi.getList(params)
  } catch (error) {
    ElMessage.error('获取指数数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleDateChange = () => {
  fetchData()
}

const handleSearch = () => {
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.index-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.index-container {
  min-height: 200px;
}

.index-card {
  margin-bottom: 20px;
  text-align: center;
}

.index-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.index-code {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.index-price {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.index-change {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
}

.index-change.positive {
  color: #f56c6c;
}

.index-change.negative {
  color: #67c23a;
}

.index-volume {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.volume-change {
  font-weight: bold;
  margin-left: 4px;
}

.volume-change.positive {
  color: #f56c6c;
}

.volume-change.negative {
  color: #67c23a;
}
</style>

