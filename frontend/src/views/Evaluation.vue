<template>
  <div class="evaluation">
    <!-- Top Section: Task Selector -->
    <el-card class="task-selector-section">
      <div class="selector-row">
        <div class="task-selector">
          <span class="label">评测任务：</span>
          <el-select
            v-model="selectedTaskId"
            placeholder="请选择评测任务"
            @change="handleTaskChange"
            style="width: 300px"
          >
            <el-option
              v-for="task in evalStore.evalTasks"
              :key="task.id"
              :label="getTaskLabel(task)"
              :value="task.id"
            >
              <span>{{ getTaskLabel(task) }}</span>
            </el-option>
          </el-select>
        </div>
        <div class="action-buttons">
          <el-button type="primary" @click="showCreateTaskDialog">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
          <el-button
            type="success"
            @click="handleRerunTask"
            :loading="evalStore.isRunning"
            :disabled="!selectedTaskId || !currentTask"
          >
            重新运行
          </el-button>
          <el-button
            type="danger"
            @click="handleDeleteTask"
            :disabled="!selectedTaskId"
          >
            删除任务
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Main Content: Task Info & Results -->
    <div v-if="selectedTaskId && currentTask && currentCaseSet" class="main-content">
      <el-row :gutter="20">
        <!-- Left: Task Information (Editable) -->
        <el-col :span="8">
          <el-card class="task-info-card">
            <template #header>
              <div class="card-header">
                <span>任务配置</span>
                <el-button type="primary" size="small" @click="saveConfig" :loading="savingConfig">
                  保存配置
                </el-button>
              </div>
            </template>

            <!-- Model Selection -->
            <el-form :model="editForm" label-width="80px" size="small">
              <el-form-item label="任务名称">
                <el-input v-model="editForm.task_name" placeholder="请输入任务名称" style="width: 100%" />
              </el-form-item>
              <el-form-item label="用例集">
                <div class="readonly-field">{{ currentCaseSet?.name || '-' }}</div>
              </el-form-item>
              <el-form-item label="模型">
                <el-select v-model="editForm.model_id" placeholder="选择模型" style="width: 100%" @change="handleModelChange">
                  <el-option-group
                    v-for="provider in groupedModels"
                    :key="provider.id"
                    :label="provider.name"
                  >
                    <el-option
                      v-for="model in provider.models"
                      :key="model.id"
                      :label="model.display_name || model.model_code"
                      :value="model.id"
                    >
                      <span>{{ model.display_name || model.model_code }}</span>
                      <span style="color: #8492a6; font-size: 12px; margin-left: 8px">
                        {{ model.model_code }}
                      </span>
                    </el-option>
                  </el-option-group>
                </el-select>
              </el-form-item>
              <el-form-item label="并发数量">
                <el-input-number
                  v-model="editForm.concurrency"
                  :min="1"
                  :max="20"
                  :step="1"
                  style="width: 100%"
                />
                <div style="color: #909399; font-size: 12px; margin-top: 4px">
                  控制并行执行的用例数量，提高评测速度
                </div>
              </el-form-item>

              <el-form-item label="评估器">
                <div class="evaluator-selector">
                  <div v-if="taskEvaluators.length === 0" class="empty-tips">
                    使用默认评估器（精确匹配）
                  </div>
                  <div v-else class="evaluator-tags">
                    <el-tag
                      v-for="(evaluator, index) in taskEvaluators"
                      :key="evaluator.id"
                      closable
                      @close="removeEvaluator(index)"
                      style="margin-right: 8px; margin-bottom: 8px"
                    >
                      {{ evaluator.name }}
                    </el-tag>
                  </div>
                  <el-button
                    size="small"
                    @click="showEvaluatorSelector"
                    :icon="Plus"
                  >
                    配置评估器
                  </el-button>
                </div>
              </el-form-item>
            </el-form>

            <el-divider>系统提示词</el-divider>
            <el-input
              v-model="editForm.system_prompt"
              type="textarea"
              :rows="3"
              placeholder="请输入系统提示词（留空则使用用例集的默认提示词）"
            />

            <el-divider>请求模板</el-divider>
            <div class="template-editor">
              <el-input
                v-model="editForm.templateJson"
                type="textarea"
                :rows="15"
                placeholder='{"model": "${model_name}", "messages": [...]'
                @input="validateTemplateJson"
              />
              <div v-if="templateError" class="error-tip">{{ templateError }}</div>
              <div class="template-help">
                <div>可用变量：</div>
                <div class="var-list">
                  <code>${model_name}</code> - 模型名称<br>
                  <code>${task_config.base_url}</code> - API地址<br>
                  <code>${task_config.api_key}</code> - API Key<br>
                  <code>${task_config.model_code}</code> - 模型代码<br>
                  <code>${system_prompt}</code> - 系统提示词（来自上方编辑框）<br>
                  <code>${case.user_input}</code> - 用例输入<br>
                  <code>${case.case_uid}</code> - 用例ID<br>
                  <code>${case.description}</code> - 用例描述
                </div>
              </div>
            </div>

            <el-button type="primary" style="width: 100%; margin-top: 15px" @click="showTestDialog">
              测试请求模板
            </el-button>
          </el-card>
        </el-col>

        <!-- Right: Runs & Results -->
        <el-col :span="16">
          <el-card class="results-area">
            <template #header>
              <span>运行历史与结果</span>
            </template>
            <div class="results-area-content">

            <!-- Progress when running -->
            <div v-if="evalStore.isRunning" class="progress-section">
              <el-progress
                :percentage="progressPercentage"
                :status="progressStatus"
              >
                <template #default="{ percentage }">
                  <span>{{ evalStore.progress.current }} / {{ evalStore.progress.total }}</span>
                </template>
              </el-progress>
            </div>

            <!-- Runs List -->
            <div class="runs-section">
              <div class="section-title">运行记录</div>
              <el-empty v-if="!evalStore.evalRuns.length" description="暂无运行记录" />
              <div v-else class="runs-list" @wheel.prevent="handleRunsWheel">
                <div
                  v-for="run in evalStore.evalRuns"
                  :key="run.id"
                  class="run-item"
                  :class="{ active: selectedRunId === run.id }"
                  @click="selectRun(run)"
                >
                  <!-- 顶部行：执行次数 + 状态图标 -->
                  <div class="run-header-row">
                    <span class="run-number">#{{ run.run_number }}</span>
                    <div class="run-status-icon" :class="getStatusIconClass(run.status)">
                      <el-icon><component :is="getStatusIcon(run.status)" /></el-icon>
                    </div>
                  </div>

                  <!-- 第一行：用例统计 + 通过率 -->
                  <div class="run-stats" v-if="run.summary">
                    <div class="stats-left">
                      <span class="stat-passed">{{ run.summary.passed }}</span>
                      <span class="stat-divider">/</span>
                      <span class="stat-failed">{{ run.summary.failed }}</span>
                      <span class="stat-divider">/</span>
                      <span class="stat-total">{{ run.summary.total }}</span>
                    </div>
                    <div class="stat-rate">{{ run.summary.pass_rate.toFixed(1) }}%</div>
                  </div>

                  <!-- 第二行：耗时、tokens、开始时间 -->
                  <div class="run-metrics">
                    <span v-if="run.total_duration_ms !== null && run.total_duration_ms !== undefined" class="metric-item">
                      ⏱ {{ formatDuration(run.total_duration_ms) }}
                    </span>
                    <span v-if="run.total_skill_tokens !== null || run.total_evaluator_tokens !== null" class="metric-item">
                      🔹 {{ formatNumber((run.total_skill_tokens || 0) + (run.total_evaluator_tokens || 0)) }}
                    </span>
                    <span class="metric-item metric-time">{{ formatTimeShort(run.started_at) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Results Table -->
            <div class="results-section" v-if="selectedRunId">
              <div class="section-title">评测结果</div>
              <div v-if="evalStore.currentRun && evalStore.currentRun.status === 'COMPLETED'" class="summary-bar">
                <el-statistic title="总用例数" :value="evalStore.currentRun.summary?.total || 0" />
                <el-statistic title="通过" :value="evalStore.currentRun.summary?.passed || 0">
                  <template #suffix>
                    <span style="color: #67c23a">✓</span>
                  </template>
                </el-statistic>
                <el-statistic title="不通过" :value="evalStore.currentRun.summary?.failed || 0">
                  <template #suffix>
                    <span style="color: #f56c6c">✗</span>
                  </template>
                </el-statistic>
                <el-statistic
                  title="通过率"
                  :value="((evalStore.currentRun.summary?.pass_rate || 0)).toFixed(1) + '%'"
                />
              </div>
              <div class="table-container">
                <el-table :data="evalStore.evalResults" stripe size="small" height="100%">
                <el-table-column label="用例编号" width="120">
                  <template #default="{ row }">
                    {{ row.case_uid || row.case_id }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tooltip v-if="row.execution_error" :content="row.execution_error" placement="top">
                      <el-tag type="warning" size="small">执行失败</el-tag>
                    </el-tooltip>
                    <el-tag v-else :type="row.is_passed ? 'success' : 'danger'" size="small">
                      {{ row.is_passed ? '通过' : '不通过' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="时长" width="80" align="center">
                  <template #default="{ row }">
                    <span v-if="row.execution_duration !== null && row.execution_duration !== undefined" class="duration-text">
                      {{ formatDuration(row.execution_duration) }}
                    </span>
                    <span v-else class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="技能Tokens" width="100" align="center">
                  <template #default="{ row }">
                    <span v-if="row.skill_tokens !== null && row.skill_tokens !== undefined" class="token-text">
                      {{ formatNumber(row.skill_tokens) }}
                    </span>
                    <span v-else class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="评估器Tokens" width="110" align="center">
                  <template #default="{ row }">
                    <span v-if="row.evaluator_tokens !== null && row.evaluator_tokens !== undefined" class="token-text">
                      {{ formatNumber(row.evaluator_tokens) }}
                    </span>
                    <span v-else class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="实际输出" min-width="150" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="output-text">{{ row.actual_output }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="showResultDetail(row)">
                      详细对比
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              </div>
            </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Empty State -->
    <el-empty v-else description="请选择或创建一个评测任务" />

    <!-- Create Task Dialog -->
    <el-dialog v-model="taskDialogVisible" title="创建评测任务" width="500px" :lock-scroll="true">
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" style="width: 100%" />
        </el-form-item>
        <el-form-item label="用例集" required>
          <el-select v-model="taskForm.set_id" placeholder="请选择用例集" style="width: 100%">
            <el-option
              v-for="cs in casesStore.caseSets"
              :key="cs.id"
              :label="cs.name"
              :value="cs.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型" required>
          <el-select v-model="taskForm.model_id" placeholder="请选择模型" style="width: 100%">
            <el-option-group
              v-for="provider in groupedModels"
              :key="provider.id"
              :label="provider.name"
            >
              <el-option
                v-for="model in provider.models"
                :key="model.id"
                :label="model.display_name || model.model_code"
                :value="model.id"
              >
                <span>{{ model.display_name || model.model_code }}</span>
                <span style="color: #8492a6; font-size: 12px; margin-left: 8px">
                  {{ model.model_code }}
                </span>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTask">创建</el-button>
      </template>
    </el-dialog>

    <!-- Test Template Dialog -->
    <el-dialog v-model="testDialogVisible" title="测试请求模板" width="900px" :lock-scroll="true">
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="测试用例">
          <el-select v-model="testForm.case_id" placeholder="选择用例（可选）" style="width: 100%" clearable>
            <el-option
              v-for="tc in testCases"
              :key="tc.id"
              :label="`${tc.case_uid} - ${tc.description || tc.user_input?.substring(0, 30)}`"
              :value="tc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="或输入测试文本">
          <el-input
            v-model="testForm.test_input"
            type="textarea"
            :rows="2"
            placeholder="直接输入测试文本（如果不选择用例）"
          />
        </el-form-item>
      </el-form>

      <el-button type="primary" @click="runTemplateTest" :loading="testLoading" style="width: 100%">
        运行测试
      </el-button>

      <template v-if="testResult">
        <el-divider>渲染后的请求</el-divider>
        <div class="test-result">
          <pre>{{ JSON.stringify(testResult.rendered_request, null, 2) }}</pre>
        </div>

        <template v-if="testResult.error">
          <el-divider>错误</el-divider>
          <el-alert type="error" :title="testResult.error" :closable="false" />
        </template>

        <template v-if="testResult.actual_response">
          <el-divider>实际响应</el-divider>
          <div class="test-response">
            <pre>{{ testResult.actual_response }}</pre>
          </div>
        </template>
      </template>
    </el-dialog>

    <!-- Result Detail Dialog -->
    <DiffViewer
      :visible="diffDialogVisible"
      :expected="currentCase?.expected_output || ''"
      :actual="currentResult?.actual_output || ''"
      :is-passed="currentResult?.is_passed || false"
      :execution-error="currentResult?.execution_error"
      :evaluator-logs="currentResult?.evaluator_logs || []"
      :execution-duration="currentResult?.execution_duration"
      :skill-tokens="currentResult?.skill_tokens"
      :evaluator-tokens="currentResult?.evaluator_tokens"
      @close="diffDialogVisible = false"
    />

    <!-- Evaluator Selector Dialog -->
    <el-dialog
      v-model="evaluatorDialogVisible"
      title="配置评估器"
      width="600px"
      :lock-scroll="true"
      @open="handleEvaluatorDialogOpen"
    >
      <div class="evaluator-selector-content">
        <div class="available-evaluators">
          <div class="section-title">可用评估器</div>
          <el-checkbox-group v-model="selectedEvaluatorIds">
            <div
              v-for="evaluator in evaluatorStore.evaluators"
              :key="evaluator.id"
              class="evaluator-option"
            >
              <el-checkbox :label="evaluator.id">
                <div class="evaluator-option-content">
                  <span class="evaluator-name">{{ evaluator.name }}</span>
                  <el-tag
                    :type="evaluator.type === 'llm_judge' ? 'warning' : 'success'"
                    size="small"
                  >
                    {{ evaluator.type === 'llm_judge' ? 'LLM' : '代码' }}
                  </el-tag>
                  <span class="evaluator-desc">{{ evaluator.description || '暂无描述' }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
        <div class="selected-count">
          已选择 {{ selectedEvaluatorIds.length }} 个评估器
        </div>
      </div>
      <template #footer>
        <el-button @click="evaluatorDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEvaluators">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Clock, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { useEvalStore } from '@/stores/eval'
import { useCasesStore } from '@/stores/cases'
import { useEvaluatorStore } from '@/stores/evaluator'
import { getModels } from '@/api/models'
import DiffViewer from '@/components/DiffViewer.vue'
import type { EvalTask, EvalResult } from '@/types/eval'
import type { TestCase } from '@/types/cases'
import type { Model } from '@/api/models'
import type { TaskEvaluatorInfo } from '@/types/evaluator'

const evalStore = useEvalStore()
const casesStore = useCasesStore()
const evaluatorStore = useEvaluatorStore()

// Dialog states
const taskDialogVisible = ref(false)
const diffDialogVisible = ref(false)
const testDialogVisible = ref(false)
const evaluatorDialogVisible = ref(false)
const currentResult = ref<EvalResult | null>(null)
const currentCase = ref<TestCase | null>(null)

// Evaluator state
const taskEvaluators = ref<TaskEvaluatorInfo[]>([])
const selectedEvaluatorIds = ref<string[]>([])

// Edit state
const editForm = ref({
  task_name: '',
  model_id: '',
  concurrency: 1,
  system_prompt: '',
  templateJson: '',
})
const templateError = ref('')
const savingConfig = ref(false)

// Test state
const testForm = ref({
  case_id: '',
  test_input: '',
})
const testResult = ref<any>(null)
const testLoading = ref(false)
const testCases = ref<TestCase[]>([])

// Models for selection
const availableModels = ref<Model[]>([])

// Selection states
const selectedTaskId = ref<string | null>(null)
const selectedRunId = ref<string | null>(null)
const currentTask = ref<EvalTask | null>(null)
const currentCaseSet = ref<any>(null)

// Form data
const taskForm = ref({
  name: '',
  set_id: '',
  model_id: '',
  evaluator_types: ['exact_match'],
  request_template: null as any,
})

// eventSource is no longer used, replaced by WebSocket

// Computed
const progressPercentage = computed(() => {
  if (evalStore.progress.total === 0) return 0
  return Math.round((evalStore.progress.current / evalStore.progress.total) * 100)
})

const progressStatus = computed(() => {
  if (progressPercentage.value === 100) return 'success'
  return undefined
})

const groupedModels = computed(() => {
  const groups: Record<string, { id: string; name: string; models: Model[] }> = {}
  availableModels.value.forEach(model => {
    const key = model.provider_name
    if (!groups[key]) {
      groups[key] = {
        id: model.provider_id,
        name: model.provider_name,
        models: [],
      }
    }
    groups[key].models.push(model)
  })
  return Object.values(groups)
})

// Flag to control auto-selection of latest run
let shouldAutoSelectLatestRun = false

onMounted(async () => {
  await casesStore.fetchCaseSets()
  await evalStore.fetchEvalTasks()
  await loadModels()

  // Auto-select first task
  if (evalStore.evalTasks.length > 0) {
    await handleTaskChange(evalStore.evalTasks[0].id)
  }
})

// Watch for new runs and auto-select the latest one when rerun is triggered
watch(() => evalStore.evalRuns, async (newRuns, oldRuns) => {
  if (shouldAutoSelectLatestRun && newRuns.length > 0) {
    // Auto-select the first run (latest, sorted by run_number desc)
    const latestRun = newRuns[0]
    if (selectedRunId.value !== latestRun.id) {
      await selectRun(latestRun)
    }
    shouldAutoSelectLatestRun = false
  }
}, { deep: true })

async function loadModels() {
  try {
    availableModels.value = await getModels()
  } catch (error: any) {
    ElMessage.error(error.message || '加载模型列表失败')
  }
}

function getTaskLabel(task: EvalTask): string {
  if (task.name) {
    return task.name
  }
  const cs = casesStore.caseSets.find((c) => c.id === task.set_id)
  const modelName = task.model_info?.display_name || task.model_info?.model_code || '未知模型'
  return `${cs?.name || task.set_id} - ${modelName}`
}

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    PENDING: 'info',
    RUNNING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger',
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    PENDING: '等待中',
    RUNNING: '运行中',
    COMPLETED: '已完成',
    FAILED: '失败',
  }
  return texts[status] || status
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function formatJson(obj: any): string {
  if (!obj) return '-'
  return JSON.stringify(obj, null, 2)
}

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`
  } else {
    const minutes = Math.floor(ms / 60000)
    const seconds = ((ms % 60000) / 1000).toFixed(0)
    return `${minutes}m${seconds}s`
  }
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

function handleRunsWheel(event: WheelEvent) {
  const target = event.currentTarget as HTMLElement
  target.scrollLeft += event.deltaY
}

function formatTimeShort(dateStr: string): string {
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

function getPassRateClass(passRate: number): string {
  if (passRate >= 80) return 'rate-high'
  if (passRate >= 60) return 'rate-medium'
  return 'rate-low'
}

function getStatusIcon(status: string) {
  const icons: Record<string, any> = {
    PENDING: Clock,
    RUNNING: Clock,
    COMPLETED: CircleCheck,
    FAILED: CircleClose,
  }
  return icons[status] || Clock
}

function getStatusIconClass(status: string) {
  return `status-icon-${status.toLowerCase()}`
}

function validateTemplateJson() {
  try {
    if (editForm.value.templateJson) {
      JSON.parse(editForm.value.templateJson)
      templateError.value = ''
    }
  } catch (e) {
    templateError.value = 'JSON 格式错误: ' + (e instanceof Error ? e.message : '未知错误')
  }
}

async function handleTaskChange(taskId: string) {
  selectedTaskId.value = taskId
  await evalStore.fetchEvalTask(taskId)
  currentTask.value = evalStore.currentTask

  // Initialize edit form with current task data
  if (currentTask.value) {
    editForm.value.task_name = currentTask.value.name || ''
    editForm.value.model_id = currentTask.value.model_id
    editForm.value.concurrency = currentTask.value.concurrency || 1
    editForm.value.templateJson = formatJson(currentTask.value.request_template)

    // Get system_prompt from task (not from request_template)
    editForm.value.system_prompt = currentTask.value.system_prompt || ''

    // Fetch case set for system prompt
    await casesStore.fetchCaseSet(currentTask.value.set_id)
    currentCaseSet.value = casesStore.currentCaseSet

    // Fetch test cases for testing
    await casesStore.fetchTestCases(currentTask.value.set_id)
    testCases.value = casesStore.testCases

    // Fetch task evaluators
    await loadTaskEvaluators(taskId)
  }

  // Fetch runs and select latest
  await evalStore.fetchEvalRuns(taskId)
  if (evalStore.evalRuns.length > 0) {
    await selectRun(evalStore.evalRuns[0])
  } else {
    selectedRunId.value = null
    evalStore.evalResults = []
  }
}

async function selectRun(row: any) {
  selectedRunId.value = row.id
  await evalStore.fetchEvalRun(row.id)
  await evalStore.fetchRunResults(row.id)
}

function showCreateTaskDialog() {
  if (!casesStore.hasCaseSets) {
    ElMessage.warning('请先创建用例集')
    return
  }
  if (!availableModels.value.length) {
    ElMessage.warning('请先在模型管理中添加模型')
    return
  }
  taskForm.value.name = ''
  taskForm.value.set_id = casesStore.caseSets[0].id
  taskForm.value.model_id = availableModels.value[0].id
  taskDialogVisible.value = true
}

async function handleCreateTask() {
  if (!taskForm.value.name || taskForm.value.name.trim() === '') {
    ElMessage.error('请输入任务名称')
    return
  }
  if (!taskForm.value.set_id) {
    ElMessage.error('请选择用例集')
    return
  }
  if (!taskForm.value.model_id) {
    ElMessage.error('请选择模型')
    return
  }

  try {
    const task = await evalStore.createEvalTask(taskForm.value as any)
    taskDialogVisible.value = false
    ElMessage.success('任务创建成功')

    // Select the new task
    await handleTaskChange(task.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '创建任务失败')
  }
}

async function handleDeleteTask() {
  if (!selectedTaskId.value) return

  try {
    await ElMessageBox.confirm('确定要删除该评测任务吗？', '确认删除', {
      type: 'warning',
    })
    await evalStore.deleteEvalTask(selectedTaskId.value)
    ElMessage.success('删除成功')

    // Reset and select first available
    selectedTaskId.value = null
    currentTask.value = null
    currentCaseSet.value = null
    selectedRunId.value = null

    await evalStore.fetchEvalTasks()
    if (evalStore.evalTasks.length > 0) {
      await handleTaskChange(evalStore.evalTasks[0].id)
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e instanceof Error ? e.message : '删除失败')
    }
  }
}

// WebSocket connection for evaluation updates
let websocket: WebSocket | null = null

async function handleRerunTask() {
  if (!selectedTaskId.value) return

  try {
    await ElMessageBox.confirm('确定要重新运行该评测任务吗？', '确认重新运行', {
      type: 'warning',
    })

    // Close existing WebSocket connection if any
    if (websocket && (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING)) {
      websocket.close()
      websocket = null
    }

    ElMessage.info('正在启动重新运行...')

    // Set flag to auto-select the latest run when runs list is updated
    shouldAutoSelectLatestRun = true

    // Start evaluation - this will connect WebSocket first, then send POST request
    // When run_created event is received, it will refresh the runs list and trigger the watch
    websocket = evalStore.startEvaluation(selectedTaskId.value)

  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e instanceof Error ? e.message : '重新运行失败')
    }
  }
}

// Clean up WebSocket connection when component is unmounted
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (websocket) {
    websocket.close()
    websocket = null
  }
})

// Edit functions
function handleModelChange(modelId: string) {
  // Model changed, will be saved when user clicks save
  editForm.value.model_id = modelId
}

async function saveConfig() {
  if (templateError.value) {
    ElMessage.error('请修正JSON格式错误')
    return
  }

  if (!editForm.value.model_id) {
    ElMessage.error('请选择模型')
    return
  }

  savingConfig.value = true

  try {
    let requestTemplate: any = {}
    if (editForm.value.templateJson) {
      requestTemplate = JSON.parse(editForm.value.templateJson)
    }

    // Update: name, model_id, concurrency, request_template, and system_prompt (as separate field)
    const updateData: any = {
      model_id: editForm.value.model_id,
      concurrency: editForm.value.concurrency,
      request_template: requestTemplate,
    }
    // Only include optional fields if they have values
    if (editForm.value.task_name !== undefined && editForm.value.task_name !== null) {
      updateData.name = editForm.value.task_name
    }
    if (editForm.value.system_prompt) {
      updateData.system_prompt = editForm.value.system_prompt
    }
    console.log('[FRONTEND] Sending update data:', updateData)
    await evalStore.updateEvalTask(selectedTaskId.value, updateData)
    ElMessage.success('配置已保存')

    // Refresh task data
    await evalStore.fetchEvalTask(selectedTaskId.value)
    currentTask.value = evalStore.currentTask

    // Update edit form with refreshed data (especially system_prompt)
    if (currentTask.value) {
      editForm.value.task_name = currentTask.value.name || ''
      editForm.value.system_prompt = currentTask.value.system_prompt || ''
      editForm.value.templateJson = formatJson(currentTask.value.request_template)
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    savingConfig.value = false
  }
}

// Test functions
async function showTestDialog() {
  testDialogVisible.value = true
  testResult.value = null
}

async function runTemplateTest() {
  if (!selectedTaskId.value) return

  testLoading.value = true
  testResult.value = null

  try {
    const result = await evalStore.testTemplate(selectedTaskId.value, {
      case_id: testForm.value.case_id || undefined,
      test_input: testForm.value.test_input || undefined,
    })
    testResult.value = result
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '测试失败')
  } finally {
    testLoading.value = false
  }
}

function showResultDetail(row: EvalResult) {
  currentResult.value = row
  // Find the corresponding test case
  currentCase.value = testCases.value.find(tc => tc.id === row.case_id) || null
  diffDialogVisible.value = true
}

// Evaluator functions
async function loadTaskEvaluators(taskId: string) {
  try {
    taskEvaluators.value = await evaluatorStore.fetchTaskEvaluators(taskId)
    selectedEvaluatorIds.value = taskEvaluators.value.map(e => e.id)
  } catch (error: any) {
    console.error('Failed to load task evaluators:', error)
    taskEvaluators.value = []
    selectedEvaluatorIds.value = []
  }
}

async function handleEvaluatorDialogOpen() {
  await evaluatorStore.fetchEvaluators()
  // Pre-select current evaluators
  selectedEvaluatorIds.value = taskEvaluators.value.map(e => e.id)
}

function showEvaluatorSelector() {
  evaluatorDialogVisible.value = true
}

function removeEvaluator(index: number) {
  const evaluator = taskEvaluators.value[index]
  if (evaluator && selectedTaskId.value) {
    selectedEvaluatorIds.value = selectedEvaluatorIds.value.filter(id => id !== evaluator.id)
    saveEvaluatorsToTask()
  }
}

async function saveEvaluators() {
  if (!selectedTaskId.value) return
  await saveEvaluatorsToTask()
  evaluatorDialogVisible.value = false
}

async function saveEvaluatorsToTask() {
  if (!selectedTaskId.value) return

  try {
    await evaluatorStore.setTaskEvaluators(selectedTaskId.value, selectedEvaluatorIds.value)
    // Clear the cache and reload from server
    evaluatorStore.clearTaskEvaluatorsCache(selectedTaskId.value)
    await loadTaskEvaluators(selectedTaskId.value)
    ElMessage.success('评估器配置已保存')
  } catch (error: any) {
    ElMessage.error(error.message || '保存评估器配置失败')
  }
}
</script>

<style scoped>
.readonly-field {
  width: 100%;
  padding: 0 30px 0 11px;
  height: 32px;
  line-height: 32px;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  cursor: not-allowed;
}

.evaluation {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow: hidden;
}

.task-selector-section {
  flex-shrink: 0;
}

.selector-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-selector .label {
  font-weight: 500;
  color: #606266;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.main-content .el-row {
  height: 100%;
}

.main-content .el-col {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.main-content .el-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.main-content .el-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  /* 隐藏滚动条但保持滚动功能 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.main-content .el-card :deep(.el-card__body)::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

/* Task Info Card */
.system-prompt {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  min-height: 60px;
  max-height: 150px;
  overflow-y: auto;
}

.request-template {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
}

.request-template pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.template-editor {
  position: relative;
}

.template-editor :deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.error-tip {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}

.template-help {
  margin-top: 10px;
  padding: 10px;
  background: #ecf5ff;
  border-radius: 4px;
  font-size: 12px;
}

.template-help code {
  background: #fff;
  padding: 2px 6px;
  border-radius: 3px;
  color: #409eff;
  font-family: 'Courier New', monospace;
}

/* Test Dialog */
.test-result,
.test-response {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
}

.test-result pre,
.test-response pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Results Area */
.section-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: #303133;
}

.runs-section {
  flex-shrink: 0;
  margin-bottom: 20px;
  height: 160px;
}

.runs-list {
  display: flex;
  flex-direction: row;
  gap: 12px;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px 0;
}

.runs-list::-webkit-scrollbar {
  height: 6px;
}

.runs-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.runs-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.runs-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.run-item {
  flex-shrink: 0;
  width: 240px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.run-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.run-item.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.run-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: -6px;
}

.run-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.run-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #909399;
  align-items: center;
  justify-content: space-between;
}

.run-number {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.run-status-icon {
  font-size: 16px;
}

.run-status-icon.status-icon-pending {
  color: #909399;
}

.run-status-icon.status-icon-running {
  color: #e6a23c;
}

.run-status-icon.status-icon-completed {
  color: #67c23a;
}

.run-status-icon.status-icon-failed {
  color: #f56c6c;
}

.stats-left {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stats-left .stat-number {
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.stats-left .stat-passed {
  font-size: 16px;
  font-weight: 600;
  color: #67c23a;
  line-height: 1;
}

.stats-left .stat-divider {
  font-size: 16px;
  color: #dcdfe6;
  font-weight: 600;
}

.stats-left .stat-failed {
  font-size: 16px;
  font-weight: 600;
  color: #f56c6c;
  line-height: 1;
}

.stats-left .stat-total {
  font-size: 16px;
  color: #909399;
  font-weight: 600;
}

.stat-rate {
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.run-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #909399;
  align-items: center;
  justify-content: space-between;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 2px;
}

.metric-item.metric-time {
  margin-left: auto;
  color: #909399;
}

.results-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #dcdfe6;
  padding-top: 20px;
  overflow: hidden;
}

.summary-bar {
  flex-shrink: 0;
  display: flex;
  gap: 30px;
  margin-bottom: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-container :deep(.el-table__body-wrapper) {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.table-container :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  display: none;
}

.results-area-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.progress-section {
  margin-bottom: 20px;
}

.evaluator-logs {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.log-reason {
  color: #606266;
}

/* Evaluator Selector Styles */
.evaluator-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-tips {
  color: #909399;
  font-size: 13px;
  padding: 8px 0;
}

.evaluator-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.evaluator-selector-content {
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.available-evaluators {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.evaluator-option {
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.evaluator-option:hover {
  background-color: #f5f7fa;
}

.evaluator-option-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.evaluator-option .evaluator-name {
  font-weight: 500;
  color: #303133;
}

.evaluator-option .evaluator-desc {
  color: #909399;
  font-size: 12px;
  margin-left: auto;
}

.selected-count {
  padding: 12px;
  text-align: center;
  color: #606266;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.duration-text {
  color: #409eff;
  font-size: 12px;
  font-weight: 500;
}

.token-text {
  color: #67c23a;
  font-size: 12px;
  font-weight: 500;
}

.text-muted {
  color: #c0c4cc;
  font-size: 12px;
}
</style>
