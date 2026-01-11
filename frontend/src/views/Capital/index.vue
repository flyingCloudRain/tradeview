<template>
  <div class="capital-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>游资榜列表</span>
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
        />
        <el-input
          v-model="capitalName"
          placeholder="游资名称"
          clearable
          style="width: 200px"
          @clear="handleSearch"
        />
        <el-button type="primary" @click="handleSearch" :loading="loading">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </div>

      <el-table :data="tableData" :loading="loading" stripe border>
        <el-table-column prop="capital_name" label="游资名称" width="200" />
        <el-table-column prop="stock_code" label="股票代码" width="120" />
        <el-table-column prop="stock_name" label="股票名称" width="150" />
        <el-table-column label="买入额" width="150">
          <template #default="{ row }">
            {{ formatAmount(row.buy_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="卖出额" width="150">
          <template #default="{ row }">
            {{ formatAmount(row.sell_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="净买额" width="150">
          <template #default="{ row }">
            <span :style="{ color: (row.net_buy_amount || 0) > 0 ? 'red' : 'green' }">
              {{ formatAmount(row.net_buy_amount) }}
            </span>
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
import { useCapitalStore } from '@/stores/capital'
import dayjs from 'dayjs'
import { formatAmount } from '@/utils/format'

const capitalStore = useCapitalStore()

const date = ref(dayjs().format('YYYY-MM-DD'))
const capitalName = ref('')

const tableData = computed(() => capitalStore.list)
const loading = computed(() => capitalStore.loading)
const pagination = computed(() => capitalStore.pagination)

const fetchData = async () => {
  await capitalStore.fetchList({
    date: date.value,
    capital_name: capitalName.value || undefined,
  })
}

const handleDateChange = () => {
  fetchData()
}

const handleSearch = () => {
  capitalStore.setPagination(1, pagination.value.pageSize)
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
})
</script>

<style scoped>
.capital-list {
  padding: 20px;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>

