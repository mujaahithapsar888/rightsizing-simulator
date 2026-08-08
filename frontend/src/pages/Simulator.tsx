import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { simulatorApi } from '../api/simulator'
import { metricsApi } from '../api/metrics'
import CostSavingsChart from '../components/charts/CostSavingsChart'
import { formatCurrency, formatNumber, statusBadgeClass, timeAgo } from '../utils/formatters'
import type { SimulationConfig, SimulationRun } from '../types'
import { useSimulatorStore } from '../store/simulatorStore'

const INSTANCE_PRESETS = [
  { type: 'c5.xlarge',  vcpu: 4,  memory_gb: 8,  cost: 0.17  },
  { type: 'c5.2xlarge', vcpu: 8,  memory_gb: 16, cost: 0.34  },
  { type: 'c5.4xlarge', vcpu: 16, memory_gb: 32, cost: 0.68  },
  { type: 'c5.9xlarge', vcpu: 36, memory_gb: 72, cost: 1.53  },
]

export default function Simulator() {
  const qc = useQueryClient()
  const { config, updateConfig, lastRun, setLastRun } = useSimulatorStore()
  const [activeTab, setActiveTab] = useState<'config' | 'results' | 'history'>('config')

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => metricsApi.list() })
  const { data: runs }     = useQuery({ queryKey: ['simulator-runs'], queryFn: () => simulatorApi.list() })

  const runMutation = useMutation({
    mutationFn: (cfg: SimulationConfig) => simulatorApi.run(cfg),
    onSuccess: (run) => {
      setLastRun(run)
      setActiveTab('results')
      qc.invalidateQueries({ queryKey: ['simulator-runs'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => simulatorApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['simulator-runs'] }),
  })

  const currentPreset = INSTANCE_PRESETS.find((p) => p.type === config.current_instance_type)

  const handleRun = () => {
    if (!config.name || !config.current_instance_type) {
      alert('Please fill in name and select a current instance type.')
      return
    }
    runMutation.mutate({
      name: config.name!,
      description: config.description,
      dataset_id: config.dataset_id,
      current_instance_type: config.current_instance_type!,
      current_vcpu: currentPreset?.vcpu ?? 4,
      current_memory_gb: currentPreset?.memory_gb ?? 8,
      current_cost_per_hour_usd: currentPreset?.cost ?? 0.17,
      target_instance_type: 'c5.xlarge', // API dynamically evaluates all candidates
      target_vcpu: 4,
      target_memory_gb: 8,
      target_cost_per_hour_usd: 0.17,
      max_cpu_threshold_pct: config.max_cpu_threshold_pct ?? 80,
      max_memory_threshold_pct: config.max_memory_threshold_pct ?? 85,
      safety_margin_pct: config.safety_margin_pct ?? 15,
      time_window_hours: config.time_window_hours ?? 168,
      instance_count: config.instance_count ?? 1,
    })
  }

  const res = lastRun?.results as any

  return (
    <div className="animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Multi-Candidate Rightsizing Simulator</h1>
          <p>Cost Optimizer: Evaluates c5 sizes against CPU, Memory, Latency, & Availability constraints</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRun}
          disabled={runMutation.isPending}
          id="run-simulation-btn"
        >
          {runMutation.isPending ? 'Optimizing Fleet...' : '▶ Run Optimization'}
        </button>
      </div>

      <div className="tab-nav mb-6">
        {(['config', 'results', 'history'] as const).map((tab) => (
          <button
            key={tab}
            className={`tab-item ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
            id={`simulator-tab-${tab}`}
          >
            {tab === 'config' ? '⚙ Configuration' : tab === 'results' ? '◈ Optimization Results' : '📋 History'}
          </button>
        ))}
      </div>

      {/* ── CONFIG TAB ──────────────────────────────────────────────────── */}
      {activeTab === 'config' && (
        <div className="grid grid-2 gap-6">
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Simulation Details</h3>
            <div className="flex flex-col gap-4">
              <div className="form-group">
                <label className="form-label" htmlFor="sim-name">Simulation Name *</label>
                <input id="sim-name" className="form-input" placeholder="e.g., Fleet Size Optimizer Run"
                  value={config.name ?? ''} onChange={(e) => updateConfig({ name: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="sim-desc">Description</label>
                <textarea id="sim-desc" className="form-textarea" rows={2} placeholder="SLA requirements: Latency <=250ms, Availability >=99.9%, CPU <=80%, Memory <=85%..."
                  value={config.description ?? ''} onChange={(e) => updateConfig({ description: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="sim-dataset">
                  Metrics Dataset
                  <span className="badge badge-gray" style={{ marginLeft: '8px', fontSize: '0.7rem' }}>Real Data</span>
                </label>
                <select id="sim-dataset" className="form-select"
                  value={config.dataset_id ?? ''}
                  onChange={(e) => updateConfig({ dataset_id: e.target.value || undefined })}>
                  <option value="">None — Use synthetic baseline simulation</option>
                  {datasets?.items.filter((d) => d.status === 'ready').map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="sim-count">Fleet Instance Count</label>
                <input id="sim-count" type="number" min={1} className="form-input"
                  value={config.instance_count ?? 1}
                  onChange={(e) => updateConfig({ instance_count: parseInt(e.target.value) || 1 })} />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="sim-window">Analysis Window (hours)</label>
                <input id="sim-window" type="number" min={1} max={720} className="form-input"
                  value={config.time_window_hours ?? 168}
                  onChange={(e) => updateConfig({ time_window_hours: parseInt(e.target.value) || 168 })} />
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Current Infrastructure Spec</h3>
            <div className="form-group">
              <label className="form-label" htmlFor="sim-current-instance">Instance Type</label>
              <select id="sim-current-instance" className="form-select"
                value={config.current_instance_type ?? ''}
                onChange={(e) => {
                  const p = INSTANCE_PRESETS.find((x) => x.type === e.target.value)
                  updateConfig({
                    current_instance_type: e.target.value,
                    current_vcpu: p?.vcpu,
                    current_memory_gb: p?.memory_gb,
                    current_cost_per_hour_usd: p?.cost
                  })
                }}>
                <option value="">Select current instance type...</option>
                {INSTANCE_PRESETS.map((p) => (
                  <option key={p.type} value={p.type}>{p.type} — {p.vcpu} vCPU / {p.memory_gb} GB — ${p.cost}/hr</option>
                ))}
              </select>
              {currentPreset && (
                <div className="flex gap-2 mt-2">
                  <span className="badge badge-indigo">{currentPreset.vcpu} vCPUs</span>
                  <span className="badge badge-cyan">{currentPreset.memory_gb} GB Memory</span>
                  <span className="badge badge-amber">${currentPreset.cost}/hour</span>
                </div>
              )}
            </div>
            
            <div className="divider" style={{ margin: '24px 0' }} />
            
            <div style={{ padding: '16px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <h4 style={{ marginBottom: '10px', color: 'var(--color-cyan-light)' }}>SLA Constraints Mandate</h4>
              <ul className="text-sm" style={{ paddingLeft: '20px', lineHeight: '1.6', margin: 0 }}>
                <li>Latency limit: <strong>&le; 250 ms</strong></li>
                <li>Availability limit: <strong>&ge; 99.9%</strong></li>
                <li>CPU target utilization: <strong>&le; 80%</strong></li>
                <li>Memory target utilization: <strong>&le; 85%</strong></li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ── RESULTS TAB ─────────────────────────────────────────────────── */}
      {activeTab === 'results' && (
        <>
          {!lastRun ? (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">◈</div>
                <div className="empty-state-title">No optimization results yet</div>
                <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('config')}>← Configure</button>
              </div>
            </div>
          ) : (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Verdict Indicator */}
              <div className="card" style={{ borderLeft: '6px solid var(--color-indigo)' }}>
                <h3 style={{ margin: 0 }}>Recommended Target Instance: <span style={{ color: 'var(--color-indigo-light)' }}>{res?.recommended_configuration?.instance_type}</span></h3>
                <p className="text-sm text-secondary mt-2" style={{ margin: 0, lineHeight: '1.6' }}>
                  <strong>Selection Logic:</strong> {res?.reasoning}
                </p>
                {res?.estimated_monthly_savings !== 0 && (
                  <div style={{ marginTop: '14px', fontSize: '1.1rem', fontWeight: 700, color: res?.estimated_monthly_savings > 0 ? 'var(--color-emerald)' : 'var(--color-rose)' }}>
                    {res?.estimated_monthly_savings > 0 
                      ? `Estimated Fleet Cost Savings: +${formatCurrency(res.estimated_monthly_savings)}/month`
                      : `SLA Safety Buffer Penalty Cost: ${formatCurrency(res.estimated_monthly_savings)}/month`
                    }
                  </div>
                )}
              </div>

              {/* Candidate Comparison Matrix */}
              <div className="card">
                <h3 style={{ marginBottom: '16px' }}>Candidate Evaluation Matrix</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Instance size</th>
                        <th>CPU % (Max 80)</th>
                        <th>Memory % (Max 85)</th>
                        <th>Latency (Max 250ms)</th>
                        <th>Availability (Min 99.9%)</th>
                        <th>Cost/mo</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {res?.candidates?.map((cand: any) => (
                        <tr key={cand.instance_type} style={{
                          background: cand.instance_type === res?.recommended_configuration?.instance_type ? 'rgba(99,102,241,0.06)' : undefined,
                          border: cand.instance_type === res?.recommended_configuration?.instance_type ? '1.5px solid var(--color-indigo)' : undefined
                        }}>
                          <td><strong>{cand.instance_type}</strong></td>
                          <td style={{ color: cand.avg_cpu > 80 ? 'var(--color-rose)' : 'inherit' }}>{cand.avg_cpu}%</td>
                          <td style={{ color: cand.avg_memory > 85 ? 'var(--color-rose)' : 'inherit' }}>{cand.avg_memory}%</td>
                          <td style={{ color: cand.avg_latency > 250 ? 'var(--color-rose)' : 'inherit' }}>{cand.avg_latency} ms</td>
                          <td style={{ color: cand.availability < 99.9 ? 'var(--color-rose)' : 'inherit' }}>{cand.availability}%</td>
                          <td><strong>{formatCurrency(cand.monthly_cost)}</strong></td>
                          <td>
                            {cand.is_valid ? (
                              <span className="badge badge-emerald">Valid</span>
                            ) : (
                              <span className="badge badge-rose" title={cand.failed_constraints?.join(', ')}>
                                Violated
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Comparison Charts */}
              <div className="grid grid-2 gap-6">
                <div className="card">
                  <h3>Candidate Cost Comparison</h3>
                  <CostSavingsChart data={{
                    labels: res?.candidates?.map((c: any) => c.instance_type) || [],
                    values: res?.candidates?.map((c: any) => c.monthly_cost) || []
                  }} />
                </div>
                <div className="card">
                  <h3>SLA Constraints Metrics</h3>
                  <div style={{ overflowX: 'auto', display: 'flex', flexDirection: 'column', gap: '14px', paddingTop: '10px' }}>
                    {res?.candidates?.map((c: any) => (
                      <div key={c.instance_type} style={{ opacity: c.is_valid ? 1 : 0.5 }}>
                        <div className="flex justify-between text-xs mb-1">
                          <strong>{c.instance_type}</strong>
                          <span>CPU: {c.avg_cpu}% | Latency: {c.avg_latency}ms</span>
                        </div>
                        <div style={{ height: '6px', background: 'var(--color-border)', borderRadius: '3px', position: 'relative' }}>
                          <div style={{
                            width: `${Math.min(100, c.avg_cpu)}%`,
                            height: '100%',
                            background: c.avg_cpu > 80 ? 'var(--color-rose)' : 'var(--color-emerald)',
                            borderRadius: '3px'
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          )}
        </>
      )}

      {/* ── HISTORY TAB ─────────────────────────────────────────────────── */}
      {activeTab === 'history' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3>Simulation History</h3>
            <span className="badge badge-gray">{runs?.total ?? 0} runs</span>
          </div>
          {(runs?.items.length ?? 0) === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-title">No history yet</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Simulation Name</th>
                    <th>Current Specs</th>
                    <th>Recommended Target</th>
                    <th>Estimated Savings</th>
                    <th>Status</th>
                    <th>Evaluated</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {runs?.items.map((run) => {
                    const r = run.results as any
                    return (
                      <tr key={run.id}>
                        <td className="font-semibold">{run.name}</td>
                        <td>{r?.current_configuration?.instance_type}</td>
                        <td>{r?.recommended_configuration?.instance_type}</td>
                        <td style={{ color: r?.estimated_monthly_savings > 0 ? 'var(--color-emerald)' : 'inherit', fontWeight: 600 }}>
                          {formatCurrency(r?.estimated_monthly_savings)}
                        </td>
                        <td><span className={`badge ${statusBadgeClass(run.status)}`}>{run.status}</span></td>
                        <td className="text-muted text-xs">{timeAgo(run.created_at)}</td>
                        <td>
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => { setLastRun(run); setActiveTab('results') }}>
                            View
                          </button>
                          <button
                            className="btn btn-ghost btn-sm"
                            style={{ color: 'var(--color-rose)', marginLeft: '4px' }}
                            onClick={() => confirm('Delete?') && deleteMutation.mutate(run.id)}
                          >×</button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
