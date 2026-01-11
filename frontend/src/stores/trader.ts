import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { traderApi, type TraderItem, type TraderCreateRequest, type TraderUpdateRequest, type TraderBranchCreateRequest } from '@/api/trader'

export const useTraderStore = defineStore('trader', () => {
  const list = ref<TraderItem[]>([])
  const loading = ref(false)

  const fetchList = async () => {
    loading.value = true
    try {
      list.value = await traderApi.list()
    } catch (e) {
      console.error('获取游资机构失败', e)
      list.value = []
    } finally {
      loading.value = false
    }
  }

  const createTrader = async (data: TraderCreateRequest) => {
    try {
      const trader = await traderApi.create(data)
      await fetchList()
      ElMessage.success('创建游资成功')
      return trader
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '创建游资失败')
      throw e
    }
  }

  const updateTrader = async (id: number, data: TraderUpdateRequest) => {
    try {
      const trader = await traderApi.update(id, data)
      await fetchList()
      ElMessage.success('更新游资成功')
      return trader
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '更新游资失败')
      throw e
    }
  }

  const deleteTrader = async (id: number) => {
    try {
      await traderApi.delete(id)
      await fetchList()
      ElMessage.success('删除游资成功')
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '删除游资失败')
      throw e
    }
  }

  const addBranch = async (traderId: number, data: TraderBranchCreateRequest) => {
    try {
      const branch = await traderApi.addBranch(traderId, data)
      await fetchList()
      ElMessage.success('添加机构成功')
      return branch
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '添加机构失败')
      throw e
    }
  }

  const updateBranch = async (traderId: number, branchId: number, data: TraderBranchCreateRequest) => {
    try {
      const branch = await traderApi.updateBranch(traderId, branchId, data)
      await fetchList()
      ElMessage.success('更新机构成功')
      return branch
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '更新机构失败')
      throw e
    }
  }

  const deleteBranch = async (traderId: number, branchId: number) => {
    try {
      await traderApi.deleteBranch(traderId, branchId)
      await fetchList()
      ElMessage.success('删除机构成功')
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '删除机构失败')
      throw e
    }
  }

  return {
    list,
    loading,
    fetchList,
    createTrader,
    updateTrader,
    deleteTrader,
    addBranch,
    updateBranch,
    deleteBranch,
  }
})

