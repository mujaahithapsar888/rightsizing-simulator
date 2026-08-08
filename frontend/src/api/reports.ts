import { apiClient } from './client'
import type { Report, ReportList } from '../types'

export const reportsApi = {
  generate: async (payload: any): Promise<Report> => {
    const { data } = await apiClient.post<Report>('/reports/generate', payload)
    return data
  },

  benchmark: async (payload: any): Promise<Report> => {
    const { data } = await apiClient.post<Report>('/reports/benchmark', payload)
    return data
  },

  list: async (skip = 0, limit = 20): Promise<ReportList> => {
    const { data } = await apiClient.get<ReportList>('/reports/', { params: { skip, limit } })
    return data
  },

  get: async (id: string): Promise<Report> => {
    const { data } = await apiClient.get<Report>(`/reports/${id}`)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/reports/${id}`)
  },
}
