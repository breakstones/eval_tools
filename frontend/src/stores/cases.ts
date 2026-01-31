import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { casesApi } from '@/api/cases'
import type { CaseSet, TestCase, CaseSetCreate, TestCaseCreate } from '@/types/cases'

export const useCasesStore = defineStore('cases', () => {
  // State
  const caseSets = ref<CaseSet[]>([])
  const currentCaseSet = ref<CaseSet | null>(null)
  const testCases = ref<TestCase[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const hasCaseSets = computed(() => caseSets.value.length > 0)

  // Actions
  async function fetchCaseSets() {
    loading.value = true
    error.value = null
    try {
      caseSets.value = await casesApi.getCaseSets()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载用例集失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchCaseSet(id: string) {
    loading.value = true
    error.value = null
    try {
      currentCaseSet.value = await casesApi.getCaseSet(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载用例集失败'
    } finally {
      loading.value = false
    }
  }

  async function createCaseSet(data: CaseSetCreate) {
    loading.value = true
    error.value = null
    try {
      const newSet = await casesApi.createCaseSet(data)
      caseSets.value.unshift(newSet)
      return newSet
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建用例集失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateCaseSet(id: string, data: Partial<CaseSetCreate>) {
    loading.value = true
    error.value = null
    try {
      const updated = await casesApi.updateCaseSet(id, data)
      const index = caseSets.value.findIndex((cs) => cs.id === id)
      if (index !== -1) {
        caseSets.value[index] = updated
      }
      if (currentCaseSet.value?.id === id) {
        currentCaseSet.value = updated
      }
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新用例集失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteCaseSet(id: string) {
    loading.value = true
    error.value = null
    try {
      await casesApi.deleteCaseSet(id)
      caseSets.value = caseSets.value.filter((cs) => cs.id !== id)
      if (currentCaseSet.value?.id === id) {
        currentCaseSet.value = null
        testCases.value = []
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除用例集失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTestCases(setId: string) {
    loading.value = true
    error.value = null
    try {
      testCases.value = await casesApi.getTestCases(setId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载测试用例失败'
    } finally {
      loading.value = false
    }
  }

  async function createTestCase(data: TestCaseCreate) {
    loading.value = true
    error.value = null
    try {
      const newCase = await casesApi.createTestCase(data)
      testCases.value.push(newCase)
      return newCase
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建测试用例失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateTestCase(id: string, data: Partial<TestCaseCreate>) {
    loading.value = true
    error.value = null
    try {
      const updated = await casesApi.updateTestCase(id, data)
      const index = testCases.value.findIndex((tc) => tc.id === id)
      if (index !== -1) {
        testCases.value[index] = updated
      }
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新测试用例失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTestCase(id: string) {
    loading.value = true
    error.value = null
    try {
      await casesApi.deleteTestCase(id)
      testCases.value = testCases.value.filter((tc) => tc.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除测试用例失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function importExcel(file: File) {
    loading.value = true
    error.value = null
    try {
      const result = await casesApi.importExcel(file)
      await fetchCaseSets()
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : '导入Excel失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function exportExcel(id: string) {
    try {
      const blob = await casesApi.exportCaseSet(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `caseset_${id}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '导出Excel失败'
      throw e
    }
  }

  return {
    // State
    caseSets,
    currentCaseSet,
    testCases,
    loading,
    error,
    // Computed
    hasCaseSets,
    // Actions
    fetchCaseSets,
    fetchCaseSet,
    createCaseSet,
    updateCaseSet,
    deleteCaseSet,
    fetchTestCases,
    createTestCase,
    updateTestCase,
    deleteTestCase,
    importExcel,
    exportExcel,
  }
})
