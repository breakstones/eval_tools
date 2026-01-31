import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCasesStore } from '@/stores/cases'

// Mock the cases API
vi.mock('@/api/cases', () => ({
  casesApi: {
    getCaseSets: vi.fn(),
    getCaseSet: vi.fn(),
    createCaseSet: vi.fn(),
    updateCaseSet: vi.fn(),
    deleteCaseSet: vi.fn(),
    getTestCases: vi.fn(),
    getTestCase: vi.fn(),
    createTestCase: vi.fn(),
    updateTestCase: vi.fn(),
    deleteTestCase: vi.fn(),
    importExcel: vi.fn(),
    exportCaseSet: vi.fn()
  }
}))

describe('Cases Store', () => {
  let store: ReturnType<typeof useCasesStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useCasesStore()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      expect(store.caseSets).toEqual([])
      expect(store.currentCaseSet).toBeNull()
      expect(store.testCases).toEqual([])
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('hasCaseSets should return false when empty', () => {
      expect(store.hasCaseSets).toBe(false)
    })

    it('hasCaseSets should return true when has items', () => {
      store.caseSets = [{ id: '1', name: 'Set 1', created_at: '2024-01-01', case_count: 0 } as any]
      expect(store.hasCaseSets).toBe(true)
    })
  })

  describe('fetchCaseSets', () => {
    it('should fetch case sets successfully', async () => {
      const { casesApi } = await import('@/api/cases')
      const mockSets = [
        { id: '1', name: 'Set 1', created_at: '2024-01-01', case_count: 0 },
        { id: '2', name: 'Set 2', created_at: '2024-01-02', case_count: 0 }
      ]
      vi.mocked(casesApi.getCaseSets).mockResolvedValue(mockSets as any)

      await store.fetchCaseSets()

      expect(store.loading).toBe(false)
      expect(store.caseSets).toEqual(mockSets)
      expect(store.error).toBeNull()
    })

    it('should handle fetch error', async () => {
      const { casesApi } = await import('@/api/cases')
      vi.mocked(casesApi.getCaseSets).mockRejectedValue(new Error('Network error'))

      await store.fetchCaseSets()

      expect(store.loading).toBe(false)
      expect(store.error).toBe('Network error')
    })
  })

  describe('fetchCaseSet', () => {
    it('should fetch a single case set', async () => {
      const { casesApi } = await import('@/api/cases')
      const mockSet = { id: '1', name: 'Set 1', created_at: '2024-01-01', case_count: 0 }
      vi.mocked(casesApi.getCaseSet).mockResolvedValue(mockSet as any)

      await store.fetchCaseSet('1')

      expect(store.currentCaseSet).toEqual(mockSet)
      expect(store.loading).toBe(false)
    })
  })

  describe('createCaseSet', () => {
    it('should create a new case set', async () => {
      const { casesApi } = await import('@/api/cases')
      const newSet = { name: 'New Set' }
      const createdSet = { id: '1', ...newSet, created_at: '2024-01-01', case_count: 0 }
      vi.mocked(casesApi.createCaseSet).mockResolvedValue(createdSet as any)

      const result = await store.createCaseSet(newSet as any)

      expect(store.caseSets[0]).toEqual(createdSet)
      expect(result).toEqual(createdSet)
      expect(store.loading).toBe(false)
    })
  })

  describe('updateCaseSet', () => {
    it('should update a case set', async () => {
      const { casesApi } = await import('@/api/cases')
      store.caseSets = [{ id: '1', name: 'Old Name', created_at: '2024-01-01', case_count: 0, system_prompt: null } as any]
      store.currentCaseSet = { id: '1', name: 'Old Name', created_at: '2024-01-01', case_count: 0, system_prompt: null } as any

      const updatedSet = { id: '1', name: 'New Name', created_at: '2024-01-01', case_count: 0 }
      vi.mocked(casesApi.updateCaseSet).mockResolvedValue(updatedSet as any)

      const result = await store.updateCaseSet('1', { name: 'New Name' })

      expect(store.caseSets[0].name).toBe('New Name')
      expect(store.currentCaseSet?.name).toBe('New Name')
      expect(result).toEqual(updatedSet)
    })
  })

  describe('deleteCaseSet', () => {
    it('should delete a case set', async () => {
      const { casesApi } = await import('@/api/cases')
      store.caseSets = [
        { id: '1', name: 'Set 1', created_at: '2024-01-01', case_count: 0 } as any,
        { id: '2', name: 'Set 2', created_at: '2024-01-02', case_count: 0 } as any
      ]
      store.currentCaseSet = { id: '1', name: 'Set 1', created_at: '2024-01-01', case_count: 0, system_prompt: null } as any
      store.testCases = [{ id: 'case-1' } as any]

      vi.mocked(casesApi.deleteCaseSet).mockResolvedValue(undefined)

      await store.deleteCaseSet('1')

      expect(store.caseSets.length).toBe(1)
      expect(store.caseSets[0].id).toBe('2')
      expect(store.currentCaseSet).toBeNull()
      expect(store.testCases).toEqual([])
    })
  })

  describe('fetchTestCases', () => {
    it('should fetch test cases for a set', async () => {
      const { casesApi } = await import('@/api/cases')
      const mockCases = [
        { id: '1', user_input: 'Input 1', expected_output: 'Output 1' },
        { id: '2', user_input: 'Input 2', expected_output: 'Output 2' }
      ]
      vi.mocked(casesApi.getTestCases).mockResolvedValue(mockCases as any)

      await store.fetchTestCases('set-1')

      expect(store.testCases).toEqual(mockCases)
    })
  })

  describe('createTestCase', () => {
    it('should create a new test case', async () => {
      const { casesApi } = await import('@/api/cases')
      const newCase = { set_id: 'set-1', user_input: 'New input', expected_output: 'New output' }
      const createdCase = { id: '1', ...newCase, created_at: '2024-01-01' }
      vi.mocked(casesApi.createTestCase).mockResolvedValue(createdCase as any)

      const result = await store.createTestCase(newCase as any)

      expect(store.testCases).toContainEqual(createdCase)
      expect(result).toEqual(createdCase)
    })
  })

  describe('updateTestCase', () => {
    it('should update a test case', async () => {
      const { casesApi } = await import('@/api/cases')
      store.testCases = [{ id: '1', user_input: 'Old input', expected_output: 'Output' } as any]

      const updatedCase = { id: '1', user_input: 'New input', expected_output: 'Output' }
      vi.mocked(casesApi.updateTestCase).mockResolvedValue(updatedCase as any)

      await store.updateTestCase('1', { user_input: 'New input' })

      expect(store.testCases[0].user_input).toBe('New input')
    })
  })

  describe('deleteTestCase', () => {
    it('should delete a test case', async () => {
      const { casesApi } = await import('@/api/cases')
      store.testCases = [
        { id: '1', user_input: 'Input 1' } as any,
        { id: '2', user_input: 'Input 2' } as any
      ]

      vi.mocked(casesApi.deleteTestCase).mockResolvedValue(undefined)

      await store.deleteTestCase('1')

      expect(store.testCases.length).toBe(1)
      expect(store.testCases[0].id).toBe('2')
    })
  })
})
