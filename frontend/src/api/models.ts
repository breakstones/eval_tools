import apiClient from './index'

// Provider APIs
export interface ModelProvider {
  id: string
  name: string
  base_url: string
  api_key: string
  created_at: string
  updated_at: string
  models_count: number
}

export interface ModelProviderCreate {
  name: string
  base_url: string
  api_key: string
}

export interface ModelProviderUpdate {
  name?: string
  base_url?: string
  api_key?: string
}

export const getProviders = async () => {
  const response = await apiClient.get<ModelProvider[]>('/models/providers')
  return response.data
}

export const getProvider = async (providerId: string) => {
  const response = await apiClient.get<ModelProvider>(`/models/providers/${providerId}`)
  return response.data
}

export const createProvider = async (data: ModelProviderCreate) => {
  const response = await apiClient.post<ModelProvider>('/models/providers', data)
  return response.data
}

export const updateProvider = async (providerId: string, data: ModelProviderUpdate) => {
  const response = await apiClient.put<ModelProvider>(`/models/providers/${providerId}`, data)
  return response.data
}

export const deleteProvider = async (providerId: string) => {
  await apiClient.delete(`/models/providers/${providerId}`)
}

// Model APIs
export interface Model {
  id: string
  provider_id: string
  model_code: string
  display_name: string
  endpoint: string
  provider_name: string
  provider_base_url: string
  created_at: string
  updated_at: string
}

export interface ModelCreate {
  provider_id: string
  model_code: string
  display_name: string
  endpoint?: string
}

export interface ModelUpdate {
  model_code?: string
  display_name?: string
  endpoint?: string
}

export const getModels = async (providerId?: string) => {
  const params = providerId ? { provider_id: providerId } : {}
  const response = await apiClient.get<Model[]>('/models/models', { params })
  return response.data
}

export const getModel = async (modelId: string) => {
  const response = await apiClient.get<any>(`/models/models/${modelId}`)
  return response.data
}

export const createModel = async (data: ModelCreate) => {
  const response = await apiClient.post<Model>('/models/models', data)
  return response.data
}

export const updateModel = async (modelId: string, data: ModelUpdate) => {
  const response = await apiClient.put<Model>(`/models/models/${modelId}`, data)
  return response.data
}

export const deleteModel = async (modelId: string) => {
  await apiClient.delete(`/models/models/${modelId}`)
}
