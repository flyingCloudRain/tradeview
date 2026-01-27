import apiClient from './client'
import { indexApi } from './index'
import { ztPoolApi } from './ztPool'
import { sectorApi } from './sector'

export interface DashboardStats {
  indexData: any[]
  ztPoolCount: number
  ztPoolDownCount: number
  sectorStats: {
    riseCount: number
    fallCount: number
    totalCount: number
  }
}

export const dashboardApi = {
  getStats: async (date: string): Promise<DashboardStats> => {
    try {
      console.log('开始获取仪表盘数据，日期:', date)
      
      // 使用 Promise.allSettled 来避免一个失败导致全部失败
      const results = await Promise.allSettled([
        indexApi.getList({ date }).catch(err => {
          console.warn('获取指数数据失败:', err)
          return []
        }),
        ztPoolApi.getList({ start_date: date, end_date: date, page: 1, page_size: 1 }).catch(err => {
          console.warn('获取涨停池数据失败:', err)
          return { total: 0, items: [] }
        }),
        ztPoolApi.getDownList({ date, page: 1, page_size: 1 }).catch(err => {
          console.warn('获取跌停池数据失败:', err)
          return { total: 0, items: [] }
        }),
        sectorApi.getList({ date }).catch(err => {
          console.warn('获取板块数据失败:', err)
          return []
        }),
      ])

      // 提取结果
      const indexData = results[0].status === 'fulfilled' ? results[0].value : []
      const ztPoolData = results[1].status === 'fulfilled' ? results[1].value : { total: 0, items: [] }
      const ztPoolDownData = results[2].status === 'fulfilled' ? results[2].value : { total: 0, items: [] }
      const sectorData = results[3].status === 'fulfilled' ? results[3].value : []

      // 统计上涨板块数量（change_percent > 0）和下跌板块数量（change_percent < 0）
      const sectorStats = {
        riseCount: sectorData.filter((item: any) => (item.change_percent || 0) > 0).length,
        fallCount: sectorData.filter((item: any) => (item.change_percent || 0) < 0).length,
        totalCount: sectorData.length,
      }

      console.log('仪表盘数据获取完成:', {
        indexCount: indexData.length,
        ztPoolCount: ztPoolData.total,
        ztPoolDownCount: ztPoolDownData.total,
        sectorCount: sectorData.length,
        sectorStats,
      })

      return {
        indexData: Array.isArray(indexData) ? indexData : [],
        ztPoolCount: ztPoolData.total || 0,
        ztPoolDownCount: ztPoolDownData.total || 0,
        sectorStats,
      }
    } catch (error) {
      console.error('获取仪表盘数据失败:', error)
      // 返回默认值而不是抛出错误
      return {
        indexData: [],
        ztPoolCount: 0,
        ztPoolDownCount: 0,
        sectorStats: {
          riseCount: 0,
          fallCount: 0,
          totalCount: 0,
        },
      }
    }
  },
}

