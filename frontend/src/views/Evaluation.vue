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
              <el-tag :type="getStatusType(task.status)" size="small" style="margin-left: 10px">
                {{ getStatusText(task.status) }}
              </el-tag>
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
              <div v-else class="runs-list">
                <div
                  v-for="run in evalStore.evalRuns"
                  :key="run.id"
                  class="run-item"
                  :class="{ active: selectedRunId === run.id }"
                  @click="selectRun(run)"
                >
                  <div class="run-header">
                    <span class="run-number">第 {{ run.run_number }} 次</span>
                    <el-tag :type="getStatusType(run.status)" size="small">
                      {{ getStatusText(run.status) }}
                    </el-tag>
                    <span class="run-time">{{ formatTime(run.started_at) }}</span>
                  </div>
                  <div class="run-stats" v-if="run.summary">
                    <span>总计: {{ run.summary.total }}</span>
                    <span class="passed">通过: {{ run.summary.passed }}</span>
                    <span class="failed">失败: {{ run.summary.failed }}</span>
                    <span>通过率: {{ (run.summary.pass_rate * 100).toFixed(1) }}%</span>
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
                <el-statistic title="失败" :value="evalStore.currentRun.summary?.failed || 0">
                  <template #suffix>
                    <span style="color: #f56c6c">✗</span>
                  </template>
                </el-statistic>
                <el-statistic
                  title="通过率"
                  :value="((evalStore.currentRun.summary?.pass_rate || 0) * 100).toFixed(1) + '%'"
                />
              </div>
              <el-table :data="evalStore.evalResults" stripe size="small" max-height="400">
                <el-table-column label="用例编号" width="150">
                  <template #default="{ row }">
                    {{ row.case_uid || row.case_id }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="90" align="center">
                  <template #default="{ row }">
                    <el-tooltip v-if="row.execution_error" :content="row.execution_error" placement="top">
                      <el-tag type="warning" size="small">执行失败</el-tag>
                    </el-tooltip>
                    <el-tag v-else :type="row.is_passed ? 'success' : 'danger'" size="small">
                      {{ row.is_passed ? '通过' : '不通过' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="actual_output" label="实际输出" show-overflow-tooltip />
                <el-table-column label="操作" width="80" align="center">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="showResultDetail(row)">
                      详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Empty State -->
    <el-empty v-else description="请选择或创建一个评测任务" />

    <!-- Create Task Dialog -->
    <el-dialog v-model="taskDialogVisible" title="创建评测任务" width="500px">
      <el-form :model="taskForm" label-width="100px">
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
    <el-dialog v-model="testDialogVisible" title="测试请求模板" width="900px">
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
      :evaluator-logs="currentResult?.evaluator_logs || []"
      @close="diffDialogVisible = false"
    />

    <!-- Result Detail Dialog (Compact) -->
    <el-dialog v-model="detailDialogVisible" title="评测详情" width="600px">
      <div v-if="currentResult" class="result-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用例ID">{{ currentResult.case_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentResult.is_passed ? 'success' : 'danger'">
              {{ currentResult.is_passed ? '通过' : '失败' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>评估器日志</el-divider>
        <div class="evaluator-logs">
          <div
            v-for="(log, index) in currentResult.evaluator_logs"
            :key="index"
            class="log-item"
          >
            <el-tag :type="log.passed ? 'success' : 'danger'" size="small">
              {{ log.name }}
            </el-tag>
            <span class="log-reason">{{ log.reason || (log.passed ? '通过' : '未通过') }}</span>
          </div>
        </div>

        <el-divider>实际输出</el-divider>
        <el-input
          :model-value="currentResult.actual_output"
          type="textarea"
          :rows="8"
          readonly
        />

        <div style="margin-top: 15px; text-align: center">
          <el-button type="primary" @click="showDiffViewer">查看详细对比</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useEvalStore } from '@/stores/eval'
import { useCasesStore } from '@/stores/cases'
import { getModels } from '@/api/models'
import DiffViewer from '@/components/DiffViewer.vue'
import type { EvalTask, EvalResult } from '@/types/eval'
import type { TestCase } from '@/types/cases'
import type { Model } from '@/api/models'

const evalStore = useEvalStore()
const casesStore = useCasesStore()

// Dialog states
const taskDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const diffDialogVisible = ref(false)
const testDialogVisible = ref(false)
const currentResult = ref<EvalResult | null>(null)
const currentCase = ref<TestCase | null>(null)

// Edit state
const editForm = ref({
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
  taskForm.value.set_id = casesStore.caseSets[0].id
  taskForm.value.model_id = availableModels.value[0].id
  taskDialogVisible.value = true
}

async function handleCreateTask() {
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

    // Update: model_id, concurrency, request_template, and system_prompt (as separate field)
    const updateData = {
      model_id: editForm.value.model_id,
      concurrency: editForm.value.concurrency,
      request_template: requestTemplate,
      system_prompt: editForm.value.system_prompt || undefined,
    }
    console.log('[FRONTEND] Sending update data:', updateData)
    await evalStore.updateEvalTask(selectedTaskId.value, updateData)
    ElMessage.success('配置已保存')

    // Refresh task data
    await evalStore.fetchEvalTask(selectedTaskId.value)
    currentTask.value = evalStore.currentTask

    // Update edit form with refreshed data (especially system_prompt)
    if (currentTask.value) {
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
  detailDialogVisible.value = true
}

function showDiffViewer() {
  detailDialogVisible.value = false
  diffDialogVisible.value = true
}
</script>

<style scoped>
.evaluation {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 40px);
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
  overflow: auto;
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
  margin-bottom: 20px;
}

.runs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow-y: auto;
}

.run-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.run-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.run-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.run-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.run-number {
  font-weight: 500;
}

.run-time {
  font-size: 12px;
  color: #909399;
}

.run-stats {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #606266;
}

.run-stats .passed {
  color: #67c23a;
}

.run-stats .failed {
  color: #f56c6c;
}

.results-section {
  border-top: 1px solid #dcdfe6;
  padding-top: 20px;
}

.summary-bar {
  display: flex;
  gap: 30px;
  margin-bottom: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
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
</style>
