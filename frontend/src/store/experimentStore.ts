import { create } from 'zustand'
import type { Experiment, ScenarioConfig } from '../types'

interface ExperimentStore {
  drafts: ScenarioConfig[]
  activeExperiment: Experiment | null

  addScenario: (scenario: ScenarioConfig) => void
  removeScenario: (index: number) => void
  updateScenario: (index: number, scenario: ScenarioConfig) => void
  clearDrafts: () => void
  setActiveExperiment: (exp: Experiment | null) => void
}

export const useExperimentStore = create<ExperimentStore>((set) => ({
  drafts: [],
  activeExperiment: null,

  addScenario: (scenario) =>
    set((s) => ({ drafts: [...s.drafts, scenario] })),

  removeScenario: (index) =>
    set((s) => ({ drafts: s.drafts.filter((_, i) => i !== index) })),

  updateScenario: (index, scenario) =>
    set((s) => {
      const next = [...s.drafts]
      next[index] = scenario
      return { drafts: next }
    }),

  clearDrafts: () => set({ drafts: [] }),
  setActiveExperiment: (exp) => set({ activeExperiment: exp }),
}))
