import apiClient from './client'

export interface FundFlowItem {
  id: number
  date: string
  stock_code: string
  stock_name: string
  current_price?: number
  change_percent?: number
  turnover_rate?: number
  main_inflow?: number
  main_outflow?: number
  main_net_inflow?: number
  turnover_amount?: number
  is_limit_up?: boolean
  is_lhb?: boolean
}

export interface FundFlowListParams {
  date?: string  // 单日期查询（可选，与日期范围查询互斥）
  start_date?: string  // 开始日期（日期范围查询，可选，默认最近3日）
  end_date?: string  // 结束日期（日期范围查询，可选，默认最近3日）
  stock_code?: string
  consecutive_days?: number  // 连续N日
  min_net_inflow?: number  // 净流入>M（单位：元）
  is_limit_up?: boolean  // 是否涨停，true=仅涨停，false=仅非涨停，undefined=全部
  page?: number
  page_size?: number
  sort_by?: 'main_inflow' | 'main_outflow' | 'main_net_inflow' | 'turnover_rate' | 'change_percent'
  order?: 'asc' | 'desc'
}

export interface FundFlowListResponse {
  items: FundFlowItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface FundFlowConceptItem {
  id?: number
  date?: string
  concept: string
  index_value?: number
  index_change_percent?: number
  inflow?: number
  outflow?: number
  net_amount?: number
  stock_count?: number
  leader_stock?: string
  leader_change_percent?: number
  leader_price?: number
  match_conditions?: Array<{
    condition_index: number
    date_range: DateRange
    date: string
  }>
}

export interface FundFlowIndustryItem {
  id: number
  date: string
  industry: string
  index_value?: number
  index_change_percent?: number
  inflow?: number
  outflow?: number
  net_amount?: number
  stock_count?: number
  leader_stock?: string
  leader_change_percent?: number
  leader_price?: number
}

export interface DateRange {
  start?: string
  end?: string
}

export interface NetInflowRange {
  min?: number
  max?: number
}

export interface LimitUpCountRange {
  min?: number
  max?: number
}

export interface DateRangeCondition {
  date_range: DateRange
  main_net_inflow?: NetInflowRange
  limit_up_count?: LimitUpCountRange
}

export interface FundFlowFilterRequest {
  conditions: DateRangeCondition[]
  concept_ids?: number[]
  concept_names?: string[]
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface FundFlowFilterItem {
  stock_code: string
  stock_name: string
  match_conditions: Array<{
    condition_index: number
    date_range: DateRange
    main_net_inflow?: NetInflowRange
    matched_count: number
    matched_records: Array<{
      date: string
      main_net_inflow: number | null
    }>
  }>
  latest_date: string | null
  latest_main_net_inflow: number | null
  concepts: Array<{
    id: number
    name: string
    code: string | null
  }>
}

export interface FundFlowFilterResponse {
  items: FundFlowFilterItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 概念资金流查询参数
export interface ConceptFundFlowQueryParams {
  // 单日期查询（可选，为空时查询最新日期）
  date?: string
  // 日期范围查询（可选，优先级高于date）
  start_date?: string
  end_date?: string
  // 概念名称（可选，模糊匹配）
  concept?: string
  limit?: number
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

// 概念资金流查询响应（单日期查询返回数组）
// 概念资金流查询响应（单日期查询返回数组，日期范围查询返回分页对象）
export type ConceptFundFlowQueryResponse = FundFlowConceptItem[] | {
  items: FundFlowConceptItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 概念资金流筛选条件
export interface ConceptNetAmountRange {
  min?: number
  max?: number
}

export interface ConceptInflowRange {
  min?: number
  max?: number
}

export interface ConceptOutflowRange {
  min?: number
  max?: number
}

export interface ConceptIndexChangeRange {
  min?: number
  max?: number
}

export interface ConceptDateRangeCondition {
  date_range?: DateRange
  net_amount?: ConceptNetAmountRange
  inflow?: ConceptInflowRange
  outflow?: ConceptOutflowRange
  index_change_percent?: ConceptIndexChangeRange
  stock_count?: LimitUpCountRange
}

export interface ConceptFundFlowFilterRequest {
  conditions: ConceptDateRangeCondition[]
  concepts?: string[]
  page?: number
  page_size?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface ConceptFundFlowFilterResponse {
  items: FundFlowConceptItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const fundFlowApi = {
  getList: async (params: FundFlowListParams): Promise<FundFlowListResponse> => {
    return await apiClient.get('/stock-fund-flow', { params })
  },

  getHistory: async (stockCode: string, startDate: string, endDate: string) => {
    return await apiClient.get(`/stock-fund-flow/${stockCode}/history`, {
      params: { start_date: startDate, end_date: endDate },
    })
  },

  getConcept: async (params: ConceptFundFlowQueryParams): Promise<ConceptFundFlowQueryResponse> => {
    // 支持单日期或日期范围查询
    const queryParams: Record<string, any> = {}
    
    console.log('getConcept 接收到的参数:', params)
    
    // 日期范围查询优先级高于单日期查询
    if (params.start_date && params.end_date) {
      queryParams.start_date = params.start_date
      queryParams.end_date = params.end_date
      console.log('设置日期范围参数:', { start_date: queryParams.start_date, end_date: queryParams.end_date })
    } else if (params.date) {
      queryParams.date = params.date
      console.log('设置单日期参数:', { date: queryParams.date })
    }
    
    if (params.concept) {
      queryParams.concept = params.concept
    }
    
    if (params.limit) {
      queryParams.limit = params.limit
    }
    
    if (params.page) {
      queryParams.page = params.page
    }
    
    if (params.page_size) {
      queryParams.page_size = params.page_size
    }
    
    if (params.sort_by) {
      queryParams.sort_by = params.sort_by
    }
    
    if (params.order) {
      queryParams.order = params.order
    }
    
    console.log('getConcept 最终查询参数:', queryParams)
    
    return await apiClient.get('/stock-fund-flow/concept', { params: queryParams })
  },

  filterConcept: async (request: ConceptFundFlowFilterRequest): Promise<ConceptFundFlowFilterResponse> => {
    return await apiClient.post('/stock-fund-flow/concept/filter', request)
  },

  getIndustry: async (date: string, limit = 200): Promise<FundFlowIndustryItem[]> => {
    return await apiClient.get('/stock-fund-flow/industry', { params: { date, limit } })
  },

  filter: async (request: FundFlowFilterRequest): Promise<FundFlowFilterResponse> => {
    return await apiClient.post('/stock-fund-flow/filter', request)
  },
}

