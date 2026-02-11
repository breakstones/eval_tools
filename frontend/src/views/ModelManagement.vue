<template>
  <div class="model-management">
    <!-- Header -->
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary" @click="showCreateProviderDialog">
        <el-icon><Plus /></el-icon>
        添加提供方
      </el-button>
    </div>

    <!-- Providers Collapse with Models -->
    <el-collapse
      v-model="expandedKeys"
      class="providers-collapse"
    >
      <el-collapse-item
        v-for="provider in providers"
        :key="provider.id"
        :name="provider.id"
      >
        <template #title>
          <div class="collapse-title">
            <span class="provider-name">{{ provider.name }}</span>
            <span class="model-count">{{ provider.models?.length || 0 }} 个模型</span>
            <span class="provider-base-url">{{ provider.base_url }}</span>
            <div class="title-actions">
              <el-button link type="primary" size="small" @click.stop="showEditProviderDialog(provider)">
                编辑
              </el-button>
              <el-button link type="primary" size="small" @click.stop="showCreateModelDialog(provider)">
                添加模型
              </el-button>
              <el-button link type="danger" size="small" @click.stop="confirmDeleteProvider(provider)">
                删除
              </el-button>
            </div>
          </div>
        </template>

        <!-- Models Table inside Collapse -->
        <el-table
          :data="provider.models || []"
          stripe
          height="250"
          class="models-table"
        >
          <el-table-column prop="display_name" label="显示名称" min-width="150" />
          <el-table-column prop="model_code" label="模型代码" min-width="120" />
          <el-table-column prop="endpoint" label="Endpoint" min-width="180" />
          <el-table-column label="操作" width="180" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click.stop="showEditModelDialog(row)">
                编辑
              </el-button>
              <el-button link type="danger" size="small" @click="confirmDeleteModel(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div style="padding: 20px 0; text-align: center; color: #909399">
              暂无模型，点击"添加模型"按钮添加
            </div>
          </template>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <!-- Empty State -->
    <el-empty v-if="!providers.length" description="暂无提供方，请先添加提供方" />

    <!-- Create/Edit Provider Dialog -->
    <el-dialog
      v-model="providerDialogVisible"
      :title="editingProvider ? '编辑提供方' : '添加提供方'"
      width="500px"
      :lock-scroll="true"
    >
      <el-form :model="providerForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="providerForm.name" placeholder="例如: OpenAI, Anthropic" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="providerForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="providerForm.api_key" type="password" placeholder="sk-..." show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProvider">保存</el-button>
      </template>
    </el-dialog>

    <!-- Create/Edit Model Dialog -->
    <el-dialog
      v-model="modelDialogVisible"
      :title="editingModel ? '编辑模型' : '添加模型'"
      width="500px"
      :lock-scroll="true"
    >
      <el-form :model="modelForm" label-width="100px">
        <el-form-item label="显示名称">
          <el-input v-model="modelForm.display_name" placeholder="例如: GPT-4" />
        </el-form-item>
        <el-form-item label="模型代码">
          <el-input v-model="modelForm.model_code" placeholder="例如: gpt-4" />
        </el-form-item>
        <el-form-item label="Endpoint">
          <el-input v-model="modelForm.endpoint" placeholder="默认为 /chat/completions，可自定义" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveModel">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ModelProvider, Model, ModelProviderCreate, ModelCreate, ModelProviderUpdate, ModelUpdate } from '@/api/models'
import {
  getProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  getModels,
  createModel,
  updateModel,
  deleteModel
} from '@/api/models'

const providers = ref<(ModelProvider & { models: Model[] })[]>([])
const providerDialogVisible = ref(false)
const modelDialogVisible = ref(false)
const editingProvider = ref<ModelProvider | null>(null)
const editingModel = ref<Model | null>(null)
const expandedKeys = ref<string[]>([])

const providerForm = ref<ModelProviderCreate>({
  name: '',
  base_url: '',
  api_key: ''
})

const modelForm = ref<ModelCreate>({
  provider_id: '',
  model_code: '',
  display_name: '',
  endpoint: ''
})

