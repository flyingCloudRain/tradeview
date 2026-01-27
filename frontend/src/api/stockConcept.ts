import apiClient from './client'

export interface StockConcept {
  id: number
  name: string
  code?: string
  description?: string
  parent_id?: number
  level: number
  path?: string
  sort_order?: number
  stock_count?: number
  created_at?: string
  updated_at?: string
  children?: StockConcept[]
}

export interface StockConceptListParams {
  name?: string
  code?: string
  level?: number
  parent_id?: number
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

export interface StockConceptMappingRequest {
  stock_name: string
  concept_ids: number[]
}

export interface StockConceptMappingResponse {
  stock_name: string
  concepts: StockConcept[]
}

export const stockConceptApi = {
  getList: async (params?: StockConceptListParams): Promise<StockConceptListResponse> => {
    const cleanParams: Record<string, any> = {}
    if (params?.name) cleanParams.name = params.name
    if (params?.code) cleanParams.code = params.code
    if (params?.level) cleanParams.level = params.level
    if (params?.parent_id) cleanParams.parent_id = params.parent_id
    if (params?.page) cleanParams.page = params.page
    if (params?.page_size) cleanParams.page_size = params.page_size
    return await apiClient.get('/stock-concepts/', { params: cleanParams })
  },

  getById: async (id: number): Promise<StockConcept> => {
    return await apiClient.get(`/stock-concepts/${id}`)
  },

  getTree: async (maxLevel: number = 3): Promise<StockConcept[]> => {
    const response = await apiClient.get('/stock-concepts/tree', { params: { max_level: maxLevel } })
    // 确保返回的是数组
    if (!Array.isArray(response)) {
      console.error('getTree: 期望返回数组，但收到:', typeof response, response)
      throw new Error('API返回格式错误：期望数组，但收到 ' + typeof response)
    }
    return response
  },

  getAncestors: async (id: number): Promise<StockConcept[]> => {
    return await apiClient.get(`/stock-concepts/${id}/ancestors`)
  },

  getDescendants: async (id: number, includeSelf: boolean = false): Promise<StockConcept[]> => {
    return await apiClient.get(`/stock-concepts/${id}/descendants`, { params: { include_self: includeSelf } })
  },

  getStocks: async (id: number, includeDescendants: boolean = true): Promise<string[]> => {
    return await apiClient.get(`/stock-concepts/${id}/stocks`, { params: { include_descendants: includeDescendants } })
  },

  create: async (data: Partial<StockConcept>): Promise<StockConcept> => {
    return await apiClient.post('/stock-concepts/', data)
  },

  update: async (id: number, data: Partial<StockConcept>): Promise<StockConcept> => {
    return await apiClient.put(`/stock-concepts/${id}`, data)
  },

  delete: async (id: number): Promise<void> => {
    return await apiClient.delete(`/stock-concepts/${id}`)
  },

  // 个股关联概念
  setStockConcepts: async (data: StockConceptMappingRequest): Promise<StockConceptMappingResponse> => {
    return await apiClient.post('/stock-concepts/mapping', data)
  },

  getStockConcepts: async (stockName: string, level?: number): Promise<StockConceptMappingResponse> => {
    const params: Record<string, any> = {}
    if (level) params.level = level
    return await apiClient.get(`/stock-concepts/mapping/${encodeURIComponent(stockName)}`, { params })
  },

  updateStockConcepts: async (stockName: string, conceptIds: number[]): Promise<StockConceptMappingResponse> => {
    return await apiClient.put(`/stock-concepts/mapping/${encodeURIComponent(stockName)}`, conceptIds)
  },

  removeStockConcept: async (stockName: string, conceptId: number): Promise<void> => {
    return await apiClient.delete(`/stock-concepts/mapping/${encodeURIComponent(stockName)}/${conceptId}`)
  },

  // 为概念添加个股
  addStockToConcept: async (conceptId: number, stockName: string): Promise<StockConcept> => {
    return await apiClient.post(`/stock-concepts/${conceptId}/stocks`, null, {
      params: { stock_name: stockName }
    })
  },

  // 从概念移除个股
  removeStockFromConcept: async (conceptId: number, stockName: string): Promise<void> => {
    return await apiClient.delete(`/stock-concepts/${conceptId}/stocks/${encodeURIComponent(stockName)}`)
  },
}
