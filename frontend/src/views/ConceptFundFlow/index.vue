<template>
  <div class="fund-flow-page">
    <div class="section-card">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="header-actions">
              <el-date-picker
                v-model="conceptDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleConceptDateRangeChange"
                style="width: 240px"
              />
              <el-input
                v-model="conceptKeyword"
                placeholder="概念名称（模糊匹配）"
                clearable
                style="width: 200px; margin-left: 10px"
              />
              <el-button type="primary" size="small" @click="refreshConcept" :loading="conceptLoading" style="margin-left: 10px">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button size="small" @click="showConceptFilterDialog" style="margin-left: 10px">
                高级筛选
              </el-button>
            </div>
          </div>
        </template>
        
        <!-- 子tabs：资金流图表和资金流明细 -->
        <el-tabs v-model="conceptSubTab" style="margin-top: 10px">
          <!-- 资金流图表 -->
          <el-tab-pane label="资金流图表" name="chart">
            <div v-if="conceptTableData.length > 0" class="chart-container">
              <el-card shadow="hover">
                <template #header>
                  <span>资金流趋势图</span>
                </template>
                <v-chart 
                  class="concept-chart" 
                  :option="conceptChartOption" 
                  autoresize 
                />
              </el-card>
            </div>
            <el-empty v-else description="暂无数据" />
          </el-tab-pane>
          
          <!-- 资金流明细 -->
          <el-tab-pane label="资金流明细" name="detail">
            <el-table
              :data="conceptTableData"
              :loading="conceptLoading"
              stripe
              border
              :default-sort="conceptDefaultSort"
              @sort-change="handleConceptSortChange"
            >
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="concept" label="概念/行业" min-width="120" show-overflow-tooltip />
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
              <el-table-column prop="stock_count" label="公司家数" width="100" align="center" sortable="custom" />
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
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 概念资金流高级筛选对话框 -->
    <el-dialog v-model="conceptFilterDialogVisible" title="概念资金流多条件联合查询" width="900px">
      <div class="filter-conditions">
        <el-form :model="conceptFilterForm" label-width="0">
          <div v-for="(condition, index) in conceptFilterForm.conditions" :key="index" class="condition-row">
            <div class="condition-label">条件 {{ index + 1 }}：</div>
            <div class="condition-fields">
              <el-date-picker
                v-model="condition.date_range.start"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                size="default"
              />
              <span class="field-separator">至</span>
              <el-date-picker
                v-model="condition.date_range.end"
                type="date"
                placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                size="default"
              />
              <span class="field-separator">净额</span>
              <div class="amount-input-group">
                <el-input-number
                  v-model="condition.displayNetMin"
                  :min="0"
                  :precision="2"
                  :step="0.1"
                  placeholder="最小值(亿)"
                  size="default"
                  style="width: 140px"
                  @change="convertConceptToYuan(condition, 'net', 'min')"
                />
                <span class="unit-label">亿</span>
              </div>
              <span class="field-separator">至</span>
              <div class="amount-input-group">
                <el-input-number
                  v-model="condition.displayNetMax"
                  :min="0"
                  :precision="2"
                  :step="0.1"
                  placeholder="最大值(亿)"
                  size="default"
                  style="width: 140px"
                  @change="convertConceptToYuan(condition, 'net', 'max')"
                />
                <span class="unit-label">亿</span>
              </div>
              <el-button
                type="danger"
                size="default"
                text
                @click="removeConceptCondition(index)"
                :disabled="conceptFilterForm.conditions.length === 1"
                style="margin-left: 10px"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <div class="condition-fields" style="margin-top: 8px">
              <span class="field-separator">流入</span>
              <el-input-number
                v-model="condition.displayInflowMin"
                :min="0"
                :precision="2"
                :step="0.1"
                placeholder="最小值(亿)"
                size="default"
                style="width: 140px"
                @change="convertConceptToYuan(condition, 'inflow', 'min')"
              />
              <span class="unit-label">亿</span>
              <span class="field-separator">至</span>
              <el-input-number
                v-model="condition.displayInflowMax"
                :min="0"
                :precision="2"
                :step="0.1"
                placeholder="最大值(亿)"
                size="default"
                style="width: 140px"
                @change="convertConceptToYuan(condition, 'inflow', 'max')"
              />
              <span class="unit-label">亿</span>
              <span class="field-separator">涨跌幅</span>
              <el-input-number
                v-model="condition.index_change_percent.min"
                :precision="2"
                :step="0.1"
                placeholder="最小值(%)"
                size="default"
                style="width: 120px"
              />
              <span class="field-separator">至</span>
              <el-input-number
                v-model="condition.index_change_percent.max"
                :precision="2"
                :step="0.1"
                placeholder="最大值(%)"
                size="default"
                style="width: 120px"
              />
            </div>
          </div>

          <el-form-item>
            <el-button type="primary" @click="handleConceptFilter" :loading="conceptLoading" size="large">
              <el-icon><Search /></el-icon>
              执行筛选
            </el-button>
            <el-button @click="resetConceptFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Search, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useFundFlowStore } from '@/stores/fundFlow'
