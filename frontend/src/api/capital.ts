import apiClient from './client'

export interface CapitalItem {
  id: number
  date: string
  capital_name: string
  stock_code: string
  stock_name: string
  buy_amount?: number
  sell_amount?: number
  net_buy_amount?: number
}

export interface CapitalListParams {
  date: string
  capital_name?: string
  page?: number
  page_size?: number
}

export interface CapitalListResponse {
  items: CapitalItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const capitalApi = {
  getList: async (params: CapitalListParams): Promise<CapitalListResponse> => {
    return await apiClient.get('/capital', { params })
  },

  getDetail: async (capitalName: string, date: string) => {
    return await apiClient.get(`/capital/${capitalName}`, {
      params: { date },
    })
  },
}

