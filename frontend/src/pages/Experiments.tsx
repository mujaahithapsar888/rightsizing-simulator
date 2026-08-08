import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { experimentsApi } from '../api/experiments'
import { metricsApi } from '../api/metrics'
import { formatCurrency, formatNumber, statusBadgeClass, timeAgo } from '../utils/formatters'

const INSTANCE_PRESETS = [
  { type: 'c5.xlarge',  vcpu: 4,  memory_gb: 8,   cost: 0.170 },
  { type: 'c5.2xlarge', vcpu: 8,  memory_gb: 16,  cost: 0.340 },
  { type: 'c5.4xlarge', vcpu: 16, memory_gb: 32,  cost: 0.680 },
  { type: 'c5.9xlarge', vcpu: 36, memory_gb: 72,  cost: 1.530 },
]

export default function Experiments() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [currentInstanceType, setCurrentInstanceType] = useState('c5.4xlarge')
  const [instanceCount, setInstanceCount] = useState(1)
  const [timeWindowHours, setTimeWindowHours] = useState(168)

  // Adjustable Parameters
  const [trafficGrowth, setTrafficGrowth] = useState(1.0)
  const [cpuThreshold, setCpuThreshold] = useState(80.0)
  const [memoryThreshold, setMemoryThreshold] = useState(85.0)
  const [latencyTarget, setLatencyTarget] = useState(250.0)
  const [availabilityTarget, setAvailabilityTarget] = useState(99.9)

  // Instance pricing overrides
  const [pricingC5Xlarge, setPricingC5Xlarge] = useState(0.17)
  const [pricingC52xlarge, setPricingC52xlarge] = useState(0.34)
  const [pricingC54xlarge, setPricingC54xlarge] = useState(0.68)
  const [pricingC59xlarge, setPricingC59xlarge] = useState(1.53)

  const [selectedExp, setSelectedExp] = useState<string | null>(null)

  const { data: experiments } = useQuery({ queryKey: ['experiments'], queryFn: () => experimentsApi.list() })
  const { data: selectedExpData } = useQuery({
    queryKey: ['experiment', selectedExp],
    queryFn: () => experimentsApi.get(selectedExp!),
    enabled: !!selectedExp,
  })
  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => metricsApi.list() })

  const createMutation = useMutation({
    mutationFn: (payload: any) => experimentsApi.create(payload),
    onSuccess: (exp) => {
      qc.invalidateQueries({ queryKey: ['experiments'] })
      setShowCreate(false)
      setName('')
      setDescription('')
      setSelectedExp(exp.id)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => experimentsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['experiments'] })
      setSelectedExp(null)
    },
  })

  const handleCreate = () => {
    if (!name) {
      alert('Please provide an experiment name')
      return
    }
    const payload = {
      name,
      description: description || undefined,
      dataset_id: datasetId || undefined,
      time_window_hours: timeWindowHours,
      current_instance_type: currentInstanceType,
      instance_count: instanceCount,
      params: {
        traffic_growth: trafficGrowth,
        cpu_threshold: cpuThreshold,
        memory_threshold: memoryThreshold,
        latency_target: latencyTarget,
        availability_target: availabilityTarget,
        pricing: {
          c5_xlarge: pricingC5Xlarge,
          c5_2xlarge: pricingC52xlarge,
          c5_4xlarge: pricingC54xlarge,
          c5_9xlarge: pricingC59xlarge
        }
      }
    }
    createMutation.mutate(payload)
  }

  const cmp = selectedExpData?.comparison_results as any
  const scenarios: any[] = cmp?.scenarios || []

  return (
    <div className="animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Scenario Simulation & Sensitivity Analyzer</h1>
          <p>Analyze recommendations under Normal, Live Sports, and Viral Spike traffic events</p>
        </div>
        <button
          id="create-experiment-btn"
          className="btn btn-primary"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? '✕ Cancel' : '⚗ Run Scenario Simulation'}
        </button>
      </div>

      {/* ── CREATE FORM ─────────────────────────────────────────────── */}
      {showCreate && (
        <div className="card mb-6 animate-slide-up">
          <h3 style={{ marginBottom: '20px' }}>Scenario Simulation Settings</h3>

          <div className="grid grid-2 gap-4 mb-5">
            <div className="form-group">
              <label className="form-label" htmlFor="exp-name">Simulation Run Name *</label>
              <input id="exp-name" className="form-input" placeholder="e.g., Q3 Capacity Optimization Run"
                value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="exp-dataset">Metrics Dataset</label>
              <select id="exp-dataset" className="form-select" value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}>
                <option value="">None — synthetic analysis</option>
                {datasets?.items.filter((d) => d.status === 'ready').map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Current Instance Type</label>
              <select className="form-select" value={currentInstanceType} onChange={(e) => setCurrentInstanceType(e.target.value)}>
                {INSTANCE_PRESETS.map(p => <option key={p.type} value={p.type}>{p.type}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Fleet Size (Instances)</label>
              <input type="number" min={1} className="form-input" value={instanceCount} onChange={(e) => setInstanceCount(parseInt(e.target.value) || 1)} />
            </div>
          </div>

          <div className="divider" style={{ margin: '20px 0' }} />

          <h4 style={{ marginBottom: '14px', color: 'var(--color-indigo-light)' }}>Adjustable Assumptions & Threshold Targets</h4>
          <div className="grid grid-3 gap-4 mb-5">
            <div className="form-group">
              <label className="form-label">Traffic Growth Multiplier</label>
              <input type="number" step="0.1" min="0.1" className="form-input" value={trafficGrowth} onChange={(e) => setTrafficGrowth(parseFloat(e.target.value) || 1.0)} />
            </div>
            <div className="form-group">
              <label className="form-label">SLA CPU Threshold (%)</label>
              <input type="number" min={10} max={100} className="form-input" value={cpuThreshold} onChange={(e) => setCpuThreshold(parseFloat(e.target.value) || 80.0)} />
            </div>
            <div className="form-group">
              <label className="form-label">SLA Memory Threshold (%)</label>
              <input type="number" min={10} max={100} className="form-input" value={memoryThreshold} onChange={(e) => setMemoryThreshold(parseFloat(e.target.value) || 85.0)} />
            </div>
            <div className="form-group">
              <label className="form-label">SLA Latency Target (ms)</label>
              <input type="number" min={10} className="form-input" value={latencyTarget} onChange={(e) => setLatencyTarget(parseFloat(e.target.value) || 250.0)} />
            </div>
            <div className="form-group">
              <label className="form-label">SLA Availability Target (%)</label>
              <input type="number" step="0.01" min={90} max={100} className="form-input" value={availabilityTarget} onChange={(e) => setAvailabilityTarget(parseFloat(e.target.value) || 99.9)} />
            </div>
            <div className="form-group">
              <label className="form-label">Evaluation Window (hours)</label>
              <input type="number" className="form-input" value={timeWindowHours} onChange={(e) => setTimeWindowHours(parseInt(e.target.value) || 168)} />
            </div>
          </div>

          <div className="divider" style={{ margin: '20px 0' }} />

          <h4 style={{ marginBottom: '14px', color: 'var(--color-indigo-light)' }}>Instance Pricing Targets ($/hour)</h4>
          <div className="grid grid-4 gap-4 mb-5">
            <div>
              <label className="form-label" style={{ fontSize: '0.75rem' }}>c5.xlarge</label>
              <input type="number" step="0.01" className="form-input" value={pricingC5Xlarge} onChange={(e) => setPricingC5Xlarge(parseFloat(e.target.value) || 0.17)} />
            </div>
            <div>
              <label className="form-label" style={{ fontSize: '0.75rem' }}>c5.2xlarge</label>
              <input type="number" step="0.01" className="form-input" value={pricingC52xlarge} onChange={(e) => setPricingC52xlarge(parseFloat(e.target.value) || 0.34)} />
            </div>
            <div>
              <label className="form-label" style={{ fontSize: '0.75rem' }}>c5.4xlarge</label>
              <input type="number" step="0.01" className="form-input" value={pricingC54xlarge} onChange={(e) => setPricingC54xlarge(parseFloat(e.target.value) || 0.68)} />
            </div>
            <div>
              <label className="form-label" style={{ fontSize: '0.75rem' }}>c5.9xlarge</label>
              <input type="number" step="0.01" className="form-input" value={pricingC59xlarge} onChange={(e) => setPricingC59xlarge(parseFloat(e.target.value) || 1.53)} />
            </div>
          </div>

          <div className="flex gap-3 justify-end">
            <button className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button
              id="create-experiment-submit-btn"
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Simulating Scenarios...' : '▶ Run Simulations'}
            </button>
          </div>
        </div>
      )}

      {/* ── MAIN LAYOUT ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ width: '260px', flexShrink: 0 }}>
          <div className="card">
            <h4>Simulation History</h4>
            <div className="flex flex-col gap-2 mt-3">
              {experiments?.items.map((exp) => (
                <div
                  key={exp.id}
                  onClick={() => setSelectedExp(exp.id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${selectedExp === exp.id ? 'var(--color-indigo)' : 'var(--color-border)'}`,
                    background: selectedExp === exp.id ? 'rgba(99,102,241,0.08)' : 'var(--color-bg-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  <div className="text-sm font-semibold">{exp.name}</div>
                  <div className="text-xs text-muted mt-1">{timeAgo(exp.created_at)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedExpData ? (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">⚗</div>
                <div className="empty-state-title">Select a simulation run</div>
              </div>
            </div>
          ) : (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="card">
                <div className="flex justify-between items-center">
                  <h3>{selectedExpData.name}</h3>
                  <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-rose)' }} onClick={() => deleteMutation.mutate(selectedExpData.id)}>✕ Delete</button>
                </div>
              </div>

              {/* Loop over Scenario Results */}
              {scenarios.map((sc: any) => (
                <div className="card" key={sc.scenario_name} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 style={{ margin: 0 }}>{sc.scenario_name}</h3>
                      <p className="text-sm text-secondary mt-1">{sc.scenario_description}</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="text-xs text-muted">Recommended Size</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--color-indigo-light)' }}>
                        {sc.recommended_configuration?.instance_type}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-2 gap-4 text-sm" style={{ background: 'var(--color-bg-secondary)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
                    <div>
                      <div><strong>Current Cost:</strong> {formatCurrency(sc.current_configuration?.monthly_cost)}/mo</div>
                      <div><strong>Projected Cost:</strong> {formatCurrency(sc.recommended_configuration?.monthly_cost)}/mo</div>
                      <div><strong>Monthly Savings:</strong> <span style={{ color: 'var(--color-emerald)', fontWeight: 600 }}>{formatCurrency(sc.estimated_monthly_savings)}/mo</span></div>
                    </div>
                    <div>
                      <div><strong>Projected Avg CPU:</strong> {sc.recommended_configuration?.avg_cpu}%</div>
                      <div><strong>Projected Avg Memory:</strong> {sc.recommended_configuration?.avg_memory}%</div>
                      <div><strong>Projected Latency:</strong> {sc.recommended_configuration?.avg_latency} ms</div>
                    </div>
                  </div>

                  {/* Sensitivity Analysis Dashboard */}
                  <div>
                    <h4 style={{ marginBottom: '10px', color: 'var(--color-cyan-light)' }}>⚡ Assumption Sensitivity Analysis</h4>
                    <div className="grid grid-4 gap-4">
                      {sc.sensitivity_analysis?.map((sens: any) => {
                        const hasChange = sens.trigger_reason !== 'No Change'
                        return (
                          <div key={sens.assumption_shift} style={{
                            padding: '12px',
                            background: 'var(--color-bg-secondary)',
                            borderRadius: 'var(--radius-md)',
                            borderLeft: `3px solid ${hasChange ? 'var(--color-rose)' : 'var(--color-emerald)'}`
                          }}>
                            <div className="text-xs text-muted">{sens.assumption_shift}</div>
                            <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: '4px' }}>{sens.result_recommendation}</div>
                            <div className="text-xs mt-1" style={{ color: hasChange ? 'var(--color-rose)' : 'var(--color-emerald)' }}>
                              {sens.trigger_reason}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
