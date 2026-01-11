import apiClient from './client'

export interface LhbInstitutionItem {
  id: number
  institution_name?: string
  buy_amount?: number
  sell_amount?: number
  net_buy_amount?: number
  flag?: string
}

export interface LhbItem {
  id: number
  date: string
  stock_code: string
  stock_name: string
  close_price?: number
  change_percent?: number
  net_buy_amount?: number
  buy_amount?: number
  sell_amount?: number
  total_amount?: number
  turnover_rate?: number
  concept?: string
  institutions_summary?: string
  institutions?: LhbInstitutionItem[]
}

export interface LhbListParams {
  date: string
  stock_code?: string
  stock_name?: string
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface LhbListResponse {
  items: LhbItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const lhbApi = {
  getList: async (params: LhbListParams): Promise<LhbListResponse> => {
    // 清理参数，移除 undefined、null 和空字符串
    const cleanParams: Record<string, any> = {
      date: params.date,
    }

    // 只添加有值的参数
    if (params.stock_code && params.stock_code.trim()) {
      cleanParams.stock_code = params.stock_code.trim()
    }
    if (params.stock_name && params.stock_name.trim()) {
      cleanParams.stock_name = params.stock_name.trim()
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

    console.log('调用 lhbApi.getList，清理后的参数:', cleanParams)
    const result = await apiClient.get('/lhb/', { params: cleanParams }) as unknown as LhbListResponse
    console.log('lhbApi.getList 返回结果:', result)
    return result
  },

  getDetail: async (stockCode: string, date: string) => {
    return await apiClient.get(`/lhb/${stockCode}`, {
      params: { date },
    })
  },

  getInstitution: async (stockCode: string, date: string) => {
    return await apiClient.get(`/lhb/${stockCode}/institution`, {
      params: { date },
    })
  },
}

