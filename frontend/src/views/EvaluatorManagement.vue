<template>
  <div class="evaluator-management">
    <!-- Header -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h2>评估器管理</h2>
          <p class="subtitle">管理LLM评估器和代码评估器，配置评测任务使用的评估器</p>
        </div>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建评估器
        </el-button>
      </div>
    </el-card>

    <!-- Filter Tabs -->
    <el-card class="filter-card">
      <el-radio-group v-model="activeTab" @change="handleTabChange">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="llm_judge">LLM评估器</el-radio-button>
        <el-radio-button label="code">代码评估器</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- Evaluator List -->
    <el-row :gutter="20" class="evaluator-list">
      <el-col
        v-for="evaluator in evaluatorStore.evaluators"
        :key="evaluator.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <el-card class="evaluator-card" :class="`type-${evaluator.type}`">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon v-if="evaluator.type === 'llm_judge'" class="type-icon"><ChatDotRound /></el-icon>
                <el-icon v-else class="type-icon"><DocumentCopy /></el-icon>
                <span class="evaluator-name">{{ evaluator.name }}</span>
              </div>
              <div class="header-actions">
                <el-tag
                  v-if="evaluator.is_system"
                  type="info"
                  size="small"
                >
                  系统内置
                </el-tag>
                <el-dropdown @command="(cmd) => handleAction(cmd, evaluator)">
                  <el-icon class="action-icon"><MoreFilled /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit" :disabled="evaluator.is_system">
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item command="test">
                        测试
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="delete"
                        :disabled="evaluator.is_system"
                        divided
                      >
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>

          <div class="evaluator-content">
            <p class="description">{{ evaluator.description || '暂无描述' }}</p>
            <div class="evaluator-meta">
              <el-tag :type="evaluator.type === 'llm_judge' ? 'warning' : 'success'" size="small">
                {{ evaluator.type === 'llm_judge' ? 'LLM评估器' : '代码评估器' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Empty State -->
      <el-col v-if="evaluatorStore.evaluators.length === 0 && !evaluatorStore.loading" :span="24">
        <el-empty description="暂无评估器，点击上方按钮创建">
          <el-button type="primary" @click="showCreateDialog">创建评估器</el-button>
        </el-empty>
      </el-col>
    </el-row>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑评估器' : '新建评估器'"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="评估器名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入评估器名称" />
        </el-form-item>

        <el-form-item label="评估器类型" prop="type">
          <el-radio-group v-model="form.type" :disabled="isEditMode">
            <el-radio label="llm_judge">LLM评估器</el-radio>
            <el-radio label="code">代码评估器</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入评估器描述"
          />
        </el-form-item>

        <!-- LLM Judge Config -->
        <template v-if="form.type === 'llm_judge'">
          <el-form-item label="评估模型" prop="config.model_id">
            <el-select v-model="form.config.model_id" placeholder="选择用于评估的模型" style="width: 100%">
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
                </el-option>
              </el-option-group>
            </el-select>
            <div class="form-tip">
              选择用于执行评估的LLM模型
            </div>
          </el-form-item>
          <el-form-item label="提示词模板" prop="config.prompt_template">
            <el-input
              v-model="form.config.prompt_template"
              type="textarea"
              :rows="10"
              placeholder="请输入提示词模板，使用 ${expected} 表示预期输出，${actual} 表示实际输出"
            />
            <div class="form-tip">
              变量说明：${expected} - 预期输出，${actual} - 实际输出
            </div>
          </el-form-item>
        </template>

        <!-- Code Evaluator Config -->
        <template v-if="form.type === 'code'">
          <el-form-item label="评估代码" prop="config.code">
            <el-input
              v-model="form.config.code"
              type="textarea"
              :rows="12"
              placeholder="请输入Python评估代码，必须实现 evaluate(expected: str, actual: str) -> dict 函数"
              font-family="monospace"
            />
            <div class="form-tip">
              函数签名: def evaluate(expected: str, actual: str) -> dict<br>
              返回格式: {"result": "passed" | "failed", "reason": "原因说明"}
            </div>
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ isEditMode ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Test Dialog -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试评估器"
      width="600px"
      @close="handleTestDialogClose"
    >
      <div v-if="currentEvaluator">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="评估器名称">
            {{ currentEvaluator.name }}
          </el-descriptions-item>
          <el-descriptions-item label="评估器类型">
            <el-tag :type="currentEvaluator.type === 'llm_judge' ? 'warning' : 'success'">
              {{ currentEvaluator.type === 'llm_judge' ? 'LLM评估器' : '代码评估器' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <el-form :model="testForm" label-width="80px">
          <el-form-item label="预期输出">
            <el-input
              v-model="testForm.expected"
              type="textarea"
              :rows="3"
              placeholder="请输入预期输出"
            />
          </el-form-item>
          <el-form-item label="实际输出">
            <el-input
              v-model="testForm.actual"
              type="textarea"
              :rows="3"
              placeholder="请输入实际输出"
            />
          </el-form-item>
        </el-form>

        <div v-if="testResult" class="test-result">
          <el-divider />
          <el-alert
            :type="testResult.result === 'passed' ? 'success' : 'error'"
            :closable="false"
            show-icon
          >
            <template #title>
              测试结果: {{ testResult.result === 'passed' ? '通过' : '失败' }}
            </template>
            <div v-if="testResult.reason">原因: {{ testResult.reason }}</div>
            <div v-if="testResult.error" class="error-text">错误: {{ testResult.error }}</div>
          </el-alert>
        </div>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleTest" :loading="testing">
          测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, ChatDotRound, DocumentCopy, MoreFilled } from '@element-plus/icons-vue'
import { useEvaluatorStore } from '@/stores/evaluator'
import { getModels } from '@/api/models'
import type { Evaluator, EvaluatorCreate, EvaluatorUpdate, EvaluatorTestRequest } from '@/types/evaluator'
import type { Model } from '@/api/models'

const evaluatorStore = useEvaluatorStore()

// State
const activeTab = ref('')
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEditMode = ref(false)
const currentEvaluator = ref<Evaluator | null>(null)
const saving = ref(false)
const testing = ref(false)
const testResult = ref<any>(null)

// Models for LLM evaluator
const availableModels = ref<Model[]>([])

// Form
const formRef = ref<FormInstance>()
const form = ref<EvaluatorCreate>({
  name: '',
  type: 'code',
  description: '',
  config: {},
})

const testForm = ref<EvaluatorTestRequest>({
  expected: '',
  actual: '',
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入评估器名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  type: [
    { required: true, message: '请选择评估器类型', trigger: 'change' },
  ],
}

// Computed
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

// Methods
async function loadModels() {
  try {
    availableModels.value = await getModels()
  } catch (error: any) {
    console.error('Failed to load models:', error)
  }
}
const handleTabChange = async () => {
  await evaluatorStore.fetchEvaluators(activeTab.value || undefined)
}

const showCreateDialog = () => {
  isEditMode.value = false
  form.value = {
    name: '',
    type: 'code',
    description: '',
    config: {},
  }
  dialogVisible.value = true
}

const showEditDialog = (evaluator: Evaluator) => {
  isEditMode.value = true
  currentEvaluator.value = evaluator
  form.value = {
    name: evaluator.name,
    type: evaluator.type,
    description: evaluator.description || '',
    config: { ...evaluator.config },
  }
  dialogVisible.value = true
}

const showTestDialog = (evaluator: Evaluator) => {
  currentEvaluator.value = evaluator
  testForm.value = {
    expected: '',
    actual: '',
  }
  testResult.value = null
  testDialogVisible.value = true
}

const handleAction = async (command: string, evaluator: Evaluator) => {
  switch (command) {
    case 'edit':
      showEditDialog(evaluator)
      break
    case 'test':
      showTestDialog(evaluator)
      break
    case 'delete':
      await handleDelete(evaluator)
      break
  }
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // Validate config based on type
    if (form.value.type === 'llm_judge' && !form.value.config.prompt_template) {
      ElMessage.error('请输入提示词模板')
      return
    }
    if (form.value.type === 'code' && !form.value.config.code) {
      ElMessage.error('请输入评估代码')
      return
    }

    saving.value = true
    try {
      if (isEditMode.value && currentEvaluator.value) {
        await evaluatorStore.updateEvaluator(currentEvaluator.value.id, {
          name: form.value.name,
          description: form.value.description,
          config: form.value.config,
        })
        ElMessage.success('评估器更新成功')
      } else {
        await evaluatorStore.createEvaluator(form.value)
        ElMessage.success('评估器创建成功')
      }
      dialogVisible.value = false
      await evaluatorStore.fetchEvaluators(activeTab.value || undefined)
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      saving.value = false
    }
  })
}

const handleDelete = async (evaluator: Evaluator) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除评估器"${evaluator.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await evaluatorStore.deleteEvaluator(evaluator.id)
    ElMessage.success('删除成功')
    await evaluatorStore.fetchEvaluators(activeTab.value || undefined)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleTest = async () => {
  if (!currentEvaluator.value) return

  if (!testForm.value.expected || !testForm.value.actual) {
    ElMessage.warning('请输入预期输出和实际输出')
    return
  }

  testing.value = true
  testResult.value = null
  try {
    const result = await evaluatorStore.testEvaluator(currentEvaluator.value.id, testForm.value)
    testResult.value = result
  } catch (error: any) {
    ElMessage.error(error.message || '测试失败')
  } finally {
    testing.value = false
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  currentEvaluator.value = null
}

const handleTestDialogClose = () => {
  testResult.value = null
  currentEvaluator.value = null
}

onMounted(async () => {
  await loadModels()
  await evaluatorStore.fetchEvaluators()
})
</script>

<style scoped>
.evaluator-management {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.evaluator-list {
  margin-top: 20px;
}

.evaluator-card {
  margin-bottom: 20px;
  transition: box-shadow 0.3s;
}

.evaluator-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.evaluator-card.type-llm_judge {
  border-left: 4px solid #e6a23c;
}

.evaluator-card.type-code {
  border-left: 4px solid #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-icon {
  font-size: 18px;
  color: #409eff;
}

.evaluator-name {
  font-weight: 600;
  font-size: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-icon {
  cursor: pointer;
  font-size: 18px;
  color: #909399;
}

.action-icon:hover {
  color: #409eff;
}

.evaluator-content {
  padding: 10px 0;
}

.description {
  color: #606266;
  font-size: 14px;
  margin: 0 0 12px 0;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.evaluator-meta {
  display: flex;
  gap: 8px;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.5;
}

.test-result {
  margin-top: 16px;
}

.error-text {
  color: #f56c6c;
  margin-top: 8px;
}
</style>
