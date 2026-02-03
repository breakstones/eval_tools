<template>
  <div class="case-management">
    <el-row :gutter="20">
      <!-- Left Panel: Case Sets -->
      <el-col :span="8">
        <el-card class="case-sets-card">
          <template #header>
            <div class="card-header">
              <span>用例集</span>
              <el-button type="primary" size="small" @click="showCreateSetDialog">
                <el-icon><Plus /></el-icon>
                新建
              </el-button>
            </div>
          </template>

          <el-empty v-if="!casesStore.hasCaseSets && !casesStore.loading" description="暂无用例集" />

          <el-table
            :data="casesStore.caseSets"
            height="100%"
            @row-click="selectCaseSet"
            highlight-current-row
            :show-header="false"
            class="case-sets-table"
          >
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="case_count" label="用例数" width="80" align="center" />
            <el-table-column width="160" align="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="handleEditSet(row)">
                  编辑
                </el-button>
                <el-button link type="primary" size="small" @click.stop="handleExport(row)">
                  <el-icon><Download /></el-icon>
                </el-button>
                <el-button link type="danger" size="small" @click.stop="handleDeleteSet(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- Right Panel: Test Cases -->
      <el-col :span="16">
        <el-card v-if="casesStore.currentCaseSet" class="test-cases-card">
          <template #header>
            <div class="card-header">
              <span>{{ casesStore.currentCaseSet.name }}</span>
              <div class="header-actions">
                <el-button
                  v-if="selectedCases.length > 0"
                  type="danger"
                  size="small"
                  @click="handleBatchDelete"
                >
                  删除选中 ({{ selectedCases.length }})
                </el-button>
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleImportExcel"
                  accept=".xlsx,.xls"
                  style="display: inline-block; margin-right: 10px"
                >
                  <el-button size="small">
                    <el-icon><Upload /></el-icon>
                    导入Excel
                  </el-button>
                </el-upload>
                <el-button type="primary" size="small" @click="showCreateCaseDialog">
                  <el-icon><Plus /></el-icon>
                  新建用例
                </el-button>
              </div>
            </div>
          </template>

          <el-table
            :data="casesStore.testCases"
            stripe
            height="100%"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="case_uid" label="编号" width="100" />
            <el-table-column prop="description" label="描述" width="200" />
            <el-table-column prop="user_input" label="用户输入" show-overflow-tooltip />
            <el-table-column prop="expected_output" label="预期输出" show-overflow-tooltip />
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleEditCase(row)">
                  编辑
                </el-button>
                <el-button link type="danger" size="small" @click="handleDeleteCase(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-empty v-else description="请选择一个用例集" />
      </el-col>
    </el-row>

    <!-- Create/Edit Case Set Dialog -->
    <el-dialog
      v-model="setDialogVisible"
      :title="editingSet ? '编辑用例集' : '新建用例集'"
      width="500px"
    >
      <el-form :model="setForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="setForm.name" placeholder="请输入用例集名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="setDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSet">确定</el-button>
      </template>
    </el-dialog>

    <!-- Create/Edit Test Case Dialog -->
    <el-dialog
      v-model="caseDialogVisible"
      :title="editingCase ? '编辑测试用例' : '新建测试用例'"
      width="800px"
    >
      <el-form :model="caseForm" label-width="100px">
        <el-form-item label="编号">
          <el-input v-model="caseForm.case_uid" placeholder="如：CASE-001" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="caseForm.description" placeholder="用例描述" />
        </el-form-item>
        <el-form-item label="用户输入" required>
          <el-input
            v-model="caseForm.user_input"
            type="textarea"
            class="case-textarea"
            placeholder="请输入用户输入"
          />
        </el-form-item>
        <el-form-item label="预期输出">
          <el-input
            v-model="caseForm.expected_output"
            type="textarea"
            class="case-textarea"
            placeholder="请输入预期输出"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCase">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Delete, Upload } from '@element-plus/icons-vue'
import { useCasesStore } from '@/stores/cases'
import type { CaseSet, TestCase } from '@/types/cases'

const casesStore = useCasesStore()

// Dialog states
const setDialogVisible = ref(false)
const caseDialogVisible = ref(false)
const editingSet = ref<CaseSet | null>(null)
const editingCase = ref<TestCase | null>(null)

// Selected cases for batch delete
const selectedCases = ref<TestCase[]>([])

// Form data
const setForm = ref({
  name: '',
})

const caseForm = ref({
  case_uid: '',
  description: '',
  user_input: '',
  expected_output: '',
})

onMounted(async () => {
  await casesStore.fetchCaseSets()
  // Auto-select first case set if available
  if (casesStore.caseSets.length > 0) {
    selectCaseSet(casesStore.caseSets[0])
  }
})

