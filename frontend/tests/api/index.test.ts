import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from '@/api/index'

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should export default api client', () => {
    expect(api).toBeDefined()
    expect(api.get).toBeDefined()
    expect(api.post).toBeDefined()
    expect(api.put).toBeDefined()
    expect(api.delete).toBeDefined()
  })

  it('should have correct baseURL', () => {
    expect(api.defaults.baseURL).toBe('/api')
  })

  it('should have correct timeout', () => {
    expect(api.defaults.timeout).toBe(30000)
  })
})
