/** Type definitions for case management */

export interface CaseSet {
  id: string
  name: string
  created_at: string
  case_count: number
}

export interface CaseSetCreate {
  name: string
}

export interface CaseSetUpdate {
  name?: string
}

export interface TestCase {
  id: string
  set_id: string
  case_uid: string | null
  description: string | null
  user_input: string
  expected_output: string | null
  created_at: string
}

export interface TestCaseCreate {
  set_id: string
  case_uid?: string
  description?: string
  user_input: string
  expected_output?: string
}

export interface TestCaseUpdate {
  case_uid?: string
  description?: string
  user_input?: string
  expected_output?: string
}

export interface ExcelImportResponse {
  case_set: CaseSet
  cases_created: number
}
