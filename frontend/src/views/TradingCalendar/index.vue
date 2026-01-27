<template>
  <div class="trading-calendar">
    <el-card>
      <div class="tabs-container">
        <el-tabs v-model="viewMode" @tab-change="handleViewModeChange" class="view-tabs" v-if="activeMainMenu === 'calendar'">
          <el-tab-pane label="交易日历" name="calendar">
            <template #label>
              <span class="tab-label">
                <el-icon><Calendar /></el-icon>
                <span>交易日历</span>
              </span>
            </template>
          <div class="calendar-view" v-if="viewMode === 'calendar'">
            <!-- 周导航 -->
            <div class="week-navigation">
              <el-button 
                @click="goToPreviousWeek" 
                :icon="ArrowLeft" 
                circle
                size="small"
              />
              <div class="week-info">
                <span class="week-label">{{ currentWeekLabel }}</span>
                <el-button 
                  @click="goToCurrentWeek" 
                  size="small"
                  type="primary"
                  plain
                >
                  今天
                </el-button>
              </div>
              <el-button 
                @click="goToNextWeek" 
                :icon="ArrowRight" 
                circle
                size="small"
              />
            </div>
            
            <!-- 周视图 -->
            <div class="week-calendar-view">
              <div class="week-header">
                <div class="week-day-header" v-for="day in weekDays" :key="day.date">
                  <div class="day-name">{{ day.name }}</div>
                  <div class="day-date">{{ day.date.split('-').slice(2).join('-') }}</div>
                </div>
              </div>
              <div class="week-body">
                <div class="week-day-cell" v-for="day in weekDays" :key="day.date">
                  <div class="calendar-items-container">
                    <!-- 买入列 -->
                    <div class="calendar-column buy-column">
                      <div class="column-header">买入</div>
                      <div class="calendar-items">
                        <template v-for="item in getBuyItemsByDate(day.date)" :key="item.id">
                          <div
                            class="calendar-item buy"
                            :class="{ 'executed': item.is_executed }"
                            @click.stop="handleEdit(item)"
                          >
                            <div class="item-main">
                              <span class="item-stock">{{ item.stock_name }}</span>
                              <el-tag
                                :type="getStrategyTagType(item.strategy)"
                                size="small"
                                effect="plain"
                                class="strategy-tag"
                              >
                                {{ item.strategy }}
                              </el-tag>
                            </div>
                          </div>
                        </template>
                      </div>
                    </div>
                    <!-- 卖出列 -->
                    <div class="calendar-column sell-column">
                      <div class="column-header">卖出</div>
                      <div class="calendar-items">
                        <template v-for="item in getSellItemsByDate(day.date)" :key="item.id">
                          <div
                            class="calendar-item sell"
                            :class="{ 'executed': item.is_executed }"
                            @click.stop="handleEdit(item)"
                          >
                            <div class="item-main">
                              <span class="item-stock">{{ item.stock_name }}</span>
                            </div>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="表格视图" name="table">
          <template #label>
            <span class="tab-label">
              <el-icon><List /></el-icon>
              <span>表格视图</span>
            </span>
          </template>
          <div class="table-view">
            <div class="filter-bar">
              <el-select
                v-model="source"
                placeholder="来源"
                clearable
                style="width: 150px"
                @change="handleSearch"
              >
                <el-option label="自己" value="自己" />
                <el-option label="云聪" value="云聪" />
                <el-option label="韩叔" value="韩叔" />
              </el-select>
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
              <el-select
                v-model="strategy"
                placeholder="策略"
                clearable
                style="width: 150px"
                @change="handleSearch"
              >
                <el-option label="低吸" value="低吸" />
                <el-option label="排板" value="排板" />
                <el-option label="加仓" value="加仓" />
              </el-select>
              <el-date-picker
                v-model="startDate"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 200px"
                @change="handleSearch"
              />
              <el-date-picker
                v-model="endDate"
                type="date"
                placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 200px"
                :disabled-date="disabledEndDate"
                @change="handleSearch"
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
              :data="groupedTableData" 
              :loading="loading" 
              stripe 
              border
              row-key="id"
              :span-method="handleSpanMethod"
            >
              <el-table-column prop="weekLabel" label="日期/周" width="180" align="center">
                <template #default="{ row }">
                  <div v-if="row.isWeekHeader" class="week-header">
                    <strong>{{ row.weekLabel }}</strong>
                    <span class="week-count">({{ row.weekItemCount }}条记录)</span>
                  </div>
                  <span v-else>{{ row.date }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="stock_name" label="股票名称" width="150" sortable="custom">
                <template #default="{ row }">
                  <span v-if="!row.isWeekHeader">{{ row.stock_name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="direction" label="操作方向" width="120" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.direction === '买入'" type="danger" size="small">买入</el-tag>
                  <el-tag v-else-if="row.direction === '卖出'" type="success" size="small">卖出</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="strategy" label="策略" width="120" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.strategy === '低吸'" type="success" size="small">低吸</el-tag>
                  <el-tag v-else-if="row.strategy === '排板'" type="warning" size="small">排板</el-tag>
                  <el-tag v-else-if="row.strategy === '加仓'" type="info" size="small">加仓</el-tag>
                  <span v-else style="color: #909399;">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="is_executed" label="是否执行" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.is_executed" type="success" size="small">已执行</el-tag>
                  <el-tag v-else type="info" size="small">未执行</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="price" label="价格" width="100" align="right">
                <template #default="{ row }">
                  <span v-if="row.price">{{ row.price.toFixed(2) }}</span>
                  <span v-else style="color: #999;">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="source" label="来源" width="150" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="!row.isWeekHeader">{{ row.source }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="!row.isWeekHeader">{{ row.notes }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button v-if="!row.isWeekHeader" type="primary" link size="small" @click="handleEdit(row)">
                    编辑
                  </el-button>
                  <el-button v-if="!row.isWeekHeader" type="danger" link size="small" @click="handleDelete(row)">
                    删除
                  </el-button>
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
          </div>
        </el-tab-pane>
      </el-tabs>
      <!-- 我的日历菜单项直接显示我的交易日志视图 -->
      <div v-if="activeMainMenu === 'my-calendar'" class="my-calendar-view">
        <div class="table-view">
          <div class="filter-bar">
            <el-select
              v-model="myTradingSource"
              placeholder="来源"
              clearable
              style="width: 150px"
              @change="handleMyTradingSearch"
            >
              <el-option label="自己" value="自己" />
              <el-option label="云聪" value="云聪" />
              <el-option label="韩叔" value="韩叔" />
            </el-select>
            <el-select
              v-model="myTradingDirection"
              placeholder="操作方向"
              clearable
              style="width: 150px"
              @change="handleMyTradingSearch"
            >
              <el-option label="买入" value="买入" />
              <el-option label="卖出" value="卖出" />
            </el-select>
            <el-select
              v-model="myTradingStrategy"
              placeholder="策略"
              clearable
              style="width: 150px"
              @change="handleMyTradingSearch"
            >
              <el-option label="低吸" value="低吸" />
              <el-option label="排板" value="排板" />
              <el-option label="加仓" value="加仓" />
            </el-select>
            <el-date-picker
              v-model="myTradingStartDate"
              type="date"
              placeholder="开始日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 200px"
              @change="handleMyTradingSearch"
            />
            <el-date-picker
              v-model="myTradingEndDate"
              type="date"
              placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 200px"
              :disabled-date="(date) => disabledEndDateForMyTrading(date)"
              @change="handleMyTradingSearch"
            />
            <el-input
              v-model="myTradingStockName"
              placeholder="股票名称（模糊查询）"
              clearable
              style="width: 200px"
              @clear="handleMyTradingSearch"
            />

            <el-button type="primary" @click="handleMyTradingSearch" :loading="myTradingLoading">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
          </div>
          <el-table 
            :data="myTradingTableData" 
            :loading="myTradingLoading" 
            stripe 
            border
            @sort-change="handleMyTradingSortChange"
          >
            <el-table-column prop="date" label="日期" width="120" sortable="custom" />
            <el-table-column prop="stock_name" label="股票名称" width="150" sortable="custom" />
            <el-table-column prop="direction" label="操作方向" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.direction === '买入'" type="danger" size="small">买入</el-tag>
                <el-tag v-else-if="row.direction === '卖出'" type="success" size="small">卖出</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="strategy" label="策略" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.strategy === '低吸'" type="success" size="small">低吸</el-tag>
                <el-tag v-else-if="row.strategy === '排板'" type="warning" size="small">排板</el-tag>
                <el-tag v-else-if="row.strategy === '加仓'" type="info" size="small">加仓</el-tag>
                <span v-else style="color: #909399;">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="is_executed" label="是否执行" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_executed" type="success" size="small">已执行</el-tag>
                <el-tag v-else type="info" size="small">未执行</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="100" align="right">
              <template #default="{ row }">
                <span v-if="row.price">{{ row.price.toFixed(2) }}</span>
                <span v-else style="color: #999;">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="150" show-overflow-tooltip />
            <el-table-column prop="notes" label="备注" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleEdit(row)">
                  编辑
                </el-button>
                <el-button type="danger" link size="small" @click="handleDelete(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="myTradingPagination.current"
            v-model:page-size="myTradingPagination.pageSize"
            :total="myTradingPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleMyTradingSizeChange"
            @current-change="handleMyTradingPageChange"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
      <el-button type="primary" @click="handleAdd" class="add-button">
        <el-icon><Plus /></el-icon>
        新增
      </el-button>
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="股票名称" prop="stock_name">
          <el-input 
            v-model="formData.stock_name" 
            placeholder="请输入股票名称" 
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="操作方向" prop="direction">
          <el-select 
            v-model="formData.direction" 
            placeholder="请选择操作方向" 
            style="width: 100%"
            @change="handleDirectionChange"
          >
            <el-option label="买入" value="买入" />
            <el-option label="卖出" value="卖出" />
          </el-select>
        </el-form-item>
        <el-form-item label="策略" prop="strategy">
          <el-select 
            v-model="formData.strategy" 
            :placeholder="formData.direction === '卖出' ? '请选择策略（卖出时可选）' : '请选择策略'" 
            :clearable="formData.direction === '卖出'"
            style="width: 100%"
          >
            <el-option label="低吸" value="低吸" />
            <el-option label="排板" value="排板" />
            <el-option label="加仓" value="加仓" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源" prop="source">
          <el-select v-model="formData.source" placeholder="请选择来源（可选）" clearable style="width: 100%">
            <el-option label="自己" value="自己" />
            <el-option label="云聪" value="云聪" />
            <el-option label="韩叔" value="韩叔" />
          </el-select>
          <el-input 
            v-if="!formData.source || (formData.source !== '自己' && formData.source !== '云聪' && formData.source !== '韩叔')"
            v-model="formData.source" 
            placeholder="或输入其他来源" 
            maxlength="100"
            show-word-limit
            style="margin-top: 10px"
          />
        </el-form-item>
        <el-form-item label="是否执行" prop="is_executed">
          <el-switch
            v-model="formData.is_executed"
            active-text="已执行"
            inactive-text="未执行"
          />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number
            v-model="formData.price"
            placeholder="请输入价格"
            :precision="2"
            :step="0.01"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="formData.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Calendar, List, User, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { tradingCalendarApi, type TradingCalendarItem, type TradingCalendarCreate, type TradingCalendarUpdate } from '@/api/tradingCalendar'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

// 根据路由查询参数设置初始菜单和tab
const getInitialMenu = (): string => {
  const menu = route.query.menu as string
  const validMenus = ['calendar', 'my-calendar']
  return menu && validMenus.includes(menu) ? menu : 'calendar'
}

const activeMainMenu = ref(getInitialMenu())

// 根据主菜单设置初始tab
const getInitialTab = (): 'calendar' | 'table' => {
  // 对于calendar菜单，根据tab参数设置，默认为table
  const tab = route.query.tab as string
  const validTabs = ['calendar', 'table']
  return tab && validTabs.includes(tab) ? tab as 'calendar' | 'table' : 'table'
}

const loading = ref(false)
const submitting = ref(false)
const viewMode = ref<'calendar' | 'table'>(getInitialTab())
const calendarDate = ref(new Date())
const tableData = ref<TradingCalendarItem[]>([])
const allCalendarData = ref<TradingCalendarItem[]>([]) // 用于日历视图的所有数据

// 周视图相关状态
const currentWeekStart = ref(dayjs().startOf('week').add(1, 'day').format('YYYY-MM-DD')) // 周一开始

// 计算当前周的日期范围标签
const currentWeekLabel = computed(() => {
  const start = dayjs(currentWeekStart.value)
  const end = start.add(6, 'day')
  return `${start.format('YYYY-MM-DD')} 至 ${end.format('YYYY-MM-DD')}`
})

// 计算当前周的所有日期（周一到周日）
const weekDays = computed(() => {
  const days = []
  const start = dayjs(currentWeekStart.value)
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  for (let i = 0; i < 7; i++) {
    const date = start.add(i, 'day')
    days.push({
      date: date.format('YYYY-MM-DD'),
      name: dayNames[i],
      dayjs: date
    })
  }
  return days
})

// 导航到上一周
const goToPreviousWeek = () => {
  currentWeekStart.value = dayjs(currentWeekStart.value).subtract(7, 'day').format('YYYY-MM-DD')
  updateWeekDateRange()
}

// 导航到下一周
const goToNextWeek = () => {
  currentWeekStart.value = dayjs(currentWeekStart.value).add(7, 'day').format('YYYY-MM-DD')
  updateWeekDateRange()
}

// 导航到当前周
const goToCurrentWeek = () => {
  currentWeekStart.value = dayjs().startOf('week').add(1, 'day').format('YYYY-MM-DD')
  updateWeekDateRange()
}

// 更新周日期范围并重新获取数据
const updateWeekDateRange = () => {
  const start = dayjs(currentWeekStart.value)
  const end = start.add(6, 'day')
  startDate.value = start.format('YYYY-MM-DD')
  endDate.value = end.format('YYYY-MM-DD')
  if (viewMode.value === 'calendar') {
    fetchData()
  }
}
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

// 获取日期所在周的周一日期（ISO周，周一开始）
const getWeekStart = (date: string): string => {
  const d = dayjs(date)
  const day = d.day()
  // dayjs的day()返回：0=周日, 1=周一, ..., 6=周六
  // 转换为ISO周（周一开始）：如果day=0（周日），则往前推6天；否则往前推(day-1)天
  const diff = day === 0 ? 6 : day - 1
  return d.subtract(diff, 'day').format('YYYY-MM-DD')
}

// 获取周的标签（周一到周日）
const getWeekLabel = (date: string): string => {
  const start = dayjs(getWeekStart(date))
  const end = start.add(6, 'day')
  return `${start.format('YYYY-MM-DD')} 至 ${end.format('YYYY-MM-DD')}`
}

// 按周分组的数据
const groupedTableData = computed(() => {
  if (!tableData.value || tableData.value.length === 0) {
    return []
  }
  
  // 按日期排序
  const sortedData = [...tableData.value].sort((a, b) => {
    return dayjs(a.date).isBefore(dayjs(b.date)) ? -1 : 1
  })
  
  // 按周分组
  const weekGroups = new Map<string, TradingCalendarItem[]>()
  sortedData.forEach(item => {
    const weekStart = getWeekStart(item.date)
    if (!weekGroups.has(weekStart)) {
      weekGroups.set(weekStart, [])
    }
    weekGroups.get(weekStart)!.push(item)
  })
  
  // 构建分组后的数据，每周先插入一个分组头，然后插入该周的数据
  const result: (TradingCalendarItem & { isWeekHeader?: boolean; weekLabel?: string; weekItemCount?: number })[] = []
  
  // 按周开始日期排序
  const sortedWeeks = Array.from(weekGroups.keys()).sort((a, b) => {
    return dayjs(a).isBefore(dayjs(b)) ? 1 : -1 // 最新的周在前面
  })
  
  sortedWeeks.forEach(weekStart => {
    const items = weekGroups.get(weekStart)!
    const firstItem = items[0]
    
    // 添加周分组头（使用负数ID避免与真实ID冲突）
    const weekStartTimestamp = dayjs(weekStart).valueOf()
    result.push({
      ...firstItem,
      isWeekHeader: true,
      weekLabel: getWeekLabel(firstItem.date),
      weekItemCount: items.length,
      id: -Math.abs(weekStartTimestamp), // 使用负数ID标识分组头
    } as any)
    
    // 添加该周的数据
    items.forEach(item => {
      result.push(item)
    })
  })
  
  return result
})

// 处理表格单元格合并
const handleSpanMethod = ({ row, column, rowIndex, columnIndex }: any) => {
  if (row.isWeekHeader) {
    // 周分组头行：第一列合并所有列
    if (columnIndex === 0) {
      return {
        rowspan: 1,
        colspan: 9, // 合并所有9列
      }
    } else {
      // 其他列不显示
      return {
        rowspan: 0,
        colspan: 0,
      }
    }
  }
  // 普通数据行不合并
  return {
    rowspan: 1,
    colspan: 1,
  }
}

const startDate = ref('')
const endDate = ref('')
const stockName = ref('')
const direction = ref<'买入' | '卖出' | ''>('')
const strategy = ref<'低吸' | '排板' | '加仓' | ''>('')
const source = ref<string>('')
const sortBy = ref<string | undefined>(undefined)
const sortOrder = ref<'asc' | 'desc'>('desc')

const dialogVisible = ref(false)
const dialogTitle = ref('新增交易日历')
const formRef = ref()
const formData = ref<TradingCalendarCreate & { id?: number }>({
  date: dayjs().format('YYYY-MM-DD'),
  stock_name: '',
  direction: '买入',
  strategy: '低吸',
  price: undefined,
  is_executed: false,
  source: '',
  notes: '',
})

const validateStockName = (rule: any, value: any, callback: any) => {
  if (!value || !value.trim()) {
    callback(new Error('请输入股票名称'))
  } else if (value.trim().length > 50) {
    callback(new Error('股票名称不能超过50个字符'))
  } else {
    callback()
  }
}

const validateDate = (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请选择日期'))
  } else {
    callback()
  }
}

const validateStrategy = (rule: any, value: any, callback: any) => {
  // 卖出操作时策略可以为空
  if (formData.value.direction === '卖出') {
    if (value && value !== '低吸' && value !== '排板' && value !== '加仓') {
      callback(new Error('策略必须是"低吸"、"排板"或"加仓"'))
    } else {
      callback()
    }
  } else {
    // 买入操作时策略必填
    if (!value) {
      callback(new Error('请选择策略'))
    } else if (value !== '低吸' && value !== '排板' && value !== '加仓') {
      callback(new Error('策略必须是"低吸"、"排板"或"加仓"'))
    } else {
      callback()
    }
  }
}

// 动态生成表单规则
const formRules = computed(() => ({
  date: [{ validator: validateDate, trigger: 'change' }],
  stock_name: [{ validator: validateStockName, trigger: 'blur' }],
  direction: [{ required: true, message: '请选择操作方向', trigger: 'change' }],
  strategy: [
    { 
      validator: validateStrategy, 
      trigger: 'change',
      // 买入时必填，卖出时可选
      required: formData.value.direction === '买入'
    }
  ],
}))

// 获取日历数据（分批加载所有数据）
const fetchCalendarData = async () => {
  const MAX_PAGE_SIZE = 100 // 后端限制的最大页面大小
  const baseParams: any = {
    page_size: MAX_PAGE_SIZE,
  }
  
  // 如果没有设置日期范围，默认获取当前周的数据
  if (!startDate.value && !endDate.value) {
    const now = dayjs()
    const weekStart = now.startOf('week').add(1, 'day') // 周一开始
    baseParams.start_date = weekStart.format('YYYY-MM-DD')
    baseParams.end_date = weekStart.add(6, 'day').format('YYYY-MM-DD')
    // 同步更新周视图的当前周
    currentWeekStart.value = weekStart.format('YYYY-MM-DD')
  } else {
    if (startDate.value) baseParams.start_date = startDate.value
    if (endDate.value) baseParams.end_date = endDate.value
  }
  
  if (stockName.value && stockName.value.trim()) baseParams.stock_name = stockName.value.trim()
  if (direction.value) baseParams.direction = direction.value
  if (strategy.value) baseParams.strategy = strategy.value
  if (source.value && source.value.trim()) baseParams.source = source.value.trim()

  // 分批加载所有数据
  const allItems: TradingCalendarItem[] = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const params = { ...baseParams, page }
    const response = await tradingCalendarApi.getList(params)
    
    allItems.push(...response.items)
    
    // 如果返回的数据少于 page_size，说明已经是最后一页
    if (response.items.length < MAX_PAGE_SIZE) {
      hasMore = false
    } else {
      page++
    }
  }

  allCalendarData.value = allItems
}

// 我的交易日志相关状态
const myTradingLoading = ref(false)
const myTradingTableData = ref<TradingCalendarItem[]>([])
const myTradingPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})
const myTradingStartDate = ref('')
const myTradingEndDate = ref('')
const myTradingStockName = ref('')
const myTradingDirection = ref<'买入' | '卖出' | ''>('')
const myTradingStrategy = ref<'低吸' | '排板' | '加仓' | ''>('')
const myTradingSource = ref<string>('自己') // 默认设置为"自己"
const myTradingSortBy = ref<string | undefined>(undefined)
const myTradingSortOrder = ref<'asc' | 'desc'>('desc')

const fetchData = async () => {
  loading.value = true
  try {
    // 如果是日历视图，需要获取所有数据（分批加载）
    if (viewMode.value === 'calendar') {
      await fetchCalendarData()
    } else if (viewMode.value === 'table') {
      await fetchTableData()
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取数据失败'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

// 获取表格数据（分页）
const fetchTableData = async () => {
  const params: any = {
    page: pagination.value.current,
    page_size: pagination.value.pageSize,
  }
  
  if (startDate.value) params.start_date = startDate.value
  if (endDate.value) params.end_date = endDate.value
  if (stockName.value && stockName.value.trim()) params.stock_name = stockName.value.trim()
  if (direction.value) params.direction = direction.value
  if (strategy.value) params.strategy = strategy.value
  if (source.value && source.value.trim()) params.source = source.value.trim()
  
  // 添加排序参数
  if (sortBy.value) {
    params.sort_by = sortBy.value
    params.order = sortOrder.value
  }

  const response = await tradingCalendarApi.getList(params)
  tableData.value = response.items
  pagination.value.total = response.total
}

// 根据日期获取该日期的交易记录信息（包含显示项和剩余数量）
const getDateItemsInfo = (date: string | undefined): { items: TradingCalendarItem[], remaining: number } => {
  if (!date || !allCalendarData.value || allCalendarData.value.length === 0) {
    return { items: [], remaining: 0 }
  }
  const items = allCalendarData.value.filter(item => item.date === date)
  const total = items.length
  return {
    items: items.slice(0, 8), // 最多返回8条记录
    remaining: total > 8 ? total - 8 : 0
  }
}

// 根据日期获取该日期的交易记录（最多8条）- 保持向后兼容
const getItemsByDate = (date: string | undefined): TradingCalendarItem[] => {
  return getDateItemsInfo(date).items
}

// 获取某天的剩余记录数（用于显示提示）
const getRemainingItemsCount = (date: string | undefined): number => {
  return getDateItemsInfo(date).remaining
}

// 根据日期获取买入记录
const getBuyItemsByDate = (date: string | undefined): TradingCalendarItem[] => {
  if (!date || !allCalendarData.value || allCalendarData.value.length === 0) {
    return []
  }
  return allCalendarData.value.filter(item => item.date === date && item.direction === '买入')
}

// 根据日期获取卖出记录
const getSellItemsByDate = (date: string | undefined): TradingCalendarItem[] => {
  if (!date || !allCalendarData.value || allCalendarData.value.length === 0) {
    return []
  }
  return allCalendarData.value.filter(item => item.date === date && item.direction === '卖出')
}

// 判断是否是周末（非交易日）
const isWeekend = (date: string | undefined): boolean => {
  if (!date) return false
  const day = dayjs(date).day()
  // 0 = 周日, 6 = 周六
  return day === 0 || day === 6
}

// 周视图不需要这个函数，但保留以防其他地方使用

const handleSearch = () => {
  // 验证日期范围
  if (startDate.value && endDate.value) {
    if (dayjs(startDate.value).isAfter(dayjs(endDate.value))) {
      ElMessage.warning('开始日期不能大于结束日期')
      return
    }
  }
  pagination.value.current = 1
  fetchData()
}

// 处理排序变化
const handleSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (!sort.prop || !sort.order) {
    // 清除排序
    sortBy.value = undefined
    sortOrder.value = 'desc'
  } else {
    // 设置排序
    sortBy.value = sort.prop
    sortOrder.value = sort.order === 'ascending' ? 'asc' : 'desc'
  }
  // 重置到第一页并重新获取数据
  pagination.value.current = 1
  fetchData()
}

// 获取我的交易日志数据（分页）
const fetchMyTradingData = async () => {
  myTradingLoading.value = true
  try {
    const params: any = {
      page: myTradingPagination.value.current,
      page_size: myTradingPagination.value.pageSize,
      source: '自己', // 固定过滤来源为"自己"
    }
    
    if (myTradingStartDate.value) params.start_date = myTradingStartDate.value
    if (myTradingEndDate.value) params.end_date = myTradingEndDate.value
    if (myTradingStockName.value && myTradingStockName.value.trim()) params.stock_name = myTradingStockName.value.trim()
    if (myTradingDirection.value) params.direction = myTradingDirection.value
    if (myTradingStrategy.value) params.strategy = myTradingStrategy.value
    
    // 添加排序参数
    if (myTradingSortBy.value) {
      params.sort_by = myTradingSortBy.value
      params.order = myTradingSortOrder.value
    }

    const response = await tradingCalendarApi.getList(params)
    myTradingTableData.value = response.items
    myTradingPagination.value.total = response.total
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取数据失败'
    ElMessage.error(errorMsg)
  } finally {
    myTradingLoading.value = false
  }
}

// 我的交易日志搜索
const handleMyTradingSearch = () => {
  // 验证日期范围
  if (myTradingStartDate.value && myTradingEndDate.value) {
    if (dayjs(myTradingStartDate.value).isAfter(dayjs(myTradingEndDate.value))) {
      ElMessage.warning('开始日期不能大于结束日期')
      return
    }
  }
  myTradingPagination.value.current = 1
  fetchMyTradingData()
}

// 我的交易日志排序变化
const handleMyTradingSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (!sort.prop || !sort.order) {
    // 清除排序
    myTradingSortBy.value = undefined
    myTradingSortOrder.value = 'desc'
  } else {
    // 设置排序
    myTradingSortBy.value = sort.prop
    myTradingSortOrder.value = sort.order === 'ascending' ? 'asc' : 'desc'
  }
  // 重置到第一页并重新获取数据
  myTradingPagination.value.current = 1
  fetchMyTradingData()
}

// 我的交易日志分页变化
const handleMyTradingSizeChange = () => {
  fetchMyTradingData()
}

const handleMyTradingPageChange = () => {
  fetchMyTradingData()
}

// 我的交易日志结束日期禁用
const disabledEndDateForMyTrading = (date: Date) => {
  if (!myTradingStartDate.value) return false
  return dayjs(date).isBefore(dayjs(myTradingStartDate.value))
}

// 监听视图模式切换
const handleViewModeChange = () => {
  pagination.value.current = 1
  // 更新路由查询参数
  router.push({
    path: route.path,
    query: {
      ...route.query,
      tab: viewMode.value
    }
  })
  // 如果切换到日历视图且没有设置日期范围，自动设置为当前周
  if (viewMode.value === 'calendar' && !startDate.value && !endDate.value) {
    const now = dayjs()
    const weekStart = now.startOf('week').add(1, 'day') // 周一开始
    startDate.value = weekStart.format('YYYY-MM-DD')
    endDate.value = weekStart.add(6, 'day').format('YYYY-MM-DD')
    currentWeekStart.value = weekStart.format('YYYY-MM-DD')
  }
  fetchData()
}

// 监听路由变化
watch(() => route.query.menu, (newMenu) => {
  if (newMenu) {
    activeMainMenu.value = newMenu as string
    if (newMenu === 'my-calendar') {
      fetchMyTradingData()
    } else if (newMenu === 'calendar') {
      const tab = route.query.tab as string
      if (tab && ['calendar', 'table'].includes(tab)) {
        viewMode.value = tab as 'calendar' | 'table'
      } else {
        viewMode.value = 'table'
      }
      fetchData()
    }
  }
}, { immediate: true })

watch(() => route.query.tab, (newTab) => {
  if (activeMainMenu.value === 'calendar' && newTab && ['calendar', 'table'].includes(newTab as string)) {
    viewMode.value = newTab as 'calendar' | 'table'
    fetchData()
  }
})

// 监听周开始日期变化，更新日期范围并重新获取数据
watch(currentWeekStart, (newWeekStart) => {
  // 如果当前是日历视图，更新日期范围
  if (viewMode.value === 'calendar') {
    const start = dayjs(newWeekStart)
    const end = start.add(6, 'day')
    const newStartStr = start.format('YYYY-MM-DD')
    const newEndStr = end.format('YYYY-MM-DD')
    
    // 只有当日期真正改变时才更新
    if (startDate.value !== newStartStr || endDate.value !== newEndStr) {
      startDate.value = newStartStr
      endDate.value = newEndStr
      // 重新获取数据
      fetchData()
    }
  }
}, { immediate: false })

const handleSizeChange = () => {
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增交易日历'
  formData.value = {
    date: dayjs().format('YYYY-MM-DD'),
    stock_name: '',
    direction: '买入',
    strategy: '低吸',
    price: undefined,
    is_executed: false,
    source: '',
    notes: '',
  }
  dialogVisible.value = true
}

const handleEdit = (row: TradingCalendarItem & { isWeekHeader?: boolean }) => {
  // 防止编辑周分组头
  if (row.isWeekHeader) {
    return
  }
  dialogTitle.value = '编辑交易日历'
  formData.value = {
    id: row.id,
    date: row.date,
    stock_name: row.stock_name,
    direction: row.direction,
    strategy: row.strategy,
    price: row.price,
    is_executed: row.is_executed ?? false,
    source: row.source || '',
    notes: row.notes || '',
  }
  dialogVisible.value = true
}

const handleDelete = async (row: TradingCalendarItem & { isWeekHeader?: boolean }) => {
  // 防止删除周分组头
  if (row.isWeekHeader) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${row.stock_name}" 的交易记录吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await tradingCalendarApi.delete(row.id)
    ElMessage.success('删除成功')
    // 根据当前菜单刷新数据
    if (activeMainMenu.value === 'my-calendar') {
      fetchMyTradingData()
    } else {
      fetchData()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error?.response?.data?.detail || error?.message || '删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    // 数据完整性检查
    if (!formData.value.date) {
      ElMessage.warning('请选择日期')
      return
    }
    
    if (!formData.value.stock_name || !formData.value.stock_name.trim()) {
      ElMessage.warning('请输入股票名称')
      return
    }
    
    if (formData.value.stock_name.trim().length > 50) {
      ElMessage.warning('股票名称不能超过50个字符')
      return
    }
    
    if (!formData.value.direction) {
      ElMessage.warning('请选择操作方向')
      return
    }
    
    // 买入操作时策略必填，卖出操作时策略可选
    if (formData.value.direction === '买入' && !formData.value.strategy) {
      ElMessage.warning('买入操作请选择策略')
      return
    }
    
    submitting.value = true
    try {
      if (formData.value.id) {
        // 更新 - 只传递有值的字段
        const updateData: TradingCalendarUpdate = {
          date: formData.value.date,
          stock_name: formData.value.stock_name.trim(),
          direction: formData.value.direction,
          strategy: formData.value.strategy || undefined, // 卖出时策略可以为空
          price: formData.value.price,
          is_executed: formData.value.is_executed,
        }
        // 只添加有值的可选字段
        if (formData.value.source && formData.value.source.trim()) {
          updateData.source = formData.value.source.trim()
        }
        if (formData.value.notes && formData.value.notes.trim()) {
          updateData.notes = formData.value.notes.trim()
        }
        console.log('更新数据:', updateData)
        await tradingCalendarApi.update(formData.value.id, updateData)
        ElMessage.success('更新成功')
      } else {
        // 新增
        const createData: TradingCalendarCreate = {
          date: formData.value.date!,
          stock_name: formData.value.stock_name!.trim(),
          direction: formData.value.direction!,
          strategy: formData.value.strategy || '', // 卖出时策略可以为空字符串
          price: formData.value.price,
          is_executed: formData.value.is_executed,
          source: formData.value.source?.trim() || undefined,
          notes: formData.value.notes?.trim() || undefined,
        }
        await tradingCalendarApi.create(createData)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      // 根据当前菜单刷新数据
      if (activeMainMenu.value === 'my-calendar') {
        fetchMyTradingData()
      } else {
        fetchData()
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || '操作失败'
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

// 处理操作方向变化
const handleDirectionChange = (value: string) => {
  // 如果切换到卖出，策略变为可选
  // 如果切换到买入且策略为空，需要提示用户选择策略
  // 重新验证策略字段
  nextTick(() => {
    formRef.value?.validateField('strategy')
  })
}

const disabledEndDate = (date: Date) => {
  if (!startDate.value) return false
  return dayjs(date).isBefore(dayjs(startDate.value))
}

// 获取策略标签类型
const getStrategyTagType = (strategy: string | undefined): string => {
  if (!strategy) return 'info'
  switch (strategy) {
    case '低吸':
      return 'success'
    case '排板':
      return 'warning'
    case '加仓':
      return 'info'
    default:
      return 'info'
  }
}

onMounted(() => {
  // 根据当前菜单和tab加载数据
  if (activeMainMenu.value === 'my-calendar') {
    fetchMyTradingData()
  } else {
    // 如果初始视图是日历视图，设置当前周
    if (viewMode.value === 'calendar' && !startDate.value && !endDate.value) {
      const now = dayjs()
      const weekStart = now.startOf('week').add(1, 'day') // 周一开始
      startDate.value = weekStart.format('YYYY-MM-DD')
      endDate.value = weekStart.add(6, 'day').format('YYYY-MM-DD')
      currentWeekStart.value = weekStart.format('YYYY-MM-DD')
    }
    fetchData()
  }
})
</script>

<style scoped>
.trading-calendar {
  padding: 20px;
}

.trading-calendar :deep(.el-card__body) {
  padding: 12px;
}

.tabs-container {
  position: relative;
  display: flex;
  align-items: flex-start;
}

.view-tabs {
  flex: 1;
}

.my-calendar-view {
  position: relative;
}

.add-button {
  position: absolute;
  right: 0;
  top: 2px;
  z-index: 10;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

/* 周视图样式 */
.week-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.week-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.week-label {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.week-calendar-view {
  width: 100%;
  background-color: #fff;
  border-radius: 4px;
  overflow: hidden;
}

.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-color: #f5f7fa;
  border-bottom: 2px solid #e4e7ed;
}

.week-day-header {
  padding: 12px 8px;
  text-align: center;
  border-right: 1px solid #e4e7ed;
}

.week-day-header:last-child {
  border-right: none;
}

.day-name {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
}

.day-date {
  font-size: 12px;
  color: #909399;
}

.week-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  min-height: 500px;
}

.week-day-cell {
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  padding: 8px;
  min-height: 500px;
  background-color: #fff;
}

.week-day-cell:last-child {
  border-right: none;
}

.week-day-cell .calendar-items-container {
  height: 100%;
  min-height: 480px;
}

.trading-calendar-view {
  width: 100%;
  font-size: 12px;
}

.trading-calendar-view :deep(.el-calendar__header) {
  padding: 10px;
  font-size: 14px;
}

.trading-calendar-view :deep(.el-calendar-table) {
  font-size: 12px;
}

.trading-calendar-view :deep(.el-calendar-table th) {
  padding:2px;
  font-size: 12px;
}

.trading-calendar-view :deep(.el-calendar-table td) {
  padding: 2px;
  height: 160px;
  vertical-align: top;
}

/* 第一列和最后一列宽度最小 */
.trading-calendar-view :deep(.el-calendar-table td:first-child),
.trading-calendar-view :deep(.el-calendar-table td:last-child) {
  width: 1%;
  min-width: 60px;
  max-width: 80px;
}

.trading-calendar-view :deep(.el-calendar-table th:first-child),
.trading-calendar-view :deep(.el-calendar-table th:last-child) {
  width: 1%;
  min-width: 60px;
  max-width: 80px;
}

.trading-calendar-view :deep(.el-calendar-table__row) {
  min-height: 600px;
}

.calendar-cell {
  height: 100%;
  min-height: 160px;
  padding: 0 px;
  display: flex;
  flex-direction: column;
}

.calendar-date {
  font-weight: 600;
  font-size: 12px;
  margin-bottom: 2px;
  color: #606266;
}

.calendar-items-container {
  flex: 1;
  display: flex;
  gap: 4px;
  height: 100%;
  min-height: 480px;
  flex-direction: column;
}

.calendar-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.column-header {
  font-size: 10px;
  font-weight: 600;
  text-align: center;
  padding: 2px 0;
  margin-bottom: 2px;
  border-bottom: 1px solid #e4e7ed;
}

.buy-column .column-header {
  color: #f56c6c;
  background-color: #fef0f0;
}

.sell-column .column-header {
  color: #67c23a;
  background-color: #f0f9ff;
}

.calendar-items {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  max-height: 450px;
  min-height: 0;
}

.calendar-item {
  padding: 0px;
  border-radius: 2px;
  cursor: pointer;
  border-left: 3px solid #909399;
  min-height: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  font-size: 10px;

}
.el-calendar__body {
    padding: 10px 10px 10px;
}
.calendar-item:hover {
  background-color: #ecf5ff;
  transform: translateX(2px);
}
.el-calendar-day {
  padding: 0px;
}
.calendar-item.buy {
  border-left-color: #f56c6c;
  background-color: #fef0f0;
}

.calendar-item.buy:hover {
  background-color: #fde2e2;
}

.calendar-item.sell {
  border-left-color: #67c23a;
  background-color: #f0f9ff;
}

.calendar-item.sell:hover {
  background-color: #e1f3d8;
}

.calendar-item.executed {
  opacity: 0.7;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
  margin-bottom: 0px;
}

.item-main .direction-tag {
  font-size: 10px;
  font-weight: 600;
}

.item-main .direction-tag :deep(.el-tag__content) {
  font-size: 10px;
  font-weight: 600;
}

.item-main .strategy-tag {
  font-size: 10px;
  font-weight: 600;
}

.item-main .strategy-tag :deep(.el-tag__content) {
  font-size: 10px;
  font-weight: 600;
}

.item-stock {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.calendar-item:hover {
  background-color: #ecf5ff;
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.item-price {
  font-size: 10px;
  color: #909399;
  margin-top: 0px;
}

.more-items-tip {
  font-size: 10px;
  color: #909399;
  text-align: center;
  padding: 2px 0;
  margin-top: 2px;
  font-style: italic;
  border-top: 1px dashed #dcdfe6;
}

.table-view {
  width: 100%;
}

.week-header {
  background-color: #f5f7fa;
  padding: 8px 12px;
  font-size: 14px;
  color: #303133;
}

.week-header strong {
  color: #409eff;
  margin-right: 8px;
}

.week-count {
  color: #909399;
  font-size: 12px;
  font-weight: normal;
}
</style>

