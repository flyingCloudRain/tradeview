import apiClient from './client'

export interface SectorItem {
  id: number
  date: string
  sector_code: string
  sector_name: string
  change_percent?: number
  rise_count?: number
  fall_count?: number
  total_count?: number
  total_amount?: number
}

export interface SectorListParams {
  date: string
  sector_code?: string
  sort_by?: string
  order?: 'asc' | 'desc'
}

export const sectorApi = {
  getList: async (params: SectorListParams): Promise<SectorItem[]> => {
    // 清理参数，只传递有效值
    const cleanParams: Record<string, any> = {
      date: params.date,
    }
    if (params.sector_code) {
      cleanParams.sector_code = params.sector_code
    }
    if (params.sort_by) {
      cleanParams.sort_by = params.sort_by
    }
    if (params.order && (params.order === 'asc' || params.order === 'desc')) {
      cleanParams.order = params.order
    }
    return await apiClient.get('/sector/', { params: cleanParams })
  },

  getDetail: async (sectorCode: string, date: string) => {
    return await apiClient.get(`/sector/${sectorCode}`, {
      params: { date },
    })
  },
}

