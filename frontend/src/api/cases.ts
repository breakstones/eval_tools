import api from './index'
import type {
  CaseSet,
  CaseSetCreate,
  CaseSetUpdate,
  TestCase,
  TestCaseCreate,
  TestCaseUpdate,
  ExcelImportResponse,
} from '@/types/cases'

export const casesApi = {
  // Case Set APIs
  getCaseSets: () =>
    api.get<CaseSet[]>('/cases/sets').then((res) => res.data),

  getCaseSet: (id: string) =>
    api.get<CaseSet>(`/cases/sets/${id}`).then((res) => res.data),

  createCaseSet: (data: CaseSetCreate) =>
    api.post<CaseSet>('/cases/sets', data).then((res) => res.data),

  updateCaseSet: (id: string, data: CaseSetUpdate) =>
    api.put<CaseSet>(`/cases/sets/${id}`, data).then((res) => res.data),

  deleteCaseSet: (id: string) =>
    api.delete(`/cases/sets/${id}`),

  exportCaseSet: (id: string) =>
    api.get(`/cases/sets/${id}/export`, {
      responseType: 'blob',
    }).then((res) => res.data),

  importExcel: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ExcelImportResponse>('/cases/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then((res) => res.data)
  },

  // Test Case APIs
  getTestCases: (setId: string) =>
    api.get<TestCase[]>(`/cases/sets/${setId}/cases`).then((res) => res.data),

  getTestCase: (id: string) =>
    api.get<TestCase>(`/cases/cases/${id}`).then((res) => res.data),

  createTestCase: (data: TestCaseCreate) =>
    api.post<TestCase>('/cases/cases', data).then((res) => res.data),

  updateTestCase: (id: string, data: TestCaseUpdate) =>
    api.put<TestCase>(`/cases/cases/${id}`, data).then((res) => res.data),

  deleteTestCase: (id: string) =>
    api.delete(`/cases/cases/${id}`),

  deleteTestCases: (setId: string) =>
    api.delete(`/cases/sets/${setId}/cases`),
}
