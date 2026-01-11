import apiClient from './client'

export interface TradingCalendarItem {
  id: number
  date: string
  stock_name: string
  direction: '买入' | '卖出'
  strategy: '低吸' | '排板'
  price?: number
  is_executed?: boolean
  source?: string
  notes?: string
  created_at: string
}

export interface TradingCalendarListParams {
  start_date?: string
  end_date?: string
  stock_name?: string
  direction?: '买入' | '卖出'
  strategy?: '低吸' | '排板'
  source?: string
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface TradingCalendarListResponse {
  items: TradingCalendarItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TradingCalendarCreate {
  date: string
  stock_name: string
  direction: '买入' | '卖出'
  strategy: '低吸' | '排板'
  price?: number
  is_executed?: boolean
  source?: string
  notes?: string
}

export interface TradingCalendarUpdate {
  date?: string
  stock_name?: string
  direction?: '买入' | '卖出'
  strategy?: '低吸' | '排板'
  price?: number
  is_executed?: boolean
  source?: string
  notes?: string
}

export const tradingCalendarApi = {
  getList: async (params: TradingCalendarListParams): Promise<TradingCalendarListResponse> => {
    const cleanParams: Record<string, any> = {}
    if (params.start_date) cleanParams.start_date = params.start_date
    if (params.end_date) cleanParams.end_date = params.end_date
    if (params.stock_name && params.stock_name.trim()) cleanParams.stock_name = params.stock_name.trim()
    if (params.direction) cleanParams.direction = params.direction
    if (params.strategy) cleanParams.strategy = params.strategy
    if (params.source && params.source.trim()) cleanParams.source = params.source.trim()
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    if (params.sort_by) cleanParams.sort_by = params.sort_by
    if (params.order) cleanParams.order = params.order
    
    return await apiClient.get('/trading-calendar', { params: cleanParams })
  },

  getById: async (id: number): Promise<TradingCalendarItem> => {
    return await apiClient.get(`/trading-calendar/${id}`)
  },

  create: async (data: TradingCalendarCreate): Promise<TradingCalendarItem> => {
    return await apiClient.post('/trading-calendar', data)
  },

  update: async (id: number, data: TradingCalendarUpdate): Promise<TradingCalendarItem> => {
    // 移除 undefined 值，确保只传递有效数据
    const cleanData = Object.fromEntries(
      Object.entries(data).filter(([_, value]) => value !== undefined)
    )
    return await apiClient.put(`/trading-calendar/${id}`, cleanData)
  },

  delete: async (id: number): Promise<void> => {
    return await apiClient.delete(`/trading-calendar/${id}`)
  },
}

