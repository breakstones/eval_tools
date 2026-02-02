/** Type definitions for evaluation */

export interface ModelInfo {
  model_code: string
  display_name: string
  provider: {
    id: string
    name: string
  }
}

export interface RequestTemplate {
  model: string
  messages: Array<{ role: string; content: string }>
  [key: string]: any
}

export interface EvalTaskCreate {
  name?: string
  set_id: string
  model_id: string
  concurrency?: number  // 并发数量，默认1
  evaluator_types?: string[]
  request_template?: RequestTemplate
  system_prompt?: string
}

export interface EvalTaskUpdate {
  name?: string
  model_id?: string
  concurrency?: number  // 并发数量
  request_template?: RequestTemplate
  system_prompt?: string
}

export interface TemplateTestRequest {
  case_id?: string
  test_input?: string
}

export interface TemplateTestResponse {
  rendered_request: Record<string, any>
  actual_response?: string
  error?: string
}

export interface EvalTask {
  id: string
  name?: string | null
  set_id: string
  model_id: string
  concurrency: number  // 并发数量
  request_template?: RequestTemplate
  system_prompt?: string
  model_info?: ModelInfo
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  summary: EvalSummary | null
  created_at: string
  updated_at: string
}

export interface EvalSummary {
  total: number
  passed: number
  failed: number
  pass_rate: number
}

export interface EvalResult {
  id: string
  run_id: string
  task_id: string
  case_id: string
  case_uid?: string | null  // 用例编号，便于展示
  actual_output: string | null
  is_passed: boolean
  execution_error?: string | null  // 执行错误信息
  evaluator_logs: EvaluatorLog[]
  execution_duration?: number | null  // 执行时长（毫秒）
  skill_tokens?: number | null  // 技能LLM调用的token消耗
  evaluator_tokens?: number | null  // LLM评估器的token消耗
  created_at: string
}

export interface EvalRun {
  id: string
  task_id: string
  run_number: number
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  summary: EvalSummary | null
  started_at: string
  completed_at: string | null
  error: string | null
  total_duration_ms?: number | null  // 总执行时长（毫秒）
  total_skill_tokens?: number | null  // 总技能LLM tokens消耗
  total_evaluator_tokens?: number | null  // 总评估器LLM tokens消耗
}

export interface EvaluatorLog {
  evaluator: string
  passed: boolean
  reason?: string
}

export interface EvalProgressEvent {
  type: 'progress' | 'result' | 'complete' | 'error'
  data: Record<string, any>
}