import {
  type ConceptFundFlowQueryParams,
  type ConceptFundFlowFilterRequest,
} from '@/api/fundFlow'
import dayjs from 'dayjs'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'
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

const conceptData = computed(() => fundFlowStore.conceptList)
const conceptLoading = computed(() => fundFlowStore.conceptLoading)
const conceptKeyword = ref('')
// 默认显示最近3天数据
const conceptDateRange = ref<[string, string] | null>([
  dayjs().subtract(2, 'day').format('YYYY-MM-DD'), // 开始日期：3天前
  dayjs().format('YYYY-MM-DD'), // 结束日期：今天
]) // 日期范围：[开始日期, 结束日期]
const conceptSubTab = ref('chart') // 概念资金流子tab：chart=资金流图表, detail=资金流明细
const conceptSort = ref<{ prop?: string; order?: 'ascending' | 'descending' | null }>({
  prop: 'net_amount',
  order: 'descending',
})
const conceptDefaultSort = computed(() => conceptSort.value)
const conceptTableData = computed(() => {
  const keyword = conceptKeyword.value.trim()
  const data = keyword
    ? conceptData.value.filter((item) => item.concept?.toLowerCase().includes(keyword.toLowerCase()))
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

onMounted(async () => {
  try {
    await refreshConcept()
  } catch (error) {
    console.error('初始化概念资金流失败:', error)
  }
})

const refreshConcept = async () => {
  try {
    const params: ConceptFundFlowQueryParams = {}
    
    // 如果选择了日期范围，使用日期范围查询
    if (conceptDateRange.value && Array.isArray(conceptDateRange.value) && conceptDateRange.value.length === 2) {
      const startDate = conceptDateRange.value[0]
      const endDate = conceptDateRange.value[1]
      
      // 确保日期有效
      if (startDate && endDate) {
        // 验证日期格式
        if (!dayjs(startDate).isValid() || !dayjs(endDate).isValid()) {
          ElMessage.warning('日期格式错误，请重新选择')
          return
        }
        
        // 确保开始日期不大于结束日期
        if (dayjs(startDate).isAfter(dayjs(endDate))) {
          ElMessage.warning('开始日期不能大于结束日期')
          return
        }
        
        params.start_date = startDate
        params.end_date = endDate
        params.page = 1
        params.page_size = 50
        params.sort_by = 'net_amount'
        params.order = 'desc'
        // 日期范围查询时不传递 limit 参数
        if (conceptKeyword.value) {
          params.concept = conceptKeyword.value.trim()
        }
        
        console.log('概念资金流日期范围查询:', { 
          start_date: params.start_date, 
          end_date: params.end_date,
          conceptDateRange_value: conceptDateRange.value
        })
      } else {
        ElMessage.warning('请选择有效的日期范围')
        return
      }
    } else {
      // 如果没有选择日期范围，使用单日期查询（查询最新日期）
      params.limit = 50
      if (conceptKeyword.value) {
        params.concept = conceptKeyword.value.trim()
      }
      console.log('概念资金流单日期查询（最新日期）')
    }
    
    await fundFlowStore.fetchConcept(params)
    
    // 检查查询结果是否为空
    if (conceptData.value.length === 0) {
      if (conceptDateRange.value && conceptDateRange.value.length === 2) {
        ElMessage.warning(`所选日期范围（${conceptDateRange.value[0]} 至 ${conceptDateRange.value[1]}）没有数据，请调整日期范围`)
      } else {
        ElMessage.warning('当前日期没有数据，请选择有数据的日期范围')
      }
    }
    
    // 如果有关键词，在前端进行过滤（仅单日期查询时）
    if (conceptKeyword.value && !conceptDateRange.value) {
      const keyword = conceptKeyword.value.trim().toLowerCase()
      conceptData.value = conceptData.value.filter((item) => 
        item.concept?.toLowerCase().includes(keyword)
      )
    }
  } catch (error: any) {
    console.error('刷新概念资金流失败:', error)
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('获取概念资金流失败，请稍后重试')
    }
  }
}

const handleConceptDateRangeChange = (value: [string, string] | null) => {
  // 日期范围改变时自动查询
  console.log('日期范围变化 - 事件值:', value, '当前conceptDateRange.value:', conceptDateRange.value)
  
  // 确保日期范围值已更新
  if (value && Array.isArray(value) && value.length === 2 && value[0] && value[1]) {
    // 直接使用事件参数值，确保使用最新选择的日期
    const startDate = value[0]
    const endDate = value[1]
    
    // 验证日期格式
    if (!dayjs(startDate).isValid() || !dayjs(endDate).isValid()) {
      ElMessage.warning('日期格式错误，请重新选择')
      return
    }
    
    // 确保开始日期不大于结束日期
    if (dayjs(startDate).isAfter(dayjs(endDate))) {
      ElMessage.warning('开始日期不能大于结束日期')
      return
    }
    
    // 立即使用选择的日期进行查询
    refreshConceptWithDates(startDate, endDate)
  } else if (value === null) {
    // 清空日期范围时，重置为默认值
    conceptDateRange.value = [
      dayjs().subtract(2, 'day').format('YYYY-MM-DD'),
      dayjs().format('YYYY-MM-DD'),
    ]
    refreshConcept()
  }
}

const refreshConceptWithDates = async (startDate: string, endDate: string) => {
  try {
    const params: ConceptFundFlowQueryParams = {
      start_date: startDate,
      end_date: endDate,
      page: 1,
      page_size: 50,
      sort_by: 'net_amount',
      order: 'desc',
    }
    
    if (conceptKeyword.value) {
      params.concept = conceptKeyword.value.trim()
    }
    
    console.log('概念资金流日期范围查询（使用指定日期）:', { 
      start_date: params.start_date, 
      end_date: params.end_date,
      params: params
    })
    
    // 直接调用API，避免store中的参数处理问题
    const response = await fundFlowApi.getConcept(params)
    
    // 处理响应
    if (Array.isArray(response)) {
      // 单日期查询
      fundFlowStore.conceptList = response
      fundFlowStore.conceptPagination.total = response.length
      fundFlowStore.conceptPagination.current = 1
      fundFlowStore.conceptPagination.pageSize = params.limit || 50
    } else {
      // 日期范围查询
      fundFlowStore.conceptList = response.items || []
      fundFlowStore.conceptPagination.total = response.total || 0
      fundFlowStore.conceptPagination.current = response.page || 1
      fundFlowStore.conceptPagination.pageSize = response.page_size || 50
    }
    
    fundFlowStore.conceptQueryParams = params
    
    // 检查查询结果是否为空
    if (conceptData.value.length === 0) {
      ElMessage.warning(`所选日期范围（${startDate} 至 ${endDate}）没有数据，请调整日期范围`)
    }
  } catch (error: any) {
    console.error('刷新概念资金流失败:', error)
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('获取概念资金流失败，请稍后重试')
    }
  }
}

const handleConceptSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  conceptSort.value = sort
  // 排序在computed中处理，不需要重新请求
}

// 资金流趋势图配置
const conceptChartOption = computed(() => {
  if (!conceptTableData.value || conceptTableData.value.length === 0) {
    return {}
  }
  
  // 按概念分组，计算每个概念的平均资金流
  const conceptMap = new Map<string, { dates: string[], netAmounts: number[], inflows: number[], outflows: number[] }>()
  
  conceptTableData.value.forEach((item: any) => {
    if (!conceptMap.has(item.concept)) {
      conceptMap.set(item.concept, { dates: [], netAmounts: [], inflows: [], outflows: [] })
    }
    const conceptData = conceptMap.get(item.concept)!
    conceptData.dates.push(item.date || '')
    conceptData.netAmounts.push((item.net_amount || 0) / 100000000) // 转换为亿元
    conceptData.inflows.push((item.inflow || 0) / 100000000)
    conceptData.outflows.push((item.outflow || 0) / 100000000)
  })
  
  // 获取所有日期（去重并排序）
  const allDates = Array.from(new Set(conceptTableData.value.map((item: any) => item.date).filter(Boolean))).sort()
  
  // 如果只有一个概念，显示该概念的详细趋势
  if (conceptMap.size === 1) {
    const conceptName = Array.from(conceptMap.keys())[0]
    const data = conceptMap.get(conceptName)!
    
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `<div style="margin-bottom: 4px;"><strong>${params[0].axisValue}</strong></div>`
          params.forEach((param: any) => {
            const value = param.value || 0
            const color = param.color
            result += `<div style="margin-bottom: 2px;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${color}; margin-right: 5px;"></span>
              <span>${param.seriesName}: </span>
              <span style="font-weight: bold; color: ${value >= 0 ? '#F56C6C' : '#67C23A'}">${value >= 0 ? '+' : ''}${value.toFixed(2)}亿元</span>
            </div>`
          })
          return result
        },
      },
      legend: {
        data: ['净额', '流入', '流出'],
        top: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.dates,
        axisLabel: {
          rotate: 45,
          fontSize: 11,
        },
      },
      yAxis: {
        type: 'value',
        name: '金额(亿元)',
        nameTextStyle: {
          fontSize: 12,
        },
        axisLabel: {
          formatter: (value: number) => `${value.toFixed(1)}`,
          fontSize: 11,
        },
        splitLine: {
          show: true,
          lineStyle: {
            type: 'dashed',
            color: '#E4E7ED',
          },
        },
      },
      series: [
        {
          name: '净额',
          type: 'line',
          data: data.netAmounts,
          smooth: true,
          itemStyle: {
            color: '#409EFF',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' },
              ],
            },
          },
        },
        {
          name: '流入',
          type: 'line',
          data: data.inflows,
          smooth: true,
          itemStyle: {
            color: '#F56C6C',
          },
        },
        {
          name: '流出',
          type: 'line',
          data: data.outflows,
          smooth: true,
          itemStyle: {
            color: '#67C23A',
          },
        },
      ],
    }
  }
  
  // 多个概念时，显示Top 10概念的净额对比
  const topConcepts = Array.from(conceptMap.entries())
    .map(([name, data]) => ({
      name,
      avgNetAmount: data.netAmounts.reduce((a, b) => a + b, 0) / data.netAmounts.length,
    }))
    .sort((a, b) => Math.abs(b.avgNetAmount) - Math.abs(a.avgNetAmount))
    .slice(0, 10)
  
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `<div style="margin-bottom: 4px;"><strong>${params[0].axisValue}</strong></div>`
        params.forEach((param: any) => {
          const value = param.value || 0
          const color = param.color
          result += `<div style="margin-bottom: 2px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: ${color}; margin-right: 5px;"></span>
            <span>${param.seriesName}: </span>
            <span style="font-weight: bold; color: ${value >= 0 ? '#F56C6C' : '#67C23A'}">${value >= 0 ? '+' : ''}${value.toFixed(2)}亿元</span>
          </div>`
        })
        return result
      },
    },
    legend: {
      data: topConcepts.map(c => c.name),
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
      fontSize: 11,
      itemWidth: 14,
      itemHeight: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: allDates,
      axisLabel: {
        rotate: 45,
        fontSize: 11,
      },
    },
    yAxis: {
      type: 'value',
      name: '净额(亿元)',
      nameTextStyle: {
        fontSize: 12,
      },
      axisLabel: {
        formatter: (value: number) => `${value.toFixed(1)}`,
        fontSize: 11,
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#E4E7ED',
        },
      },
    },
    series: topConcepts.map((concept) => {
      const data = conceptMap.get(concept.name)!
      // 按日期对齐数据
      const alignedData = allDates.map(date => {
        const idx = data.dates.indexOf(date)
        return idx >= 0 ? data.netAmounts[idx] : null
      })
      
      return {
        name: concept.name,
        type: 'line',
        data: alignedData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
      }
    }),
  }
})

