import apiClient from './client'
import { indexApi } from './index'
import { lhbApi } from './lhb'
import { ztPoolApi } from './ztPool'
import { sectorApi } from './sector'

export interface DashboardStats {
  indexData: any[]
  lhbCount: number
  ztPoolCount: number
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
        lhbApi.getList({ date, page: 1, page_size: 1 }).catch(err => {
          console.warn('获取龙虎榜数据失败:', err)
          return { total: 0, items: [] }
        }),
        ztPoolApi.getList({ date, page: 1, page_size: 1 }).catch(err => {
          console.warn('获取涨停池数据失败:', err)
          return { total: 0, items: [] }
        }),
        sectorApi.getList({ date }).catch(err => {
          console.warn('获取板块数据失败:', err)
          return []
        }),
      ])

      // 提取结果
      const indexData = results[0].status === 'fulfilled' ? results[0].value : []
      const lhbData = results[1].status === 'fulfilled' ? results[1].value : { total: 0, items: [] }
      const ztPoolData = results[2].status === 'fulfilled' ? results[2].value : { total: 0, items: [] }
      const sectorData = results[3].status === 'fulfilled' ? results[3].value : []

      const sectorStats = {
        riseCount: sectorData.reduce((sum: number, item: any) => sum + (item.rise_count || 0), 0),
        fallCount: sectorData.reduce((sum: number, item: any) => sum + (item.fall_count || 0), 0),
        totalCount: sectorData.reduce((sum: number, item: any) => sum + (item.total_count || 0), 0),
      }

      console.log('仪表盘数据获取完成:', {
        indexCount: indexData.length,
        lhbCount: lhbData.total,
        ztPoolCount: ztPoolData.total,
        sectorCount: sectorData.length,
      })

      return {
        indexData: Array.isArray(indexData) ? indexData : [],
        lhbCount: lhbData.total || 0,
        ztPoolCount: ztPoolData.total || 0,
        sectorStats,
      }
    } catch (error) {
      console.error('获取仪表盘数据失败:', error)
      // 返回默认值而不是抛出错误
      return {
        indexData: [],
        lhbCount: 0,
        ztPoolCount: 0,
        sectorStats: {
          riseCount: 0,
          fallCount: 0,
          totalCount: 0,
        },
      }
    }
  },
}

