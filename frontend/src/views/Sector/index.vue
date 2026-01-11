<template>
  <div class="sector-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>概念板块</span>
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

      <div class="filter-bar">
        <el-input
          v-model="sectorCode"
          placeholder="板块代码"
          clearable
          style="width: 200px"
        />
        <el-button type="primary" @click="handleSearch" :loading="loading">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </div>

      <el-table :data="tableData" :loading="loading" stripe border>
        <el-table-column prop="date" label="日期" width="130" />
        <el-table-column prop="sector_code" label="板块代码" width="120" />
        <el-table-column prop="sector_name" label="板块名称" width="200" />
        <el-table-column label="涨跌幅(%)" width="120">
          <template #default="{ row }">
            <span :style="{ color: (row.change_percent || 0) > 0 ? 'red' : 'green' }">
              {{ formatPercent(row.change_percent) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="rise_count" label="上涨数" width="100" />
        <el-table-column prop="fall_count" label="下跌数" width="100" />
        <el-table-column prop="total_count" label="总数" width="100" />
        <el-table-column label="成交额" width="150">
          <template #default="{ row }">
            {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { sectorApi } from '@/api/sector'
import { formatPercent, formatAmount } from '@/utils/format'
import dayjs from 'dayjs'

const date = ref(dayjs().format('YYYY-MM-DD'))
const sectorCode = ref('')
const sortBy = ref('change_percent')
const order = ref<'asc' | 'desc'>('desc')
const loading = ref(false)
const tableData = ref<any[]>([])

const fetchData = async () => {
  loading.value = true
  try {
    tableData.value = await sectorApi.getList({
      date: date.value,
      sector_code: sectorCode.value || undefined,
      sort_by: sortBy.value,
      order: order.value,
    })
  } catch (error) {
    ElMessage.error('获取板块数据失败')
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
.sector-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>