// 概念资金流高级筛选相关
interface ConceptExtendedCondition {
  date_range?: {
    start?: string
    end?: string
  }
  net_amount?: {
    min?: number
    max?: number
  }
  inflow?: {
    min?: number
    max?: number
  }
  outflow?: {
    min?: number
    max?: number
  }
  index_change_percent?: {
    min?: number
    max?: number
  }
  stock_count?: {
    min?: number
    max?: number
  }
  displayNetMin?: number
  displayNetMax?: number
  displayInflowMin?: number
  displayInflowMax?: number
}

const conceptFilterDialogVisible = ref(false)
const conceptFilterForm = ref<{
  conditions: ConceptExtendedCondition[]
  concepts?: string[]
  page: number
  page_size: number
  sort_by: string
  order: 'asc' | 'desc'
}>({
  conditions: [
    {
      date_range: {
        start: dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
        end: dayjs().format('YYYY-MM-DD'),
      },
      displayNetMin: undefined,
      displayNetMax: undefined,
      displayInflowMin: undefined,
      displayInflowMax: undefined,
      index_change_percent: {
        min: undefined,
        max: undefined,
      },
    },
  ],
  page: 1,
  page_size: 20,
  sort_by: 'net_amount',
  order: 'desc',
})

const showConceptFilterDialog = () => {
  conceptFilterDialogVisible.value = true
}

