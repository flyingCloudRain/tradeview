import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ztPoolApi, type ZtPoolItem, type ZtPoolListParams } from '@/api/ztPool'

export const useZtPoolStore = defineStore('ztPool', () => {
  const list = ref<ZtPoolItem[]>([])
  const loading = ref(false)
  const activeType = ref<'up' | 'down'>('up')
  const pagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const filters = ref<ZtPoolListParams>({})
  const analysis = ref<any>(null)

  const fetchList = async (params?: Partial<ZtPoolListParams>) => {
    loading.value = true
    try {
      const queryParams = {
        ...filters.value,
        ...params,
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
      }
      // 清理无效排序值
      if (queryParams.order && !['asc', 'desc'].includes(queryParams.order)) {
        delete (queryParams as any).order
      }
      if (!queryParams.sort_by) {
        delete (queryParams as any).sort_by
      }
      // 清理date参数，优先使用start_date和end_date
      if (queryParams.start_date && queryParams.end_date) {
        delete (queryParams as any).date
      }
      const response =
        activeType.value === 'up'
          ? await ztPoolApi.getList(queryParams)
          : await ztPoolApi.getDownList({ ...queryParams, order: queryParams.order ?? 'asc' })
      list.value = response.items
      pagination.value.total = response.total
    } catch (error) {
      console.error('获取涨停池列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  const updateItem = async (id: number, payload: Partial<Pick<ZtPoolItem, 'concept' | 'limit_up_reason'>>) => {
    try {
      await ztPoolApi.updateItem(id, payload)
    } catch (error) {
      console.error('更新涨停池记录失败:', error)
      throw error
    }
  }

  const fetchAnalysis = async (date: string) => {
    try {
      analysis.value = await ztPoolApi.getAnalysis(date)
    } catch (error) {
      console.error('获取涨停分析失败:', error)
    }
  }

  const setFilters = (newFilters: Partial<ZtPoolListParams>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.current = 1
  }

  const setPagination = (page: number, pageSize: number) => {
    pagination.value.current = page
    pagination.value.pageSize = pageSize
  }

  const setActiveType = (type: 'up' | 'down') => {
    activeType.value = type
    pagination.value.current = 1
  }

  return {
    list,
    loading,
    activeType,
    pagination,
    filters,
    analysis,
    fetchList,
    fetchAnalysis,
    setFilters,
    setPagination,
    updateItem,
    setActiveType,
  }
})

