import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { evalApi } from '@/api/eval'
import type { EvalTask, EvalTaskCreate, EvalTaskUpdate, EvalResult, EvalRun } from '@/types/eval'

export const useEvalStore = defineStore('eval', () => {
  // State
  const evalTasks = ref<EvalTask[]>([])
  const currentTask = ref<EvalTask | null>(null)
  // Store results by run_id to support switching between runs while evaluation is running
  const resultsByRunId = ref<Record<string, EvalResult[]>>({})
  // Current displayed results (updated when switching runs or when new results arrive for current run)
  const evalResults = ref<EvalResult[]>([])
  const evalRuns = ref<EvalRun[]>([])
  const currentRun = ref<EvalRun | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const isRunning = ref(false)
  const progress = ref({ current: 0, total: 0 })

  // Computed
  const hasTasks = computed(() => evalTasks.value.length > 0)

  // Actions
  async function fetchEvalTasks(setId?: string) {
    loading.value = true
    error.value = null
    try {
      evalTasks.value = await evalApi.getEvalTasks(setId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载评测任务失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchEvalTask(id: string) {
    loading.value = true
    error.value = null
    try {
      currentTask.value = await evalApi.getEvalTask(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载评测任务失败'
    } finally {
      loading.value = false
    }
  }

  async function createEvalTask(data: EvalTaskCreate) {
    loading.value = true
    error.value = null
    try {
      const task = await evalApi.createEvalTask(data)
      evalTasks.value.unshift(task)
      return task
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建评测任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateEvalTask(id: string, data: EvalTaskUpdate) {
    loading.value = true
    error.value = null
    try {
      const task = await evalApi.updateEvalTask(id, data)
      const index = evalTasks.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        evalTasks.value[index] = task
      }
      if (currentTask.value?.id === id) {
        currentTask.value = task
      }
      return task
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新评测任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function testTemplate(id: string, data: { case_id?: string; test_input?: string }) {
    loading.value = true
    error.value = null
    try {
      const result = await evalApi.testTemplate(id, data)
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : '测试模板失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteEvalTask(id: string) {
    loading.value = true
    error.value = null
    try {
      await evalApi.deleteEvalTask(id)
      evalTasks.value = evalTasks.value.filter((t) => t.id !== id)
      if (currentTask.value?.id === id) {
        currentTask.value = null
        // Clear all results for this task's runs
        evalRuns.value.forEach(run => {
          delete resultsByRunId.value[run.id]
        })
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除评测任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchEvalResults(taskId: string) {
    loading.value = true
    error.value = null
    try {
      // Note: This function fetches results by task_id, not by run_id
      const results = await evalApi.getEvalResults(taskId)
      // Since this fetches by task_id (not run_id), we can't store it in resultsByRunId
      // Just display the results directly
      evalResults.value = results
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载评测结果失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchEvalRuns(taskId: string) {
    loading.value = true
    error.value = null
    try {
      evalRuns.value = await evalApi.getEvalRuns(taskId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载运行记录失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchEvalRun(runId: string) {
    loading.value = true
    error.value = null
    try {
      const run = await evalApi.getEvalRun(runId)
      console.log('[fetchEvalRun] Fetched run:', runId, 'status:', run.status, 'summary:', run.summary)
      currentRun.value = run
      // Ensure the array exists
      if (!resultsByRunId.value[runId]) {
        resultsByRunId.value[runId] = []
      }
      // Use spread to trigger reactivity
      evalResults.value = [...resultsByRunId.value[runId]]
      console.log('[fetchEvalRun] runId:', runId, 'status:', run.status, 'cached results count:', resultsByRunId.value[runId].length)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载运行记录失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchRunResults(runId: string) {
    loading.value = true
    error.value = null
    try {
      const results = await evalApi.getRunResults(runId)
      // Store results by run_id and update current display
      resultsByRunId.value[runId] = results
      evalResults.value = results
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载运行结果失败'
    } finally {
      loading.value = false
    }
  }

  function startEvaluation(taskId: string) {
    isRunning.value = true
    progress.value = { current: 0, total: 0 }

    let wsStarted = false
    // Track the current run ID for this evaluation
    let currentRunId: string | null = null

    // First, connect to WebSocket
    const ws = evalApi.connectEvaluationWebSocket(
      taskId,
      (data) => {
        console.log('WebSocket message:', data)
        if (data.type === 'connected') {
          console.log('WebSocket connected, starting evaluation')
          // Now start the evaluation after WebSocket is connected
          if (!wsStarted) {
            wsStarted = true
            evalApi.startEvaluation(taskId).then((run) => {
              console.log('Evaluation started:', run)
              currentRun.value = run
              currentRunId = run.id
              // Refresh runs list to get the new run
              fetchEvalRuns(taskId)
            }).catch((err) => {
              console.error('Failed to start evaluation:', err)
              isRunning.value = false
              error.value = err.message || '启动评测失败'
            })
          }
        } else if (data.type === 'run_created') {
          console.log('Run created:', data.data)
          const runId = data.data.run_id
          currentRunId = runId
          // Refresh runs list and select the new run
          fetchEvalRuns(taskId).then(() => {
            // Fetch the new run's full info (including status)
            fetchEvalRun(runId)
          })
        } else if (data.type === 'result') {
          progress.value = {
            current: data.data.index || 0,
            total: data.data.total || 0,
          }
          // Store result by run_id, so results are accumulated even if user switches to another run
          const runId = data.data.run_id
          if (!resultsByRunId.value[runId]) {
            resultsByRunId.value[runId] = []
          }
          const result: EvalResult = {
            id: data.data.case_id,
            run_id: runId,
            task_id: taskId,
            case_id: data.data.case_id,
            case_uid: data.data.case_uid || null,
            actual_output: data.data.actual_output,
            is_passed: data.data.is_passed,
            execution_error: data.data.execution_error || null,
            evaluator_logs: data.data.evaluator_logs || [],
            execution_duration: data.data.execution_duration || null,
            skill_tokens: data.data.skill_tokens || null,
            evaluator_tokens: data.data.evaluator_tokens || null,
            created_at: new Date().toISOString(),
          }
          resultsByRunId.value[runId].push(result)
          console.log('[WS] Result added for run:', runId, 'currentRun:', currentRun.value?.id, 'results count:', resultsByRunId.value[runId].length)
          // If this is the currently selected run, update displayed results
          if (runId === currentRun.value?.id) {
            console.log('[WS] Updating evalResults for current run, count:', resultsByRunId.value[runId].length)
            evalResults.value = [...resultsByRunId.value[runId]]
          }
        } else if (data.type === 'complete') {
          console.log('[WS] Evaluation complete')
          isRunning.value = false
          progress.value = { current: progress.value.total, total: progress.value.total }
          // Use the tracked run ID to refresh the run status
          if (currentRunId) {
            console.log('[WS] Refreshing current run after complete, runId:', currentRunId)
            // First refresh runs list to get updated status
            fetchEvalRuns(taskId).then(() => {
              // Then fetch the complete run info (including status and summary)
              fetchEvalRun(currentRunId)
            })
          }
          // Refresh task to get summary
          fetchEvalTask(taskId)
        } else if (data.type === 'error') {
          isRunning.value = false
          error.value = data.data.error || '评测过程中发生错误'
        }
      },
      () => {
        isRunning.value = false
        error.value = '连接中断'
      }
    )

    return ws
  }

  return {
    // State
    evalTasks,
    currentTask,
    evalResults,
    evalRuns,
    currentRun,
    loading,
    error,
    isRunning,
    progress,
    // Computed
    hasTasks,
    // Actions
    fetchEvalTasks,
    fetchEvalTask,
    createEvalTask,
    updateEvalTask,
    deleteEvalTask,
    fetchEvalResults,
    fetchEvalRuns,
    fetchEvalRun,
    fetchRunResults,
    startEvaluation,
    testTemplate,
  }
})
