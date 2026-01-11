<template>
  <div class="zt-pool">
    <el-tabs v-model="activeType" @tab-change="handleTypeChange" class="zt-tabs">
      <el-tab-pane label="涨停股" name="up">
        <div class="section-card">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>涨停池</span>
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
                v-model="stockCode"
                placeholder="股票代码"
                clearable
                style="width: 200px"
              />
              <el-button type="primary" @click="handleSearch" :loading="loading">
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
              <el-table-column prop="change_percent" label="涨跌幅(%)" width="120" sortable="custom">
                <template #default="{ row }">
                  <span :style="{ color: row.change_percent > 0 ? 'red' : 'green' }">
                    {{ formatPercent(row.change_percent) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="is_lhb" label="龙虎榜" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.is_lhb" type="danger" size="small">是</el-tag>
                  <span v-else style="color: #909399">否</span>
                </template>
              </el-table-column>
              <el-table-column prop="industry" label="行业" width="150" sortable="custom" />
              <el-table-column prop="concept" label="概念" min-width="200">
                <template #default="{ row }">
                  <el-select
                    v-if="row._editing"
                    v-model="row.conceptArray"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    :reserve-keyword="false"
                    placeholder="选择或输入概念"
                    size="small"
                    style="width: 100%"
                    @change="handleConceptChange(row)"
                  >
                    <el-option
                      v-for="concept in conceptOptions"
                      :key="concept"
                      :label="concept"
                      :value="concept"
                    />
                  </el-select>
                  <div v-else class="concept-tags">
                    <el-tag
                      v-for="(concept, idx) in getConceptList(row.concept)"
                      :key="idx"
                      size="small"
                      style="margin-right: 4px; margin-bottom: 4px"
                    >
                      {{ concept }}
                    </el-tag>
                    <span v-if="!row.concept || getConceptList(row.concept).length === 0" style="color: #909399">
                      无
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="limit_up_reason" label="涨停原因" min-width="200">
                <template #default="{ row }">
                  <el-input v-if="row._editing" v-model="row.limit_up_reason" size="small" />
                  <span v-else>{{ row.limit_up_reason }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="140">
                <template #default="{ row }">
                  <template v-if="row._editing">
                    <el-button type="primary" link size="small" @click="handleSave(row)">保存</el-button>
                    <el-button type="default" link size="small" @click="handleEditToggle(row, false)">取消</el-button>
                  </template>
                  <template v-else>
                    <el-button type="primary" link size="small" @click="handleEditToggle(row, true)">编辑</el-button>
                  </template>
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

      <el-tab-pane label="跌停股" name="down">
        <div class="section-card">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>跌停池</span>
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
                v-model="stockCode"
                placeholder="股票代码"
                clearable
                style="width: 200px"
              />
              <el-button type="primary" @click="handleSearch" :loading="loading">
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
              <el-table-column prop="change_percent" label="涨跌幅(%)" width="120" sortable="custom">
                <template #default="{ row }">
                  <span :style="{ color: row.change_percent > 0 ? 'red' : 'green' }">
                    {{ formatPercent(row.change_percent) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="industry" label="行业" width="150" sortable="custom" />
              <el-table-column prop="concept" label="概念" min-width="200">
                <template #default="{ row }">
                  <el-select
                    v-if="row._editing"
                    v-model="row.conceptArray"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    :reserve-keyword="false"
                    placeholder="选择或输入概念"
                    size="small"
                    style="width: 100%"
                    @change="handleConceptChange(row)"
                  >
                    <el-option
                      v-for="concept in conceptOptions"
                      :key="concept"
                      :label="concept"
                      :value="concept"
                    />
                  </el-select>
                  <div v-else class="concept-tags">
                    <el-tag
                      v-for="(concept, idx) in getConceptList(row.concept)"
                      :key="idx"
                      size="small"
                      style="margin-right: 4px; margin-bottom: 4px"
                    >
                      {{ concept }}
                    </el-tag>
                    <span v-if="!row.concept || getConceptList(row.concept).length === 0" style="color: #909399">
                      无
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="limit_up_reason" label="跌停原因" min-width="200">
                <template #default="{ row }">
                  <el-input v-if="row._editing" v-model="row.limit_up_reason" size="small" />
                  <span v-else>{{ row.limit_up_reason }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="140">
                <template #default="{ row }">
                  <template v-if="row._editing">
                    <el-button type="primary" link size="small" @click="handleSave(row)">保存</el-button>
                    <el-button type="default" link size="small" @click="handleEditToggle(row, false)">取消</el-button>
                  </template>
                  <template v-else>
                    <el-button type="primary" link size="small" @click="handleEditToggle(row, true)">编辑</el-button>
                  </template>
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
import { useZtPoolStore } from '@/stores/ztPool'
import { ztPoolApi } from '@/api/ztPool'
import dayjs from 'dayjs'
import { formatPercent } from '@/utils/format'
import { ElMessage } from 'element-plus'

const ztPoolStore = useZtPoolStore()

const date = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const activeType = computed({
  get: () => ztPoolStore.activeType,
  set: (v) => ztPoolStore.setActiveType(v as 'up' | 'down'),
})
const conceptOptions = ref<string[]>([])

const tableData = computed(() => ztPoolStore.list)
const loading = computed(() => ztPoolStore.loading)
const pagination = computed(() => ztPoolStore.pagination)
const defaultSort = computed(() =>
  activeType.value === 'up'
    ? { prop: 'change_percent', order: 'descending' }
    : { prop: 'change_percent', order: 'ascending' },
)

const fetchData = async () => {
  await ztPoolStore.fetchList({
    date: date.value,
    stock_code: stockCode.value || undefined,
  })
}

const handleDateChange = () => {
  fetchData()
}

const handleSearch = () => {
  ztPoolStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

const handleEditToggle = (row: any, editing: boolean) => {
  row._editing = editing
  if (editing) {
    // 初始化概念数组
    row.conceptArray = getConceptList(row.concept)
  } else {
    // 取消编辑时清除临时数组
    delete row.conceptArray
  }
}

const handleConceptChange = (row: any) => {
  // 将数组转换为逗号分隔的字符串
  row.concept = row.conceptArray ? row.conceptArray.join(',') : ''
}

const handleSave = async (row: any) => {
  try {
    await ztPoolStore.updateItem(row.id, {
      concept: row.concept,
      limit_up_reason: row.limit_up_reason,
    })
    row._editing = false
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
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
  ztPoolStore.setFilters({
    sort_by: sortBy,
    order,
  })
  fetchData()
}

const loadConceptOptions = async () => {
  try {
    conceptOptions.value = await ztPoolApi.getConcepts()
  } catch (e) {
    console.error('加载概念列表失败:', e)
  }
}

onMounted(() => {
  fetchData()
  loadConceptOptions()
})

const handleTypeChange = () => {
  ztPoolStore.setPagination(1, pagination.value.pageSize)
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
</script>

<style scoped>
.zt-pool {
  padding: 20px;
}

.zt-tabs :deep(.el-tabs__header) {
  margin-bottom: 12px;
}

.section-card {
  margin-top: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-bar :deep(.el-input),
.filter-bar :deep(.el-date-editor) {
  width: 200px;
}

.concept-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>

