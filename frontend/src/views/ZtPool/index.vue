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
              />
              <el-input
                v-model="stockName"
                placeholder="股票名称"
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
              <el-table-column 
                v-if="isDateRangeQuery && activeType === 'up'" 
                prop="limit_up_count" 
                label="涨停次数" 
                width="100" 
                align="center"
                sortable="custom"
              >
                <template #default="{ row }">
                  <el-tag type="danger" size="small">{{ row.limit_up_count || 0 }}</el-tag>
                </template>
              </el-table-column>
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
              <el-table-column prop="limit_up_capital" label="封板资金" width="120" align="right" sortable="custom">
                <template #default="{ row }">
                  <span>{{ formatAmount(row.limit_up_capital) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="first_limit_time" label="首次封板时间" width="130" align="center">
                <template #default="{ row }">
                  <span>{{ formatTime(row.first_limit_time) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="is_lhb" label="龙虎榜" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.is_lhb" type="danger" size="small">是</el-tag>
                  <span v-else style="color: #909399">否</span>
                </template>
              </el-table-column>
              <el-table-column prop="industry" label="行业" width="150" sortable="custom" />
              <el-table-column prop="concepts" label="概念题材" min-width="250">
                <template #default="{ row }">
                  <el-select
                    v-if="row._editing"
                    v-model="row.conceptIds"
                    multiple
                    filterable
                    placeholder="选择概念题材"
                    size="small"
                    style="width: 100%"
                    @change="handleConceptChange(row)"
                  >
                    <el-option-group
                      v-for="group in conceptTreeGroups"
                      :key="group.level"
                      :label="`${group.label}概念`"
                    >
                      <el-option
                        v-for="concept in group.concepts"
                        :key="concept.id"
                        :label="`${concept.name}${concept.code ? ' (' + concept.code + ')' : ''}`"
                        :value="concept.id"
                      >
                        <span>{{ concept.name }}</span>
                        <el-tag v-if="concept.code" size="small" style="margin-left: 8px">{{ concept.code }}</el-tag>
                      </el-option>
                    </el-option-group>
                  </el-select>
                  <div v-else class="concept-tags">
                    <el-tag
                      v-for="(concept, idx) in row.concepts || []"
                      :key="idx"
                      :type="getConceptLevelTagType(concept.level)"
                      size="small"
                      style="margin-right: 4px; margin-bottom: 4px"
                    >
                      {{ concept.name }}
                      <span v-if="concept.level" class="level-badge">L{{ concept.level }}</span>
                    </el-tag>
                    <el-button
                      v-if="!row.concepts || row.concepts.length === 0"
                      text
                      type="primary"
                      size="small"
                      @click="handleEditToggle(row, true)"
                    >
                      添加概念
                    </el-button>
                    <span v-else-if="row.concepts.length === 0" style="color: #909399">无</span>
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
                    <el-button type="default" link size="small" @click="handleCancelEdit(row)">取消</el-button>
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
              <el-table-column 
                v-if="isDateRangeQuery && activeType === 'down'" 
                prop="limit_up_count" 
                label="跌停次数" 
                width="100" 
                align="center"
                sortable="custom"
              >
                <template #default="{ row }">
                  <el-tag type="danger" size="small">{{ row.limit_up_count || 0 }}</el-tag>
                </template>
              </el-table-column>
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
                    <el-button type="default" link size="small" @click="handleCancelEdit(row)">取消</el-button>
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
import { formatPercent, formatAmount } from '@/utils/format'
import { ElMessage } from 'element-plus'

const ztPoolStore = useZtPoolStore()

const date = ref(dayjs().format('YYYY-MM-DD'))
const startDate = ref(dayjs().format('YYYY-MM-DD'))
const endDate = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const stockName = ref('')
const limitUpStatistics = ref('')
const selectedConceptIds = ref<number[]>([])
const isLhb = ref<boolean | undefined>(undefined)
const activeType = computed({
  get: () => ztPoolStore.activeType,
  set: (v) => ztPoolStore.setActiveType(v as 'up' | 'down'),
})
const conceptOptions = ref<string[]>([])
const conceptList = ref<StockConcept[]>([])
const conceptTreeGroups = ref<Array<{ level: number; label: string; concepts: StockConcept[] }>>([])

// 判断是否是日期范围查询
const isDateRangeQuery = computed(() => {
  return !!(startDate.value && endDate.value)
})

const tableData = computed(() => ztPoolStore.list)
const loading = computed(() => ztPoolStore.loading)
const pagination = computed(() => ztPoolStore.pagination)
const defaultSort = computed(() =>
  activeType.value === 'up'
    ? { prop: 'change_percent', order: 'descending' }
    : { prop: 'change_percent', order: 'ascending' },
)

const getConceptLevelTagType = (level: number) => {
  const map: Record<number, string> = { 1: 'primary', 2: 'success', 3: 'warning' }
  return map[level] || ''
}

const fetchData = async () => {
  const params: ZtPoolListParams = {}
  
  // 涨停股和跌停股都使用日期范围查询
  if (activeType.value === 'up') {
    // 涨停股：必须使用日期范围
    if (!startDate.value || !endDate.value) {
      ElMessage.warning('请选择开始日期和结束日期')
      return
    }
    params.start_date = startDate.value
    params.end_date = endDate.value
  } else {
    // 跌停股：使用日期范围查询
    if (!startDate.value || !endDate.value) {
      ElMessage.warning('请选择开始日期和结束日期')
      return
    }
    params.start_date = startDate.value
    params.end_date = endDate.value
  }
  
  params.stock_code = stockCode.value?.trim() || undefined
  params.stock_name = stockName.value?.trim() || undefined
  params.limit_up_statistics = limitUpStatistics.value?.trim() || undefined
  params.concept_ids = selectedConceptIds.value.length > 0 ? selectedConceptIds.value : undefined
  params.is_lhb = isLhb.value
  
  await ztPoolStore.fetchList(params)
}

const handleDateRangeChange = () => {
  fetchData()
}

const handleDateChange = () => {
  fetchData()
}

const disabledEndDate = (date: Date) => {
  if (!startDate.value) return false
  return dayjs(date).isBefore(dayjs(startDate.value))
}

const handleSearch = () => {
  ztPoolStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

const handleEditToggle = async (row: any, editing: boolean) => {
  row._editing = editing
  if (editing) {
    // 保存原始概念，用于取消时恢复
    row._originalConcepts = row.concepts ? [...row.concepts] : []
    // 加载该股票的概念
    try {
      const res = await stockConceptApi.getStockConcepts(row.stock_name)
      row.conceptIds = res.concepts.map((c) => c.id)
      // 确保 concepts 是最新的，使用新数组引用触发响应式更新
      row.concepts = res.concepts ? [...res.concepts] : []
    } catch (error) {
      row.conceptIds = []
      row.concepts = []
    }
  } else {
    // 退出编辑模式时，确保概念信息是最新的
    if (row.conceptIds !== undefined) {
      try {
        const res = await stockConceptApi.getStockConcepts(row.stock_name)
        row.concepts = res.concepts ? [...res.concepts] : []
      } catch (error) {
        // 如果加载失败，保持当前概念
      }
    }
    // 清除临时数组
    delete row.conceptIds
    delete row._originalConcepts
  }
}

const handleConceptChange = async (row: any) => {
  // 保存概念关联
  try {
    await stockConceptApi.setStockConcepts({
      stock_name: row.stock_name,
      concept_ids: row.conceptIds || [],
    })
    // 重新加载概念信息，使用新数组引用触发响应式更新
    const res = await stockConceptApi.getStockConcepts(row.stock_name)
    // 使用 Vue 的响应式更新方式
    row.concepts = res.concepts ? [...res.concepts] : []
    ElMessage.success('概念关联已更新')
  } catch (error: any) {
    ElMessage.error(error.message || '更新失败')
    // 保存失败时恢复原始概念ID和概念列表
    if (row._originalConcepts) {
      row.conceptIds = row._originalConcepts.map((c: any) => c.id)
      row.concepts = [...row._originalConcepts]
    }
  }
}

const handleSave = async (row: any) => {
  try {
    await ztPoolStore.updateItem(row.id, {
      limit_up_reason: row.limit_up_reason,
    })
    // 确保概念信息是最新的
    if (row.conceptIds !== undefined) {
      const res = await stockConceptApi.getStockConcepts(row.stock_name)
      row.concepts = [...res.concepts]
    }
    row._editing = false
    delete row.conceptIds
    delete row._originalConcepts
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const handleCancelEdit = async (row: any) => {
  // 恢复原始概念
  if (row._originalConcepts) {
    row.concepts = [...row._originalConcepts]
  }
  row._editing = false
  delete row.conceptIds
  delete row._originalConcepts
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
    
    // 按层级分组，用于概念选择器
    const groups: Record<number, StockConcept[]> = { 1: [], 2: [], 3: [] }
    response.items.forEach((concept) => {
      if (concept.level >= 1 && concept.level <= 3) {
        groups[concept.level].push(concept)
      }
    })
    
    conceptTreeGroups.value = [
      { level: 1, label: '一级', concepts: groups[1] },
      { level: 2, label: '二级', concepts: groups[2] },
      { level: 3, label: '三级', concepts: groups[3] },
    ]
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

// 格式化时间字段（HH:MM:SS 或 HH:MM）
const formatTime = (time: string | null | undefined): string => {
  if (!time) return '-'
  
  // 如果已经是格式化的时间字符串，直接返回
  if (typeof time === 'string') {
    // 匹配 HH:MM:SS 或 HH:MM 格式
    const timeMatch = time.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/)
    if (timeMatch) {
      const hours = timeMatch[1].padStart(2, '0')
      const minutes = timeMatch[2]
      const seconds = timeMatch[3] || '00'
      return `${hours}:${minutes}:${seconds}`
    }
    return time
  }
  
  return '-'
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

.date-separator {
  margin: 0 8px;
  color: #909399;
  font-size: 14px;
}

.concept-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>

