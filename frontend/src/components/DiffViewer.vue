<template>
  <el-dialog
    :model-value="visible"
    title="评测详细结果"
    width="900px"
    @close="$emit('close')"
  >
    <div class="result-container">
      <!-- 1. 评测结果 -->
      <div class="result-header">
        <span class="result-label">评测结果：</span>
        <el-tag :type="isPassed ? 'success' : 'danger'" size="large">
          {{ isPassed ? '通过' : '失败' }}
        </el-tag>
      </div>

      <!-- 2. 评估器列表 -->
      <div v-if="evaluatorLogs && evaluatorLogs.length > 0" class="evaluators-section">
        <div class="section-title">评估器 ({{ evaluatorLogs.length }})</div>
        <div class="evaluators-list">
          <div v-for="(log, index) in evaluatorLogs" :key="index" class="evaluator-item">
            <div class="evaluator-header">
              <div class="evaluator-index">{{ index + 1 }}</div>
              <div class="evaluator-info">
                <div class="evaluator-name">{{ log.evaluator }}</div>
                <div class="evaluator-divider"></div>
                <el-tag :type="log.passed ? 'success' : 'danger'" size="small">
                  {{ log.passed ? '通过' : '失败' }}
                </el-tag>
              </div>
            </div>
            <div v-if="log.reason" class="evaluator-reason">
              <span class="reason-icon">📋</span>
              <span class="reason-text">{{ log.reason }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 输出对比 -->
      <div class="output-section">
        <div class="section-title">输出对比</div>
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="output-group">
              <div class="output-label">预期输出</div>
              <div class="output-content expected-content" v-html="expectedHtml"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="output-group">
              <div class="output-label">实际输出</div>
              <div class="output-content actual-content" v-html="actualHtml"></div>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('close')">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { diff_match_patch, DIFF_DELETE, DIFF_INSERT, DIFF_EQUAL } from 'diff-match-patch'

interface Props {
  visible: boolean
  expected: string
  actual: string
  isPassed: boolean
  evaluatorLogs?: Array<{ evaluator: string; passed: boolean; reason?: string }>
}

const props = withDefaults(defineProps<Props>(), {
  evaluatorLogs: () => [],
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const expectedHtml = ref('')
const actualHtml = ref('')
const dmp = new diff_match_patch()

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function generateDiff() {
  const expectedText = props.expected || ''
  const actualText = props.actual || ''

  // 如果任一为空，直接显示原内容
  if (!expectedText || !actualText) {
    expectedHtml.value = escapeHtml(expectedText)
    actualHtml.value = escapeHtml(actualText)
    return
  }

  const diffs = dmp.diff_main(expectedText, actualText)
  dmp.diff_cleanupSemantic(diffs)

  let expectedParts: string[] = []
  let actualParts: string[] = []
  let expectedPos = 0
  let actualPos = 0

  for (const diff of diffs) {
    const [type, text] = diff
    const escaped = escapeHtml(text)

    if (type === DIFF_DELETE) {
      // 删除的内容：只在左侧（预期）显示，红色标记
      expectedParts.push(`<span class="diff-delete">${escaped}</span>`)
    } else if (type === DIFF_INSERT) {
      // 插入的内容：只在右侧（实际）显示，绿色标记
      actualParts.push(`<span class="diff-insert">${escaped}</span>`)
    } else {
      // 相同的内容：两侧都显示，正常颜色
      expectedParts.push(escaped)
      actualParts.push(escaped)
    }
  }

  expectedHtml.value = expectedParts.join('')
  actualHtml.value = actualParts.join('')
}

watch(
  () => [props.expected, props.actual],
  () => {
    generateDiff()
  },
  { immediate: true }
)
</script>

<style scoped>
.result-container {
  padding: 5px 0;
}

/* 评测结果头部 */
.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 20px;
}

.result-label {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 评估器列表 */
.evaluators-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.evaluators-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.evaluator-item {
  padding: 0;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.evaluator-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.evaluator-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.evaluator-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background-color: #409eff;
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.evaluator-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.evaluator-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.evaluator-divider {
  width: 1px;
  height: 16px;
  background-color: #dcdfe6;
}

.evaluator-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  background-color: #fff;
}

.reason-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.reason-text {
  flex: 1;
  word-break: break-word;
}

/* 输出对比 */
.output-section {
  margin-bottom: 10px;
}

.output-group {
  margin-bottom: 12px;
}

.output-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.output-content {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 12px;
  min-height: 280px;
  max-height: 400px;
  overflow: auto;
  background-color: #fafafa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  color: #303133;
}

.expected-content {
  background-color: #fff5f5;
}

.actual-content {
  background-color: #f0f9ff;
}

/* 差异高亮 */
.output-content :deep(.diff-delete) {
  background-color: #fecaca;
  color: #dc2626;
  text-decoration: line-through;
  padding: 0 2px;
  border-radius: 2px;
}

.output-content :deep(.diff-insert) {
  background-color: #bbf7d0;
  color: #16a34a;
  padding: 0 2px;
  border-radius: 2px;
}

/* 滚动条样式 */
.output-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.output-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.output-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.output-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
