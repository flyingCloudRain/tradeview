import apiClient from './client'

export interface StockConcept {
  id: number
  name: string
  code?: string
  description?: string
  created_at?: string
  updated_at?: string
}

export interface StockConceptListParams {
  name?: string
  code?: string
  page?: number
  page_size?: number
}

export interface StockConceptListResponse {
  items: StockConcept[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const stockConceptApi = {
  getList: async (params?: StockConceptListParams): Promise<StockConceptListResponse> => {
    const cleanParams: Record<string, any> = {}
    if (params?.name) cleanParams.name = params.name
    if (params?.code) cleanParams.code = params.code
    if (params?.page) cleanParams.page = params.page
    if (params?.page_size) cleanParams.page_size = params.page_size
    return await apiClient.get('/stock-concept/', { params: cleanParams })
  },

  getById: async (id: number): Promise<StockConcept> => {
    return await apiClient.get(`/stock-concept/${id}`)
  },
}
