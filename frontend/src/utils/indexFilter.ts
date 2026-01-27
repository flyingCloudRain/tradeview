/**
 * 指数过滤工具
 * 定义主要指数的代码和名称映射
 */

// 主要指数代码映射（代码 -> 名称）
// 按显示顺序排列
export const MAIN_INDEX_CODES: Record<string, string> = {
  '000001': '上证指数',
  '000016': '上证50',
  '399001': '深证成指',
  '399006': '创业板指',
  '000688': '科创50',
  '000680': '科创综指', // 注意：实际代码是000680
  '899050': '北证50',
  '000300': '沪深300',
  '000905': '中证500',
  '000852': '中证1000',
  '932000': '中证2000',
}

// 主要指数名称关键词（用于模糊匹配）
export const MAIN_INDEX_KEYWORDS: string[] = [
  '上证指数',
  '上证50',
  '深证成指',
  '深证指数',
  '创业板指',
  '创业板指数',
  '科创50',
  '科创综指',
  '北证50',
  '沪深300',
  '中证500',
  '中证1000',
  '中证2000',
]

// 主要指数名称映射（名称 -> 代码）
export const MAIN_INDEX_NAMES: Record<string, string> = {
  '上证指数': '000001',
  '上证50': '000016',
  '深证成指': '399001',
  '深证指数': '399001',
  '创业板指': '399006',
  '创业板指数': '399006',
  '科创50': '000688',
  '科创综指': '000698',
  '北证50': '899050',
  '沪深300': '000300',
  '中证500': '000905',
  '中证1000': '000852',
  '中证2000': '932000',
}

/**
 * 过滤主要指数
 * @param indices 所有指数数据
 * @returns 过滤后的主要指数数据
 */
export function filterMainIndices(indices: any[]): any[] {
  if (!indices || indices.length === 0) {
    return []
  }

  // 创建代码和名称的集合用于快速查找
  const mainCodes = new Set(Object.keys(MAIN_INDEX_CODES))
  const mainNames = new Set(Object.keys(MAIN_INDEX_NAMES))

  // 过滤指数
  const filtered = indices.filter((index) => {
    const code = index.index_code || ''
    const name = index.index_name || ''

    // 通过代码匹配
    if (mainCodes.has(code)) {
      return true
    }

    // 通过名称关键词匹配（支持部分匹配）
    for (const keyword of MAIN_INDEX_KEYWORDS) {
      if (name.includes(keyword) || keyword.includes(name)) {
        return true
      }
    }

    // 通过名称映射匹配
    for (const mainName of mainNames) {
      if (name === mainName || name.includes(mainName) || mainName.includes(name)) {
        return true
      }
    }

    return false
  })

  // 按照预定义的顺序排序
  const sorted = filtered.sort((a, b) => {
    const codeA = a.index_code || ''
    const codeB = b.index_code || ''
    const orderA = Object.keys(MAIN_INDEX_CODES).indexOf(codeA)
    const orderB = Object.keys(MAIN_INDEX_CODES).indexOf(codeB)

    // 如果都在预定义列表中，按顺序排序
    if (orderA !== -1 && orderB !== -1) {
      return orderA - orderB
    }
    // 如果只有一个在列表中，优先显示
    if (orderA !== -1) return -1
    if (orderB !== -1) return 1
    // 都不在列表中，按名称排序
    return (a.index_name || '').localeCompare(b.index_name || '')
  })

  return sorted
}

/**
 * 检查是否为主要指数
 */
export function isMainIndex(index: any): boolean {
  if (!index) return false

  const code = index.index_code || ''
  const name = index.index_name || ''

  if (MAIN_INDEX_CODES[code]) return true

  for (const mainName of Object.keys(MAIN_INDEX_NAMES)) {
    if (name.includes(mainName) || mainName.includes(name)) {
      return true
    }
  }

  return false
}

