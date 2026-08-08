import { apiClient } from './client'

export const modelsApi = {
  /** Trains/Retrains predictive models for a given dataset. */
  train: async (datasetId: string): Promise<any> => {
    const { data } = await apiClient.post(`/models/${datasetId}/train`)
    return data
  },

  /** Retrieves the status and evaluation metrics of the model. */
  status: async (datasetId: string): Promise<any> => {
    const { data } = await apiClient.get(`/models/${datasetId}/status`)
    return data
  }
}
