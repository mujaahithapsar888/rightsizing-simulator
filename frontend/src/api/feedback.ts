import { apiClient } from './client'

export const feedbackApi = {
  submit: async (payload: {
    ease_of_use: number
    recommendation_quality: number
    trust: number
    overall_satisfaction: number
    comments?: string
  }): Promise<any> => {
    const { data } = await apiClient.post('/feedback/', payload)
    return data
  },

  getAverages: async (): Promise<any> => {
    const { data } = await apiClient.get('/feedback/')
    return data
  }
}
