import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { reportsApi } from '../api/reports'
import { simulatorApi } from '../api/simulator'
import { experimentsApi } from '../api/experiments'
import { formatCurrency, formatDateTime, formatPercent, statusBadgeClass, timeAgo } from '../utils/formatters'
import type { ReportCreate } from '../types'

const REPORT_TYPES = [
  { value: 'simulation_summary', label: 'Simulation Summary' },
  { value: 'experiment_comparison', label: 'Experiment Comparison' },
  { value: 'cost_analysis', label: 'Fleet Cost Analysis' },
  { value: 'performance_impact', label: 'Performance & Risk Impact' },
] as const

const INSTANCE_PRESETS = [
  { type: 'c5.xlarge',  vcpu: 4,  memory_gb: 8,   cost: 0.170 },
  { type: 'c5.2xlarge', vcpu: 8,  memory_gb: 16,  cost: 0.340 },
  { type: 'c5.4xlarge', vcpu: 16, memory_gb: 32,  cost: 0.680 },
  { type: 'c5.9xlarge', vcpu: 36, memory_gb: 72,  cost: 1.530 },
]

export default function Reports() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [showBenchmarkCreate, setShowBenchmarkCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [reportType, setReportType] = useState<ReportCreate['report_type']>('simulation_summary')
  const [simId, setSimId] = useState('')
  const [expId, setExpId] = useState('')
  const [selectedReport, setSelectedReport] = useState<string | null>(null)

  // Benchmarking State
  const [benchmarkInstance, setBenchmarkInstance] = useState('c5.4xlarge')

  const { data: reports } = useQuery({ queryKey: ['reports'], queryFn: () => reportsApi.list() })
  const { data: runs } = useQuery({ queryKey: ['simulator-runs'], queryFn: () => simulatorApi.list() })
  const { data: experiments } = useQuery({ queryKey: ['experiments'], queryFn: () => experimentsApi.list() })

  const { data: selectedReportData } = useQuery({
    queryKey: ['report', selectedReport],
    queryFn: () => reportsApi.get(selectedReport!),
    enabled: !!selectedReport,
  })

  const generateMutation = useMutation({
    mutationFn: (payload: ReportCreate) => reportsApi.generate(payload),
    onSuccess: (report) => {
      qc.invalidateQueries({ queryKey: ['reports'] })
      setSelectedReport(report.id)
      setShowCreate(false)
      setTitle('')
    },
  })

  const benchmarkMutation = useMutation({
    mutationFn: (payload: any) => reportsApi.benchmark(payload),
    onSuccess: (report) => {
      qc.invalidateQueries({ queryKey: ['reports'] })
      setSelectedReport(report.id)
      setShowBenchmarkCreate(false)
      setTitle('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reports'] })
      setSelectedReport(null)
    },
  })

  const handleGenerate = () => {
    if (!title) { alert('Please provide a report title'); return }
    generateMutation.mutate({
      title,
      report_type: reportType,
      simulation_id: simId || undefined,
      experiment_id: expId || undefined,
    })
  }

  const handleBenchmark = () => {
    if (!title) { alert('Please provide a benchmark report title'); return }
    benchmarkMutation.mutate({
      title,
      current_instance_type: benchmarkInstance
    })
  }

  const handleDownloadJSON = (report: any) => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.title.replace(/\s+/g, '-')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const renderReportContent = (r: any) => {
    if (!r || !r.content) return null
    const c = r.content

    // Render Benchmark Performance Table & Charts
    if (c.benchmarks) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ padding: '16px', background: 'var(--color-bg-secondary)', borderLeft: '4px solid var(--color-indigo)', borderRadius: 'var(--radius-md)' }}>
            <strong>Benchmarking Suite Evaluation:</strong> This performance report compares the <strong>Baseline Decision Engine</strong> against the <strong>Optimized Multi-Candidate Rightsizing Simulator</strong> under extreme adversarial boundary conditions.
          </div>

          <div className="card" style={{ background: 'var(--color-bg-secondary)', margin: 0 }}>
            <h4 style={{ marginBottom: '14px' }}>Performance & SLA Error Matrix</h4>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Edge Case</th>
                    <th>Engine</th>
                    <th>Instance size</th>
                    <th>Cost/mo</th>
                    <th>CPU %</th>
                    <th>Memory %</th>
                    <th>Latency</th>
                    <th>Availability</th>
                    <th>Cost Impr. %</th>
                  </tr>
                </thead>
                <tbody>
                  {c.benchmarks.map((b: any) => (
                    <>
                      <tr key={`${b.edge_case_key}-base`} style={{ borderBottom: 'none' }}>
                        <td rowSpan={2}><strong>{b.edge_case_name}</strong></td>
                        <td>Baseline</td>
                        <td>{b.baseline.instance_type}</td>
                        <td>{formatCurrency(b.baseline.monthly_cost)}</td>
                        <td>{b.baseline.avg_cpu}%</td>
                        <td>{b.baseline.avg_memory}%</td>
                        <td>{b.baseline.avg_latency} ms</td>
                        <td>{b.baseline.availability}%</td>
                        <td rowSpan={2} style={{ color: 'var(--color-emerald)', fontWeight: 700, verticalAlign: 'middle', textAlign: 'center' }}>
                          +{b.improvements.monthly_cost_percent}%
                        </td>
                      </tr>
                      <tr key={`${b.edge_case_key}-opt`} style={{ background: 'rgba(99,102,241,0.04)' }}>
                        <td><strong>Optimized</strong></td>
                        <td><strong>{b.optimized.instance_type}</strong></td>
                        <td><strong>{formatCurrency(b.optimized.monthly_cost)}</strong></td>
                        <td><strong>{b.optimized.avg_cpu}%</strong></td>
                        <td><strong>{b.optimized.avg_memory}%</strong></td>
                        <td><strong>{b.optimized.avg_latency} ms</strong></td>
                        <td><strong>{b.optimized.availability}%</strong></td>
                      </tr>
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Performance Improvement summary */}
          <div className="card" style={{ background: 'var(--color-bg-secondary)', margin: 0 }}>
            <h4 style={{ marginBottom: '10px' }}>Bottleneck Improvement & Error Reduction</h4>
            <div className="grid grid-3 gap-4 text-sm">
              {c.benchmarks.map((b: any) => (
                <div key={b.edge_case_key} style={{ padding: '10px', background: 'var(--color-bg-card)', borderRadius: 'var(--radius-sm)' }}>
                  <strong>{b.edge_case_name}</strong>
                  <div className="mt-2 text-xs">
                    <div>Latency reduction: <span style={{ color: 'var(--color-emerald)' }}>{b.improvements.latency_percent}%</span></div>
                    <div>Availability SLA Risk drop: <span style={{ color: 'var(--color-emerald)' }}>{b.improvements.availability_error_reduction_percent}%</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {c.executive_summary && (
          <div style={{
            padding: '16px',
            background: 'var(--color-bg-secondary)',
            borderLeft: '4px solid var(--color-indigo)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.9rem',
            lineHeight: '1.6',
            color: 'var(--color-text-secondary)'
          }}>
            <strong>Executive Summary:</strong> {c.executive_summary}
          </div>
        )}

        {r.report_type === 'simulation_summary' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="grid grid-2 gap-4">
              <div className="card" style={{ background: 'var(--color-bg-secondary)', margin: 0 }}>
                <h4 style={{ marginBottom: '10px' }}>Configuration</h4>
                <div className="text-sm">
                  <div><strong>Current:</strong> {c.configuration?.current_instance} (×{c.configuration?.instance_count})</div>
                  <div><strong>Target:</strong> {c.configuration?.target_instance}</div>
                  <div><strong>Analysis Window:</strong> {c.configuration?.time_window_hours} hours</div>
                  <div><strong>Safety Margin:</strong> {c.configuration?.safety_margin_pct}%</div>
                </div>
              </div>
              <div className="card" style={{ background: 'var(--color-bg-secondary)', margin: 0 }}>
                <h4 style={{ marginBottom: '10px' }}>Cost Profile</h4>
                <div className="text-sm">
                  <div><strong>Monthly Savings:</strong> <span style={{ color: 'var(--color-emerald)' }}>{c.cost_analysis?.monthly_savings_fmt}</span></div>
                  <div><strong>Annual Savings:</strong> <span style={{ color: 'var(--color-cyan-light)' }}>{c.cost_analysis?.annual_savings_fmt}</span></div>
                  <div><strong>Reduction:</strong> {c.cost_analysis?.savings_pct}%</div>
                  <div><strong>ROI:</strong> {c.cost_analysis?.roi_months} months</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Reports & Automated Benchmarking</h1>
          <p>Generate reports and run boundary comparison tests between Baseline and Optimized simulators</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary" onClick={() => setShowBenchmarkCreate(!showBenchmarkCreate)}>
            {showBenchmarkCreate ? '✕ Cancel' : '⚡ Run Benchmark Test'}
          </button>
          <button className="btn btn-primary" id="generate-report-btn" onClick={() => setShowCreate(!showCreate)}>
            {showCreate ? '✕ Cancel' : '📊 Generate Report'}
          </button>
        </div>
      </div>

      {/* Benchmark Creation Form */}
      {showBenchmarkCreate && (
        <div className="card mb-6 animate-slide-up">
          <h3 style={{ marginBottom: '20px' }}>Configure Benchmark Evaluation</h3>
          <div className="grid grid-2 gap-4 mb-4">
            <div className="form-group">
              <label className="form-label">Benchmark Report Title *</label>
              <input className="form-input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Q3 SLA Engine Benchmark" />
            </div>
            <div className="form-group">
              <label className="form-label">Current Fleet Instance Size</label>
              <select className="form-select" value={benchmarkInstance} onChange={(e) => setBenchmarkInstance(e.target.value)}>
                {INSTANCE_PRESETS.map(p => <option key={p.type} value={p.type}>{p.type}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <button className="btn btn-ghost" onClick={() => setShowBenchmarkCreate(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleBenchmark} disabled={benchmarkMutation.isPending}>
              {benchmarkMutation.isPending ? 'Executing benchmarks...' : '▶ Execute Benchmarks'}
            </button>
          </div>
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <div className="card mb-6 animate-slide-up">
          <h3 style={{ marginBottom: '20px' }}>Generate New Report</h3>
          <div className="grid grid-2 gap-4 mb-4">
            <div className="form-group">
              <label className="form-label" htmlFor="report-title">Report Title *</label>
              <input
                id="report-title"
                className="form-input"
                placeholder="e.g., Q3 2026 Fleet Rightsizing Analysis"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="report-type">Report Type</label>
              <select
                id="report-type"
                className="form-select"
                value={reportType}
                onChange={(e) => setReportType(e.target.value as ReportCreate['report_type'])}
              >
                {REPORT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <button className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={generateMutation.isPending}
            >
              {generateMutation.isPending ? 'Generating…' : '📊 Generate'}
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px' }}>
        {/* Report List (Sidebar) */}
        <div style={{ width: '260px', flexShrink: 0 }}>
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h4>All Reports</h4>
              <span className="badge badge-gray">{reports?.total ?? 0}</span>
            </div>
            <div className="flex flex-col gap-2">
              {reports?.items.map((r) => (
                <div
                  key={r.id}
                  onClick={() => setSelectedReport(r.id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${selectedReport === r.id ? 'var(--color-indigo)' : 'var(--color-border)'}`,
                    background: selectedReport === r.id ? 'rgba(99,102,241,0.08)' : 'var(--color-bg-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  <div className="text-sm font-semibold mb-1" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.title}
                  </div>
                  <div className="text-xs text-muted">{timeAgo(r.created_at)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Report Detail Panel */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedReportData ? (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">📊</div>
                <div className="empty-state-title">Select a report</div>
              </div>
            </div>
          ) : (
            <div className="animate-fade-in">
              <div className="card mb-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3>{selectedReportData.title}</h3>
                    <div className="text-xs text-muted mt-1">Generated {timeAgo(selectedReportData.created_at)}</div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="btn btn-ghost btn-sm"
                      style={{ color: 'var(--color-rose)' }}
                      onClick={() => confirm('Delete report?') && deleteMutation.mutate(selectedReportData.id)}
                    >
                      Delete
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleDownloadJSON(selectedReportData)}
                    >
                      Download JSON
                    </button>
                  </div>
                </div>

                <div className="divider" />

                {renderReportContent(selectedReportData)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
