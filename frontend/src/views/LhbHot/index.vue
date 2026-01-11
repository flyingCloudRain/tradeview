<template>
  <div class="lhb-hot">
    <el-card>
      <template #header>
        <span>机构榜</span>
      </template>

      <div class="filter-bar">
        <el-date-picker
          v-model="date"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
          style="width: 200px"
        />
        <el-input
          v-model="stockCode"
          placeholder="股票代码"
          clearable
          style="width: 150px"
          @clear="handleSearch"
        />
        <el-input
          v-model="stockName"
          placeholder="股票名称（模糊查询）"
          clearable
          style="width: 200px"
          @clear="handleSearch"
        />
        <el-select
          v-model="direction"
          placeholder="操作方向"
          clearable
          style="width: 150px"
          @change="handleSearch"
        >
          <el-option label="买入" value="买入" />
          <el-option label="卖出" value="卖出" />
        </el-select>
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
        @sort-change="handleSortChange"
      >
        <el-table-column prop="date" label="上榜日" width="120" />
        <el-table-column prop="institution_name" label="营业部名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="stock_code" label="股票代码" width="120" />
        <el-table-column prop="stock_name" label="股票名称" width="150" show-overflow-tooltip />
        <el-table-column prop="flag" label="操作方向" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.flag === '买入'" type="danger" size="small">买入</el-tag>
            <el-tag v-else-if="row.flag === '卖出'" type="success" size="small">卖出</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="150" align="right" sortable="custom" :sort-method="sortByAmount">
          <template #default="{ row }">
            <span v-if="row.flag === '买入' && row.buy_amount" style="color: red">
              {{ formatAmount(row.buy_amount) }}
            </span>
            <span v-else-if="row.flag === '卖出' && row.sell_amount" style="color: green">
              {{ formatAmount(row.sell_amount) }}
            </span>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { formatAmount } from '@/utils/format'
import { useLhbHotStore } from '@/stores/lhbHot'
import { ElMessage } from 'element-plus'

const lhbHotStore = useLhbHotStore()

const date = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const stockName = ref('')
const direction = ref<'买入' | '卖出' | ''>('')

const tableData = computed(() => lhbHotStore.list)
const loading = computed(() => lhbHotStore.loading)
const pagination = computed(() => lhbHotStore.pagination)

const fetchData = async () => {
  try {
    await lhbHotStore.fetchList({
      date: date.value || undefined,
      stock_code: stockCode.value || undefined,
      stock_name: stockName.value || undefined,
      flag: direction.value || undefined,
    })
    if (tableData.value.length === 0 && !loading.value) {
      ElMessage.info(`该日期(${date.value})暂无机构榜数据`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取机构榜失败')
  }
}

const handleDateChange = () => {
  lhbHotStore.setFilters({ date: date.value || undefined })
  fetchData()
}

const handleSearch = () => {
  lhbHotStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

const handleSizeChange = () => {
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  let sortBy = sort.order ? sort.prop : undefined
  // 如果按金额排序，需要根据操作方向选择对应的字段
  if (sortBy === 'amount') {
    // 后端需要支持按buy_amount或sell_amount排序，这里先使用buy_amount
    sortBy = 'buy_amount'
  }
  const order = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : undefined
  lhbHotStore.setFilters({
    sort_by: sortBy,
    order,
  })
  fetchData()
}

const sortByAmount = (a: any, b: any) => {
  const aAmount = a.flag === '买入' ? (a.buy_amount || 0) : (a.sell_amount || 0)
  const bAmount = b.flag === '买入' ? (b.buy_amount || 0) : (b.sell_amount || 0)
  return aAmount - bAmount
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.lhb-hot {
  padding: 20px;
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
</style>

