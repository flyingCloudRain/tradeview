import { defineStore } from 'pinia'
import { ref } from 'vue'
import { 
  institutionTradingApi, 
  type InstitutionTradingStatisticsItem, 
  type InstitutionTradingStatisticsListParams,
  type InstitutionTradingStatisticsAggregatedItem,
  type InstitutionTradingStatisticsAggregatedParams
} from '@/api/institutionTrading'

export const useInstitutionTradingStore = defineStore('institutionTrading', () => {
  const list = ref<InstitutionTradingStatisticsItem[]>([])
  const aggregatedList = ref<InstitutionTradingStatisticsAggregatedItem[]>([])
  const loading = ref(false)
  const aggregatedLoading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const aggregatedPagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const filters = ref<InstitutionTradingStatisticsListParams>({
    date: '',
    start_date: '',
    end_date: '',
    stock_code: '',
    stock_name: '',
    sort_by: 'institution_net_buy_amount',
    order: 'desc',
  })
  const aggregatedFilters = ref<InstitutionTradingStatisticsAggregatedParams>({
    start_date: '',
    end_date: '',
    stock_code: '',
    stock_name: '',
    min_appear_count: undefined,
    max_appear_count: undefined,
    min_total_net_buy_amount: undefined,
    max_total_net_buy_amount: undefined,
    min_total_buy_amount: undefined,
    max_total_buy_amount: undefined,
    min_total_sell_amount: undefined,
    max_total_sell_amount: undefined,
    sort_by: 'appear_count', // 默认按上榜次数排序
    order: 'desc', // 倒序
  })

  const fetchList = async (params?: Partial<InstitutionTradingStatisticsListParams>) => {
    loading.value = true
    try {
      const queryParams: InstitutionTradingStatisticsListParams = {
        ...filters.value,
        ...params,
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
      }
      // 清理空值
      if (!queryParams.date) delete (queryParams as any).date
      if (!queryParams.start_date) delete (queryParams as any).start_date
      if (!queryParams.end_date) delete (queryParams as any).end_date
      if (!queryParams.stock_code) delete (queryParams as any).stock_code
      if (!queryParams.stock_name) delete (queryParams as any).stock_name
      if (queryParams.order && !['asc', 'desc'].includes(queryParams.order)) {
        delete (queryParams as any).order
      }
      if (!queryParams.sort_by) {
        delete (queryParams as any).sort_by
      }
      const res = await institutionTradingApi.getList(queryParams)
      list.value = res.items
      pagination.value.total = res.total
    } catch (e) {
      console.error('获取机构交易统计数据失败', e)
      list.value = []
      pagination.value.total = 0
    } finally {
      loading.value = false
    }
  }

  const fetchAggregated = async (params?: Partial<InstitutionTradingStatisticsAggregatedParams>) => {
    aggregatedLoading.value = true
    try {
      const queryParams: InstitutionTradingStatisticsAggregatedParams = {
        ...aggregatedFilters.value,
        ...params,
        page: aggregatedPagination.value.current,
        page_size: aggregatedPagination.value.pageSize,
      }
      // 清理空值
      if (!queryParams.stock_code) delete (queryParams as any).stock_code
      if (!queryParams.stock_name) delete (queryParams as any).stock_name
      if (queryParams.min_appear_count === undefined || queryParams.min_appear_count === null) delete (queryParams as any).min_appear_count
      if (queryParams.max_appear_count === undefined || queryParams.max_appear_count === null) delete (queryParams as any).max_appear_count
      if (queryParams.min_total_net_buy_amount === undefined || queryParams.min_total_net_buy_amount === null) delete (queryParams as any).min_total_net_buy_amount
      if (queryParams.max_total_net_buy_amount === undefined || queryParams.max_total_net_buy_amount === null) delete (queryParams as any).max_total_net_buy_amount
      if (queryParams.min_total_buy_amount === undefined || queryParams.min_total_buy_amount === null) delete (queryParams as any).min_total_buy_amount
      if (queryParams.max_total_buy_amount === undefined || queryParams.max_total_buy_amount === null) delete (queryParams as any).max_total_buy_amount
      if (queryParams.min_total_sell_amount === undefined || queryParams.min_total_sell_amount === null) delete (queryParams as any).min_total_sell_amount
      if (queryParams.max_total_sell_amount === undefined || queryParams.max_total_sell_amount === null) delete (queryParams as any).max_total_sell_amount
      if (queryParams.order && !['asc', 'desc'].includes(queryParams.order)) {
        delete (queryParams as any).order
      }
      if (!queryParams.sort_by) {
        delete (queryParams as any).sort_by
      }
      const res = await institutionTradingApi.getAggregated(queryParams)
      // 如果使用默认排序（按上榜次数且倒序），进行二次排序：按上榜次数倒序
      // 如果用户手动点击了其他字段排序，则使用后端返回的排序结果
      let sortedItems = res.items
      if ((!queryParams.sort_by || queryParams.sort_by === 'appear_count') && queryParams.order === 'desc') {
        sortedItems = [...res.items].sort((a, b) => {
          // 按上榜次数倒序（从多到少）
          const appearCountDiff = (b.appear_count || 0) - (a.appear_count || 0)
          return appearCountDiff
        })
      }
      aggregatedList.value = sortedItems
      aggregatedPagination.value.total = res.total
    } catch (e) {
      console.error('获取机构交易统计汇总数据失败', e)
      aggregatedList.value = []
      aggregatedPagination.value.total = 0
      throw e
    } finally {
      aggregatedLoading.value = false
    }
  }

  const setFilters = (payload: Partial<InstitutionTradingStatisticsListParams>) => {
    filters.value = { ...filters.value, ...payload }
    pagination.value.current = 1
  }

  const setAggregatedFilters = (payload: Partial<InstitutionTradingStatisticsAggregatedParams>) => {
    aggregatedFilters.value = { ...aggregatedFilters.value, ...payload }
    aggregatedPagination.value.current = 1
  }

  const setPagination = (page: number, pageSize: number) => {
    pagination.value.current = page
    pagination.value.pageSize = pageSize
  }

  const setAggregatedPagination = (page: number, pageSize: number) => {
    aggregatedPagination.value.current = page
    aggregatedPagination.value.pageSize = pageSize
  }

  return {
    list,
    aggregatedList,
    loading,
    aggregatedLoading,
    pagination,
    aggregatedPagination,
    filters,
    aggregatedFilters,
    fetchList,
    fetchAggregated,
    setFilters,
    setAggregatedFilters,
    setPagination,
    setAggregatedPagination,
  }
})
