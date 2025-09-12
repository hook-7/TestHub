/**
 * 消息处理工具函数
 */

/**
 * 清理消息，去除尾部的\r\n和多余空格
 * @param message 原始消息
 * @returns 清理后的消息
 */
export function cleanMessage(message: string | undefined | null): string {
  if (!message) return ''
  
  return message
    .replace(/\r\n$/, '')  // 去除尾部的\r\n
    .replace(/\r$/, '')    // 去除尾部的\r
    .replace(/\n$/, '')    // 去除尾部的\n
    .trim()                // 去除首尾空格
}

/**
 * 检查消息是否包含期望的响应（忽略\r\n）
 * @param message 接收到的消息
 * @param expectedResponse 期望的响应
 * @returns 是否匹配
 */
export function matchesExpectedResponse(message: string, expectedResponse: string): boolean {
  const cleanMsg = cleanMessage(message)
  const cleanExpected = cleanMessage(expectedResponse)
  
  return cleanMsg.includes(cleanExpected)
}

/**
 * 使用正则表达式检查消息是否匹配期望的响应
 * @param message 接收到的消息
 * @param expectedResponse 期望的响应（正则表达式）
 * @returns 是否匹配
 */
export function matchesExpectedResponseRegex(message: string, expectedResponse: string): boolean {
  try {
    const cleanMsg = cleanMessage(message)
    const regex = new RegExp(expectedResponse)
    return regex.test(cleanMsg)
  } catch (e) {
    // 正则表达式无效，返回false
    return false
  }
}
