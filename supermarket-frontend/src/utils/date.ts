/**
 * 日期格式化工具函数
 */

/**
 * 格式化日期时间
 * @param dateString 日期字符串
 * @param options 格式化选项
 * @returns 格式化后的日期字符串
 */
export const formatDate = (dateString: string | null | undefined, options?: Intl.DateTimeFormatOptions): string => {
  if (!dateString) return '-'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '-'
    
    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }
    
    return date.toLocaleString('zh-CN', { ...defaultOptions, ...options })
  } catch (error) {
    return '-'
  }
}

/**
 * 格式化日期（不包含时间）
 * @param dateString 日期字符串
 * @returns 格式化后的日期字符串
 */
export const formatDateOnly = (dateString: string | null | undefined): string => {
  return formatDate(dateString, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * 格式化时间（不包含日期）
 * @param dateString 日期字符串
 * @returns 格式化后的时间字符串
 */
export const formatTimeOnly = (dateString: string | null | undefined): string => {
  return formatDate(dateString, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 格式化相对时间（如：2小时前）
 * @param dateString 日期字符串
 * @returns 相对时间字符串
 */
export const formatRelativeTime = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '-'
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffSeconds < 60) {
      return '刚刚'
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`
    } else if (diffHours < 24) {
      return `${diffHours}小时前`
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return formatDateOnly(dateString)
    }
  } catch (error) {
    return '-'
  }
} 