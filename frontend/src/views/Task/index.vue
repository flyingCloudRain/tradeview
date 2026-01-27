<template>
  <div class="task-management">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>任务管理</span>
          <el-button type="primary" @click="showRunDialog = true" :loading="running">
            <el-icon><Plus /></el-icon>
            手动执行任务
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 任务状态汇总 Tab -->
        <el-tab-pane label="任务状态" name="status">
          <el-card shadow="never" class="status-summary">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>任务状态汇总</span>
                <el-button text @click="loadStatusSummary" :loading="loadingStatus">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            
            <!-- 表格视图 -->
            <el-table
              :data="statusSummaryList"
              v-loading="loadingStatus"
              stripe
              style="width: 100%"
              :default-sort="{ prop: 'task_type', order: 'ascending' }"
            >
              <el-table-column prop="task_name" label="任务名称" min-width="180" sortable />
              <el-table-column prop="task_type" label="任务类型" width="150" sortable />
              <el-table-column prop="status" label="状态" width="100" sortable>
                <template #default="{ row }">
                  <el-tag
                    :type="getStatusType(row.status)"
                    size="small"
                  >
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="last_run_time" label="最后执行时间" width="180" sortable>
                <template #default="{ row }">
                  <span v-if="row.last_run_time">{{ formatTime(row.last_run_time) }}</span>
                  <span v-else class="text-muted">从未执行</span>
                </template>
              </el-table-column>
              <el-table-column prop="last_success_time" label="最后成功时间" width="180" sortable>
                <template #default="{ row }">
                  <span v-if="row.last_success_time">{{ formatTime(row.last_success_time) }}</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="执行时长" width="100" sortable>
                <template #default="{ row }">
                  <span v-if="row.duration">{{ row.duration }}秒</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
            </el-table>
            
            <!-- 卡片视图（可选，保留作为备选） -->
            <div class="status-grid" style="display: none;">
              <div
                v-for="(status, taskType) in statusSummary"
                :key="taskType"
                class="status-item"
              >
                <div class="status-header">
                  <span class="task-name">{{ status.task_name }}</span>
                  <el-tag
                    :type="getStatusType(status.status)"
                    size="small"
                  >
                    {{ getStatusText(status.status) }}
                  </el-tag>
                </div>
                <div class="status-details">
                  <div v-if="status.last_run_time" class="detail-item">
                    <span class="label">最后执行:</span>
                    <span class="value">{{ formatTime(status.last_run_time) }}</span>
                  </div>
                  <div v-else class="detail-item">
                    <span class="label">最后执行:</span>
                    <span class="value text-muted">从未执行</span>
                  </div>
                  <div v-if="status.last_success_time" class="detail-item">
                    <span class="label">最后成功:</span>
                    <span class="value">{{ formatTime(status.last_success_time) }}</span>
                  </div>
                  <div v-if="status.duration" class="detail-item">
                    <span class="label">执行时长:</span>
                    <span class="value">{{ status.duration }}秒</span>
                  </div>
                  <div v-if="status.error_message" class="detail-item error">
                    <span class="label">错误信息:</span>
                    <span class="value">{{ status.error_message }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <!-- 执行历史 Tab -->
        <el-tab-pane label="执行历史" name="history">
          <el-card shadow="never" class="execution-history">
            <template #header>
              <span>执行历史</span>
            </template>

        <!-- 筛选条件 -->
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="任务类型">
            <el-select
              v-model="filterForm.task_type"
              placeholder="全部"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="type in taskTypes"
                :key="type"
                :label="taskNames[type] || type"
                :value="type"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="执行状态">
            <el-select
              v-model="filterForm.status"
              placeholder="全部"
              clearable
              style="width: 120px"
            >
              <el-option label="等待执行" value="pending" />
              <el-option label="执行中" value="running" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadExecutions">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- 表格 -->
        <el-table
          :data="executions"
          v-loading="loading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="task_name" label="任务名称" min-width="150" />
          <el-table-column prop="task_type" label="任务类型" width="120">
            <template #default="{ row }">
              {{ taskNames[row.task_type] || row.task_type }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="triggered_by" label="触发方式" width="100">
            <template #default="{ row }">
              {{ row.triggered_by === 'scheduler' ? '定时任务' : '手动执行' }}
            </template>
          </el-table-column>
          <el-table-column prop="target_date" label="目标日期" width="120" />
          <el-table-column prop="start_time" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="end_time" label="结束时间" width="180">
            <template #default="{ row }">
              {{ row.end_time ? formatTime(row.end_time) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="执行时长" width="100">
            <template #default="{ row }">
              {{ row.duration ? `${row.duration}秒` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="viewDetails(row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadExecutions"
            @current-change="loadExecutions"
          />
          </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 手动执行任务对话框 -->
    <el-dialog
      v-model="showRunDialog"
      title="手动执行任务"
      width="500px"
    >
      <el-form :model="runForm" label-width="100px">
        <el-form-item label="任务类型">
          <el-select
            v-model="runForm.task_types"
            multiple
            placeholder="不选择则执行所有任务"
            style="width: 100%"
          >
            <el-option
              v-for="type in taskTypes"
              :key="type"
              :label="taskNames[type] || type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标日期">
          <el-date-picker
            v-model="runForm.target_date"
            type="date"
            placeholder="不选择则使用交易日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRunDialog = false">取消</el-button>
        <el-button type="primary" @click="runTasks" :loading="running">
          执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="showDetailsDialog"
      title="执行详情"
      width="800px"
    >
      <div v-if="selectedExecution">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">
            {{ selectedExecution.task_name }}
          </el-descriptions-item>
          <el-descriptions-item label="任务类型">
            {{ taskNames[selectedExecution.task_type] || selectedExecution.task_type }}
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="getStatusType(selectedExecution.status)">
              {{ getStatusText(selectedExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="触发方式">
            {{ selectedExecution.triggered_by === 'scheduler' ? '定时任务' : '手动执行' }}
          </el-descriptions-item>
          <el-descriptions-item label="目标日期">
            {{ selectedExecution.target_date || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时长">
            {{ selectedExecution.duration ? `${selectedExecution.duration}秒` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间" :span="2">
            {{ formatTime(selectedExecution.start_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间" :span="2">
            {{ selectedExecution.end_time ? formatTime(selectedExecution.end_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="selectedExecution.error_message"
            label="错误信息"
            :span="2"
          >
            <el-alert
              :title="selectedExecution.error_message"
              type="error"
              :closable="false"
            />
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedExecution.result" style="margin-top: 20px">
          <h4>执行结果详情</h4>
          <el-table
            v-if="selectedExecution.result.task_results"
            :data="Object.entries(selectedExecution.result.task_results)"
            border
            style="width: 100%"
          >
            <el-table-column prop="[0]" label="任务类型" width="150">
              <template #default="{ row }">
                {{ taskNames[row[0]] || row[0] }}
              </template>
            </el-table-column>
            <el-table-column prop="[1].success" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row[1].success ? 'success' : 'danger'" size="small">
                  {{ row[1].success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="[1].duration" label="执行时长" width="120">
              <template #default="{ row }">
                {{ row[1].duration ? `${row[1].duration}秒` : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="[1].message" label="消息" />
          </el-table>
          <div v-else>
            <p>成功: {{ selectedExecution.result.success_count || 0 }} / 总数: {{ selectedExecution.result.total_count || 0 }}</p>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { taskApi, type TaskExecution, type TaskStatusSummary, type TaskStatus } from '@/api/task'
import dayjs from 'dayjs'

const activeTab = ref('status')
const loading = ref(false)
const loadingStatus = ref(false)
const running = ref(false)
const showRunDialog = ref(false)
const showDetailsDialog = ref(false)
const selectedExecution = ref<TaskExecution | null>(null)

const executions = ref<TaskExecution[]>([])
const statusSummary = ref<TaskStatusSummary>({})
const taskTypes = ref<string[]>([])
const taskNames = ref<Record<string, string>>({})

// 将状态汇总转换为列表格式，方便表格显示
const statusSummaryList = computed(() => {
  return Object.entries(statusSummary.value).map(([taskType, status]) => {
    // 格式化任务名称为"中文(英文)"格式
    const chineseName = status.task_name || taskNames.value[taskType] || taskType
    const englishName = taskType
    const displayName = `${chineseName}(${englishName})`
    
    return {
      task_type: taskType,
      task_name: displayName,
      status: status.status,
      last_run_time: status.last_run_time,
      last_success_time: status.last_success_time,
      duration: status.duration,
      error_message: status.error_message,
    }
  })
})

const filterForm = ref({
  task_type: '',
  status: '' as TaskStatus | '',
})

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

const runForm = ref({
  task_types: [] as string[],
  target_date: '',
})

const loadTaskTypes = async () => {
  try {
    const data = await taskApi.getTaskTypes()
    taskTypes.value = data.task_types
    taskNames.value = data.task_names
  } catch (error: any) {
    ElMessage.error('加载任务类型失败: ' + (error.message || '未知错误'))
  }
}

const loadStatusSummary = async () => {
  loadingStatus.value = true
  try {
    statusSummary.value = await taskApi.getStatusSummary()
  } catch (error: any) {
    ElMessage.error('加载状态汇总失败: ' + (error.message || '未知错误'))
  } finally {
    loadingStatus.value = false
  }
}

const loadExecutions = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
    }
    if (filterForm.value.task_type) {
      params.task_type = filterForm.value.task_type
    }
    if (filterForm.value.status) {
      params.status = filterForm.value.status
    }

    const data = await taskApi.getExecutions(params)
    executions.value = data.items
    pagination.value.total = data.total
  } catch (error: any) {
    ElMessage.error('加载执行历史失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.value = {
    task_type: '',
    status: '',
  }
  pagination.value.page = 1
  loadExecutions()
}

const runTasks = async () => {
  running.value = true
  try {
    const data = await taskApi.runTasks({
      task_types: runForm.value.task_types.length > 0 ? runForm.value.task_types : undefined,
      target_date: runForm.value.target_date || undefined,
    })
    ElMessage.success('任务已提交执行')
    showRunDialog.value = false
    runForm.value = {
      task_types: [],
      target_date: '',
    }
    // 刷新列表和状态
    await Promise.all([loadExecutions(), loadStatusSummary()])
  } catch (error: any) {
    ElMessage.error('执行任务失败: ' + (error.message || '未知错误'))
  } finally {
    running.value = false
  }
}

const viewDetails = async (execution: TaskExecution) => {
  try {
    const data = await taskApi.getExecutionById(execution.id)
    selectedExecution.value = data
    showDetailsDialog.value = true
  } catch (error: any) {
    ElMessage.error('加载详情失败: ' + (error.message || '未知错误'))
  }
}

const getStatusType = (status: TaskStatus): string => {
  const map: Record<TaskStatus, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

const getStatusText = (status: TaskStatus): string => {
  const map: Record<TaskStatus, string> = {
    pending: '等待执行',
    running: '执行中',
    success: '成功',
    failed: '失败',
  }
  return map[status] || status
}

const formatTime = (time: string): string => {
  try {
    return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
  } catch {
    return time
  }
}

const handleTabChange = (tabName: string) => {
  if (tabName === 'status') {
    loadStatusSummary()
  } else if (tabName === 'history') {
    loadExecutions()
  }
}

onMounted(() => {
  loadTaskTypes()
  loadStatusSummary()
  loadExecutions()
})
</script>

<style scoped>
.task-management {
  padding: 20px;
}

.task-management .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-management .status-summary .status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.task-management .status-summary .status-grid .status-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fafafa;
}

.task-management .status-summary .status-grid .status-item .status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-management .status-summary .status-grid .status-item .status-header .task-name {
  font-weight: 500;
  font-size: 14px;
}

.task-management .status-summary .status-grid .status-item .status-details .detail-item {
  display: flex;
  margin-bottom: 8px;
  font-size: 12px;
}

.task-management .status-summary .status-grid .status-item .status-details .detail-item.error {
  color: #f56c6c;
}

.task-management .status-summary .status-grid .status-item .status-details .detail-item .label {
  color: #909399;
  margin-right: 8px;
  min-width: 60px;
}

.task-management .status-summary .status-grid .status-item .status-details .detail-item .value {
  flex: 1;
  word-break: break-all;
}

.task-management .execution-history .filter-form {
  margin-bottom: 16px;
}

.task-management .execution-history .pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.task-management .text-muted {
  color: #909399;
  font-style: italic;
}

.task-management .error-text {
  color: #f56c6c;
}
</style>

