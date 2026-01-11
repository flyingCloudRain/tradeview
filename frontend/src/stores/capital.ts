import { defineStore } from 'pinia'
import { ref } from 'vue'
import { capitalApi, type CapitalItem, type CapitalListParams } from '@/api/capital'

export const useCapitalStore = defineStore('capital', () => {
  const list = ref<CapitalItem[]>([])
  const loading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const filters = ref<CapitalListParams>({
    date: '',
    capital_name: '',
  })

  const fetchList = async (params?: Partial<CapitalListParams>) => {
    loading.value = true
    try {
      const queryParams = {
        ...filters.value,
        ...params,
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
      }
      const response = await capitalApi.getList(queryParams)
      list.value = response.items
      pagination.value.total = response.total
    } catch (error) {
      console.error('获取游资榜列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  const setFilters = (newFilters: Partial<CapitalListParams>) => {
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
    pagination,
    filters,
    fetchList,
    setFilters,
    setPagination,
  }
})

