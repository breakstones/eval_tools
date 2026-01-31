import { describe, it, expect, vi, beforeEach } from 'vitest'
import { casesApi } from '@/api/cases'
import api from '@/api/index'

// Mock the API client
vi.mock('@/api/index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

const mockApi = vi.mocked(api)

describe('Cases API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Case Set APIs', () => {
    it('getCaseSets should fetch all case sets', async () => {
      const mockData = [
        { id: '1', name: 'Set 1', created_at: '2024-01-01' },
        { id: '2', name: 'Set 2', created_at: '2024-01-02' }
      ]
      vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

      const result = await casesApi.getCaseSets()

      expect(mockApi.get).toHaveBeenCalledWith('/cases/sets')
      expect(result).toEqual(mockData)
    })

    it('getCaseSet should fetch a single case set', async () => {
      const mockData = { id: '1', name: 'Set 1', created_at: '2024-01-01' }
      vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

      const result = await casesApi.getCaseSet('1')

      expect(mockApi.get).toHaveBeenCalledWith('/cases/sets/1')
      expect(result).toEqual(mockData)
    })

    it('createCaseSet should create a new case set', async () => {
      const newData = { name: 'New Set', system_prompt: 'Test' }
      const mockResult = { id: '1', ...newData, created_at: '2024-01-01' }
      vi.mocked(mockApi.post).mockResolvedValue({ data: mockResult } as any)

      const result = await casesApi.createCaseSet(newData as any)

      expect(mockApi.post).toHaveBeenCalledWith('/cases/sets', newData)
      expect(result).toEqual(mockResult)
    })

    it('updateCaseSet should update a case set', async () => {
      const updateData = { name: 'Updated Set' }
      const mockResult = { id: '1', ...updateData, created_at: '2024-01-01' }
      vi.mocked(mockApi.put).mockResolvedValue({ data: mockResult } as any)

      const result = await casesApi.updateCaseSet('1', updateData)

      expect(mockApi.put).toHaveBeenCalledWith('/cases/sets/1', updateData)
      expect(result).toEqual(mockResult)
    })

    it('deleteCaseSet should delete a case set', async () => {
      vi.mocked(mockApi.delete).mockResolvedValue({} as any)

      await casesApi.deleteCaseSet('1')

      expect(mockApi.delete).toHaveBeenCalledWith('/cases/sets/1')
    })

    it('exportCaseSet should export a case set as blob', async () => {
      const mockBlob = new Blob(['test data'])
      vi.mocked(mockApi.get).mockResolvedValue({ data: mockBlob } as any)

      const result = await casesApi.exportCaseSet('1')

      expect(mockApi.get).toHaveBeenCalledWith('/cases/sets/1/export', {
        responseType: 'blob'
      })
      expect(result).toEqual(mockBlob)
    })

    it('importExcel should import an Excel file', async () => {
      const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const mockResult = { case_set_id: '1', imported_count: 5 }
      vi.mocked(mockApi.post).mockResolvedValue({ data: mockResult } as any)

      const result = await casesApi.importExcel(file)

      expect(mockApi.post).toHaveBeenCalledWith(
        '/cases/import',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
      expect(result).toEqual(mockResult)
    })
  })

  describe('Test Case APIs', () => {
    it('getTestCases should fetch test cases for a set', async () => {
      const mockData = [
        { id: '1', user_input: 'Input 1', expected_output: 'Output 1' },
        { id: '2', user_input: 'Input 2', expected_output: 'Output 2' }
      ]
      vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

      const result = await casesApi.getTestCases('set-1')

      expect(mockApi.get).toHaveBeenCalledWith('/cases/sets/set-1/cases')
      expect(result).toEqual(mockData)
    })

    it('getTestCase should fetch a single test case', async () => {
      const mockData = { id: '1', user_input: 'Input 1', expected_output: 'Output 1' }
      vi.mocked(mockApi.get).mockResolvedValue({ data: mockData } as any)

      const result = await casesApi.getTestCase('1')

      expect(mockApi.get).toHaveBeenCalledWith('/cases/cases/1')
      expect(result).toEqual(mockData)
    })

    it('createTestCase should create a new test case', async () => {
      const newData = { set_id: 'set-1', user_input: 'New input', expected_output: 'New output' }
      const mockResult = { id: '1', ...newData, created_at: '2024-01-01' }
      vi.mocked(mockApi.post).mockResolvedValue({ data: mockResult } as any)

      const result = await casesApi.createTestCase(newData as any)

      expect(mockApi.post).toHaveBeenCalledWith('/cases/cases', newData)
      expect(result).toEqual(mockResult)
    })

    it('updateTestCase should update a test case', async () => {
      const updateData = { user_input: 'Updated input' }
      const mockResult = { id: '1', ...updateData, created_at: '2024-01-01' }
      vi.mocked(mockApi.put).mockResolvedValue({ data: mockResult } as any)

      const result = await casesApi.updateTestCase('1', updateData)

      expect(mockApi.put).toHaveBeenCalledWith('/cases/cases/1', updateData)
      expect(result).toEqual(mockResult)
    })

    it('deleteTestCase should delete a test case', async () => {
      vi.mocked(mockApi.delete).mockResolvedValue({} as any)

      await casesApi.deleteTestCase('1')

      expect(mockApi.delete).toHaveBeenCalledWith('/cases/cases/1')
    })

    it('deleteTestCases should delete all test cases for a set', async () => {
      vi.mocked(mockApi.delete).mockResolvedValue({} as any)

      await casesApi.deleteTestCases('set-1')

      expect(mockApi.delete).toHaveBeenCalledWith('/cases/sets/set-1/cases')
    })
  })
})
