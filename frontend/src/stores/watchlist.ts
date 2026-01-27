import { defineStore } from 'pinia'
import { ref } from 'vue'

const WATCHLIST_STORAGE_KEY = 'stock_watchlist'

export const useWatchlistStore = defineStore('watchlist', () => {
  const stocks = ref<string[]>([])

  // 从 localStorage 加载关注列表
  const loadWatchlist = () => {
    try {
      const stored = localStorage.getItem(WATCHLIST_STORAGE_KEY)
      if (stored) {
        stocks.value = JSON.parse(stored)
      }
    } catch (error) {
      console.error('加载关注列表失败:', error)
      stocks.value = []
    }
  }

  // 保存关注列表到 localStorage
  const saveWatchlist = () => {
    try {
      localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(stocks.value))
    } catch (error) {
      console.error('保存关注列表失败:', error)
    }
  }

  // 添加股票到关注列表
  const addStock = (stockCode: string) => {
    if (!stockCode || stockCode.trim() === '') return false
    
    const code = stockCode.trim()
    if (!stocks.value.includes(code)) {
      stocks.value.push(code)
      saveWatchlist()
      return true
    }
    return false
  }

  // 从关注列表移除股票
  const removeStock = (stockCode: string) => {
    const index = stocks.value.indexOf(stockCode)
    if (index > -1) {
      stocks.value.splice(index, 1)
      saveWatchlist()
      return true
    }
    return false
  }

  // 检查股票是否在关注列表中
  const isWatched = (stockCode: string): boolean => {
    return stocks.value.includes(stockCode)
  }

  // 切换股票关注状态
  const toggleStock = (stockCode: string) => {
    if (isWatched(stockCode)) {
      removeStock(stockCode)
      return false
    } else {
      addStock(stockCode)
      return true
    }
  }

  // 清空关注列表
  const clearWatchlist = () => {
    stocks.value = []
    saveWatchlist()
  }

  // 初始化时加载
  loadWatchlist()

  return {
    stocks,
    addStock,
    removeStock,
    isWatched,
    toggleStock,
    clearWatchlist,
    loadWatchlist,
  }
})
