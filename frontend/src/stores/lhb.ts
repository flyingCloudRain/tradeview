import { defineStore } from 'pinia'
import { ref } from 'vue'
import { lhbApi, type LhbItem, type LhbListParams } from '@/api/lhb'

export const useLhbStore = defineStore('lhb', () => {
  const list = ref<LhbItem[]>([])
  const loading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const filters = ref<LhbListParams>({
    date: '',
    stock_code: '',
    stock_name: '',
  })

  const fetchList = async (params?: Partial<LhbListParams>) => {
    loading.value = true
    try {
      // 合并参数，确保日期格式正确
      const mergedParams = {
        ...filters.value,
        ...params,
      }
      
      // 确保日期是字符串格式
      if (mergedParams.date && typeof mergedParams.date !== 'string') {
        mergedParams.date = String(mergedParams.date)
      }
      
      // 构建查询参数，只包含有效值
      const queryParams: any = {
        date: mergedParams.date || '',
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
      }
      
      // 只在有值时才添加可选参数
      if (mergedParams.stock_code) {
        queryParams.stock_code = mergedParams.stock_code
      }
      if (mergedParams.stock_name) {
        queryParams.stock_name = mergedParams.stock_name
      }
      if (mergedParams.sort_by) {
        queryParams.sort_by = mergedParams.sort_by
      }
      if (mergedParams.order && (mergedParams.order === 'asc' || mergedParams.order === 'desc')) {
        queryParams.order = mergedParams.order
      }
      
      console.log('请求参数:', JSON.stringify(queryParams, null, 2))
      console.log('日期值:', queryParams.date, '类型:', typeof queryParams.date)
      
      const response = await lhbApi.getList(queryParams)
      console.log('API响应:', response)
      console.log('响应类型检查:', {
        isArray: Array.isArray(response?.items),
        itemsLength: response?.items?.length,
        total: response?.total,
      })
      
      // 确保数据存在
      if (response && Array.isArray(response.items)) {
        list.value = response.items
        pagination.value.total = response.total || 0
        console.log(`✅ 成功获取 ${response.items.length} 条数据，总计 ${response.total} 条`)
        
        if (response.items.length > 0) {
          console.log('第一条数据:', response.items[0])
        }
      } else {
        console.warn('⚠️  API返回数据格式异常:', response)
        console.warn('响应结构:', Object.keys(response || {}))
        list.value = []
        pagination.value.total = 0
      }
    } catch (error: any) {
      console.error('❌ 获取龙虎榜列表失败:', error)
      console.error('错误详情:', error.response || error.message)
      if (error.response) {
        console.error('错误响应数据:', error.response.data)
        console.error('错误状态码:', error.response.status)
      }
      list.value = []
      pagination.value.total = 0
      throw error // 重新抛出错误以便上层处理
    } finally {
      loading.value = false
    }
  }

  const setFilters = (newFilters: Partial<LhbListParams>) => {
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

