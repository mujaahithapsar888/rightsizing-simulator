import { apiClient } from './client'
import type { Experiment, ExperimentList } from '../types'

export const experimentsApi = {
  create: async (payload: any): Promise<Experiment> => {
    const { data } = await apiClient.post<Experiment>('/experiments/run-scenarios', payload)
    return data
  },

  list: async (skip = 0, limit = 20): Promise<ExperimentList> => {
    const { data } = await apiClient.get<ExperimentList>('/experiments/', { params: { skip, limit } })
    return data
  },

  get: async (id: string): Promise<Experiment> => {
    const { data } = await apiClient.get<Experiment>(`/experiments/${id}`)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/experiments/${id}`)
  },
}
