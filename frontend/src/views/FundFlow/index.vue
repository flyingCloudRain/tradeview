<template>
  <div class="fund-flow-page">
    <el-tabs v-model="activeTab" class="fund-flow-tabs">
      <el-tab-pane label="个股资金流" name="stock">
        <div class="section-card">
          <el-card>
            <div class="filter-bar">
              <el-date-picker
                v-model="date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateChange"
              />
              <el-input
                v-model="stockCode"
                placeholder="股票代码"
                clearable
                style="width: 200px"
                @clear="handleSearch"
              />
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

      <el-tab-pane label="概念资金流" name="concept">
        <div class="section-card">
          <el-card>
            <template #header>
              <div class="card-header">
                <div class="header-actions">
                  <el-input
                    v-model="conceptKeyword"
                    placeholder="按概念筛选"
                    clearable
                    style="width: 200px "
                  />
                  <el-date-picker
                    v-model="conceptDate"
                    type="date"
                    placeholder="选择日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    @change="refreshConcept"
                  />
                  <el-button type="primary" size="small" @click="refreshConcept" :loading="conceptLoading">
                    查询
                  </el-button>
                </div>
              </div>
            </template>
            <el-table
              :data="conceptTableData"
              :loading="conceptLoading"
              stripe
              border
              :default-sort="conceptDefaultSort"
              @sort-change="handleConceptSortChange"
            >
              <el-table-column prop="concept" label="概念/行业" min-width="160" show-overflow-tooltip />
              <el-table-column prop="index_value" label="指数" width="120" align="right" />
              <el-table-column
                prop="index_change_percent"
                label="指数涨跌幅"
                width="120"
                align="right"
                sortable="custom"
              >
                <template #default="{ row }">
                  <span :style="{ color: (row.index_change_percent || 0) > 0 ? 'red' : 'green' }">
                    {{ formatPercent(row.index_change_percent) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="net_amount" label="净额(亿元)" width="150" align="right" sortable="custom">
                <template #default="{ row }">
                  <span :style="{ color: (row.net_amount || 0) > 0 ? 'red' : 'green' }">
                    {{ formatAmount(row.net_amount) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="inflow" label="流入(亿元)" width="140" align="right" sortable="custom">
                <template #default="{ row }">
                  {{ formatAmount(row.inflow) }}
                </template>
              </el-table-column>
              <el-table-column prop="outflow" label="流出(亿元)" width="140" align="right" sortable="custom">
                <template #default="{ row }">
                  {{ formatAmount(row.outflow) }}
                </template>
              </el-table-column>
              <el-table-column prop="stock_count" label="公司家数" width="100" align="center" />
              <el-table-column prop="leader_stock" label="领涨股" width="150" show-overflow-tooltip />
              <el-table-column prop="leader_change_percent" label="领涨股涨跌幅" width="140" align="right">
                <template #default="{ row }">
                  <span :style="{ color: (row.leader_change_percent || 0) > 0 ? 'red' : 'green' }">
                    {{ formatPercent(row.leader_change_percent) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="leader_price" label="领涨股价" width="120" align="right">
                <template #default="{ row }">
                  {{ formatPrice(row.leader_price) }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useFundFlowStore } from '@/stores/fundFlow'
import dayjs from 'dayjs'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'

const fundFlowStore = useFundFlowStore()

const activeTab = ref('stock')
const date = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')

const tableData = computed(() => fundFlowStore.list)
const loading = computed(() => fundFlowStore.loading)
const conceptData = computed(() => fundFlowStore.conceptList)
const conceptLoading = computed(() => fundFlowStore.conceptLoading)
const pagination = computed(() => fundFlowStore.pagination)
const conceptKeyword = ref('')
const conceptSort = ref<{ prop?: string; order?: 'ascending' | 'descending' | null }>({
  prop: 'net_amount',
  order: 'descending',
})
const conceptDefaultSort = computed(() => conceptSort.value)
const conceptTableData = computed(() => {
  const keyword = conceptKeyword.value.trim()
  const data = keyword
    ? conceptData.value.filter((item) => item.concept?.includes(keyword))
    : [...conceptData.value]
  const { prop, order } = conceptSort.value
  if (!prop || !order) return data
  const asc = order === 'ascending'
  return data.sort((a: any, b: any) => {
    const va = Number(a[prop]) || 0
    const vb = Number(b[prop]) || 0
    return asc ? va - vb : vb - va
  })
})

const fetchData = async () => {
  await fundFlowStore.fetchList({
    date: date.value,
    stock_code: stockCode.value || undefined,
  })
}

const handleDateChange = () => {
  fetchData()
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

onMounted(() => {
  fetchData()
  refreshConcept()
})

const refreshConcept = async () => {
  await fundFlowStore.fetchConcept(50, conceptDate.value)
}

const conceptDate = ref(dayjs().format('YYYY-MM-DD'))
const handleConceptSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  conceptSort.value = sort
}

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

.header-actions {
  display: flex;
  align-items: center;
}
</style>

