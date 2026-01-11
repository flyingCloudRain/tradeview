import apiClient from './client'

export interface StockConcept {
  id: number
  name: string
  code?: string
}

export interface ZtPoolItem {
  id: number
  date: string
  stock_code: string
  stock_name: string
  change_percent?: number
  latest_price?: number
  turnover_amount?: number
  circulation_market_value?: number
  total_market_value?: number
  turnover_rate?: number
  limit_up_capital?: number
  first_limit_time?: string
  last_limit_time?: string
  explosion_count?: number
  limit_up_statistics?: string
  consecutive_limit_count?: number
  industry?: string
  concept?: string  // 保留用于兼容，优先使用 concepts
  concepts?: StockConcept[]  // 概念板块数组
  limit_up_reason?: string
  is_lhb?: boolean  // 是否属于当日龙虎榜
}

export interface ZtPoolListParams {
  date: string
  stock_code?: string
  concept?: string  // 保留用于兼容旧接口
  industry?: string
  consecutive_limit_count?: number
  limit_up_statistics?: string
  concept_ids?: number[]  // 概念板块ID列表
  concept_names?: string[]  // 概念板块名称列表
  is_lhb?: boolean  // 是否龙虎榜筛选，true表示只返回龙虎榜股票，false表示只返回非龙虎榜股票
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface ZtPoolListResponse {
  items: ZtPoolItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ZtPoolAnalysis {
  total_count: number
  industry_distribution: Record<string, number>
  concept_distribution: Record<string, number>
  reason_distribution: Record<string, number>
  consecutive_limit_distribution: Record<string, number>
}

export const ztPoolApi = {
  getList: async (params: ZtPoolListParams): Promise<ZtPoolListResponse> => {
    // 清理参数，只传递有效值
    const cleanParams: Record<string, any> = {
      date: params.date,
    }
    if (params.stock_code) {
      cleanParams.stock_code = params.stock_code
    }
    if (params.concept) {
      cleanParams.concept = params.concept
    }
    if (params.industry) {
      cleanParams.industry = params.industry
    }
    if (params.consecutive_limit_count !== undefined) {
      cleanParams.consecutive_limit_count = params.consecutive_limit_count
    }
    if (params.limit_up_statistics) {
      cleanParams.limit_up_statistics = params.limit_up_statistics
    }
    // 概念板块筛选参数
    if (params.concept_ids && params.concept_ids.length > 0) {
      cleanParams.concept_ids = params.concept_ids.join(',')
    }
    if (params.concept_names && params.concept_names.length > 0) {
      cleanParams.concept_names = params.concept_names.join(',')
    }
    if (params.is_lhb !== undefined) {
      cleanParams.is_lhb = params.is_lhb
    }
    if (params.page) {
      cleanParams.page = params.page
    }
    if (params.page_size) {
      cleanParams.page_size = params.page_size
    }
    if (params.sort_by) {
      cleanParams.sort_by = params.sort_by
    }
    if (params.order && (params.order === 'asc' || params.order === 'desc')) {
      cleanParams.order = params.order
    }
    return await apiClient.get('/zt-pool/', { params: cleanParams })
  },

  getAnalysis: async (date: string): Promise<ZtPoolAnalysis> => {
    return await apiClient.get('/zt-pool/analysis', { params: { date } })
  },

  getConcepts: async (date?: string): Promise<string[]> => {
    const params = date ? { date } : {}
    return await apiClient.get('/zt-pool/concepts', { params })
  },

  updateItem: async (id: number, payload: Partial<Pick<ZtPoolItem, 'concept' | 'limit_up_reason'>>) => {
    return await apiClient.patch(`/zt-pool/${id}`, payload)
  },

  // 跌停池
  getDownList: async (params: ZtPoolListParams): Promise<ZtPoolListResponse> => {
    const cleanParams: Record<string, any> = { date: params.date }
    if (params.stock_code) cleanParams.stock_code = params.stock_code
    if (params.concept) cleanParams.concept = params.concept
    if (params.industry) cleanParams.industry = params.industry
    if (params.consecutive_limit_count !== undefined) cleanParams.consecutive_limit_count = params.consecutive_limit_count
    // 概念板块筛选参数（如果后端支持）
    if (params.concept_ids && params.concept_ids.length > 0) {
      cleanParams.concept_ids = params.concept_ids.join(',')
    }
    if (params.concept_names && params.concept_names.length > 0) {
      cleanParams.concept_names = params.concept_names.join(',')
    }
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    if (params.sort_by) cleanParams.sort_by = params.sort_by
    if (params.order && (params.order === 'asc' || params.order === 'desc')) cleanParams.order = params.order
    return await apiClient.get('/zt-pool-down/', { params: cleanParams })
  },
}

