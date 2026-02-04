import api from './index'
import type {
  EvalTask,
  EvalTaskCreate,
  EvalTaskUpdate,
  EvalResult,
  EvalSummary,
  EvalRun,
  TemplateTestRequest,
  TemplateTestResponse,
} from '@/types/eval'

export const evalApi = {
  getEvalTasks: (setId?: string) =>
    api.get<EvalTask[]>('/eval/tasks', {
      params: { set_id: setId },
    }).then((res) => res.data),

  getEvalTask: (id: string) =>
    api.get<EvalTask>(`/eval/tasks/${id}`).then((res) => res.data),

  createEvalTask: (data: EvalTaskCreate) =>
    api.post<EvalTask>('/eval/tasks', data).then((res) => res.data),

  updateEvalTask: (id: string, data: EvalTaskUpdate) =>
    api.put<EvalTask>(`/eval/tasks/${id}`, data).then((res) => res.data),

  deleteEvalTask: (id: string) =>
    api.delete(`/eval/tasks/${id}`),

  testTemplate: (id: string, data: TemplateTestRequest) =>
    api.post<TemplateTestResponse>(`/eval/tasks/${id}/test-template`, data).then((res) => res.data),

  getEvalResults: (taskId: string) =>
    api.get<EvalResult[]>(`/eval/tasks/${taskId}/results`).then((res) => res.data),

  getEvalResult: (id: string) =>
    api.get<EvalResult>(`/eval/results/${id}`).then((res) => res.data),

  // Run history APIs
  getEvalRuns: (taskId: string) =>
    api.get<EvalRun[]>(`/eval/tasks/${taskId}/runs`).then((res) => res.data),

  getEvalRun: (runId: string) =>
    api.get<EvalRun>(`/eval/runs/${runId}`).then((res) => res.data),

  getRunResults: (runId: string) =>
    api.get<EvalResult[]>(`/eval/runs/${runId}/results`).then((res) => res.data),

  // Start a new evaluation run (POST - returns immediately, runs in background)
  startEvaluation: (taskId: string) =>
    api.post<EvalRun>(`/eval/tasks/${taskId}/rerun`).then((res) => res.data),

  // WebSocket for evaluation progress (returns the WebSocket instance)
  connectEvaluationWebSocket: (
    taskId: string,
    onMessage: (data: any) => void,
    onError?: () => void,
  ) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/eval/ws/eval/${taskId}`
    console.log('Connecting to WebSocket:', wsUrl)

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected for task:', taskId)
    }

    ws.onmessage = (event) => {
      console.log('WebSocket message received:', event.data)
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error for task:', taskId, error)
      if (onError) onError()
    }

    ws.onclose = (event) => {
      console.log('WebSocket closed for task:', taskId, event.code, event.reason)
    }

    return ws
  },

  // 导出评测结果为 Excel
  exportRunResults: (runId: string, failedOnly = false) => {
    return api.get(`/eval/runs/${runId}/export`, {
      params: { failed_only: failedOnly },
      responseType: 'blob',
    }).then((res) => res.data)
  },
}
