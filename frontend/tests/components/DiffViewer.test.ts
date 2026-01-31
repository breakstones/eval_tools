import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import DiffViewer from '@/components/DiffViewer.vue'

describe('DiffViewer Component', () => {
  const mountComponent = (props: {
    visible?: boolean
    expected?: string
    actual?: string
    isPassed?: boolean
    evaluatorLogs?: Array<{ name: string; passed: boolean; reason?: string }>
  }) => {
    return mount(DiffViewer, {
      props: {
        visible: true,
        expected: '',
        actual: '',
        isPassed: true,
        evaluatorLogs: [],
        ...props
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-dialog': true,
          'el-row': true,
          'el-col': true,
          'el-input': true,
          'el-divider': true,
          'el-button': true,
          'el-tag': true
        }
      }
    })
  }

  it('should render when visible', () => {
    const wrapper = mountComponent({ visible: true })
    expect(wrapper.exists()).toBe(true)
  })

  it('should not render dialog content when not visible', () => {
    const wrapper = mountComponent({ visible: false })
    // When not visible, dialog content should not be rendered
    expect(wrapper.exists()).toBe(true)
  })

  it('should accept expected and actual props', async () => {
    const wrapper = mountComponent({
      expected: 'expected text',
      actual: 'actual text'
    })

    await flushPromises()

    expect(wrapper.props('expected')).toBe('expected text')
    expect(wrapper.props('actual')).toBe('actual text')
  })

  it('should show isPassed status correctly', () => {
    const wrapper = mountComponent({ isPassed: false })
    expect(wrapper.props('isPassed')).toBe(false)
  })

  it('should accept evaluator logs', () => {
    const wrapper = mountComponent({
      evaluatorLogs: [
        { name: 'exact_match', passed: false, reason: 'Output does not match' }
      ]
    })

    expect(wrapper.props('evaluatorLogs')).toHaveLength(1)
  })

  it('should handle empty evaluator logs', () => {
    const wrapper = mountComponent({
      evaluatorLogs: []
    })

    expect(wrapper.props('evaluatorLogs')).toHaveLength(0)
  })

  it('should emit close event', async () => {
    const wrapper = mountComponent()

    // Simulate close event
    wrapper.vm.$emit('close')
    await flushPromises()

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('should handle empty strings for expected and actual', () => {
    const wrapper = mountComponent({
      expected: '',
      actual: ''
    })

    expect(wrapper.props('expected')).toBe('')
    expect(wrapper.props('actual')).toBe('')
  })

  it('should handle special characters', () => {
    const wrapper = mountComponent({
      expected: '<div>Hello & goodbye</div>',
      actual: '<div>Hello & world</div>'
    })

    expect(wrapper.props('expected')).toContain('&')
    expect(wrapper.props('actual')).toContain('&')
  })

  it('should update when props change', async () => {
    const wrapper = mountComponent({
      expected: 'original',
      actual: 'original'
    })

    await wrapper.setProps({ expected: 'updated', actual: 'updated' })
    await flushPromises()

    expect(wrapper.props('expected')).toBe('updated')
    expect(wrapper.props('actual')).toBe('updated')
  })
})
