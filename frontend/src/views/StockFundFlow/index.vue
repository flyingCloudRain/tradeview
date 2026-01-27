<template>
  <div class="fund-flow-page">
    <el-tabs v-model="activeTab" class="fund-flow-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="个股资金流" name="stock">
        <div class="section-card">
          <el-card>
            <div class="filter-bar">
              <el-date-picker
                v-model="startDate"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateRangeChange"
                style="width: 200px"
              />
              <span class="date-separator">至</span>
              <el-date-picker
                v-model="endDate"
                type="date"
                placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledEndDate"
                @change="handleDateRangeChange"
                style="width: 200px"
              />
              <el-input
                v-model="stockCode"
                placeholder="股票代码"
                clearable
                style="width: 200px"
                @clear="handleSearch"
              />
              <el-input
                v-model="stockName"
                placeholder="股票名称"
                clearable
                style="width: 200px"
                @clear="handleSearch"
              />
              <el-input-number
                v-model="consecutiveDays"
                :min="1"
                :precision="0"
                placeholder="连续N日"
                clearable
                style="width: 120px"
              />
              <span class="field-separator">净流入>M</span>
              <el-input-number
                v-model="minNetInflowDisplay"
                :min="0"
                :precision="2"
                :step="0.1"
                placeholder="最小值(亿)"
                clearable
                style="width: 140px"
                @change="convertNetInflowToYuan"
              />
              <span class="unit-label">亿元</span>
              <el-select
                v-model="isLimitUp"
                placeholder="是否涨停"
                clearable
                style="width: 150px"
              >
                <el-option label="全部" :value="undefined" />
                <el-option label="仅涨停" :value="true" />
                <el-option label="仅非涨停" :value="false" />
              </el-select>
              <el-select
                v-model="isWatched"
                placeholder="是否关注"
                clearable
                style="width: 150px"
              >
                <el-option label="全部" :value="undefined" />
                <el-option label="仅关注" :value="true" />
                <el-option label="仅未关注" :value="false" />
              </el-select>
              <el-button type="primary" @click="handleSearch" :loading="loading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
            </div>

            <!-- 跨日期查询时显示表格/折线图切换 -->
            <el-tabs 
              v-if="isDateRangeQuery" 
              v-model="stockSubTab" 
              class="stock-sub-tabs" 
              @tab-change="handleStockSubTabChange"
            >
              <el-tab-pane label="表格视图" name="table">
                <el-table
                  :data="tableData"
                  :loading="loading"
                  stripe
                  border
                  :default-sort="defaultSort"
                  @sort-change="handleSortChange"
                  @expand-change="handleStockExpandChange"
                >
              <el-table-column type="expand" width="50">
                <template #default="{ row }">
                  <div class="history-container">
                    <div class="history-header">
                      <span class="history-title">{{ row.stock_name }}({{ row.stock_code }}) 每日净流入详情</span>
                      <el-button
                        v-if="stockHistoryLoadingMap[row.stock_code]"
                        :loading="true"
                        size="small"
                        type="primary"
                      >
                        加载中...
                      </el-button>
                    </div>
                    <el-table
                      :data="stockHistoryDataMap[row.stock_code] || []"
                      stripe
                      border
                      size="small"
                      v-if="stockHistoryDataMap[row.stock_code] && stockHistoryDataMap[row.stock_code].length > 0"
                    >
                      <el-table-column prop="date" label="日期" width="120" align="center" />
                      <el-table-column prop="main_net_inflow" label="主力净流入(亿元)" width="150" align="right">
                        <template #default="{ row: historyRow }">
                          <span
                            :style="{
                              color: (historyRow.main_net_inflow || 0) > 0 ? 'red' : 'green',
                            }"
                          >
                            {{ formatAmount(historyRow.main_net_inflow) }}
                          </span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="main_inflow" label="主力流入(亿元)" width="150" align="right">
                        <template #default="{ row: historyRow }">
                          <span style="color: red">{{ formatAmount(historyRow.main_inflow) }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="main_outflow" label="主力流出(亿元)" width="150" align="right">
                        <template #default="{ row: historyRow }">
                          <span style="color: green">{{ formatAmount(historyRow.main_outflow) }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="current_price" label="最新价" width="100" align="right">
                        <template #default="{ row: historyRow }">
                          {{ formatPrice(historyRow.current_price) }}
                        </template>
                      </el-table-column>
                      <el-table-column prop="change_percent" label="涨幅(%)" width="120" align="right">
                        <template #default="{ row: historyRow }">
                          <span :style="{ color: (historyRow.change_percent || 0) > 0 ? 'red' : 'green' }">
                            {{ formatPercent(historyRow.change_percent) }}
                          </span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="turnover_rate" label="换手率(%)" width="120" align="right" />
                      <el-table-column prop="is_limit_up" label="是否涨停" width="100" align="center">
                        <template #default="{ row: historyRow }">
                          <el-tag v-if="historyRow.is_limit_up" type="danger" size="small">涨停</el-tag>
                          <span v-else>-</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="is_lhb" label="是否龙虎榜" width="110" align="center">
                        <template #default="{ row: historyRow }">
                          <el-tag v-if="historyRow.is_lhb" type="warning" size="small">龙虎榜</el-tag>
                          <span v-else>-</span>
                        </template>
                      </el-table-column>
                    </el-table>
                    <el-empty
                      v-else-if="!stockHistoryLoadingMap[row.stock_code]"
                      description="暂无历史数据"
                      :image-size="80"
                    />
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="stock_code" label="股票代码" width="120" />
              <el-table-column prop="stock_name" label="股票名称" width="150" />
              <el-table-column label="操作" width="100" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    link
                    type="primary"
                    size="small"
                    @click="handleAddToWatchlist(row.stock_code)"
                  >
                    <el-icon><Plus /></el-icon>
                    关注
                  </el-button>
                </template>
              </el-table-column>
              <el-table-column
                prop="current_price"
                label="最新价"
                width="100"
                align="right"
              >
                <template #default="{ row }">
                  {{ formatPrice(row.current_price) }}
                </template>
              </el-table-column>
              <el-table-column
                prop="main_net_inflow"
                label="主力净流入(亿元)"
                width="150"
                sortable="custom"
                align="right"
              >
                <template #default="{ row }">
                  <span
                    :style="{
                      color: (row.main_net_inflow || 0) > 0 ? 'red' : 'green',
                    }"
                  >
                    {{ formatAmount(row.main_net_inflow) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="main_inflow"
                label="主力流入(亿元)"
                width="150"
                sortable="custom"
                align="right"
              >
                <template #default="{ row }">
                  <span style="color: red">{{ formatAmount(row.main_inflow) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="main_outflow"
                label="主力流出(亿元)"
                width="150"
                sortable="custom"
                align="right"
              >
                <template #default="{ row }">
                  <span style="color: green">{{ formatAmount(row.main_outflow) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="turnover_rate"
                label="换手率(%)"
                width="120"
                sortable="custom"
                align="right"
              />
              <el-table-column
                prop="change_percent"
                label="涨幅(%)"
                width="120"
                sortable="custom"
                align="right"
              >
                <template #default="{ row }">
                  <span :style="{ color: (row.change_percent || 0) > 0 ? 'red' : 'green' }">
                    {{ formatPercent(row.change_percent) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="is_limit_up"
                label="是否涨停"
                width="100"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag v-if="row.is_limit_up" type="danger" size="small">涨停</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="is_lhb"
                label="是否龙虎榜"
                width="110"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag v-if="row.is_lhb" type="warning" size="small">龙虎榜</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>

                <el-pagination
                  v-model:current-page="pagination.current"
                  v-model:page-size="pagination.pageSize"
                  :total="pagination.total"
                  :page-sizes="[10, 20, 50, 100]"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleSizeChange"
                  @current-change="handlePageChange"
                  style="margin-top: 20px; justify-content: flex-end"
                />
              </el-tab-pane>
              <el-tab-pane label="折线图" name="chart">
                <div v-if="stockChartData.length > 0" class="chart-container">
                  <v-chart 
                    class="stock-chart" 
                    :option="stockChartOption" 
                    autoresize
                    v-loading="stockChartLoading"
                  />
                </div>
                <el-empty v-else description="暂无数据，请先查询" />
              </el-tab-pane>
            </el-tabs>

            <!-- 单日期查询时只显示表格 -->
            <template v-else>
              <el-table
                :data="tableData"
                :loading="loading"
                stripe
                border
                :default-sort="defaultSort"
                @sort-change="handleSortChange"
              >
                <el-table-column prop="stock_code" label="股票代码" width="120" />
                <el-table-column prop="stock_name" label="股票名称" width="150" />
                <el-table-column label="操作" width="100" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      link
                      type="primary"
                      size="small"
                      @click="handleAddToWatchlist(row.stock_code)"
                    >
                      <el-icon><Plus /></el-icon>
                      关注
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="current_price"
                  label="最新价"
                  width="100"
                  align="right"
                >
                  <template #default="{ row }">
                    {{ formatPrice(row.current_price) }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="main_net_inflow"
                  label="主力净流入(亿元)"
                  width="150"
                  sortable="custom"
                  align="right"
                >
                  <template #default="{ row }">
                    <span
                      :style="{
                        color: (row.main_net_inflow || 0) > 0 ? 'red' : 'green',
                      }"
                    >
                      {{ formatAmount(row.main_net_inflow) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="main_inflow"
                  label="主力流入(亿元)"
                  width="150"
                  sortable="custom"
                  align="right"
                >
                  <template #default="{ row }">
                    <span style="color: red">{{ formatAmount(row.main_inflow) }}</span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="main_outflow"
                  label="主力流出(亿元)"
                  width="150"
                  sortable="custom"
                  align="right"
                >
                  <template #default="{ row }">
                    <span style="color: green">{{ formatAmount(row.main_outflow) }}</span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="turnover_rate"
                  label="换手率(%)"
                  width="120"
                  sortable="custom"
                  align="right"
                />
                <el-table-column
                  prop="change_percent"
                  label="涨幅(%)"
                  width="120"
                  sortable="custom"
                  align="right"
                >
                  <template #default="{ row }">
                    <span :style="{ color: (row.change_percent || 0) > 0 ? 'red' : 'green' }">
                      {{ formatPercent(row.change_percent) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="is_limit_up"
                  label="是否涨停"
                  width="100"
                  align="center"
                >
                  <template #default="{ row }">
                    <el-tag v-if="row.is_limit_up" type="danger" size="small">涨停</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="is_lhb"
                  label="是否龙虎榜"
                  width="110"
                  align="center"
                >
                  <template #default="{ row }">
                    <el-tag v-if="row.is_lhb" type="warning" size="small">龙虎榜</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
              </el-table>

              <el-pagination
                v-model:current-page="pagination.current"
                v-model:page-size="pagination.pageSize"
                :total="pagination.total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
                style="margin-top: 20px; justify-content: flex-end"
              />
            </template>
          </el-card>
        </div>
      </el-tab-pane>
      <el-tab-pane label="关注个股资金流" name="watched">
        <div class="section-card">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>关注个股资金流</span>
                <div>
                  <el-input
                    v-model="watchlistStockCode"
                    placeholder="输入股票代码"
                    clearable
                    style="width: 150px; margin-right: 10px"
                    @keyup.enter="handleAddToWatchlist(watchlistStockCode)"
                  />
                  <el-button type="primary" size="small" @click="handleAddToWatchlist(watchlistStockCode)">
                    <el-icon><Plus /></el-icon>
                    添加关注
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    :disabled="watchlistStore.stocks.length === 0"
                    @click="handleClearWatchlist"
                    style="margin-left: 10px"
                  >
                    清空列表
                  </el-button>
                </div>
              </div>
            </template>
            <div class="filter-bar">
              <el-date-picker
                v-model="watchedStartDate"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleWatchedDateRangeChange"
                style="width: 200px"
              />
              <span class="date-separator">至</span>
              <el-date-picker
                v-model="watchedEndDate"
                type="date"
                placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledWatchedEndDate"
                @change="handleWatchedDateRangeChange"
                style="width: 200px"
              />
              <el-select
                v-model="watchedIsLimitUp"
                placeholder="是否涨停"
                clearable
                style="width: 150px"
              >
                <el-option label="全部" :value="undefined" />
                <el-option label="仅涨停" :value="true" />
                <el-option label="仅非涨停" :value="false" />
              </el-select>
              <el-button type="primary" @click="handleWatchedSearch" :loading="watchedLoading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <span v-if="watchlistStore.stocks.length > 0" class="watchlist-info">
                已关注 {{ watchlistStore.stocks.length }} 只股票
              </span>
            </div>

            <el-empty v-if="watchlistStore.stocks.length === 0" description="暂无关注股票，请先添加关注" />

            <div v-else>
              <!-- 表格/折线图切换 -->
              <el-tabs 
                v-model="watchedSubTab" 
                class="watched-sub-tabs" 
                @tab-change="handleWatchedSubTabChange"
              >
                <el-tab-pane label="表格视图" name="table">
                  <!-- 日期选择器：选择要显示的交易日 -->
                  <div class="date-selector-bar" style="margin-bottom: 16px;">
                    <el-checkbox-group 
                      v-model="watchedSelectedDates" 
                      @change="handleWatchedDateSelectionChange"
                      style="display: inline-flex; flex-wrap: wrap; gap: 8px;"
                    >
                      <el-checkbox 
                        v-for="date in availableTradingDates" 
                        :key="date"
                        :label="date"
                        :value="date"
                      >
                        {{ formatTableDateLabel(date) }}
                      </el-checkbox>
                    </el-checkbox-group>
                    <el-button 
                      type="primary" 
                      size="small" 
                      style="margin-left: 12px"
                      @click="handleSelectAllDates"
                    >
                      全选
                    </el-button>
                    <el-button 
                      size="small" 
                      style="margin-left: 8px"
                      @click="handleClearDateSelection"
                    >
                      清空
                    </el-button>
                  </div>

                  <!-- 表格视图：个股为行，交易日为列 -->
                  <el-table
                    :data="watchedTableData"
                    :loading="watchedLoading"
                    stripe
                    border
                    style="width: 100%"
                    max-height="600"
                  >
                    <el-table-column prop="stock_code" label="股票代码" width="120" fixed="left" />
                    <el-table-column prop="stock_name" label="股票名称" width="120" fixed="left" />
                    <el-table-column 
                      v-for="date in watchedSelectedDatesSorted" 
                      :key="date"
                      :label="formatTableDateLabel(date)"
                      width="140"
                      align="right"
                    >
                      <template #default="{ row }">
                        <span :class="getNetInflowClass(row[date])">
                          {{ formatNetInflow(row[date]) }}
                        </span>
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-empty v-if="watchedTableData.length === 0 && !watchedLoading" description="请选择交易日并查询数据" />
                </el-tab-pane>
                <el-tab-pane label="折线图" name="chart">
                  <div class="chart-container">
                    <v-chart 
                      class="watched-chart" 
                      :option="watchedChartOption" 
                      autoresize
                      v-loading="watchedLoading"
                    />
                    <el-empty v-if="watchedChartData.length === 0 && !watchedLoading" description="暂无数据，请先查询" />
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { Search, Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFundFlowStore } from '@/stores/fundFlow'
import { useWatchlistStore } from '@/stores/watchlist'
import { fundFlowApi } from '@/api/fundFlow'
import dayjs from 'dayjs'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'
import type { FundFlowItem } from '@/api/fundFlow'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const fundFlowStore = useFundFlowStore()
const watchlistStore = useWatchlistStore()

const activeTab = ref('stock')

// 计算最近10个交易日的日期范围（往前推约20天，确保包含10个交易日）
const getLast10TradingDaysRange = () => {
  const end = dayjs()
  // 往前推约20天，确保包含10个交易日（考虑周末和节假日）
  const start = end.subtract(20, 'day')
  return {
    start: start.format('YYYY-MM-DD'),
    end: end.format('YYYY-MM-DD')
  }
}

const dateRange = getLast10TradingDaysRange()
const startDate = ref(dateRange.start)
const endDate = ref(dateRange.end)
const stockCode = ref('')
const stockName = ref('')
const consecutiveDays = ref<number | undefined>(undefined)
const minNetInflowDisplay = ref<number | undefined>(undefined)
const minNetInflow = ref<number | undefined>(undefined)
const isLimitUp = ref<boolean | undefined>(undefined)
const isWatched = ref<boolean | undefined>(undefined)

// 个股资金流子tab和折线图相关状态
const stockSubTab = ref('table') // table=表格视图, chart=折线图
const stockChartData = ref<FundFlowItem[]>([]) // 折线图每日数据
const stockChartLoading = ref(false)

// 关注个股资金流相关状态
const watchedDateRange = getLast10TradingDaysRange()
const watchedStartDate = ref(watchedDateRange.start)
const watchedEndDate = ref(watchedDateRange.end)
const watchedLoading = ref(false)
const watchedChartData = ref<FundFlowItem[]>([]) // 折线图数据
const watchlistStockCode = ref('')
const watchedIsLimitUp = ref<boolean | undefined>(undefined)
const watchedSubTab = ref('table') // table=表格视图, chart=折线图
const watchedSelectedDates = ref<string[]>([]) // 选择的交易日列表
const watchedTableData = ref<Record<string, any>[]>([]) // 表格数据

// 历史数据相关状态（关注个股资金流）
const historyDataMap = ref<Record<string, FundFlowItem[]>>({})
const historyLoadingMap = ref<Record<string, boolean>>({})
const historyRequestMap = ref<Record<string, Promise<FundFlowItem[]>>>({}) // 请求去重

// 个股资金流每日详情数据相关状态
const stockHistoryDataMap = ref<Record<string, FundFlowItem[]>>({})
const stockHistoryLoadingMap = ref<Record<string, boolean>>({})
const stockHistoryRequestMap = ref<Record<string, Promise<FundFlowItem[]>>>({}) // 请求去重

// 过滤后的数据
const filteredData = computed(() => {
  let data = fundFlowStore.list
  
  // 根据是否关注筛选
  if (isWatched.value !== undefined) {
    data = data.filter((item) => {
      const isInWatchlist = watchlistStore.isWatched(item.stock_code)
      return isWatched.value ? isInWatchlist : !isInWatchlist
    })
  }
  
  return data
})

// 分页后的数据
const tableData = computed(() => {
  const data = filteredData.value
  const currentPage = pagination.value.current
  const pageSize = pagination.value.pageSize
  const start = (currentPage - 1) * pageSize
  const end = start + pageSize
  return data.slice(start, end)
})

const loading = computed(() => fundFlowStore.loading)

// 更新后的分页信息
const pagination = computed(() => {
  const basePagination = fundFlowStore.pagination
  if (isWatched.value !== undefined) {
    // 使用"是否关注"筛选时，使用过滤后的总数
    return {
      ...basePagination,
      total: filteredData.value.length,
    }
  }
  return basePagination
})

// 判断是否为跨日期查询
const isDateRangeQuery = computed(() => {
  return startDate.value && endDate.value && startDate.value !== endDate.value
})

const convertNetInflowToYuan = () => {
  if (minNetInflowDisplay.value === undefined || minNetInflowDisplay.value === null) {
    minNetInflow.value = undefined
    return
  }
  // 将亿元转换为元
  minNetInflow.value = Math.round(minNetInflowDisplay.value * 100000000)
}

const fetchData = async () => {
  // 确保净流入值已转换
  if (minNetInflowDisplay.value !== undefined && minNetInflowDisplay.value !== null) {
    convertNetInflowToYuan()
  }
  
  // 使用日期范围查询
  if (!startDate.value || !endDate.value) {
    ElMessage.warning('请选择开始日期和结束日期')
    return
  }
  
  // 如果使用"是否关注"筛选，需要获取所有数据以便前端过滤和分页
  if (isWatched.value !== undefined) {
    // 获取所有数据
    let page = 1
    const allData: FundFlowItem[] = []
    
    while (true) {
      const response = await fundFlowApi.getList({
        start_date: startDate.value,
        end_date: endDate.value,
        stock_code: stockCode.value || undefined,
        stock_name: stockName.value || undefined,
        consecutive_days: consecutiveDays.value || undefined,
        min_net_inflow: minNetInflow.value || undefined,
        is_limit_up: isLimitUp.value,
        page: page,
        page_size: 100,
      })
      
      if (response.items && response.items.length > 0) {
        allData.push(...response.items)
        
        if (response.items.length < 100 || (response.total_pages && page >= response.total_pages)) {
          break
        }
        page++
      } else {
        break
      }
    }
    
    // 更新store中的数据
    fundFlowStore.list = allData
  } else {
    // 不使用"是否关注"筛选时，使用正常分页
    await fundFlowStore.fetchList({
      start_date: startDate.value,
      end_date: endDate.value,
      stock_code: stockCode.value || undefined,
      stock_name: stockName.value || undefined,
      consecutive_days: consecutiveDays.value || undefined,
      min_net_inflow: minNetInflow.value || undefined,
      is_limit_up: isLimitUp.value,
    })
  }
  
  // 如果当前在折线图视图，更新折线图数据
  if (isDateRangeQuery.value && stockSubTab.value === 'chart') {
    fetchStockChartData()
  }
}

const handleDateRangeChange = () => {
  // 清除每日详情数据缓存，以便重新加载
  stockHistoryDataMap.value = {}
  stockHistoryLoadingMap.value = {}
  stockHistoryRequestMap.value = {}
  fetchData()
}

const disabledEndDate = (date: Date) => {
  if (!startDate.value) return false
  return dayjs(date).isBefore(dayjs(startDate.value))
}

const handleSearch = () => {
  // 清除每日详情数据缓存
  stockHistoryDataMap.value = {}
  stockHistoryLoadingMap.value = {}
  stockHistoryRequestMap.value = {}
  fundFlowStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

// 监听是否关注筛选条件变化，重置分页
watch(() => isWatched.value, () => {
  fundFlowStore.setPagination(1, pagination.value.pageSize)
})

const handleSizeChange = () => {
  // 如果使用"是否关注"筛选，不需要重新获取数据，只需要重新分页
  if (isWatched.value !== undefined) {
    // 前端分页，不需要重新请求
    return
  }
  fetchData()
}

const handlePageChange = () => {
  // 如果使用"是否关注"筛选，不需要重新获取数据，只需要重新分页
  if (isWatched.value !== undefined) {
    // 前端分页，不需要重新请求
    return
  }
  fetchData()
}

onMounted(async () => {
  try {
    await fetchData()
  } catch (error) {
    console.error('初始化个股资金流失败:', error)
  }
})

// 个股资金流排序
const defaultSort = computed(() => {
  const { sort_by, order } = fundFlowStore.sortParams
  if (!sort_by) return undefined
  return {
    prop: sort_by,
    order: order === 'asc' ? 'ascending' : 'descending',
  }
})

const handleSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (!sort.prop || !sort.order) {
    // 清除排序
    fundFlowStore.setSortParams(undefined, 'desc')
  } else {
    const order = sort.order === 'ascending' ? 'asc' : 'desc'
    fundFlowStore.setSortParams(
      sort.prop as 'main_inflow' | 'main_outflow' | 'main_net_inflow' | 'turnover_rate' | 'change_percent',
      order
    )
  }
  fetchData()
}

// 关注个股资金流相关方法
const handleTabChange = (tabName: string) => {
  if (tabName === 'watched' && watchlistStore.stocks.length > 0) {
    fetchWatchedData()
  }
}

const fetchWatchedData = async () => {
  if (watchlistStore.stocks.length === 0) {
    watchedChartData.value = []
    return
  }

  if (!watchedStartDate.value || !watchedEndDate.value) {
    ElMessage.warning('请选择开始日期和结束日期')
    return
  }

  watchedLoading.value = true
  try {
    // 获取所有关注股票的每日资金流数据（用于折线图）
    const allDailyData: FundFlowItem[] = []
    const stockCodes = watchlistStore.stocks
    
    // 逐个查询每个股票的每日数据
    for (const stockCode of stockCodes) {
      try {
        // 使用 getHistory API 获取每日数据
        const response = await fundFlowApi.getHistory(
          stockCode,
          watchedStartDate.value,
          watchedEndDate.value
        )
        
        const dataArray = Array.isArray(response) ? response : []
        
        // 如果指定了涨停筛选，过滤数据
        if (watchedIsLimitUp.value !== undefined) {
          const filteredData = dataArray.filter(item => item.is_limit_up === watchedIsLimitUp.value)
          allDailyData.push(...filteredData)
        } else {
          allDailyData.push(...dataArray)
        }
      } catch (error) {
        console.error(`获取股票 ${stockCode} 的每日数据失败:`, error)
        // 继续查询其他股票
      }
    }

    // 按日期和股票代码排序
    allDailyData.sort((a, b) => {
      if (a.date && b.date) {
        const dateCompare = a.date.localeCompare(b.date)
        if (dateCompare !== 0) return dateCompare
      }
      if (a.stock_code && b.stock_code) {
        return a.stock_code.localeCompare(b.stock_code)
      }
      return 0
    })

    watchedChartData.value = allDailyData
    
    // 如果当前是表格视图且没有选择日期，自动选择所有可用交易日
    if (watchedSubTab.value === 'table' && watchedSelectedDates.value.length === 0 && availableTradingDates.value.length > 0) {
      watchedSelectedDates.value = [...availableTradingDates.value]
      handleUpdateWatchedTable()
    }
  } catch (error) {
    console.error('获取关注个股资金流失败:', error)
    ElMessage.error('获取关注个股资金流失败')
    watchedChartData.value = []
  } finally {
    watchedLoading.value = false
  }
}

const handleWatchedDateRangeChange = () => {
  if (activeTab.value === 'watched') {
    fetchWatchedData()
  }
}

const disabledWatchedEndDate = (date: Date) => {
  if (!watchedStartDate.value) return false
  return dayjs(date).isBefore(dayjs(watchedStartDate.value))
}

const handleWatchedSearch = () => {
  fetchWatchedData()
  // 如果当前是表格视图，也更新表格
  if (watchedSubTab.value === 'table') {
    handleUpdateWatchedTable()
  }
}

const handleWatchedSubTabChange = (tabName: string) => {
  if (tabName === 'table') {
    // 如果切换到表格视图且没有选择日期，自动选择所有可用交易日
    if (watchedSelectedDates.value.length === 0 && availableTradingDates.value.length > 0) {
      watchedSelectedDates.value = [...availableTradingDates.value]
    }
    handleUpdateWatchedTable()
  }
}

// 获取可用的交易日列表（从查询结果中提取）
const availableTradingDates = computed(() => {
  if (watchedChartData.value.length === 0) return []
  const dates = new Set<string>()
  watchedChartData.value.forEach(item => {
    if (item.date) {
      dates.add(item.date)
    }
  })
  return Array.from(dates).sort()
})

// 日期选择变化处理
const handleWatchedDateSelectionChange = () => {
  handleUpdateWatchedTable()
}

// 全选日期
const handleSelectAllDates = () => {
  watchedSelectedDates.value = [...availableTradingDates.value]
  handleUpdateWatchedTable()
}

// 清空日期选择
const handleClearDateSelection = () => {
  watchedSelectedDates.value = []
  watchedTableData.value = []
}

// 更新表格数据
const handleUpdateWatchedTable = () => {
  if (watchedSelectedDates.value.length === 0) {
    ElMessage.warning('请先选择要显示的交易日')
    return
  }
  
  if (watchedChartData.value.length === 0) {
    ElMessage.warning('请先查询数据')
    return
  }
  
  // 按股票代码分组数据
  const dataByStock: Record<string, Record<string, FundFlowItem>> = {}
  watchedChartData.value.forEach((item) => {
    if (!item.stock_code || !item.date) return
    
    if (!dataByStock[item.stock_code]) {
      dataByStock[item.stock_code] = {}
    }
    dataByStock[item.stock_code][item.date] = item
  })
  
  // 构建表格数据：每行是一个股票，列是选择的交易日
  const tableRows: Record<string, any>[] = []
  Object.entries(dataByStock).forEach(([stockCode, dateMap]) => {
    const firstItem = Object.values(dateMap)[0]
    const row: Record<string, any> = {
      stock_code: stockCode,
      stock_name: firstItem?.stock_name || stockCode,
    }
    
    // 为每个选择的日期添加净流入数据
    watchedSelectedDates.value.forEach(date => {
      const item = dateMap[date]
      row[date] = item?.main_net_inflow || null
    })
    
    tableRows.push(row)
  })
  
  // 按股票代码排序
  tableRows.sort((a, b) => a.stock_code.localeCompare(b.stock_code))
  
  watchedTableData.value = tableRows
}

// 排序后的选择日期列表
const watchedSelectedDatesSorted = computed(() => {
  return [...watchedSelectedDates.value].sort()
})

// 格式化表格日期标签
const formatTableDateLabel = (dateStr: string) => {
  if (!dateStr) return ''
  const date = dayjs(dateStr)
  return date.format('MM-DD')
}

// 格式化净流入显示
const formatNetInflow = (value: number | null) => {
  if (value === null || value === undefined) return '-'
  if (value >= 100000000) {
    return `${(value / 100000000).toFixed(2)}亿`
  } else if (value >= 10000) {
    return `${(value / 10000).toFixed(2)}万`
  }
  return value.toFixed(2)
}

// 获取净流入样式类
const getNetInflowClass = (value: number | null) => {
  if (value === null || value === undefined) return ''
  if (value > 0) return 'net-inflow-positive'
  if (value < 0) return 'net-inflow-negative'
  return ''
}

const handleAddToWatchlist = (code: string) => {
  if (!code || code.trim() === '') {
    ElMessage.warning('请输入股票代码')
    return
  }

  const stockCode = code.trim()
  if (watchlistStore.addStock(stockCode)) {
    ElMessage.success(`已添加 ${stockCode} 到关注列表`)
    watchlistStockCode.value = ''
    
    // 如果在关注标签页，刷新数据
    if (activeTab.value === 'watched') {
      fetchWatchedData()
    }
  } else {
    ElMessage.warning(`${stockCode} 已在关注列表中`)
  }
}

const handleRemoveFromWatchlist = (code: string) => {
  if (watchlistStore.removeStock(code)) {
    ElMessage.success(`已取消关注 ${code}`)
    
    // 如果在关注标签页，刷新数据
    if (activeTab.value === 'watched') {
      fetchWatchedData()
    }
  }
}

const handleClearWatchlist = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有关注股票吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    watchlistStore.clearWatchlist()
    ElMessage.success('已清空关注列表')
    watchedTableData.value = []
    watchedPagination.value.total = 0
  } catch {
    // 用户取消
  }
}

// 监听关注列表变化，如果在关注标签页则刷新数据
watch(() => watchlistStore.stocks, () => {
  if (activeTab.value === 'watched') {
    fetchWatchedData()
  }
}, { deep: true })

// 获取股票近15个交易日的历史数据
const fetchStockHistory = async (stockCode: string) => {
  // 如果已经加载过，不再重复加载
  if (historyDataMap.value[stockCode]) {
    return
  }

  // 如果正在请求中，等待现有请求完成（请求去重）
  if (historyRequestMap.value[stockCode]) {
    try {
      const data = await historyRequestMap.value[stockCode]
      historyDataMap.value[stockCode] = data
      return
    } catch (error) {
      // 如果请求失败，继续执行新的请求
      console.error(`等待中的请求失败:`, error)
    }
  }

  historyLoadingMap.value[stockCode] = true
  
  // 创建请求Promise并缓存，避免重复请求
  const requestPromise = (async () => {
    try {
      // 优化：计算更精确的日期范围
      // 从结束日期往前推约20个交易日（约30天，考虑周末和节假日）
      // 这样可以减少查询的数据量，提高性能
      const endDate = dayjs(watchedEndDate.value || dayjs().format('YYYY-MM-DD'))
      const startDate = endDate.subtract(20, 'day') // 减少到20天，足够获取15个交易日

      const response = await fundFlowApi.getHistory(
        stockCode,
        startDate.format('YYYY-MM-DD'),
        endDate.format('YYYY-MM-DD')
      )

      // 确保response是数组
      const dataArray = Array.isArray(response) ? response : []
      
      // 按日期倒序排序，取前15条
      const sortedData = dataArray
        .sort((a, b) => {
          if (!a.date || !b.date) return 0
          return b.date.localeCompare(a.date)
        })
        .slice(0, 15)

      return sortedData
    } catch (error) {
      console.error(`获取股票 ${stockCode} 的历史数据失败:`, error)
      ElMessage.error(`获取股票 ${stockCode} 的历史数据失败`)
      return []
    }
  })()

  // 缓存请求Promise
  historyRequestMap.value[stockCode] = requestPromise

  try {
    const sortedData = await requestPromise
    historyDataMap.value[stockCode] = sortedData
  } finally {
    historyLoadingMap.value[stockCode] = false
    // 请求完成后清除Promise缓存（保留数据缓存）
    delete historyRequestMap.value[stockCode]
  }
}

// 处理表格展开事件（关注个股资金流）
const handleExpandChange = (row: FundFlowItem, expandedRows: FundFlowItem[]) => {
  if (expandedRows.includes(row)) {
    // 展开时加载历史数据
    fetchStockHistory(row.stock_code)
  }
}

// 处理个股资金流表格展开事件
const handleStockExpandChange = (row: FundFlowItem, expandedRows: FundFlowItem[]) => {
  if (expandedRows.includes(row)) {
    // 展开时加载该股票在查询日期范围内的每日数据
    fetchStockDailyDetail(row.stock_code)
  }
}

// 获取个股资金流每日详情数据（根据查询的日期范围）
const fetchStockDailyDetail = async (stockCode: string) => {
  // 如果已经加载过，不再重复加载
  if (stockHistoryDataMap.value[stockCode]) {
    return
  }

  // 如果正在请求中，等待现有请求完成（请求去重）
  if (stockHistoryRequestMap.value[stockCode]) {
    try {
      const data = await stockHistoryRequestMap.value[stockCode]
      stockHistoryDataMap.value[stockCode] = data
      return
    } catch (error) {
      // 如果请求失败，继续执行新的请求
      console.error(`等待中的请求失败:`, error)
    }
  }

  if (!startDate.value || !endDate.value) {
    return
  }

  stockHistoryLoadingMap.value[stockCode] = true
  
  // 创建请求Promise并缓存，避免重复请求
  const requestPromise = (async () => {
    try {
      const response = await fundFlowApi.getHistory(
        stockCode,
        startDate.value,
        endDate.value
      )

      // 确保response是数组
      const dataArray = Array.isArray(response) ? response : []
      
      // 按日期倒序排序
      const sortedData = dataArray.sort((a, b) => {
        if (!a.date || !b.date) return 0
        return b.date.localeCompare(a.date)
      })

      return sortedData
    } catch (error) {
      console.error(`获取股票 ${stockCode} 的每日详情失败:`, error)
      ElMessage.error(`获取股票 ${stockCode} 的每日详情失败`)
      return []
    }
  })()

  // 缓存请求Promise
  stockHistoryRequestMap.value[stockCode] = requestPromise

  try {
    const sortedData = await requestPromise
    stockHistoryDataMap.value[stockCode] = sortedData
  } finally {
    stockHistoryLoadingMap.value[stockCode] = false
    // 请求完成后清除Promise缓存（保留数据缓存）
    delete stockHistoryRequestMap.value[stockCode]
  }
}


// 处理个股资金流子tab切换
const handleStockSubTabChange = (tabName: string) => {
  if (tabName === 'chart') {
    fetchStockChartData()
  }
}

// 获取个股资金流折线图数据（每日数据）
const fetchStockChartData = async () => {
  if (!startDate.value || !endDate.value) {
    return
  }

  stockChartLoading.value = true
  try {
    // 获取所有匹配的股票代码
    const stockCodes = new Set<string>()
    
    // 如果有指定股票代码，只查询该股票
    if (stockCode.value) {
      stockCodes.add(stockCode.value)
    } else {
      // 否则需要获取所有匹配的股票代码（分页获取所有数据）
      // 先获取第一页数据，获取总页数，然后获取所有页的数据
      let page = 1
      const pageSize = 100 // 使用较大的页面大小
      let allStockCodes = new Set<string>()
      
      while (true) {
        try {
          const response = await fundFlowApi.getList({
            start_date: startDate.value,
            end_date: endDate.value,
            stock_code: stockCode.value || undefined,
            stock_name: stockName.value || undefined,
            consecutive_days: consecutiveDays.value || undefined,
            min_net_inflow: minNetInflow.value || undefined,
            is_limit_up: isLimitUp.value,
            page: page,
            page_size: pageSize,
          })
          
          if (response.items && response.items.length > 0) {
            response.items.forEach((item: FundFlowItem) => {
              if (item.stock_code) {
                allStockCodes.add(item.stock_code)
              }
            })
            
            // 如果返回的数据少于pageSize，说明已经是最后一页
            if (response.items.length < pageSize) {
              break
            }
            
            // 如果总页数已到达，停止分页
            if (response.total_pages && page >= response.total_pages) {
              break
            }
            
            page++
          } else {
            break
          }
        } catch (error) {
          console.error(`获取股票列表失败 (page ${page}):`, error)
          break
        }
      }
      
      stockCodes = allStockCodes
    }

    if (stockCodes.size === 0) {
      stockChartData.value = []
      return
    }

    // 获取每个股票的每日数据
    const allDailyData: FundFlowItem[] = []
    
    console.log(`开始获取 ${stockCodes.size} 个股票的每日数据，日期范围: ${startDate.value} 至 ${endDate.value}`)
    
    for (const code of stockCodes) {
      try {
        const response = await fundFlowApi.getHistory(
          code,
          startDate.value,
          endDate.value
        )
        
        const dataArray = Array.isArray(response) ? response : []
        console.log(`股票 ${code} 获取到 ${dataArray.length} 条每日数据`)
        
        if (dataArray.length > 0) {
          // 验证数据是否包含日期字段
          const dates = dataArray.map(item => item.date).filter(Boolean)
          console.log(`股票 ${code} 的日期范围: ${dates[0]} 至 ${dates[dates.length - 1]}, 共 ${dates.length} 个交易日`)
        }
        
        allDailyData.push(...dataArray)
      } catch (error) {
        console.error(`获取股票 ${code} 的每日数据失败:`, error)
      }
    }

    console.log(`总共获取到 ${allDailyData.length} 条每日数据`)

    // 按日期和股票代码排序
    allDailyData.sort((a, b) => {
      if (a.date && b.date) {
        const dateCompare = a.date.localeCompare(b.date)
        if (dateCompare !== 0) return dateCompare
      }
      if (a.stock_code && b.stock_code) {
        return a.stock_code.localeCompare(b.stock_code)
      }
      return 0
    })

    // 统计所有唯一的日期
    const uniqueDates = new Set(allDailyData.map(item => item.date).filter(Boolean))
    console.log(`折线图将显示 ${uniqueDates.size} 个交易日的数据:`, Array.from(uniqueDates).sort())

    stockChartData.value = allDailyData
  } catch (error) {
    console.error('获取折线图数据失败:', error)
    ElMessage.error('获取折线图数据失败')
    stockChartData.value = []
  } finally {
    stockChartLoading.value = false
  }
}

// 个股资金流折线图配置
const stockChartOption = computed(() => {
  if (!stockChartData.value || stockChartData.value.length === 0) {
    return {
      title: {
        text: '个股资金流趋势',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        data: [],
        top: 30,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: [],
        name: '日期',
      },
      yAxis: {
        type: 'value',
        name: '主力净流入(亿元)',
      },
      series: [],
    }
  }

  // 按股票代码分组数据
  const dataByStock: Record<string, FundFlowItem[]> = {}
  stockChartData.value.forEach((item) => {
    if (!dataByStock[item.stock_code]) {
      dataByStock[item.stock_code] = []
    }
    dataByStock[item.stock_code].push(item)
  })

  // 获取所有日期并排序
  const allDates = new Set<string>()
  Object.values(dataByStock).forEach((items) => {
    items.forEach((item) => {
      if (item.date) {
        allDates.add(item.date)
      }
    })
  })
  const sortedDates = Array.from(allDates).sort()
  
  // 格式化日期显示：根据日期数量和跨度决定显示格式
  const formatDateLabel = (dateStr: string) => {
    if (!dateStr) return ''
    const date = dayjs(dateStr)
    
    // 计算日期跨度
    if (sortedDates.length > 0) {
      const firstDate = dayjs(sortedDates[0])
      const lastDate = dayjs(sortedDates[sortedDates.length - 1])
      const daysDiff = lastDate.diff(firstDate, 'day')
      
      // 如果日期跨度超过30天或日期数量>15，使用 MM-DD 格式
      if (daysDiff > 30 || sortedDates.length > 15) {
        return date.format('MM-DD')
      }
    }
    
    // 默认使用完整日期格式
    return date.format('YYYY-MM-DD')
  }

  // 生成系列数据
  const series = Object.entries(dataByStock).map(([stockCode, items]) => {
    const stockName = items[0]?.stock_name || stockCode
    // 按日期排序
    const sortedItems = [...items].sort((a, b) => {
      if (!a.date || !b.date) return 0
      return a.date.localeCompare(b.date)
    })

    // 创建日期到数据的映射
    const dataMap = new Map<string, FundFlowItem>()
    sortedItems.forEach((item) => {
      if (item.date) {
        dataMap.set(item.date, item)
      }
    })

    // 生成数据点
    const data = sortedDates.map((date) => {
      const item = dataMap.get(date)
      if (item && item.main_net_inflow !== undefined && item.main_net_inflow !== null) {
        // 转换为亿元，返回数字类型
        return Number((item.main_net_inflow / 100000000).toFixed(2))
      }
      return null
    })

    return {
      name: `${stockName}(${stockCode})`,
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2,
      },
    }
  })

  return {
    title: {
      text: '个股资金流 - 主力净流入趋势',
      left: 'center',
      top: 10,
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        // 格式化日期显示
        const dateValue = params[0]?.axisValue || ''
        const formattedDate = dateValue ? dayjs(dateValue).format('YYYY-MM-DD') : ''
        let result = `<div style="margin-bottom: 4px; font-weight: bold;">${formattedDate}</div>`
        params.forEach((param: any) => {
          const value = param.value
          if (value !== null && value !== undefined) {
            const numValue = parseFloat(value)
            const formattedValue = numValue >= 0 
              ? `<span style="color: red;">+${numValue.toFixed(2)}亿</span>`
              : `<span style="color: green;">${numValue.toFixed(2)}亿</span>`
            result += `<div>${param.marker} ${param.seriesName}: ${formattedValue}</div>`
          } else {
            result += `<div>${param.marker} ${param.seriesName}: -</div>`
          }
        })
        return result
      },
    },
    legend: {
      data: series.map((s) => s.name),
      top: 40,
      type: 'scroll',
      orient: 'horizontal',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      name: '日期',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        rotate: 45,
        interval: 0,
        formatter: (value: string) => {
          return formatDateLabel(value)
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '主力净流入(亿元)',
      axisLabel: {
        formatter: (value: number) => {
          if (value >= 0) {
            return `+${value.toFixed(2)}`
          }
          return value.toFixed(2)
        },
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
        },
      },
    },
    series: series,
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 20,
        bottom: 10,
      },
    ],
  }
})

// 关注个股资金流折线图配置
const watchedChartOption = computed(() => {
  if (!watchedChartData.value || watchedChartData.value.length === 0) {
    return {
      title: {
        text: '关注个股资金流',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        data: [],
        top: 30,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: [],
      },
      yAxis: {
        type: 'value',
        name: '主力净流入(亿元)',
        axisLabel: {
          formatter: (value: number) => {
            if (value >= 100000000) {
              return `${(value / 100000000).toFixed(2)}亿`
            } else if (value >= 10000) {
              return `${(value / 10000).toFixed(2)}万`
            }
            return value.toFixed(2)
          },
        },
      },
      series: [],
    }
  }

  // 按股票代码分组数据
  const dataByStock: Record<string, FundFlowItem[]> = {}
  watchedChartData.value.forEach((item) => {
    if (!dataByStock[item.stock_code]) {
      dataByStock[item.stock_code] = []
    }
    dataByStock[item.stock_code].push(item)
  })

  // 获取所有日期并排序
  const allDates = new Set<string>()
  Object.values(dataByStock).forEach((items) => {
    items.forEach((item) => {
      if (item.date) {
        allDates.add(item.date)
      }
    })
  })
  const sortedDates = Array.from(allDates).sort()
  
  // 格式化日期显示：根据日期数量和跨度决定显示格式
  const formatDateLabel = (dateStr: string) => {
    if (!dateStr) return ''
    const date = dayjs(dateStr)
    
    // 计算日期跨度
    if (sortedDates.length > 0) {
      const firstDate = dayjs(sortedDates[0])
      const lastDate = dayjs(sortedDates[sortedDates.length - 1])
      const daysDiff = lastDate.diff(firstDate, 'day')
      
      // 如果日期跨度超过30天或日期数量>15，使用 MM-DD 格式
      if (daysDiff > 30 || sortedDates.length > 15) {
        return date.format('MM-DD')
      }
    }
    
    // 默认使用完整日期格式
    return date.format('YYYY-MM-DD')
  }

  // 生成系列数据
  const series = Object.entries(dataByStock).map(([stockCode, items]) => {
    const stockName = items[0]?.stock_name || stockCode
    // 按日期排序
    const sortedItems = [...items].sort((a, b) => {
      if (!a.date || !b.date) return 0
      return a.date.localeCompare(b.date)
    })

    // 创建日期到数据的映射
    const dataMap = new Map<string, FundFlowItem>()
    sortedItems.forEach((item) => {
      if (item.date) {
        dataMap.set(item.date, item)
      }
    })

    // 生成数据点
    const data = sortedDates.map((date) => {
      const item = dataMap.get(date)
      if (item && item.main_net_inflow !== undefined && item.main_net_inflow !== null) {
        // 转换为亿元，返回数字类型
        return Number((item.main_net_inflow / 100000000).toFixed(2))
      }
      return null
    })

    return {
      name: `${stockName}(${stockCode})`,
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2,
      },
    }
  })

  return {
    title: {
      text: '关注个股资金流 - 主力净流入趋势',
      left: 'center',
      top: 10,
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        // 格式化日期显示
        const dateValue = params[0]?.axisValue || ''
        const formattedDate = dateValue ? dayjs(dateValue).format('YYYY-MM-DD') : ''
        let result = `<div style="margin-bottom: 4px; font-weight: bold;">${formattedDate}</div>`
        params.forEach((param: any) => {
          const value = param.value
          if (value !== null && value !== undefined) {
            const numValue = parseFloat(value)
            const formattedValue = numValue >= 0 
              ? `<span style="color: red;">+${numValue.toFixed(2)}亿</span>`
              : `<span style="color: green;">${numValue.toFixed(2)}亿</span>`
            result += `<div>${param.marker} ${param.seriesName}: ${formattedValue}</div>`
          } else {
            result += `<div>${param.marker} ${param.seriesName}: -</div>`
          }
        })
        return result
      },
    },
    legend: {
      data: series.map((s) => s.name),
      top: 40,
      type: 'scroll',
      orient: 'horizontal',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      name: '日期',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        rotate: 45,
        interval: 0,
        formatter: (value: string) => {
          return formatDateLabel(value)
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '主力净流入(亿元)',
      axisLabel: {
        formatter: (value: number) => {
          if (value >= 0) {
            return `+${value.toFixed(2)}`
          }
          return value.toFixed(2)
        },
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
        },
      },
    },
    series: series,
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 20,
        bottom: 10,
      },
    ],
  }
})
</script>

<style scoped>
.fund-flow-page {
  padding: 20px;
}

.fund-flow-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}

.section-card {
  margin-top: 8px;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.date-separator {
  margin: 0 8px;
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-info {
  margin-left: 20px;
  color: #909399;
  font-size: 14px;
}

.watched-sub-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}

.stock-sub-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}

.chart-container {
  padding: 20px;
  height: 600px;
}

.date-selector-bar {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  flex-wrap: wrap;
  gap: 8px;
}

.date-selector-bar .el-checkbox-group {
  flex: 1;
  min-width: 300px;
}

.net-inflow-positive {
  color: #f56c6c;
  font-weight: 500;
}

.net-inflow-negative {
  color: #67c23a;
  font-weight: 500;
}

.watched-chart {
  width: 100%;
  height: 100%;
}

.stock-chart {
  width: 100%;
  height: 100%;
}

.field-separator {
  margin: 0 8px;
  color: #909399;
  font-size: 14px;
}

.unit-label {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.history-container {
  padding: 20px;
  background-color: #f5f7fa;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
</style>
