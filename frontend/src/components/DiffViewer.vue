<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    width="800px"
    @close="$emit('close')"
  >
    <div class="diff-container">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="diff-section">
            <div class="diff-label">预期输出</div>
            <el-input
              :model-value="expected"
              type="textarea"
              :rows="15"
              readonly
              class="diff-textarea"
            />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="diff-section">
            <div class="diff-label">实际输出</div>
            <el-input
              :model-value="actual"
              type="textarea"
              :rows="15"
              readonly
              class="diff-textarea"
              :class="{ 'diff-failed': !isPassed }"
            />
          </div>
        </el-col>
      </el-row>

      <!-- Diff 视图 -->
      <div v-if="diffHtml" class="diff-view">
        <el-divider>差异对比</el-divider>
        <div v-html="diffHtml" class="diff-content"></div>
      </div>

      <!-- 评估日志 -->
      <div v-if="evaluatorLogs && evaluatorLogs.length > 0" class="evaluator-logs">
        <el-divider>评估结果</el-divider>
        <div v-for="(log, index) in evaluatorLogs" :key="index" class="log-item">
          <el-tag :type="log.passed ? 'success' : 'danger'" size="small">
            {{ log.name }}
          </el-tag>
          <span class="log-reason">{{ log.reason || (log.passed ? '通过' : '未通过') }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('close')">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { diff_match_patch, DIFF_DELETE, DIFF_INSERT, DIFF_EQUAL } from 'diff-match-patch'

interface Props {
  visible: boolean
  expected: string
  actual: string
  isPassed: boolean
  evaluatorLogs?: Array<{ name: string; passed: boolean; reason?: string }>
}

const props = withDefaults(defineProps<Props>(), {
  evaluatorLogs: () => [],
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const title = computed(() => props.isPassed ? '评测结果 - 通过' : '评测结果 - 失败')

const diffHtml = ref('')

const dmp = new diff_match_patch()

function generateDiff(): string {
  const expectedText = props.expected || ''
  const actualText = props.actual || ''

  const diffs = dmp.diff_main(expectedText, actualText)
  dmp.diff_cleanupSemantic(diffs)

  const htmlParts: string[] = []

  for (const diff of diffs) {
    const [type, text] = diff
    const escapedText = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')

    if (type === DIFF_DELETE) {
      htmlParts.push(`<span class="diff-delete">${escapedText}</span>`)
    } else if (type === DIFF_INSERT) {
      htmlParts.push(`<span class="diff-insert">${escapedText}</span>`)
    } else {
      htmlParts.push(`<span class="diff-equal">${escapedText}</span>`)
    }
  }

  return htmlParts.join('')
}

watch(
  () => [props.expected, props.actual],
  () => {
    diffHtml.value = generateDiff()
  },
  { immediate: true }
)
</script>

<style scoped>
.diff-container {
  padding: 10px 0;
}

.diff-section {
  margin-bottom: 20px;
}

.diff-label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #606266;
}

.diff-textarea :deep(textarea) {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.diff-textarea.diff-failed :deep(textarea) {
  background-color: #fef0f0;
}

.diff-view {
  margin-top: 20px;
}

.diff-content {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-delete {
  background-color: #fecaca;
  color: #dc2626;
  text-decoration: line-through;
}

.diff-insert {
  background-color: #bbf7d0;
  color: #16a34a;
}

.diff-equal {
  color: #606266;
}

.evaluator-logs {
  margin-top: 20px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.log-reason {
  color: #606266;
  font-size: 14px;
}
</style>
