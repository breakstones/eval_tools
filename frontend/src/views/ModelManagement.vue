<template>
  <div class="model-management">
    <el-container>
      <el-header>
        <h2>模型管理</h2>
      </el-header>

      <el-container>
        <!-- Providers Panel -->
        <el-aside width="350px">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>提供方列表</span>
                <el-button type="primary" size="small" @click="showCreateProviderDialog">
                  添加提供方
                </el-button>
              </div>
            </template>

            <el-table :data="providers" @row-click="selectProvider" row-class-name="provider-row">
              <el-table-column prop="name" label="名称" />
              <el-table-column label="模型数" width="60">
                <template #default="{ row }">
                  {{ row.models_count || 0 }}
                </template>
              </el-table-column>
              <el-table-column width="80">
                <template #default="{ row }">
                  <el-button link type="danger" size="small" @click.stop="confirmDeleteProvider(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-aside>

        <!-- Models Panel -->
        <el-main>
          <el-card v-if="selectedProvider">
            <template #header>
              <div class="card-header">
                <span>{{ selectedProvider.name }} - 模型列表</span>
                <el-button type="primary" size="small" @click="showCreateModelDialog">
                  添加模型
                </el-button>
              </div>
            </template>

            <el-table :data="models">
              <el-table-column prop="display_name" label="显示名称" />
              <el-table-column prop="model_code" label="模型代码" />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button link type="danger" size="small" @click="confirmDeleteModel(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-empty v-else description="请选择一个提供方查看模型" />
        </el-main>
      </el-container>
    </el-container>

    <!-- Create/Edit Provider Dialog -->
    <el-dialog v-model="providerDialogVisible" :title="editingProvider ? '编辑提供方' : '添加提供方'" width="500px">
      <el-form :model="providerForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="providerForm.name" placeholder="例如: OpenAI, Anthropic" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="providerForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="providerForm.api_key" type="password" placeholder="sk-..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProvider">保存</el-button>
      </template>
    </el-dialog>

    <!-- Create/Edit Model Dialog -->
    <el-dialog v-model="modelDialogVisible" :title="editingModel ? '编辑模型' : '添加模型'" width="500px">
      <el-form :model="modelForm" label-width="100px">
        <el-form-item label="显示名称">
          <el-input v-model="modelForm.display_name" placeholder="例如: GPT-4" />
        </el-form-item>
        <el-form-item label="模型代码">
          <el-input v-model="modelForm.model_code" placeholder="例如: gpt-4" />
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

const providers = ref<ModelProvider[]>([])
const models = ref<Model[]>([])
const selectedProvider = ref<ModelProvider | null>(null)

const providerDialogVisible = ref(false)
const modelDialogVisible = ref(false)
const editingProvider = ref<ModelProvider | null>(null)
const editingModel = ref<Model | null>(null)

const providerForm = ref<ModelProviderCreate>({
  name: '',
  base_url: '',
  api_key: ''
})

const modelForm = ref<ModelCreate>({
  provider_id: '',
  model_code: '',
  display_name: ''
})

const loadProviders = async () => {
  try {
    providers.value = await getProviders()
  } catch (error: any) {
    ElMessage.error(error.message || '加载提供方列表失败')
  }
}

const loadModels = async (providerId: string) => {
  try {
    models.value = await getModels(providerId)
  } catch (error: any) {
    ElMessage.error(error.message || '加载模型列表失败')
  }
}

const selectProvider = (provider: ModelProvider) => {
  selectedProvider.value = provider
  loadModels(provider.id)
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

    if (selectedProvider.value?.id === provider.id) {
      selectedProvider.value = null
      models.value = []
    }

    await loadProviders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const showCreateModelDialog = () => {
  if (!selectedProvider.value) {
    ElMessage.warning('请先选择一个提供方')
    return
  }

  editingModel.value = null
  modelForm.value = {
    provider_id: selectedProvider.value.id,
    model_code: '',
    display_name: ''
  }
  modelDialogVisible.value = true
}

const showEditModelDialog = (model: Model) => {
  editingModel.value = model
  modelForm.value = {
    provider_id: model.provider_id,
    model_code: model.model_code,
    display_name: model.display_name
  }
  modelDialogVisible.value = true
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
    if (selectedProvider.value) {
      await loadModels(selectedProvider.value.id)
      await loadProviders() // 更新模型计数
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  }
}

const confirmDeleteModel = async (model: Model) => {
  try {
    await ElMessageBox.confirm(`确定要删除模型 "${model.display_name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteModel(model.id)
    ElMessage.success('删除成功')

    if (selectedProvider.value) {
      await loadModels(selectedProvider.value.id)
      await loadProviders() // 更新模型计数
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

onMounted(() => {
  loadProviders()
})
</script>

<style scoped>
.model-management {
  height: 100%;
}

.el-container {
  height: 100%;
}

.el-header {
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.el-aside {
  background-color: #fafafa;
  padding: 20px;
}

.el-main {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.provider-row) {
  cursor: pointer;
}

:deep(.provider-row:hover) {
  background-color: #f0f0f0;
}
</style>
