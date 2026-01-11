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

export const traderApi = {
  list: async (): Promise<TraderItem[]> => {
    return await apiClient.get('/lhb/traders')
  },
}

