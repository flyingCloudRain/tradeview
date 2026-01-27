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

export interface LhbStockStatisticsParams {
  start_date: string
  end_date: string
  stock_code?: string
  stock_name?: string
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface LhbStockStatisticsItem {
  stock_code: string
  stock_name: string
  appear_count: number  // 上榜次数
  total_net_buy_amount: number  // 净流入总额
  total_buy_amount: number  // 买入总额
  total_sell_amount: number  // 卖出总额
  first_date?: string  // 首次上榜日期
  last_date?: string  // 最后上榜日期
}

export interface LhbStockStatisticsResponse {
  items: LhbStockStatisticsItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  start_date: string
  end_date: string
}

export interface ActiveBranchItem {
  id: number
  date: string
  institution_name: string
  institution_code?: string
  buy_stock_count?: number
  sell_stock_count?: number
  buy_amount?: number
  sell_amount?: number
  net_amount?: number
  buy_stocks?: string
  created_at: string
}

export interface ActiveBranchListParams {
  date?: string
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
  institution_name?: string
  institution_code?: string
  buy_stock_name?: string
}

export interface ActiveBranchListResponse {
  items: ActiveBranchItem[]
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

  getActiveBranchList: async (params: ActiveBranchListParams): Promise<ActiveBranchListResponse> => {
    const cleanParams: Record<string, any> = {}
    
    if (params.date) {
      cleanParams.date = params.date
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
    if (params.institution_name && params.institution_name.trim()) {
      cleanParams.institution_name = params.institution_name.trim()
    }
    if (params.institution_code && params.institution_code.trim()) {
      cleanParams.institution_code = params.institution_code.trim()
    }
    if (params.buy_stock_name && params.buy_stock_name.trim()) {
      cleanParams.buy_stock_name = params.buy_stock_name.trim()
    }

    return await apiClient.get('/lhb/active-branch', { params: cleanParams }) as unknown as ActiveBranchListResponse
  },

  getActiveBranchDetail: async (institutionCode: string, params: {
    date?: string
    page?: number
    page_size?: number
    sort_by?: string
    order?: 'asc' | 'desc'
    stock_code?: string
    stock_name?: string
  }): Promise<ActiveBranchDetailListResponse> => {
    const cleanParams: Record<string, any> = {}
    
    if (params.date) {
      cleanParams.date = params.date
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
    if (params.stock_code && params.stock_code.trim()) {
      cleanParams.stock_code = params.stock_code.trim()
    }
    if (params.stock_name && params.stock_name.trim()) {
      cleanParams.stock_name = params.stock_name.trim()
    }

    return await apiClient.get(`/lhb/active-branch/${institutionCode}/detail`, { params: cleanParams }) as unknown as ActiveBranchDetailListResponse
  },

  getBuyStocksStatistics: async (params: BuyStockStatisticsParams): Promise<BuyStockStatisticsResponse> => {
    const cleanParams: Record<string, any> = {}
    
    if (params.date) {
      cleanParams.date = params.date
    }
    if (params.page) {
      cleanParams.page = params.page
    }
    if (params.page_size) {
      cleanParams.page_size = params.page_size
    }

    return await apiClient.get('/lhb/active-branch/buy-stocks-statistics', { params: cleanParams }) as unknown as BuyStockStatisticsResponse
  },

  getBranchesByStockName: async (stockName: string, params: {
    date?: string
    page?: number
    page_size?: number
  }): Promise<BuyStockBranchesResponse> => {
    const cleanParams: Record<string, any> = {}
    
    if (params.date) {
      cleanParams.date = params.date
    }
    if (params.page) {
      cleanParams.page = params.page
    }
    if (params.page_size) {
      cleanParams.page_size = params.page_size
    }

    return await apiClient.get(`/lhb/active-branch/buy-stocks-statistics/${encodeURIComponent(stockName)}/branches`, { params: cleanParams }) as unknown as BuyStockBranchesResponse
  },

  getActiveBranchDetailByStockName: async (stockName: string, params: {
    date?: string
    page?: number
    page_size?: number
    sort_by?: string
    order?: 'asc' | 'desc'
    stock_code?: string
  }): Promise<ActiveBranchDetailListResponse> => {
    const cleanParams: Record<string, any> = {
      stock_name: stockName,
    }
    
    if (params.date) {
      cleanParams.date = params.date
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
    if (params.stock_code && params.stock_code.trim()) {
      cleanParams.stock_code = params.stock_code.trim()
    }

    return await apiClient.get('/lhb/active-branch-detail/by-stock-name', { params: cleanParams }) as unknown as ActiveBranchDetailListResponse
  },

  getStocksStatistics: async (params: LhbStockStatisticsParams): Promise<LhbStockStatisticsResponse> => {
    const cleanParams: Record<string, any> = {
      start_date: params.start_date,
      end_date: params.end_date,
    }
    
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
    
    return await apiClient.get('/lhb/stocks-statistics', { params: cleanParams }) as unknown as LhbStockStatisticsResponse
  },
}

export interface ActiveBranchDetailItem {
  id: number
  institution_code: string
  institution_name?: string
  date: string
  stock_code: string
  stock_name: string
  change_percent?: number
  buy_amount?: number
  sell_amount?: number
  net_amount?: number
  reason?: string
  after_1d?: number
  after_2d?: number
  after_3d?: number
  after_5d?: number
  after_10d?: number
  after_20d?: number
  after_30d?: number
  created_at: string
}

export interface ActiveBranchDetailStatistics {
  buy_branch_count: number  // 买入营业部个数
  sell_branch_count: number  // 卖出营业部个数
  total_buy_amount: number  // 买入总金额
  total_sell_amount: number  // 卖出总金额
}

export interface ActiveBranchDetailListResponse {
  items: ActiveBranchDetailItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  statistics?: ActiveBranchDetailStatistics  // 统计信息
}

export interface BuyStockStatisticsItem {
  stock_name: string
  appear_count: number
  buy_branch_count: number  // 买入营业部数
  sell_branch_count: number  // 卖出营业部数
  net_buy_amount: number  // 净买入额
  net_sell_amount: number  // 净卖出额
}

export interface BuyStockStatisticsParams {
  date?: string
  page?: number
  page_size?: number
}

export interface BuyStockStatisticsResponse {
  items: BuyStockStatisticsItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  date: string
}

export interface BuyStockBranchesResponse {
  items: ActiveBranchItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  stock_name: string
  date: string
}
