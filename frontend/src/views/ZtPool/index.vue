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
              <el-input
                v-model="limitUpStatistics"
                placeholder="板数（如：首板、1、2、2/3）"
                clearable
                style="width: 200px"
              />
              <el-select
                v-model="selectedConceptIds"
                multiple
                filterable
                placeholder="选择概念"
                clearable
                style="width: 300px"
              >
                <el-option
                  v-for="concept in conceptList"
                  :key="concept.id"
                  :label="concept.name"
                  :value="concept.id"
                />
              </el-select>
              <el-select
                v-model="isLhb"
                placeholder="是否龙虎榜"
                clearable
                style="width: 150px"
              >
                <el-option label="是" :value="true" />
                <el-option label="否" :value="false" />
              </el-select>
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
              <el-table-column prop="limit_up_statistics" label="板数" width="100" align="center">
                <template #default="{ row }">
                  <span>{{ formatLimitUpStatistics(row.limit_up_statistics) }}</span>
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
              <el-select
                v-model="selectedConceptIds"
                multiple
                filterable
                placeholder="选择概念"
                clearable
                style="width: 300px"
              >
                <el-option
                  v-for="concept in conceptList"
                  :key="concept.id"
                  :label="concept.name"
                  :value="concept.id"
                />
              </el-select>
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
                      v-for="(concept, idx) in getConceptDisplayList(row)"
                      :key="idx"
                      size="small"
                      style="margin-right: 4px; margin-bottom: 4px"
                    >
                      {{ concept }}
                    </el-tag>
                    <span v-if="getConceptDisplayList(row).length === 0" style="color: #909399">
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
import { stockConceptApi, type StockConcept } from '@/api/stockConcept'
import dayjs from 'dayjs'
import { formatPercent } from '@/utils/format'
import { ElMessage } from 'element-plus'

const ztPoolStore = useZtPoolStore()

const date = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const limitUpStatistics = ref('')
const selectedConceptIds = ref<number[]>([])
const isLhb = ref<boolean | undefined>(undefined)
const activeType = computed({
  get: () => ztPoolStore.activeType,
  set: (v) => ztPoolStore.setActiveType(v as 'up' | 'down'),
})
const conceptOptions = ref<string[]>([])
const conceptList = ref<StockConcept[]>([])

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
    limit_up_statistics: limitUpStatistics.value || undefined,
    concept_ids: selectedConceptIds.value.length > 0 ? selectedConceptIds.value : undefined,
    is_lhb: isLhb.value,
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

const loadConceptList = async () => {
  try {
    const response = await stockConceptApi.getList({ page_size: 1000 })
    conceptList.value = response.items
  } catch (e) {
    console.error('加载概念板块列表失败:', e)
    ElMessage.error('加载概念板块列表失败')
  }
}

onMounted(() => {
  fetchData()
  loadConceptOptions()
  loadConceptList()
})

const handleTypeChange = () => {
  ztPoolStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

// 获取概念显示列表（优先使用 concepts 数组，否则解析 concept 文本字段）
const getConceptDisplayList = (row: any): string[] => {
  // 优先使用 concepts 数组（概念板块关联数据）
  if (row.concepts && Array.isArray(row.concepts) && row.concepts.length > 0) {
    return row.concepts.map((c: any) => c.name || c)
  }
  // 回退到解析 concept 文本字段（兼容旧数据）
  return getConceptList(row.concept)
}

// 解析概念字符串为数组（支持逗号、空格分隔）
const getConceptList = (conceptStr: string | null | undefined): string[] => {
  if (!conceptStr) return []
  return conceptStr
    .split(/[,，\s]+/)
    .map((c) => c.trim())
    .filter((c) => c.length > 0)
}

// 格式化涨停统计字段
const formatLimitUpStatistics = (statistics: string | null | undefined): string => {
  if (!statistics) return '-'
  
  // 匹配 ?/? 格式（例如：1/1, 2/3, 5/10 等）
  const match = statistics.match(/^(\d+)\/(\d+)$/)
  if (match) {
    const days = parseInt(match[1])
    const boards = parseInt(match[2])
    
    // 如果是 1/1，显示"首板"
    if (days === 1 && boards === 1) {
      return '首板'
    }
    
    // 其他情况显示 "?天/?板"
    return `${days}天/${boards}板`
  }
  
  // 如果格式不匹配，直接返回原值
  return statistics
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