// Load providers and their models
const loadProviders = async () => {
  try {
    const data = await getProviders()
    // Initialize providers with empty models array
    providers.value = data.map(p => ({ ...p, models: [] }))

    // Set all providers as expanded by default
    expandedKeys.value = data.map(p => p.id)

    // Load models for each provider
    await Promise.all(
      providers.value.map(async (provider) => {
        try {
          const models = await getModels(provider.id)
          provider.models = models
        } catch (error) {
          console.error(`Failed to load models for provider ${provider.id}:`, error)
        }
      })
    )
  } catch (error: any) {
    ElMessage.error(error.message || '加载提供方列表失败')
  }
}

const showCreateProviderDialog = () => {
  editingProvider.value = null
  providerForm.value = { name: '', base_url: '', api_key: '' }
  providerDialogVisible.value = true
}

const showEditProviderDialog = (provider: ModelProvider) => {
  editingProvider.value = provider
  providerForm.value = {
    name: provider.name,
    base_url: provider.base_url,
    api_key: provider.api_key
  }
  providerDialogVisible.value = true
}

const saveProvider = async () => {
  try {
    if (!providerForm.value.name || !providerForm.value.base_url || !providerForm.value.api_key) {
      ElMessage.warning('请填写所有字段')
      return
    }

    if (editingProvider.value) {
      const updateData: ModelProviderUpdate = {
        name: providerForm.value.name,
        base_url: providerForm.value.base_url,
        api_key: providerForm.value.api_key
      }
      await updateProvider(editingProvider.value.id, updateData)
      ElMessage.success('提供方更新成功')
    } else {
      await createProvider(providerForm.value)
      ElMessage.success('提供方创建成功')
    }

    providerDialogVisible.value = false
    await loadProviders()
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  }
}

const confirmDeleteProvider = async (provider: ModelProvider) => {
  try {
    await ElMessageBox.confirm(`确定要删除提供方 "${provider.name}" 吗？这将同时删除其下的所有模型。`, '确认删除', {
      type: 'warning'
    })
    await deleteProvider(provider.id)
    ElMessage.success('删除成功')
    await loadProviders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const showCreateModelDialog = (provider: ModelProvider) => {
  editingModel.value = null
  modelForm.value = {
    provider_id: provider.id,
    model_code: '',
    display_name: ''
  }
  modelDialogVisible.value = true
}

const showEditModelDialog = (row: Model) => {
  editingModel.value = row
  modelForm.value = {
    provider_id: row.provider_id,
    model_code: row.model_code || '',
    display_name: row.display_name || '',
    endpoint: row.endpoint || ''
  }
  modelDialogVisible.value = true
}

const confirmDeleteModel = async (model: Model) => {
  try {
    await ElMessageBox.confirm(`确定要删除模型 "${model.display_name || model.model_code}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteModel(model.id)
    ElMessage.success('删除成功')
    await loadProviders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const saveModel = async () => {
  try {
    if (!modelForm.value.model_code || !modelForm.value.display_name) {
      ElMessage.warning('请填写所有字段')
      return
    }

    if (editingModel.value) {
      const updateData: ModelUpdate = {
        model_code: modelForm.value.model_code,
        display_name: modelForm.value.display_name
      }
      await updateModel(editingModel.value.id, updateData)
      ElMessage.success('模型更新成功')
    } else {
      await createModel(modelForm.value)
      ElMessage.success('模型创建成功')
    }

    modelDialogVisible.value = false
    await loadProviders()
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  }
}

onMounted(() => {
  loadProviders()
})
</script>

<style scoped>
.model-management {
  padding: 20px;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.page-header h2 {
  margin: 0;
}

.providers-collapse {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.providers-collapse :deep(.el-collapse-item__header) {
  height: auto;
  line-height: normal;
  padding: 20px;
}

.providers-collapse :deep(.el-collapse-item__wrap) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.providers-collapse :deep(.el-collapse-item__content) {
  flex: 1;
  overflow: hidden;
  padding: 20px;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding-right: 16px;
}

.provider-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.model-count {
  font-size: 13px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.provider-base-url {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
}

.title-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.models-table {
  border: none;
}

.models-table :deep(.el-table__body-wrapper) {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.models-table :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  display: none;
}

.models-table :deep(.el-table__empty-block) {
  display: none;
}
</style>