const addConceptCondition = () => {
  conceptFilterForm.value.conditions.push({
    date_range: {
      start: dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
      end: dayjs().format('YYYY-MM-DD'),
    },
    displayNetMin: undefined,
    displayNetMax: undefined,
    displayInflowMin: undefined,
    displayInflowMax: undefined,
    index_change_percent: {
      min: undefined,
      max: undefined,
    },
  })
}

const removeConceptCondition = (index: number) => {
  if (conceptFilterForm.value.conditions.length > 1) {
    conceptFilterForm.value.conditions.splice(index, 1)
  }
}

const convertConceptToYuan = (
  condition: ConceptExtendedCondition,
  type: 'net' | 'inflow',
  field: 'min' | 'max'
) => {
  const displayValue = type === 'net'
    ? (field === 'min' ? condition.displayNetMin : condition.displayNetMax)
    : (field === 'min' ? condition.displayInflowMin : condition.displayInflowMax)
  
  if (displayValue === undefined || displayValue === null) {
    if (type === 'net') {
      if (!condition.net_amount) condition.net_amount = {}
      condition.net_amount[field] = undefined
    } else {
      if (!condition.inflow) condition.inflow = {}
      condition.inflow[field] = undefined
    }
    return
  }

  const yuanValue = displayValue * 100000000 // 转换为元（亿 * 100000000）

  if (type === 'net') {
    if (!condition.net_amount) condition.net_amount = {}
    condition.net_amount[field] = Math.round(yuanValue)
  } else {
    if (!condition.inflow) condition.inflow = {}
    condition.inflow[field] = Math.round(yuanValue)
  }
}

