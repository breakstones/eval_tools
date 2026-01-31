/** Store for evaluator management */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { evaluatorApi } from '@/api/evaluators'
import type {
  Evaluator,
  EvaluatorCreate,
  EvaluatorUpdate,
  TaskEvaluatorInfo,
  EvaluatorTestRequest,
  EvaluatorTestResponse,
} from '@/types/evaluator'

export const useEvaluatorStore = defineStore('evaluator', () => {
  // State
  const evaluators = ref<Evaluator[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Task evaluators cache
  const taskEvaluatorsCache = ref<Map<string, TaskEvaluatorInfo[]>>(new Map())

  // Computed
  const llmJudges = computed(() =>
    evaluators.value.filter(e => e.type === 'llm_judge')
  )

  const codeEvaluators = computed(() =>
    evaluators.value.filter(e => e.type === 'code')
  )

  const userEvaluators = computed(() =>
    evaluators.value.filter(e => !e.is_system)
  )

  // Actions
  async function fetchEvaluators(typeFilter?: string) {
    loading.value = true
    error.value = null
    try {
      evaluators.value = await evaluatorApi.getEvaluators(typeFilter)
    } catch (err: any) {
      error.value = err.message || '获取评估器列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createEvaluator(data: EvaluatorCreate) {
    loading.value = true
    error.value = null
    try {
      const newEvaluator = await evaluatorApi.createEvaluator(data)
      evaluators.value.unshift(newEvaluator)
      return newEvaluator
    } catch (err: any) {
      error.value = err.message || '创建评估器失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateEvaluator(id: string, data: EvaluatorUpdate) {
    loading.value = true
    error.value = null
    try {
      const updated = await evaluatorApi.updateEvaluator(id, data)
      const index = evaluators.value.findIndex(e => e.id === id)
      if (index !== -1) {
        evaluators.value[index] = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.message || '更新评估器失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteEvaluator(id: string) {
    loading.value = true
    error.value = null
    try {
      await evaluatorApi.deleteEvaluator(id)
      evaluators.value = evaluators.value.filter(e => e.id !== id)
    } catch (err: any) {
      error.value = err.message || '删除评估器失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function testEvaluator(id: string, request: EvaluatorTestRequest): Promise<EvaluatorTestResponse> {
    loading.value = true
    error.value = null
    try {
      const result = await evaluatorApi.testEvaluator(id, request)
      return result
    } catch (err: any) {
      error.value = err.message || '测试评估器失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskEvaluators(taskId: string) {
    loading.value = true
    error.value = null
    try {
      const taskEvaluators = await evaluatorApi.getTaskEvaluators(taskId)
      taskEvaluatorsCache.value.set(taskId, taskEvaluators)
      return taskEvaluators
    } catch (err: any) {
      error.value = err.message || '获取任务评估器失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function setTaskEvaluators(taskId: string, evaluatorIds: string[]) {
    loading.value = true
    error.value = null
    try {
      await evaluatorApi.setTaskEvaluators(taskId, evaluatorIds)
      // Clear the cache to force a refetch from server
      taskEvaluatorsCache.value.delete(taskId)
    } catch (err: any) {
      error.value = err.message || '设置任务评估器失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  function getTaskEvaluatorsFromCache(taskId: string): TaskEvaluatorInfo[] | undefined {
    return taskEvaluatorsCache.value.get(taskId)
  }

  function clearTaskEvaluatorsCache(taskId?: string) {
    if (taskId) {
      taskEvaluatorsCache.value.delete(taskId)
    } else {
      taskEvaluatorsCache.value.clear()
    }
  }

  return {
    // State
    evaluators,
    loading,
    error,
    taskEvaluatorsCache,

    // Computed
    llmJudges,
    codeEvaluators,
    userEvaluators,

    // Actions
    fetchEvaluators,
    createEvaluator,
    updateEvaluator,
    deleteEvaluator,
    testEvaluator,
    fetchTaskEvaluators,
    setTaskEvaluators,
    getTaskEvaluatorsFromCache,
    clearTaskEvaluatorsCache,
  }
})
