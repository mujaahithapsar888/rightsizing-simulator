import { apiClient } from './client'

export const eventRecoveryApi = {
  simulate: async (): Promise<any> => {
    const { data } = await apiClient.post('/event-recovery/simulate')
    return data
  }
}
