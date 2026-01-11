<template>
  <div class="trading-calendar">
    <el-card>
      <div class="tabs-container">
        <el-tabs v-model="viewMode" @tab-change="handleViewModeChange" class="view-tabs">
          <el-tab-pane label="日历视图" name="calendar">
            <template #label>
              <span class="tab-label">
                <el-icon><Calendar /></el-icon>
                <span>日历视图</span>
              </span>
            </template>
          <div class="calendar-view" v-if="viewMode === 'calendar'">
            <el-calendar 
              v-model="calendarDate" 
              class="trading-calendar-view"
              :key="`calendar-${allCalendarData.length}`"
            >
              <template #date-cell="{ data }">
                <div class="calendar-cell" v-if="data.day">
                  <div class="calendar-date">{{ data.day.split('-').slice(2).join('-') }}</div>
                  <div class="calendar-items-container">
                    <!-- 买入列 -->
                    <div class="calendar-column buy-column">
                      <div class="column-header" v-if="shouldShowColumnHeader(data.day)">买入</div>
                      <div class="calendar-items">
                        <template v-for="item in getBuyItemsByDate(data.day)" :key="item.id">
                          <div
                            class="calendar-item buy"
                            :class="{ 'executed': item.is_executed }"
                            @click.stop="handleEdit(item)"
                          >
                            <div class="item-main">
                              <span class="item-stock">{{ item.stock_name }}</span>
                              <el-tag
                                :type="item.strategy === '低吸' ? 'success' : 'warning'"
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
                      <div class="column-header" v-if="shouldShowColumnHeader(data.day)">卖出</div>
                      <div class="calendar-items">
                        <template v-for="item in getSellItemsByDate(data.day)" :key="item.id">
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
                <div v-else class="calendar-cell">
                  <div class="calendar-date"></div>
                  <div class="calendar-items-container">
                    <div class="calendar-column buy-column">
                      <div class="column-header"></div>
                      <div class="calendar-items"></div>
                    </div>
                    <div class="calendar-column sell-column">
                      <div class="column-header"></div>
                      <div class="calendar-items"></div>
                    </div>
                  </div>
                </div>
              </template>
            </el-calendar>
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
            <el-table :data="tableData" :loading="loading" stripe border>
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="stock_name" label="股票名称" width="150" />
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
          <el-select v-model="formData.direction" placeholder="请选择操作方向" style="width: 100%">
            <el-option label="买入" value="买入" />
            <el-option label="卖出" value="卖出" />
          </el-select>
        </el-form-item>
        <el-form-item label="策略" prop="strategy">
          <el-select v-model="formData.strategy" placeholder="请选择策略" style="width: 100%">
            <el-option label="排板" value="排板" />
            <el-option label="低吸" value="低吸" />
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
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Calendar, List } from '@element-plus/icons-vue'
import { tradingCalendarApi, type TradingCalendarItem, type TradingCalendarCreate, type TradingCalendarUpdate } from '@/api/tradingCalendar'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const viewMode = ref<'calendar' | 'table'>('table')
const calendarDate = ref(new Date())
const tableData = ref<TradingCalendarItem[]>([])
const allCalendarData = ref<TradingCalendarItem[]>([]) // 用于日历视图的所有数据
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

const startDate = ref('')
const endDate = ref('')
const stockName = ref('')
const direction = ref<'买入' | '卖出' | ''>('')
const strategy = ref<'低吸' | '排板' | ''>('')
const source = ref<string>('')

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
  if (!value) {
    callback(new Error('请选择策略'))
  } else if (value !== '低吸' && value !== '排板') {
    callback(new Error('策略必须是"低吸"或"排板"'))
  } else {
    callback()
  }
}

const formRules = {
  date: [{ validator: validateDate, trigger: 'change' }],
  stock_name: [{ validator: validateStockName, trigger: 'blur' }],
  direction: [{ required: true, message: '请选择操作方向', trigger: 'change' }],
  strategy: [{ validator: validateStrategy, trigger: 'change' }],
}

const fetchData = async () => {
  loading.value = true
  try {
    // 如果是日历视图，需要获取所有数据（分批加载）
    if (viewMode.value === 'calendar') {
      await fetchCalendarData()
    } else {
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

  const response = await tradingCalendarApi.getList(params)
  tableData.value = response.items
  pagination.value.total = response.total
}

// 获取日历数据（分批加载所有数据）
const fetchCalendarData = async () => {
  const MAX_PAGE_SIZE = 100 // 后端限制的最大页面大小
  const baseParams: any = {
    page_size: MAX_PAGE_SIZE,
  }
  
  // 如果没有设置日期范围，默认获取当前月份的数据
  if (!startDate.value && !endDate.value) {
    const now = dayjs()
    baseParams.start_date = now.startOf('month').format('YYYY-MM-DD')
    baseParams.end_date = now.endOf('month').format('YYYY-MM-DD')
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

// 判断是否应该显示列标题（第一列和最后一列的非交易日不显示）
const shouldShowColumnHeader = (date: string | undefined): boolean => {
  if (!date) return false
  const day = dayjs(date).day()
  // 第一列（周一，day=1）和最后一列（周日，day=0）如果是非交易日，不显示标题
  // 周一通常不是非交易日，但如果是节假日可能是非交易日
  // 周日通常是非交易日
  if (day === 0 || day === 6) {
    // 周末（非交易日）不显示标题
    return false
  }
  return true
}

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

// 监听视图模式切换
const handleViewModeChange = () => {
  pagination.value.current = 1
  // 如果切换到日历视图且没有设置日期范围，自动设置为当前月份
  if (viewMode.value === 'calendar' && !startDate.value && !endDate.value) {
    const now = dayjs()
    startDate.value = now.startOf('month').format('YYYY-MM-DD')
    endDate.value = now.endOf('month').format('YYYY-MM-DD')
  }
  fetchData()
}

// 监听日历日期变化（月份切换）
watch(calendarDate, (newDate) => {
  // 如果当前是日历视图且没有手动设置日期范围，自动更新为选中月份
  if (viewMode.value === 'calendar' && (!startDate.value || !endDate.value)) {
    const selectedDate = dayjs(newDate)
    const newStartDate = selectedDate.startOf('month').format('YYYY-MM-DD')
    const newEndDate = selectedDate.endOf('month').format('YYYY-MM-DD')
    
    // 只有当月份真正改变时才更新
    if (startDate.value !== newStartDate || endDate.value !== newEndDate) {
      startDate.value = newStartDate
      endDate.value = newEndDate
      fetchData()
    }
  }
})

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

const handleEdit = (row: TradingCalendarItem) => {
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

const handleDelete = async (row: TradingCalendarItem) => {
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
    fetchData()
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
    
    if (!formData.value.strategy) {
      ElMessage.warning('请选择策略')
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
          strategy: formData.value.strategy,
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
          strategy: formData.value.strategy!,
          price: formData.value.price,
          is_executed: formData.value.is_executed,
          source: formData.value.source?.trim() || undefined,
          notes: formData.value.notes?.trim() || undefined,
        }
        await tradingCalendarApi.create(createData)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchData()
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

const disabledEndDate = (date: Date) => {
  if (!startDate.value) return false
  return dayjs(date).isBefore(dayjs(startDate.value))
}

onMounted(() => {
  fetchData()
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

/* 日历视图样式 */
.calendar-view {
  min-height: 1000px;
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
  gap: 2px;
  height: 100%;
  min-height: 140px;
}

.calendar-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
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
  gap: 1px;
  overflow-y: auto;
  max-height: 580px;
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
</style>

