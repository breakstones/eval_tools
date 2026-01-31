import { describe, it, expect, vi, beforeEach } from 'vitest'
import { evalApi } from '@/api/eval'
import api from '@/api/index'

// Mock the API client
vi.mock('@/api/index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))

const mockApi = vi.mocked(api)

describe('Eval API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getEvalTasks should fetch all eval tasks', async () => {
    const mockData = [
      { id: '1', set_id: 'set-1', status: 'COMPLETED' },
      { id: '2', set_id: 'set-2', status: 'PENDING' }
    ]
    vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

    const result = await evalApi.getEvalTasks()

    expect(mockApi.get).toHaveBeenCalledWith('/eval/tasks', {
      params: { set_id: undefined }
    })
    expect(result).toEqual(mockData)
  })

  it('getEvalTasks should fetch tasks filtered by set_id', async () => {
    const mockData = [
      { id: '1', set_id: 'set-1', status: 'COMPLETED' }
    ]
    vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

    const result = await evalApi.getEvalTasks('set-1')

    expect(mockApi.get).toHaveBeenCalledWith('/eval/tasks', {
      params: { set_id: 'set-1' }
    })
    expect(result).toEqual(mockData)
  })

  it('getEvalTask should fetch a single eval task', async () => {
    const mockData = { id: '1', set_id: 'set-1', status: 'COMPLETED' }
    vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

    const result = await evalApi.getEvalTask('1')

    expect(mockApi.get).toHaveBeenCalledWith('/eval/tasks/1')
    expect(result).toEqual(mockData)
  })

  it('createEvalTask should create a new eval task', async () => {
    const newData = {
      set_id: 'set-1',
      llm_config: {
        base_url: 'https://api.openai.com/v1',
        api_key: 'test-key',
        model_code: 'gpt-4',
        request_template: { model: 'gpt-4' }
      },
      evaluator_types: ['exact_match']
    }
    const mockResult = { id: '1', ...newData, status: 'PENDING' }
    vi.mocked(mockApi.post).mockResolvedValue({ data: mockResult } as any)

    const result = await evalApi.createEvalTask(newData as any)

    expect(mockApi.post).toHaveBeenCalledWith('/eval/tasks', newData)
    expect(result).toEqual(mockResult)
  })

  it('deleteEvalTask should delete an eval task', async () => {
    vi.mocked(mockApi.delete).mockResolvedValue({} as any)

    await evalApi.deleteEvalTask('1')

    expect(mockApi.delete).toHaveBeenCalledWith('/eval/tasks/1')
  })

  it('getEvalResults should fetch eval results for a task', async () => {
    const mockData = [
      { id: '1', task_id: 'task-1', case_id: 'case-1', is_passed: true },
      { id: '2', task_id: 'task-1', case_id: 'case-2', is_passed: false }
    ]
    vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

    const result = await evalApi.getEvalResults('task-1')

    expect(mockApi.get).toHaveBeenCalledWith('/eval/tasks/task-1/results')
    expect(result).toEqual(mockData)
  })

  it('getEvalResult should fetch a single eval result', async () => {
    const mockData = { id: '1', task_id: 'task-1', case_id: 'case-1', is_passed: true }
    vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

    const result = await evalApi.getEvalResult('1')

    expect(mockApi.get).toHaveBeenCalledWith('/eval/results/1')
    expect(result).toEqual(mockData)
  })

  it('streamEvaluation should create an EventSource for SSE', () => {
    // Mock EventSource
    const mockEventSource = vi.fn()
    global.EventSource = mockEventSource as any

    const onMessage = vi.fn()
    const onError = vi.fn()

    evalApi.streamEvaluation('task-1', onMessage, onError)

    expect(mockEventSource).toHaveBeenCalledWith('/api/eval/stream/task-1')
  })

  it('streamEvaluation should handle missing onError', () => {
    const mockEventSource = vi.fn()
    global.EventSource = mockEventSource as any

    const onMessage = vi.fn()

    evalApi.streamEvaluation('task-1', onMessage)

    expect(mockEventSource).toHaveBeenCalledWith('/api/eval/stream/task-1')
  })
})
