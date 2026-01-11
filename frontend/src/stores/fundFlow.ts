import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fundFlowApi,
  type FundFlowItem,
  type FundFlowListParams,
  type FundFlowConceptItem,
  type FundFlowIndustryItem,
} from '@/api/fundFlow'

export const useFundFlowStore = defineStore('fundFlow', () => {
  const list = ref<FundFlowItem[]>([])
  const loading = ref(false)
  const conceptList = ref<FundFlowConceptItem[]>([])
  const conceptLoading = ref(false)
  const industryList = ref<FundFlowIndustryItem[]>([])
  const industryLoading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 20,
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

  const fetchConcept = async (limit = 50, date?: string) => {
    conceptLoading.value = true
    try {
      conceptList.value = await fundFlowApi.getConcept(limit, date)
    } catch (error) {
      console.error('获取概念资金流失败:', error)
      conceptList.value = []
    } finally {
      conceptLoading.value = false
    }
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
    industryList,
    industryLoading,
    pagination,
    filters,
    sortParams,
    fetchList,
    fetchConcept,
    fetchIndustry,
    setFilters,
    setPagination,
    setSortParams,
  }
})

