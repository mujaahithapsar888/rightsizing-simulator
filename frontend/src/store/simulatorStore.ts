import { create } from 'zustand'
import type { SimulationConfig, SimulationRun } from '../types'

interface SimulatorStore {
  config: Partial<SimulationConfig>
  lastRun: SimulationRun | null
  isRunning: boolean

  setConfig: (config: Partial<SimulationConfig>) => void
  updateConfig: (patch: Partial<SimulationConfig>) => void
  setLastRun: (run: SimulationRun | null) => void
  setIsRunning: (v: boolean) => void
  resetConfig: () => void
}

const defaultConfig: Partial<SimulationConfig> = {
  max_cpu_threshold_pct: 80,
  max_memory_threshold_pct: 85,
  safety_margin_pct: 15,
  time_window_hours: 168,
  instance_count: 1,
}

export const useSimulatorStore = create<SimulatorStore>((set) => ({
  config: defaultConfig,
  lastRun: null,
  isRunning: false,

  setConfig: (config) => set({ config }),
  updateConfig: (patch) => set((s) => ({ config: { ...s.config, ...patch } })),
  setLastRun: (run) => set({ lastRun: run }),
  setIsRunning: (v) => set({ isRunning: v }),
  resetConfig: () => set({ config: defaultConfig, lastRun: null }),
}))
