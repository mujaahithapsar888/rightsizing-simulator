import { apiClient } from './client'
import type {
  DatasetStats,
  MetricDataset,
  MetricDatasetList,
  MetricRecordList,
  UploadResponse,
} from '../types'

export const metricsApi = {
  /** Upload a CSV/Parquet file and trigger the ingestion pipeline. */
  upload: async (file: File, name: string, description?: string): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    if (description) formData.append('description', description)
    const { data } = await apiClient.post<UploadResponse>('/metrics/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /** List all datasets (paginated). */
  list: async (skip = 0, limit = 20): Promise<MetricDatasetList> => {
    const { data } = await apiClient.get<MetricDatasetList>('/metrics/', { params: { skip, limit } })
    return data
  },

  /** Get metadata for a single dataset. */
  get: async (id: string): Promise<MetricDataset> => {
    const { data } = await apiClient.get<MetricDataset>(`/metrics/${id}`)
    return data
  },

  /**
   * Get paginated metric records for a dataset.
   * @param search - partial match on instance_type
   * @param instanceType - exact match on instance_type
   */
  records: async (
    id: string,
    skip = 0,
    limit = 50,
    search?: string,
    instanceType?: string,
  ): Promise<MetricRecordList> => {
    const { data } = await apiClient.get<MetricRecordList>(`/metrics/${id}/records`, {
      params: { skip, limit, search, instance_type: instanceType },
    })
    return data
  },

  /** Get pre-computed summary statistics for a dataset. */
  stats: async (id: string): Promise<DatasetStats> => {
    const { data } = await apiClient.get<DatasetStats>(`/metrics/${id}/stats`)
    return data
  },

  /** Delete a dataset, its file, and all associated records. */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/metrics/${id}`)
  },
}
