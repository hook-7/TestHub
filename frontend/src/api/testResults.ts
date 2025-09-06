/**
 * Test Results API
 * 测试结果相关的API接口
 */

import { api } from './index'

// 测试项结果接口
export interface TestItemResult {
  id: string
  name: string
  command: string
  expected_response: string
  actual_response?: string
  is_ok: boolean
  reason: string
  timestamp: number
  has_notification: boolean
  user_choice?: boolean
}

// 测试结果接口
export interface TestResult {
  mac_address: string
  test_items: TestItemResult[]
  start_time: number
  end_time?: number
  total_tests: number
  passed_tests: number
  failed_tests: number
  skipped_tests: number
  operator?: string
  workstation?: string
  device_id?: string
}

// 保存测试结果请求接口
export interface SaveTestResultRequest extends TestResult {}

// 测试结果响应接口
export interface TestResultResponse {
  id: string
  mac_address: string
  start_time: number
  end_time?: number
  total_tests: number
  passed_tests: number
  failed_tests: number
  skipped_tests: number
  operator?: string
  workstation?: string
  device_id?: string
  created_at: number
}

// 测试结果详情响应接口
export interface TestResultDetailResponse extends TestResultResponse {
  test_items: TestItemResult[]
}

// 测试结果列表响应接口
export interface TestResultListResponse {
  results: TestResultResponse[]
  total: number
  page: number
  page_size: number
}

// 获取测试结果列表的查询参数
export interface GetTestResultsParams {
  page?: number
  page_size?: number
  mac_address?: string
  operator?: string
  workstation?: string
  device_id?: string
  start_date?: string // YYYY-MM-DD
  end_date?: string // YYYY-MM-DD
}

/**
 * 测试结果API类
 */
export class TestResultsAPI {
  /**
   * 保存测试结果
   */
  static async saveTestResult(data: SaveTestResultRequest): Promise<TestResultResponse> {
    const response = await api.post('/test-results/save', data)
    return response
  }

  /**
   * 获取测试结果详情
   */
  static async getTestResultDetail(testResultId: string): Promise<TestResultDetailResponse> {
    const response = await api.get(`/test-results/${testResultId}`)
    return response
  }

  /**
   * 获取测试结果列表
   */
  static async getTestResults(params: GetTestResultsParams = {}): Promise<TestResultListResponse> {
    const response = await api.get('/test-results/', { params })
    return response
  }

  /**
   * 删除测试结果
   */
  static async deleteTestResult(testResultId: string): Promise<void> {
    await api.delete(`/test-results/${testResultId}`)
  }
}

// 导出API实例
export const testResultsAPI = TestResultsAPI