const resetConceptFilter = () => {
  conceptFilterForm.value = {
    conditions: [
      {
        date_range: {
          start: dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
          end: dayjs().format('YYYY-MM-DD'),
        },
        displayNetMin: undefined,
        displayNetMax: undefined,
        displayInflowMin: undefined,
        displayInflowMax: undefined,
        index_change_percent: {
          min: undefined,
          max: undefined,
        },
      },
    ],
    page: 1,
    page_size: 20,
    sort_by: 'net_amount',
    order: 'desc',
  }
}

const handleConceptFilter = async () => {
  // 验证条件
  for (const condition of conceptFilterForm.value.conditions) {
    // 如果填写了日期范围，则验证日期范围的有效性
    if (condition.date_range?.start && condition.date_range?.end) {
      if (condition.date_range.start > condition.date_range.end) {
        ElMessage.warning('开始日期不能大于结束日期')
        return
      }
    }
    
    // 确保显示值已转换为元
    if (condition.displayNetMin !== undefined && condition.displayNetMin !== null) {
      convertConceptToYuan(condition, 'net', 'min')
    }
    if (condition.displayNetMax !== undefined && condition.displayNetMax !== null) {
      convertConceptToYuan(condition, 'net', 'max')
    }
    if (condition.displayInflowMin !== undefined && condition.displayInflowMin !== null) {
      convertConceptToYuan(condition, 'inflow', 'min')
    }
    if (condition.displayInflowMax !== undefined && condition.displayInflowMax !== null) {
      convertConceptToYuan(condition, 'inflow', 'max')
    }
  }

  try {
    const request: ConceptFundFlowFilterRequest = {
      conditions: conceptFilterForm.value.conditions.map((cond) => {
        const condition: any = {}
        
        // 只有当日期范围完整时才添加
        if (cond.date_range?.start && cond.date_range?.end) {
          condition.date_range = cond.date_range
        }
        
        if (cond.net_amount && (cond.net_amount.min !== undefined || cond.net_amount.max !== undefined)) {
          condition.net_amount = cond.net_amount
        }
        if (cond.inflow && (cond.inflow.min !== undefined || cond.inflow.max !== undefined)) {
          condition.inflow = cond.inflow
        }
        if (cond.outflow && (cond.outflow.min !== undefined || cond.outflow.max !== undefined)) {
          condition.outflow = cond.outflow
        }
        if (cond.index_change_percent && (cond.index_change_percent.min !== undefined || cond.index_change_percent.max !== undefined)) {
          condition.index_change_percent = cond.index_change_percent
        }
        if (cond.stock_count && (cond.stock_count.min !== undefined || cond.stock_count.max !== undefined)) {
          condition.stock_count = cond.stock_count
        }
        
        return condition
      }),
      concepts: conceptFilterForm.value.concepts,
      page: conceptFilterForm.value.page,
      page_size: conceptFilterForm.value.page_size,
      sort_by: conceptFilterForm.value.sort_by,
      order: conceptFilterForm.value.order,
    }
    
    await fundFlowStore.filterConcept(request)
    conceptFilterDialogVisible.value = false
    ElMessage.success('筛选完成')
  } catch (error) {
    console.error('概念资金流筛选失败:', error)
    ElMessage.error('筛选失败，请检查条件设置')
  }
}
</script>

<style scoped>
.fund-flow-page {
  padding: 20px;
}

.section-card {
  margin-top: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-conditions {
  margin-bottom: 20px;
}

.condition-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.condition-label {
  min-width: 80px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.condition-fields {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 8px;
  flex-wrap: wrap;
}

.field-separator {
  color: #909399;
  font-size: 14px;
  margin: 0 4px;
}

.amount-input-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.unit-label {
  color: #606266;
  font-size: 14px;
  min-width: 20px;
}

.chart-container {
  padding: 10px 0;
}

.concept-chart {
  width: 100%;
  height: 400px;
}

</style>
