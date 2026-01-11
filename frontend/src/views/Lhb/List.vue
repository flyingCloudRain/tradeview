<template>
  <div class="lhb-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>龙虎榜列表</span>
        </div>
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
          style="width: 200px"
          @clear="handleSearch"
        />
        <el-input
          v-model="stockName"
          placeholder="股票名称（模糊查询）"
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
        :default-sort="{ prop: 'net_buy_amount', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column type="expand" width="50">
          <template #default="{ row }">
            <div class="institution-detail">
              <el-table
                :data="row.institutions || []"
                size="small"
                border
                :default-sort="{ prop: 'net_buy_amount', order: 'descending' }"
              >
                <el-table-column prop="institution_name" label="机构名称" min-width="200" show-overflow-tooltip />
                <el-table-column label="净流入" width="150" align="right" sortable>
                  <template #default="{ row: inst }">
                    <span :style="{ color: (parseFloat(inst.net_buy_amount) || 0) > 0 ? 'red' : (parseFloat(inst.net_buy_amount) || 0) < 0 ? 'green' : '' }">
                      {{ formatAmount(inst.net_buy_amount) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="买入金额" width="150" align="right">
                  <template #default="{ row: inst }">
                    {{ formatAmount(inst.buy_amount) }}
                  </template>
                </el-table-column>
                <el-table-column label="卖出金额" width="150" align="right">
                  <template #default="{ row: inst }">
                    {{ formatAmount(inst.sell_amount) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="stock_code" label="股票代码" width="120" />
        <el-table-column prop="stock_name" label="股票名称" width="150" />
        <el-table-column label="涨跌幅(%)" width="120">
          <template #default="{ row }">
            <span :style="{ color: (parseFloat(row.change_percent) || 0) > 0 ? 'red' : 'green' }">
              {{ formatPercent(row.change_percent) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="net_buy_amount" label="净买额" width="150" sortable="custom" align="right">
          <template #default="{ row }">
            <span :style="{ color: (parseFloat(row.net_buy_amount) || 0) > 0 ? 'red' : (parseFloat(row.net_buy_amount) || 0) < 0 ? 'green' : '' }">
              {{ formatAmount(row.net_buy_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="turnover_rate" label="换手率(%)" width="120" sortable="custom" />
        <el-table-column prop="concept" label="概念" min-width="200">
          <template #default="{ row }">
            <div v-if="getConceptList(row.concept).length > 0" class="concept-tags">
              <el-tag
                v-for="(concept, idx) in getConceptList(row.concept)"
                :key="idx"
                size="small"
                style="margin-right: 4px; margin-bottom: 4px"
              >
                {{ concept }}
              </el-tag>
            </div>
            <span v-else style="color: #909399">无</span>
          </template>
        </el-table-column>
        <el-table-column label="交易机构" width="150">
          <template #default="{ row }">
            <span v-if="row.institutions && row.institutions.length > 0">
              {{ row.institutions.length }} 家机构
            </span>
            <span v-else class="text-gray">暂无</span>
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useLhbStore } from '@/stores/lhb'
import dayjs from 'dayjs'
import { formatAmount, formatPercent } from '@/utils/format'

const lhbStore = useLhbStore()

const date = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const stockName = ref('')

const tableData = computed(() => lhbStore.list)
const loading = computed(() => lhbStore.loading)
const pagination = computed(() => lhbStore.pagination)

const fetchData = async () => {
  try {
    console.log('开始获取数据，日期:', date.value, '类型:', typeof date.value)
    console.log('日期值:', JSON.stringify(date.value))
    
    // 确保日期格式正确
    const dateStr = date.value
    if (!dateStr) {
      ElMessage.warning('请选择日期')
      return
    }
    
    await lhbStore.fetchList({
      date: dateStr,
      stock_code: stockCode.value || undefined,
      stock_name: stockName.value || undefined,
    })
    
    console.log('数据获取完成，列表长度:', tableData.value.length)
    console.log('Store中的列表:', lhbStore.list)
    console.log('分页信息:', lhbStore.pagination)
    
    // 如果没有数据，显示提示
    if (tableData.value.length === 0 && !loading.value) {
      ElMessage.info(`该日期(${dateStr})暂无龙虎榜数据，请检查日期是否正确`)
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取数据失败，请稍后重试'
    ElMessage.error(errorMsg)
    console.error('获取龙虎榜数据失败:', error)
    console.error('错误响应:', error?.response)
    console.error('错误堆栈:', error?.stack)
  }
}

const handleDateChange = () => {
  fetchData()
}

const handleSearch = () => {
  lhbStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

const handleSizeChange = () => {
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  const sortBy = sort.order ? sort.prop : undefined
  const order = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : undefined
  lhbStore.setFilters({
    sort_by: sortBy,
    order,
  })
  fetchData()
}

// 解析概念字符串为数组（支持逗号、空格分隔）
const getConceptList = (conceptStr: string | null | undefined): string[] => {
  if (!conceptStr) return []
  return conceptStr
    .split(/[,，\s]+/)
    .map((c) => c.trim())
    .filter((c) => c.length > 0)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.lhb-list {
  padding: 20px;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.institution-detail {
  padding: 10px;
  background-color: #f5f7fa;
}

.text-gray {
  color: #909399;
}

.concept-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>

