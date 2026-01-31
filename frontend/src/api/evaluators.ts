/** API for evaluator management */

import apiClient from './index'
import type {
  Evaluator,
  EvaluatorCreate,
  EvaluatorUpdate,
  TaskEvaluatorInfo,
  EvaluatorTestRequest,
  EvaluatorTestResponse,
} from '@/types/evaluator'

export const evaluatorApi = {
  /**
   * Get all evaluators
   */
  async getEvaluators(typeFilter?: string): Promise<Evaluator[]> {
    const params = typeFilter ? { type: typeFilter } : {}
    const response = await apiClient.get<{ evaluators?: Evaluator[] }>('/evaluators', { params })
    // Handle both array response and object with evaluators property
    return Array.isArray(response.data) ? response.data : (response.data.evaluators || [])
  },

  /**
   * Get an evaluator by ID
   */
  async getEvaluator(id: string): Promise<Evaluator> {
    const response = await apiClient.get<Evaluator>(`/evaluators/${id}`)
    return response.data
  },

  /**
   * Create a new evaluator
   */
  async createEvaluator(data: EvaluatorCreate): Promise<Evaluator> {
    const response = await apiClient.post<Evaluator>('/evaluators', data)
    return response.data
  },

  /**
   * Update an evaluator
   */
  async updateEvaluator(id: string, data: EvaluatorUpdate): Promise<Evaluator> {
    const response = await apiClient.put<Evaluator>(`/evaluators/${id}`, data)
    return response.data
  },

  /**
   * Delete an evaluator
   */
  async deleteEvaluator(id: string): Promise<void> {
    await apiClient.delete(`/evaluators/${id}`)
  },

  /**
   * Test an evaluator with sample data
   */
  async testEvaluator(id: string, request: EvaluatorTestRequest): Promise<EvaluatorTestResponse> {
    const response = await apiClient.post<EvaluatorTestResponse>(`/evaluators/${id}/test`, request)
    return response.data
  },

  /**
   * Get evaluators configured for a task
   */
  async getTaskEvaluators(taskId: string): Promise<TaskEvaluatorInfo[]> {
    const response = await apiClient.get<{ evaluators: TaskEvaluatorInfo[] }>(`/evaluators/tasks/${taskId}/evaluators`)
    return response.data.evaluators || []
  },

  /**
   * Set evaluators for a task
   */
  async setTaskEvaluators(taskId: string, evaluatorIds: string[]): Promise<void> {
    await apiClient.put(`/evaluators/tasks/${taskId}/evaluators`, { evaluator_ids: evaluatorIds })
  },
}