function selectCaseSet(row: CaseSet) {
  casesStore.fetchCaseSet(row.id)
  casesStore.fetchTestCases(row.id)
}

function showCreateSetDialog() {
  editingSet.value = null
  setForm.value = { name: '' }
  setDialogVisible.value = true
}

function showCreateCaseDialog() {
  if (!casesStore.currentCaseSet) {
    ElMessage.warning('请先选择用例集')
    return
  }
  editingCase.value = null
  caseForm.value = {
    case_uid: '',
    description: '',
    user_input: '',
    expected_output: '',
  }
  caseDialogVisible.value = true
}

function handleEditSet(row: CaseSet) {
  editingSet.value = row
  setForm.value = {
    name: row.name,
  }
  setDialogVisible.value = true
}

function handleSelectionChange(selection: TestCase[]) {
  selectedCases.value = selection
}

function handleEditCase(row: TestCase) {
  editingCase.value = row
  caseForm.value = {
    case_uid: row.case_uid || '',
    description: row.description || '',
    user_input: row.user_input,
    expected_output: row.expected_output || '',
  }
  caseDialogVisible.value = true
}

async function handleSaveSet() {
  if (!setForm.value.name) {
    ElMessage.error('请输入用例集名称')
    return
  }

  try {
    if (editingSet.value) {
      await casesStore.updateCaseSet(editingSet.value.id, setForm.value)
      ElMessage.success('更新成功')
    } else {
      await casesStore.createCaseSet(setForm.value)
      ElMessage.success('创建成功')
    }
    setDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  }
}

async function handleSaveCase() {
  if (!caseForm.value.user_input) {
    ElMessage.error('请输入用户输入')
    return
  }

  try {
    if (editingCase.value) {
      await casesStore.updateTestCase(editingCase.value.id, caseForm.value)
      ElMessage.success('更新成功')
    } else {
      await casesStore.createTestCase({
        set_id: casesStore.currentCaseSet!.id,
        ...caseForm.value,
      })
      ElMessage.success('创建成功')
    }
    caseDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  }
}

async function handleDeleteSet(row: CaseSet) {
  try {
    await ElMessageBox.confirm('确定要删除该用例集吗？', '确认删除', {
      type: 'warning',
    })
    await casesStore.deleteCaseSet(row.id)
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e instanceof Error ? e.message : '删除失败')
    }
  }
}

async function handleDeleteCase(row: TestCase) {
  try {
    await ElMessageBox.confirm('确定要删除该测试用例吗？', '确认删除', {
      type: 'warning',
    })
    await casesStore.deleteTestCase(row.id)
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e instanceof Error ? e.message : '删除失败')
    }
  }
}

async function handleBatchDelete() {
  if (selectedCases.value.length === 0) {
    return
  }
  const count = selectedCases.value.length
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${count} 个测试用例吗？`,
      '确认批量删除',
      { type: 'warning' }
    )
    // Delete all selected cases
    await Promise.all(
      selectedCases.value.map(tc => casesStore.deleteTestCase(tc.id))
    )
    selectedCases.value = []
    ElMessage.success(`成功删除 ${count} 个测试用例`)
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e instanceof Error ? e.message : '删除失败')
    }
  }
}

async function handleImportExcel(file: File) {
  try {
    // Import to current selected case set, or create new if none selected
    const setId = casesStore.currentCaseSet?.id
    console.log('[FRONTEND] Importing Excel with setId:', setId)
    const result = await casesStore.importExcel(file, setId)
    const action = setId ? '追加' : '创建'
    ElMessage.success(`导入成功，${action}了 ${result.cases_created} 个测试用例`)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '导入失败')
  }
  return false
}

async function handleExport(row: CaseSet) {
  try {
    await casesStore.exportExcel(row.id)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '导出失败')
  }
}
</script>

<style scoped>
.case-management {
  padding: 20px;
  height: 100%;
  overflow: hidden;
  display: flex;
  gap: 20px;
}

.case-management .el-row {
  height: 100%;
  width: 100%;
  margin: 0 !important;
}

.case-management .el-col {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.case-management .el-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.case-management .el-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.case-management .el-card :deep(.el-card__body)::-webkit-scrollbar {
  display: none;
}

.case-management :deep(.el-table__body-wrapper) {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.case-management :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  display: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.case-sets-table {
  cursor: pointer;
}

.case-sets-table :deep(.el-table__row) {
  cursor: pointer;
}

.case-sets-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.case-textarea :deep(.el-textarea__inner) {
  height: 400px !important;
  min-height: 400px !important;
}
</style>
