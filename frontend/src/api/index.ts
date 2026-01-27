import apiClient from './client'

export interface IndexItem {
  id: number
  date: string
  index_code: string
  index_name: string
  close_price?: number
  change_percent?: number
  volume?: number
  amount?: number
  volume_change_percent?: number  // 成交量变化比例（相比前一交易日）
}

export interface IndexListParams {
  date: string
  index_code?: string
}

export interface IndexKlineItem {
  date: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  volume: number | null
  amount: number | null
}

export const indexApi = {
  getList: async (params: IndexListParams): Promise<IndexItem[]> => {
    // 清理参数，只传递有效值
    const cleanParams: Record<string, any> = {
      date: params.date,
    }
    if (params.index_code) {
      cleanParams.index_code = params.index_code
    }
    return await apiClient.get('/index/', { params: cleanParams })
  },

  getHistory: async (indexCode: string, startDate: string, endDate: string) => {
    return await apiClient.get(`/index/${indexCode}/history`, {
      params: { start_date: startDate, end_date: endDate },
    })
  },

  getKline: async (indexCode: string, startDate: string, endDate: string): Promise<IndexKlineItem[]> => {
    return await apiClient.get(`/index/${indexCode}/kline`, {
      params: { start_date: startDate, end_date: endDate },
    })
  },
}

