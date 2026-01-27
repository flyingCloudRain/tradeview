import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fundFlowApi,
  type FundFlowItem,
  type FundFlowListParams,
  type FundFlowConceptItem,
  type FundFlowIndustryItem,
  type ConceptFundFlowQueryParams,
  type ConceptFundFlowQueryResponse,
  type ConceptFundFlowFilterRequest,
  type ConceptFundFlowFilterResponse,
} from '@/api/fundFlow'

export const useFundFlowStore = defineStore('fundFlow', () => {
  const list = ref<FundFlowItem[]>([])
  const loading = ref(false)
  const conceptList = ref<FundFlowConceptItem[]>([])
  const conceptLoading = ref(false)
  const conceptPagination = ref({
    current: 1,
    pageSize: 50,
    total: 0,
  })
  const conceptQueryParams = ref<Partial<ConceptFundFlowQueryParams>>({})
  const industryList = ref<FundFlowIndustryItem[]>([])
  const industryLoading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 50,
    total: 0,
  })
  const filters = ref<FundFlowListParams>({
    date: '',
    stock_code: '',
  })
  const sortParams = ref<{
    sort_by?: 'main_inflow' | 'main_outflow' | 'main_net_inflow' | 'turnover_rate' | 'change_percent'
    order?: 'asc' | 'desc'
  }>({
    sort_by: 'main_net_inflow',
    order: 'desc',
  })

  const fetchList = async (params?: Partial<FundFlowListParams>) => {
    loading.value = true
    try {
      const queryParams = {
        ...filters.value,
        ...params,
        ...sortParams.value,
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
      }
      const response = await fundFlowApi.getList(queryParams)
      list.value = response.items
      pagination.value.total = response.total
    } catch (error) {
      console.error('获取资金流列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  const setSortParams = (sortBy?: 'main_inflow' | 'main_outflow' | 'main_net_inflow' | 'turnover_rate' | 'change_percent', order: 'asc' | 'desc' = 'desc') => {
    sortParams.value = { sort_by: sortBy, order }
    pagination.value.current = 1
  }

  const fetchConcept = async (params: ConceptFundFlowQueryParams) => {
    conceptLoading.value = true
    try {
      const response = await fundFlowApi.getConcept(params)
      
      // 日期范围查询返回对象，单日期查询返回数组
      if (Array.isArray(response)) {
        // 单日期查询
        conceptList.value = response
        conceptPagination.value.total = response.length
        conceptPagination.value.current = 1
        conceptPagination.value.pageSize = params.limit || 50
      } else {
        // 日期范围查询
        conceptList.value = response.items || []
        conceptPagination.value.total = response.total || 0
        conceptPagination.value.current = response.page || 1
        conceptPagination.value.pageSize = response.page_size || 50
      }
      
      conceptQueryParams.value = params
    } catch (error) {
      console.error('获取概念资金流失败:', error)
      conceptList.value = []
      conceptPagination.value.total = 0
      throw error
    } finally {
      conceptLoading.value = false
    }
  }

  const filterConcept = async (request: ConceptFundFlowFilterRequest) => {
    conceptLoading.value = true
    try {
      const response: ConceptFundFlowFilterResponse = await fundFlowApi.filterConcept(request)
      conceptList.value = response.items
      conceptPagination.value.total = response.total
      conceptPagination.value.current = response.page
      conceptPagination.value.pageSize = response.page_size
      return response
    } catch (error) {
      console.error('概念资金流筛选失败:', error)
      conceptList.value = []
      conceptPagination.value.total = 0
      throw error
    } finally {
      conceptLoading.value = false
    }
  }

  const setConceptPagination = (page: number, pageSize: number) => {
    conceptPagination.value.current = page
    conceptPagination.value.pageSize = pageSize
  }

  const fetchIndustry = async (date: string, limit = 200) => {
    industryLoading.value = true
    try {
      industryList.value = await fundFlowApi.getIndustry(date, limit)
    } catch (error) {
      console.error('获取行业资金流失败:', error)
      industryList.value = []
    } finally {
      industryLoading.value = false
    }
  }

  const setFilters = (newFilters: Partial<FundFlowListParams>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.current = 1
  }

  const setPagination = (page: number, pageSize: number) => {
    pagination.value.current = page
    pagination.value.pageSize = pageSize
  }

  return {
    list,
    loading,
    conceptList,
    conceptLoading,
    conceptPagination,
    conceptQueryParams,
    industryList,
    industryLoading,
    pagination,
    filters,
    sortParams,
    fetchList,
    fetchConcept,
    filterConcept,
    fetchIndustry,
    setFilters,
    setPagination,
    setConceptPagination,
    setSortParams,
  }
})

