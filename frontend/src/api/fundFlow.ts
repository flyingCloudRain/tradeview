import apiClient from './client'

export interface FundFlowItem {
  id: number
  date: string
  stock_code: string
  stock_name: string
  current_price?: number
  change_percent?: number
  turnover_rate?: number
  main_inflow?: number
  main_outflow?: number
  main_net_inflow?: number
  turnover_amount?: number
  is_limit_up?: boolean
  is_lhb?: boolean
}

export interface FundFlowListParams {
  date: string
  stock_code?: string
  page?: number
  page_size?: number
  sort_by?: 'main_inflow' | 'main_outflow' | 'main_net_inflow' | 'turnover_rate' | 'change_percent'
  order?: 'asc' | 'desc'
}

export interface FundFlowListResponse {
  items: FundFlowItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface FundFlowConceptItem {
  concept: string
  index_value?: number
  index_change_percent?: number
  inflow?: number
  outflow?: number
  net_amount?: number
  stock_count?: number
  leader_stock?: string
  leader_change_percent?: number
  leader_price?: number
}

export interface FundFlowIndustryItem {
  id: number
  date: string
  industry: string
  index_value?: number
  index_change_percent?: number
  inflow?: number
  outflow?: number
  net_amount?: number
  stock_count?: number
  leader_stock?: string
  leader_change_percent?: number
  leader_price?: number
}

export const fundFlowApi = {
  getList: async (params: FundFlowListParams): Promise<FundFlowListResponse> => {
    return await apiClient.get('/stock-fund-flow', { params })
  },

  getHistory: async (stockCode: string, startDate: string, endDate: string) => {
    return await apiClient.get(`/stock-fund-flow/${stockCode}/history`, {
      params: { start_date: startDate, end_date: endDate },
    })
  },

  getConcept: async (limit = 50, date?: string): Promise<FundFlowConceptItem[]> => {
    const params: Record<string, any> = { limit }
    if (date) params.date = date
    return await apiClient.get('/stock-fund-flow/concept', { params })
  },

  getIndustry: async (date: string, limit = 200): Promise<FundFlowIndustryItem[]> => {
    return await apiClient.get('/stock-fund-flow/industry', { params: { date, limit } })
  },
}

