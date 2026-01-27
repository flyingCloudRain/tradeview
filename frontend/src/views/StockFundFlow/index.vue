<template>
  <div class="fund-flow-page">
    <el-tabs v-model="activeTab" class="fund-flow-tabs">
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
              <el-button type="primary" @click="handleSearch" :loading="loading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
            </div>

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
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useFundFlowStore } from '@/stores/fundFlow'
import dayjs from 'dayjs'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'

const fundFlowStore = useFundFlowStore()

const activeTab = ref('stock')
const startDate = ref(dayjs().format('YYYY-MM-DD'))
const endDate = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const consecutiveDays = ref<number | undefined>(undefined)
const minNetInflowDisplay = ref<number | undefined>(undefined)
const minNetInflow = ref<number | undefined>(undefined)

const tableData = computed(() => fundFlowStore.list)
const loading = computed(() => fundFlowStore.loading)
const pagination = computed(() => fundFlowStore.pagination)

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
  
  await fundFlowStore.fetchList({
    start_date: startDate.value,
    end_date: endDate.value,
    stock_code: stockCode.value || undefined,
    consecutive_days: consecutiveDays.value || undefined,
    min_net_inflow: minNetInflow.value || undefined,
  })
}

const handleDateRangeChange = () => {
  fetchData()
}

const disabledEndDate = (date: Date) => {
  if (!startDate.value) return false
  return dayjs(date).isBefore(dayjs(startDate.value))
}

const handleSearch = () => {
  fundFlowStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

const handleSizeChange = () => {
  fetchData()
}

const handlePageChange = () => {
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
</style>
