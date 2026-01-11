import apiClient from './client'

export interface TraderBranch {
  id: number
  trader_id: number
  institution_name: string
  institution_code?: string
}

export interface TraderItem {
  id: number
  name: string
  aka?: string
  branches: TraderBranch[]
}

export interface TraderCreateRequest {
  name: string
  aka?: string
  branches?: string[]
}

export interface TraderUpdateRequest {
  name?: string
  aka?: string
}

export interface TraderBranchCreateRequest {
  institution_name: string
  institution_code?: string
}

export const traderApi = {
  list: async (): Promise<TraderItem[]> => {
    return await apiClient.get('/lhb/traders')
  },
  
  get: async (id: number): Promise<TraderItem> => {
    return await apiClient.get(`/lhb/traders/${id}`)
  },
  
  create: async (data: TraderCreateRequest): Promise<TraderItem> => {
    return await apiClient.post('/lhb/traders', data)
  },
  
  update: async (id: number, data: TraderUpdateRequest): Promise<TraderItem> => {
    return await apiClient.put(`/lhb/traders/${id}`, data)
  },
  
  delete: async (id: number): Promise<void> => {
    return await apiClient.delete(`/lhb/traders/${id}`)
  },
  
  addBranch: async (traderId: number, data: TraderBranchCreateRequest): Promise<TraderBranch> => {
    return await apiClient.post(`/lhb/traders/${traderId}/branches`, data)
  },
  
  updateBranch: async (traderId: number, branchId: number, data: TraderBranchCreateRequest): Promise<TraderBranch> => {
    return await apiClient.put(`/lhb/traders/${traderId}/branches/${branchId}`, data)
  },
  
  deleteBranch: async (traderId: number, branchId: number): Promise<void> => {
    return await apiClient.delete(`/lhb/traders/${traderId}/branches/${branchId}`)
  },
}

