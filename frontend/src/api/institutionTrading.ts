import apiClient from './client'

export interface InstitutionTradingStatisticsItem {
  id: number
  date: string
  stock_code: string
  stock_name: string
  close_price?: number
  change_percent?: number
  buyer_institution_count?: number
  seller_institution_count?: number
  institution_buy_amount?: number
  institution_sell_amount?: number
  institution_net_buy_amount?: number
  market_total_amount?: number
  net_buy_ratio?: number
  turnover_rate?: number
  circulation_market_value?: number
  created_at: string
}

export interface InstitutionTradingStatisticsListParams {
  date?: string
  start_date?: string
  end_date?: string
  stock_code?: string
  stock_name?: string
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface InstitutionTradingStatisticsListResponse {
  items: InstitutionTradingStatisticsItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface InstitutionTradingStatisticsAggregatedItem {
  stock_code: string
  stock_name: string
  appear_count: number
  total_buy_amount?: number
  total_sell_amount?: number
  total_net_buy_amount?: number
  total_market_amount?: number
  net_buy_ratio?: number
  avg_close_price?: number
  avg_circulation_market_value?: number
  avg_turnover_rate?: number
  max_change_percent?: number
  min_change_percent?: number
  earliest_date: string
  latest_date: string
}

export interface InstitutionTradingStatisticsAggregatedParams {
  start_date: string
  end_date: string
  stock_code?: string
  stock_name?: string
  min_appear_count?: number
  max_appear_count?: number
  min_total_net_buy_amount?: number
  max_total_net_buy_amount?: number
  min_total_buy_amount?: number
  max_total_buy_amount?: number
  min_total_sell_amount?: number
  max_total_sell_amount?: number
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface InstitutionTradingStatisticsAggregatedResponse {
  items: InstitutionTradingStatisticsAggregatedItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const institutionTradingApi = {
  getList: async (params: InstitutionTradingStatisticsListParams): Promise<InstitutionTradingStatisticsListResponse> => {
    const cleanParams: Record<string, any> = {}
    if (params.date) cleanParams.date = params.date
    if (params.start_date) cleanParams.start_date = params.start_date
    if (params.end_date) cleanParams.end_date = params.end_date
    if (params.stock_code && params.stock_code.trim()) cleanParams.stock_code = params.stock_code.trim()
    if (params.stock_name && params.stock_name.trim()) cleanParams.stock_name = params.stock_name.trim()
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    if (params.sort_by) cleanParams.sort_by = params.sort_by
    if (params.order && (params.order === 'asc' || params.order === 'desc')) cleanParams.order = params.order
    return await apiClient.get('/lhb/institution-trading-statistics', { params: cleanParams })
  },
  getAggregated: async (params: InstitutionTradingStatisticsAggregatedParams): Promise<InstitutionTradingStatisticsAggregatedResponse> => {
    const cleanParams: Record<string, any> = {
      start_date: params.start_date,
      end_date: params.end_date,
    }
    if (params.stock_code && params.stock_code.trim()) cleanParams.stock_code = params.stock_code.trim()
    if (params.stock_name && params.stock_name.trim()) cleanParams.stock_name = params.stock_name.trim()
    if (params.min_appear_count !== undefined && params.min_appear_count !== null) cleanParams.min_appear_count = params.min_appear_count
    if (params.max_appear_count !== undefined && params.max_appear_count !== null) cleanParams.max_appear_count = params.max_appear_count
    if (params.min_total_net_buy_amount !== undefined && params.min_total_net_buy_amount !== null) cleanParams.min_total_net_buy_amount = params.min_total_net_buy_amount
    if (params.max_total_net_buy_amount !== undefined && params.max_total_net_buy_amount !== null) cleanParams.max_total_net_buy_amount = params.max_total_net_buy_amount
    if (params.min_total_buy_amount !== undefined && params.min_total_buy_amount !== null) cleanParams.min_total_buy_amount = params.min_total_buy_amount
    if (params.max_total_buy_amount !== undefined && params.max_total_buy_amount !== null) cleanParams.max_total_buy_amount = params.max_total_buy_amount
    if (params.min_total_sell_amount !== undefined && params.min_total_sell_amount !== null) cleanParams.min_total_sell_amount = params.min_total_sell_amount
    if (params.max_total_sell_amount !== undefined && params.max_total_sell_amount !== null) cleanParams.max_total_sell_amount = params.max_total_sell_amount
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    if (params.sort_by) cleanParams.sort_by = params.sort_by
    if (params.order && (params.order === 'asc' || params.order === 'desc')) cleanParams.order = params.order
    return await apiClient.get('/lhb/institution-trading-statistics/aggregated', { params: cleanParams })
  },
}
