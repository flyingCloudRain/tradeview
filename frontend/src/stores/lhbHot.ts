import { defineStore } from 'pinia'
import { ref } from 'vue'
import { lhbHotApi, type LhbHotItem, type LhbHotListParams } from '@/api/lhbHot'

export const useLhbHotStore = defineStore('lhbHot', () => {
  const list = ref<LhbHotItem[]>([])
  const loading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const filters = ref<LhbHotListParams>({
    date: '',
    stock_code: '',
    stock_name: '',
    flag: undefined,
    sort_by: 'buy_amount',
    order: 'desc',
  })

  const fetchList = async (params?: Partial<LhbHotListParams>) => {
    loading.value = true
    try {
      const queryParams: LhbHotListParams = {
        ...filters.value,
        ...params,
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
      }
      // 清理空值
      if (!queryParams.stock_code) delete (queryParams as any).stock_code
      if (!queryParams.stock_name) delete (queryParams as any).stock_name
      if (!queryParams.flag) delete (queryParams as any).flag
      if (queryParams.order && !['asc', 'desc'].includes(queryParams.order)) {
        delete (queryParams as any).order
      }
      if (!queryParams.sort_by) {
        delete (queryParams as any).sort_by
      }
      const res = await lhbHotApi.getList(queryParams)
      list.value = res.items
      pagination.value.total = res.total
    } catch (e) {
      console.error('获取游资榜失败', e)
      list.value = []
      pagination.value.total = 0
    } finally {
      loading.value = false
    }
  }

  const setFilters = (payload: Partial<LhbHotListParams>) => {
    filters.value = { ...filters.value, ...payload }
    pagination.value.current = 1
  }

  const setPagination = (page: number, pageSize: number) => {
    pagination.value.current = page
    pagination.value.pageSize = pageSize
  }

  return {
    list,
    loading,
    pagination,
    filters,
    fetchList,
    setFilters,
    setPagination,
  }
})

