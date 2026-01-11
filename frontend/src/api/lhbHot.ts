import apiClient from './client'

export interface LhbHotItem {
  id: number
  date: string
  institution_name?: string
  stock_code: string
  stock_name?: string
  flag?: string  // 操作方向：买入/卖出
  buy_amount?: number
  sell_amount?: number
  net_buy_amount?: number
}

export interface LhbHotListParams {
  date?: string
  stock_code?: string
  stock_name?: string
  flag?: '买入' | '卖出'
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface LhbHotListResponse {
  items: LhbHotItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const lhbHotApi = {
  getList: async (params: LhbHotListParams): Promise<LhbHotListResponse> => {
    const cleanParams: Record<string, any> = {}
    if (params.date) cleanParams.date = params.date
    if (params.stock_code && params.stock_code.trim()) cleanParams.stock_code = params.stock_code.trim()
    if (params.stock_name && params.stock_name.trim()) cleanParams.stock_name = params.stock_name.trim()
    if (params.flag) cleanParams.flag = params.flag
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    if (params.sort_by) cleanParams.sort_by = params.sort_by
    if (params.order && (params.order === 'asc' || params.order === 'desc')) cleanParams.order = params.order
    return await apiClient.get('/lhb/institution', { params: cleanParams })
  },
}

