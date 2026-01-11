import apiClient from './client'

export type TaskStatus = 'pending' | 'running' | 'success' | 'failed'

export interface TaskExecution {
  id: number
  task_name: string
  task_type: string
  status: TaskStatus
  start_time: string
  end_time?: string
  duration?: string
  result?: {
    success_count?: number
    total_count?: number
    task_results?: Record<string, any>
  }
  error_message?: string
  triggered_by: string
  target_date?: string
  created_at: string
}

export interface TaskExecutionListParams {
  page?: number
  page_size?: number
  task_type?: string
  status?: TaskStatus
  task_name?: string
}

export interface TaskExecutionListResponse {
  items: TaskExecution[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TaskStatusSummary {
  [taskType: string]: {
    task_name: string
    status: TaskStatus
    last_run_time?: string
    last_success_time?: string
    duration?: string
    error_message?: string
  }
}

export interface TaskRunRequest {
  task_types?: string[]
  target_date?: string
}

export interface TaskRunResponse {
  execution_id: number
  message: string
  task_types: string[]
}

export interface TaskTypesResponse {
  task_types: string[]
  task_names: Record<string, string>
}

export const taskApi = {
  getExecutions: async (params: TaskExecutionListParams): Promise<TaskExecutionListResponse> => {
    const cleanParams: Record<string, any> = {}
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    if (params.task_type) cleanParams.task_type = params.task_type
    if (params.status) cleanParams.status = params.status
    if (params.task_name) cleanParams.task_name = params.task_name
    
    return await apiClient.get('/tasks/executions', { params: cleanParams })
  },

  getExecutionById: async (id: number): Promise<TaskExecution> => {
    return await apiClient.get(`/tasks/executions/${id}`)
  },

  getStatusSummary: async (): Promise<TaskStatusSummary> => {
    return await apiClient.get('/tasks/status')
  },

  runTasks: async (data: TaskRunRequest): Promise<TaskRunResponse> => {
    return await apiClient.post('/tasks/run', data)
  },

  getTaskTypes: async (): Promise<TaskTypesResponse> => {
    return await apiClient.get('/tasks/task-types')
  },
}

