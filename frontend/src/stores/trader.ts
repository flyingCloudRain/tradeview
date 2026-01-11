import { defineStore } from 'pinia'
import { ref } from 'vue'
import { traderApi, type TraderItem } from '@/api/trader'

export const useTraderStore = defineStore('trader', () => {
  const list = ref<TraderItem[]>([])
  const loading = ref(false)

  const fetchList = async () => {
    loading.value = true
    try {
      list.value = await traderApi.list()
    } catch (e) {
      console.error('获取游资映射失败', e)
      list.value = []
    } finally {
      loading.value = false
    }
  }

  return {
    list,
    loading,
    fetchList,
  }
})

