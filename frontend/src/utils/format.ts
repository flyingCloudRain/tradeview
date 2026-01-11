/**
 * 将值转换为数字（支持字符串和数字）
 */
function toNumber(value: number | string | null | undefined): number | null {
  if (value === undefined || value === null || value === '') {
    return null
  }
  if (typeof value === 'number') {
    return value
  }
  if (typeof value === 'string') {
    const num = parseFloat(value)
    return isNaN(num) ? null : num
  }
  return null
}

export function formatAmount(amount?: number | string): string {
  const num = toNumber(amount)
  if (num === null) {
    return "-"
  }
  
  // 使用绝对值来判断单位，保留原始符号
  const absNum = Math.abs(num)
  const sign = num < 0 ? "-" : ""
  
  if (absNum >= 100000000) {
    return `${sign}${(absNum / 100000000).toFixed(2)}亿`
  } else if (absNum >= 10000) {
    return `${sign}${(absNum / 10000).toFixed(2)}万`
  } else {
    return `${num.toFixed(2)}`
  }
}

export function formatPercent(value?: number | string, decimals: number = 2): string {
  const num = toNumber(value)
  if (num === null) {
    return "-"
  }
  
  const sign = num > 0 ? "+" : ""
  return `${sign}${num.toFixed(decimals)}%`
}

export function formatPrice(price?: number | string, decimals: number = 2): string {
  const num = toNumber(price)
  if (num === null) {
    return "-"
  }
  
  return num.toFixed(decimals)
}

