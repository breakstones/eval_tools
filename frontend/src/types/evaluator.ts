/** Evaluator types */

export type EvaluatorType = 'llm_judge' | 'code'

export interface Evaluator {
  id: string
  name: string
  description: string | null
  type: EvaluatorType
  config: Record<string, any>
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface EvaluatorCreate {
  name: string
  description?: string
  type: EvaluatorType
  config: Record<string, any>
}

export interface EvaluatorUpdate {
  name?: string
  description?: string
  config?: Record<string, any>
}

export interface TaskEvaluatorInfo {
  id: string
  name: string
  description: string | null
  type: EvaluatorType
  config: Record<string, any>
  is_system: boolean
  order_index: number
}

export interface EvaluatorTestRequest {
  expected: string
  actual: string
}

export interface EvaluatorTestResponse {
  result: 'passed' | 'failed'
  reason?: string
  error?: string
}
