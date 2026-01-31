import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEvalStore } from '@/stores/eval'

// Mock the eval API
vi.mock('@/api/eval', () => ({
  evalApi: {
    getEvalTasks: vi.fn(),
    getEvalTask: vi.fn(),
    createEvalTask: vi.fn(),
    deleteEvalTask: vi.fn(),
    getEvalResults: vi.fn(),
    getEvalResult: vi.fn(),
    streamEvaluation: vi.fn()
  }
}))

describe('Eval Store', () => {
  let store: ReturnType<typeof useEvalStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useEvalStore()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      expect(store.evalTasks).toEqual([])
      expect(store.currentTask).toBeNull()
      expect(store.evalResults).toEqual([])
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.isRunning).toBe(false)
      expect(store.progress).toEqual({ current: 0, total: 0 })
    })

    it('hasTasks should return false when empty', () => {
      expect(store.hasTasks).toBe(false)
    })

    it('hasTasks should return true when has items', () => {
      store.evalTasks = [{ id: '1', set_id: 'set-1', status: 'PENDING' } as any]
      expect(store.hasTasks).toBe(true)
    })
  })

  describe('fetchEvalTasks', () => {
    it('should fetch eval tasks successfully', async () => {
      const { evalApi } = await import('@/api/eval')
      const mockTasks = [
        { id: '1', set_id: 'set-1', status: 'COMPLETED' },
        { id: '2', set_id: 'set-2', status: 'PENDING' }
      ]
      vi.mocked(evalApi.getEvalTasks).mockResolvedValue(mockTasks as any)

      await store.fetchEvalTasks()

      expect(store.loading).toBe(false)
      expect(store.evalTasks).toEqual(mockTasks)
      expect(store.error).toBeNull()
    })

    it('should fetch eval tasks with set_id filter', async () => {
      const { evalApi } = await import('@/api/eval')
      const mockTasks = [
        { id: '1', set_id: 'set-1', status: 'COMPLETED' }
      ]
      vi.mocked(evalApi.getEvalTasks).mockResolvedValue(mockTasks as any)

      await store.fetchEvalTasks('set-1')

      expect(evalApi.getEvalTasks).toHaveBeenCalledWith('set-1')
      expect(store.evalTasks).toEqual(mockTasks)
    })

    it('should handle fetch error', async () => {
      const { evalApi } = await import('@/api/eval')
      vi.mocked(evalApi.getEvalTasks).mockRejectedValue(new Error('Network error'))

      await store.fetchEvalTasks()

      expect(store.loading).toBe(false)
      expect(store.error).toBe('Network error')
    })
  })

  describe('fetchEvalTask', () => {
    it('should fetch a single eval task', async () => {
      const { evalApi } = await import('@/api/eval')
      const mockTask = { id: '1', set_id: 'set-1', status: 'COMPLETED', summary: null }
      vi.mocked(evalApi.getEvalTask).mockResolvedValue(mockTask as any)

      await store.fetchEvalTask('1')

      expect(store.currentTask).toEqual(mockTask)
      expect(store.loading).toBe(false)
    })
  })

  describe('createEvalTask', () => {
    it('should create a new eval task', async () => {
      const { evalApi } = await import('@/api/eval')
      const newTask = {
        set_id: 'set-1',
        llm_config: {
          base_url: 'https://api.openai.com/v1',
          api_key: 'test-key',
          model_code: 'gpt-4',
          request_template: { model: 'gpt-4' }
        },
        evaluator_types: ['exact_match']
      }
      const createdTask = { id: '1', ...newTask, status: 'PENDING', summary: null }
      vi.mocked(evalApi.createEvalTask).mockResolvedValue(createdTask as any)

      const result = await store.createEvalTask(newTask as any)

      expect(store.evalTasks[0]).toEqual(createdTask)
      expect(result).toEqual(createdTask)
      expect(store.loading).toBe(false)
    })

    it('should handle create error', async () => {
      const { evalApi } = await import('@/api/eval')
      vi.mocked(evalApi.createEvalTask).mockRejectedValue(new Error('Creation failed'))

      await expect(store.createEvalTask({} as any)).rejects.toThrow()
      expect(store.error).toBe('Creation failed')
    })
  })

  describe('deleteEvalTask', () => {
    it('should delete an eval task', async () => {
      const { evalApi } = await import('@/api/eval')
      store.evalTasks = [
        { id: '1', set_id: 'set-1', status: 'PENDING' } as any,
        { id: '2', set_id: 'set-2', status: 'PENDING' } as any
      ]
      store.currentTask = { id: '1', set_id: 'set-1', status: 'PENDING', summary: null } as any
      store.evalResults = [{ id: 'result-1' } as any]

      vi.mocked(evalApi.deleteEvalTask).mockResolvedValue(undefined)

      await store.deleteEvalTask('1')

      expect(store.evalTasks.length).toBe(1)
      expect(store.evalTasks[0].id).toBe('2')
      expect(store.currentTask).toBeNull()
      expect(store.evalResults).toEqual([])
    })
  })

  describe('fetchEvalResults', () => {
    it('should fetch eval results for a task', async () => {
      const { evalApi } = await import('@/api/eval')
      const mockResults = [
        { id: '1', task_id: 'task-1', case_id: 'case-1', is_passed: true },
        { id: '2', task_id: 'task-1', case_id: 'case-2', is_passed: false }
      ]
      vi.mocked(evalApi.getEvalResults).mockResolvedValue(mockResults as any)

      await store.fetchEvalResults('task-1')

      expect(store.evalResults).toEqual(mockResults)
    })
  })

  describe('startEvaluation', () => {
    beforeEach(() => {
      // Mock EventSource globally
      global.EventSource = vi.fn().mockImplementation(() => ({
        onmessage: null,
        onerror: null,
        close: vi.fn()
      })) as any
    })

    it('should start evaluation with SSE', async () => {
      const { evalApi } = await import('@/api/eval')
      const mockEventSource = {
        onmessage: null,
        onerror: null,
        close: vi.fn()
      }
      vi.mocked(evalApi.streamEvaluation).mockReturnValue(mockEventSource as any)

      store.startEvaluation('task-1')

      expect(store.isRunning).toBe(true)
      expect(store.progress).toEqual({ current: 0, total: 0 })
      expect(evalApi.streamEvaluation).toHaveBeenCalledWith(
        'task-1',
        expect.any(Function),
        expect.any(Function)
      )
    })

    it('should handle SSE result event', async () => {
      const { evalApi } = await import('@/api/eval')
      let messageCallback: any
      const mockEventSource = {
        onmessage: null,
        onerror: null,
        close: vi.fn()
      }

      vi.mocked(evalApi.streamEvaluation).mockImplementation((_id: string, onMessage: any) => {
        messageCallback = onMessage
        return mockEventSource
      })

      store.startEvaluation('task-1')

      // Simulate result event
      messageCallback({ data: JSON.stringify({
        type: 'result',
        case_id: 'case-1',
        task_id: 'task-1',
        index: 1,
        total: 10,
        is_passed: true,
        actual_output: 'test output'
      }) })

      expect(store.progress.current).toBe(1)
      expect(store.progress.total).toBe(10)
      expect(store.evalResults.length).toBe(1)
    })

    it('should handle SSE complete event', async () => {
      const { evalApi } = await import('@/api/eval')
      let messageCallback: any
      const mockEventSource = { onmessage: null, onerror: null, close: vi.fn() }

      vi.mocked(evalApi.streamEvaluation).mockImplementation((_id: string, onMessage: any) => {
        messageCallback = onMessage
        return mockEventSource
      })

      store.startEvaluation('task-1')
      store.progress = { current: 5, total: 10 }

      // Simulate complete event
      messageCallback({ data: JSON.stringify({
        type: 'complete',
        summary: { total: 10, passed: 8, failed: 2 }
      }) })

      expect(store.isRunning).toBe(false)
      expect(store.progress.current).toBe(10)
    })

    it('should handle SSE error event', async () => {
      const { evalApi } = await import('@/api/eval')
      let messageCallback: any
      const mockEventSource = { onmessage: null, onerror: null, close: vi.fn() }

      vi.mocked(evalApi.streamEvaluation).mockImplementation((_id: string, onMessage: any) => {
        messageCallback = onMessage
        return mockEventSource
      })

      store.startEvaluation('task-1')

      // Simulate error event
      messageCallback({ data: JSON.stringify({
        type: 'error',
        message: 'Evaluation failed'
      }) })

      expect(store.isRunning).toBe(false)
      expect(store.error).toBe('Evaluation failed')
    })
  })
})
