<template>
  <div class="index-page">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="指数列表" name="list">
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
                  ({{ formatPercent(index.volume_change_percent) }})
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
                      {{ formatPercent(row.volume_change_percent) }}
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
      </el-tab-pane>

      <el-tab-pane label="日K线图" name="kline">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>重要大盘指数日K线图</span>
              <div class="header-actions">
                <el-select
                  v-model="selectedIndexCode"
                  placeholder="选择指数"
                  size="small"
                  style="width: 200px"
                  @change="handleKlineIndexChange"
                >
                  <el-option
                    v-for="index in mainIndices"
                    :key="index.index_code"
                    :label="`${index.index_name} (${index.index_code})`"
                    :value="index.index_code"
                  />
                </el-select>
                <el-date-picker
                  v-model="klineDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  size="small"
                  @change="handleKlineDateChange"
                />
                <el-button type="primary" size="small" :loading="klineLoading" @click="fetchKlineData">查询</el-button>
              </div>
            </div>
          </template>

          <div v-loading="klineLoading" class="kline-container">
            <div v-if="klineData && klineData.length > 0" class="kline-chart-wrapper">
              <v-chart class="kline-chart" :option="klineChartOption" autoresize />
            </div>
            <el-empty v-else description="请选择指数和日期范围查询K线数据" />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { indexApi, type IndexKlineItem } from '@/api/index'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'
import { filterMainIndices } from '@/utils/indexFilter'
import dayjs from 'dayjs'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  CandlestickChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent,
])

const activeTab = ref('list')
const date = ref(dayjs().format('YYYY-MM-DD'))
const loading = ref(false)
const indexData = ref<any[]>([])
const showAll = ref(false) // 是否显示所有指数
const indexCode = ref('')

// K线图相关
const selectedIndexCode = ref('')
const klineDateRange = ref<[string, string] | null>([
  dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD'),
])
const klineLoading = ref(false)
const klineData = ref<IndexKlineItem[]>([])

// 主要/全部指数列表
const summaryIndices = computed(() => (showAll.value ? indexData.value : filterMainIndices(indexData.value)))
const mainIndices = computed(() => filterMainIndices(indexData.value))
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

const handleTabChange = (tab: string) => {
  if (tab === 'kline') {
    // 如果还没有加载指数列表，先加载
    if (indexData.value.length === 0) {
      fetchData().then(() => {
        // 加载完成后，如果没有选择指数，默认选择第一个主要指数
        const main = mainIndices.value
        if (main.length > 0 && !selectedIndexCode.value) {
          selectedIndexCode.value = main[0].index_code
          fetchKlineData()
        }
      })
    } else if (!selectedIndexCode.value) {
      // 如果已经有数据但没有选择指数，默认选择第一个主要指数
      const main = mainIndices.value
      if (main.length > 0) {
        selectedIndexCode.value = main[0].index_code
        fetchKlineData()
      }
    }
  }
}

const handleKlineIndexChange = () => {
  if (selectedIndexCode.value && klineDateRange.value) {
    fetchKlineData()
  }
}

const handleKlineDateChange = () => {
  if (selectedIndexCode.value && klineDateRange.value) {
    fetchKlineData()
  }
}

const fetchKlineData = async () => {
  if (!selectedIndexCode.value || !klineDateRange.value) {
    ElMessage.warning('请选择指数和日期范围')
    return
  }

  klineLoading.value = true
  try {
    const [startDate, endDate] = klineDateRange.value
    klineData.value = await indexApi.getKline(selectedIndexCode.value, startDate, endDate)
    
    if (klineData.value.length === 0) {
      ElMessage.warning('未获取到K线数据')
    }
  } catch (error) {
    ElMessage.error('获取K线数据失败')
    console.error(error)
  } finally {
    klineLoading.value = false
  }
}

// K线图配置
const klineChartOption = computed(() => {
  if (!klineData.value || klineData.value.length === 0) {
    return {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
      },
    }
  }

  const dates = klineData.value.map(item => item?.date || '').filter(Boolean)
  const values = klineData.value.map(item => [
    item?.open || 0,
    item?.close || 0,
    item?.low || 0,
    item?.high || 0,
  ])
  const volumes = klineData.value.map(item => item?.volume || 0)

  // 找到当前选择的指数名称
  const selectedIndex = indexData.value?.find(idx => idx.index_code === selectedIndexCode.value)
  const indexName = selectedIndex?.index_name || selectedIndexCode.value || '指数'

  return {
    title: {
      text: `${indexName} 日K线图`,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
      formatter: (params: any) => {
        if (!params || !Array.isArray(params) || params.length === 0) {
          return ''
        }
        const param = params[0]
        if (!param || typeof param.dataIndex !== 'number') {
          return ''
        }
        const data = klineData.value[param.dataIndex]
        if (!data) return ''
        return `
          <div style="margin-bottom: 4px;"><strong>${data.date || ''}</strong></div>
          <div>开盘: ${formatPrice(data.open)}</div>
          <div>收盘: ${formatPrice(data.close)}</div>
          <div>最高: ${formatPrice(data.high)}</div>
          <div>最低: ${formatPrice(data.low)}</div>
          <div>成交量: ${formatVolume(data.volume)}</div>
        `
      },
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        top: '15%',
        height: '50%',
      },
      {
        left: '10%',
        right: '8%',
        top: '70%',
        height: '15%',
      },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
      },
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true,
        },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '90%',
        start: 0,
        end: 100,
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#f56c6c',
          color0: '#67c23a',
          borderColor: '#f56c6c',
          borderColor0: '#67c23a',
        },
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: (params: any) => {
            if (!params || typeof params.dataIndex !== 'number') {
              return '#999'
            }
            const data = klineData.value[params.dataIndex]
            if (!data || data.open === null || data.open === undefined || 
                data.close === null || data.close === undefined) {
              return '#999'
            }
            return data.close >= data.open ? '#f56c6c' : '#67c23a'
          },
        },
      },
    ],
  }
})

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

.kline-container {
  min-height: 500px;
}

.kline-chart-wrapper {
  width: 100%;
  height: 600px;
}

.kline-chart {
  width: 100%;
  height: 100%;
}
</style>

