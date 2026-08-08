import { apiClient } from './client'
import type { SimulationConfig, SimulationRun, SimulationRunList, TimeseriesData } from '../types'

export const simulatorApi = {
  run: async (config: SimulationConfig): Promise<SimulationRun> => {
    const { data } = await apiClient.post<SimulationRun>('/simulator/run', config)
    return data
  },

  list: async (skip = 0, limit = 20): Promise<SimulationRunList> => {
    const { data } = await apiClient.get<SimulationRunList>('/simulator/runs', { params: { skip, limit } })
    return data
  },

  get: async (id: string): Promise<SimulationRun> => {
    const { data } = await apiClient.get<SimulationRun>(`/simulator/runs/${id}`)
    return data
  },

  /** Fetch raw CPU/Memory time-series used in a simulation run (for charts). */
  timeseries: async (id: string): Promise<TimeseriesData> => {
    const { data } = await apiClient.get<TimeseriesData>(`/simulator/runs/${id}/timeseries`)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/simulator/runs/${id}`)
  },
}
