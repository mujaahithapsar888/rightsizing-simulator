import { useCallback, useDeferredValue, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { metricsApi } from '../api/metrics'
import { modelsApi } from '../api/models'
import {
  formatBytes,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercent,
  statusBadgeClass,
  timeAgo,
} from '../utils/formatters'
import type { MetricDataset, ValidationReport } from '../types'

const REQUIRED_COLUMNS = [
  { col: 'timestamp',          alias: null,             note: 'ISO-8601, UTC' },
  { col: 'cpu_utilization',    alias: null,             note: '0–100 %' },
  { col: 'memory_utilization', alias: null,             note: '0–100 %' },
  { col: 'latency',            alias: 'latency_ms',     note: 'milliseconds' },
  { col: 'request_volume',     alias: null,             note: 'requests per period' },
  { col: 'instance_count',     alias: null,             note: 'integer ≥ 1' },
  { col: 'instance_type',      alias: null,             note: 'e.g. c5.xlarge' },
  { col: 'instance_price',     alias: null,             note: 'USD/hour' },
  { col: 'availability',       alias: null,             note: '0–100 %' },
  { col: 'error_rate',         alias: 'error_rate_pct', note: '0–100 %' },
]

function StatCard({
  label, value, unit, color, icon,
}: { label: string; value: string | number | null; unit?: string; color: string; icon: string }) {
  return (
    <div className="kpi-card" style={{ flex: 1 }}>
      <div className="flex items-center gap-2 mb-1">
        <span style={{ fontSize: '1.1rem' }}>{icon}</span>
        <div className="kpi-label">{label}</div>
      </div>
      {value === null || value === undefined ? (
        <div className="kpi-value" style={{ fontSize: '1.3rem', color: 'var(--color-text-muted)', background: 'none', WebkitTextFillColor: 'var(--color-text-muted)' }}>—</div>
      ) : (
        <div className="kpi-value" style={{ fontSize: '1.3rem', color, background: 'none', WebkitTextFillColor: color }}>
          {value}{unit && <span style={{ fontSize: '0.75rem', fontWeight: 400, marginLeft: '2px', color: 'var(--color-text-muted)' }}>{unit}</span>}
        </div>
      )}
    </div>
  )
}

function ValidationPanel({ report }: { report: ValidationReport }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div
      style={{
        marginTop: '16px',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 14px',
          background: 'var(--color-bg-secondary)',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--color-text-primary)',
          fontWeight: 600,
          fontSize: '0.875rem',
        }}
      >
        <div className="flex items-center gap-2">
          <span>📋</span> Validation Report
          <span className="badge badge-indigo">{formatNumber(report.raw_rows)} raw rows</span>
          <span className="badge badge-emerald">{formatNumber(report.final_rows)} imported</span>
          {report.duplicates_removed > 0 && (
            <span className="badge badge-amber">{formatNumber(report.duplicates_removed)} dupes removed</span>
          )}
        </div>
        <span style={{ color: 'var(--color-text-muted)' }}>{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div style={{ padding: '14px' }}>
          {report.warnings.length > 0 && (
            <div
              style={{
                marginBottom: '12px',
                background: 'rgba(245, 158, 11, 0.08)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 12px',
              }}
            >
              {report.warnings.map((w, i) => (
                <div key={i} className="text-sm" style={{ color: 'var(--color-amber)', marginBottom: '4px' }}>
                  ⚠ {w}
                </div>
              ))}
            </div>
          )}

          <table className="data-table">
            <thead>
              <tr>
                <th>Column</th>
                <th>Required</th>
                <th>Present</th>
                <th>Missing Values</th>
                <th>Missing %</th>
              </tr>
            </thead>
            <tbody>
              {report.columns.map((col) => (
                <tr key={col.column}>
                  <td>
                    <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--color-indigo-light)' }}>
                      {col.column}
                    </code>
                  </td>
                  <td>
                    <span className={`badge ${col.required ? 'badge-rose' : 'badge-gray'}`}>
                      {col.required ? 'Required' : 'Optional'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${col.present ? 'badge-emerald' : 'badge-rose'}`}>
                      {col.present ? '✓ Yes' : '✕ Missing'}
                    </span>
                  </td>
                  <td>{col.present ? formatNumber(col.missing_count) : '—'}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div
                        style={{
                          width: '60px',
                          height: '4px',
                          borderRadius: '2px',
                          background: 'var(--color-border)',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.min(col.missing_pct, 100)}%`,
                            height: '100%',
                            background: col.missing_pct > 50
                              ? 'var(--color-rose)'
                              : col.missing_pct > 10
                                ? 'var(--color-amber)'
                                : 'var(--color-emerald)',
                          }}
                        />
                      </div>
                      <span className="text-xs">{formatPercent(col.missing_pct)}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function RecordsTable({ dataset }: { dataset: MetricDataset }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const limit = 50
  const deferredSearch = useDeferredValue(search)

  const { data, isLoading } = useQuery({
    queryKey: ['records', dataset.id, page, deferredSearch],
    queryFn: () => metricsApi.records(dataset.id, page * limit, limit, deferredSearch || undefined),
    enabled: dataset.status === 'ready',
  })

  const totalPages = Math.ceil((data?.total ?? 0) / limit)

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <input
            id="records-search"
            className="form-input"
            style={{ width: '220px', padding: '6px 12px' }}
            placeholder="Search instance type…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0) }}
          />
          <span className="text-xs text-muted">
            {formatNumber(data?.total ?? 0)} records
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn btn-ghost btn-sm"
            disabled={page === 0}
            onClick={() => setPage(p => p - 1)}
          >← Prev</button>
          <span className="text-xs text-muted">
            Page {page + 1} / {Math.max(totalPages, 1)}
          </span>
          <button
            className="btn btn-ghost btn-sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage(p => p + 1)}
          >Next →</button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center" style={{ padding: '32px' }}>
          <div className="spinner" />
        </div>
      ) : (data?.items.length ?? 0) === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-title">No records match</div>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table" style={{ fontSize: '0.8rem' }}>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Instance Type</th>
                <th>CPU %</th>
                <th>Memory %</th>
                <th>Latency (ms)</th>
                <th>Req Volume</th>
                <th>Error %</th>
                <th>Availability</th>
                <th># Instances</th>
                <th>Price/hr</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((rec) => (
                <tr key={rec.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                    {formatDateTime(rec.timestamp)}
                  </td>
                  <td>
                    <span className="badge badge-indigo" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                      {rec.instance_type ?? '—'}
                    </span>
                  </td>
                  <td>{rec.cpu_utilization?.toFixed(1) ?? '—'}%</td>
                  <td>{rec.memory_utilization?.toFixed(1) ?? '—'}%</td>
                  <td>{rec.latency_ms?.toFixed(1) ?? '—'} ms</td>
                  <td>{rec.request_volume != null ? formatNumber(rec.request_volume) : '—'}</td>
                  <td>{rec.error_rate_pct?.toFixed(2) ?? '—'}%</td>
                  <td>{rec.availability?.toFixed(2) ?? '—'}%</td>
                  <td>{rec.instance_count ?? '—'}</td>
                  <td>{rec.instance_price != null ? `$${rec.instance_price.toFixed(3)}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function UploadData() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<{
    message: string
    report: ValidationReport
  } | null>(null)
  const [selectedDataset, setSelectedDataset] = useState<MetricDataset | null>(null)
  const [activeView, setActiveView] = useState<'upload' | 'data'>('upload')

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => metricsApi.list(),
  })

  const { data: modelStatus, refetch: refetchModelStatus } = useQuery({
    queryKey: ['model-status', selectedDataset?.id],
    queryFn: () => modelsApi.status(selectedDataset!.id),
    enabled: !!selectedDataset,
  })

  const trainMutation = useMutation({
    mutationFn: (datasetId: string) => modelsApi.train(datasetId),
    onSuccess: () => {
      refetchModelStatus()
      alert('✓ Random Forest models trained successfully!')
    },
    onError: (err: any) => {
      alert(`Training failed: ${err?.response?.data?.detail || err.message}`)
    }
  })

  const uploadMutation = useMutation({
    mutationFn: () => metricsApi.upload(file!, name, description || undefined),
    onSuccess: (data) => {
      setUploadResult({ message: data.message, report: data.validation_report })
      setFile(null)
      setName('')
      setDescription('')
      qc.invalidateQueries({ queryKey: ['datasets'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => metricsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['datasets'] })
      if (selectedDataset && selectedDataset.id === deleteMutation.variables) {
        setSelectedDataset(null)
      }
    },
  })

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) {
        setFile(accepted[0])
        setUploadResult(null)
        if (!name) setName(accepted[0].name.replace(/\.[^.]+$/, ''))
      }
    },
    [name],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/octet-stream': ['.parquet'] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  })

  const openDataset = (ds: MetricDataset) => {
    setSelectedDataset(ds)
    setActiveView('data')
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Historical Monitoring Data</h1>
          <p>Import, validate, and train predictive models on cloud metrics</p>
        </div>
        <div className="tab-nav">
          <button
            className={`tab-item ${activeView === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveView('upload')}
          >
            ↑ Upload
          </button>
          <button
            className={`tab-item ${activeView === 'data' ? 'active' : ''}`}
            onClick={() => setActiveView('data')}
          >
            📋 Datasets {datasets?.total ? `(${datasets.total})` : ''}
          </button>
        </div>
      </div>

      {activeView === 'upload' && (
        <div className="animate-fade-in">
          <div className="grid grid-2 gap-6 mb-6">
            <div className="card">
              <h3 style={{ marginBottom: '20px' }}>Import Dataset</h3>

              {uploadResult && (
                <div
                  style={{
                    background: 'rgba(16, 185, 129, 0.08)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: 'var(--radius-md)',
                    padding: '10px 14px',
                    fontSize: '0.875rem',
                    color: 'var(--color-emerald-light)',
                    marginBottom: '16px',
                  }}
                >
                  {uploadResult.message}
                </div>
              )}

              {uploadMutation.isError && (
                <div className="login-error" style={{ marginBottom: '16px' }}>
                  {(uploadMutation.error as any)?.response?.data?.detail ?? 'Upload failed. Check file format.'}
                </div>
              )}

              <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
                style={{ marginBottom: '20px' }}
              >
                <input {...getInputProps()} />
                {file ? (
                  <div>
                    <div className="dropzone-icon" style={{ color: 'var(--color-emerald-light)' }}>✓</div>
                    <div className="dropzone-title">{file.name}</div>
                    <div className="dropzone-hint">{formatBytes(file.size)}</div>
                  </div>
                ) : (
                  <div>
                    <div className="dropzone-icon">↑</div>
                    <div className="dropzone-title">
                      {isDragActive ? 'Drop file here…' : 'Drag & drop CSV or Parquet file'}
                    </div>
                    <div className="dropzone-hint">or click to browse · Max 50 MB</div>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-4">
                <div className="form-group">
                  <label className="form-label" htmlFor="dataset-name">Dataset Name *</label>
                  <input
                    id="dataset-name"
                    className="form-input"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="dataset-desc">Description</label>
                  <textarea
                    id="dataset-desc"
                    className="form-textarea"
                    rows={2}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <button
                  className="btn btn-primary"
                  disabled={!file || !name || uploadMutation.isPending}
                  onClick={() => uploadMutation.mutate()}
                >
                  {uploadMutation.isPending ? 'Processing & Storing…' : '↑ Upload & Process Dataset'}
                </button>
              </div>

              {uploadResult?.report && (
                <ValidationPanel report={uploadResult.report} />
              )}
            </div>

            <div className="card">
              <h3 style={{ marginBottom: '16px' }}>Required CSV Columns</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {REQUIRED_COLUMNS.map((c) => (
                  <div
                    key={c.col}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '7px 10px',
                      background: 'var(--color-bg-secondary)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-border)',
                    }}
                  >
                    <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--color-indigo-light)' }}>
                      {c.col}
                    </code>
                    <span className="text-xs text-muted">{c.note}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeView === 'data' && (
        <div className="animate-fade-in">
          <div className="card mb-6">
            <h3>All Datasets</h3>
            <div style={{ overflowX: 'auto', marginTop: '14px' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Rows</th>
                    <th>Avg CPU</th>
                    <th>Avg Memory</th>
                    <th>Avg Latency</th>
                    <th>Date Range</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets?.items.map((d) => (
                    <tr
                      key={d.id}
                      style={{ cursor: 'pointer', background: selectedDataset?.id === d.id ? 'rgba(99,102,241,0.06)' : undefined }}
                      onClick={() => openDataset(d)}
                    >
                      <td style={{ fontWeight: 600 }}>{d.name}</td>
                      <td>{formatNumber(d.row_count)}</td>
                      <td>{d.avg_cpu_utilization != null ? `${d.avg_cpu_utilization.toFixed(1)}%` : '—'}</td>
                      <td>{d.avg_memory_utilization != null ? `${d.avg_memory_utilization.toFixed(1)}%` : '—'}</td>
                      <td>{d.avg_latency_ms != null ? `${d.avg_latency_ms.toFixed(0)} ms` : '—'}</td>
                      <td className="text-xs text-muted">
                        {d.ts_min ? formatDate(d.ts_min) : '—'}
                        {d.ts_max && d.ts_min ? <> → {formatDate(d.ts_max)}</> : ''}
                      </td>
                      <td><span className={`badge ${statusBadgeClass(d.status)}`}>{d.status}</span></td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <button className="btn btn-ghost btn-sm" onClick={() => openDataset(d)}>Explore</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {selectedDataset && (
            <div className="animate-slide-up">
              {/* ML Model Training Section */}
              <div className="card mb-6" style={{ border: '1px solid var(--color-indigo)' }}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 style={{ margin: 0 }}>🧠 Random Forest Prediction Models</h3>
                    <p className="text-sm text-muted mt-1" style={{ margin: 0 }}>
                      Train Scikit-Learn regressors (80% training / 20% test split) to predict performance metrics on downsizing.
                    </p>
                  </div>
                  <button
                    className="btn btn-primary"
                    disabled={trainMutation.isPending}
                    onClick={() => trainMutation.mutate(selectedDataset.id)}
                  >
                    {trainMutation.isPending ? 'Training Regressors...' : '⚙ Train/Retrain Models'}
                  </button>
                </div>

                {modelStatus?.is_trained && modelStatus?.metrics && (
                  <div style={{ marginTop: '20px' }}>
                    <div className="text-xs font-bold text-indigo-light mb-3">MODEL EVALUATION METRICS (TEST SPLIT)</div>
                    <div className="grid grid-4 gap-4">
                      {Object.entries(modelStatus.metrics).map(([metricName, scores]: [string, any]) => (
                        <div key={metricName} style={{ padding: '12px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                          <div className="text-sm font-semibold capitalize">{metricName.replace('_', ' ')}</div>
                          <div className="text-xs mt-2">
                            <div><strong>MAE:</strong> {scores.mae}</div>
                            <div><strong>RMSE:</strong> {scores.rmse}</div>
                            <div><strong>R² Score:</strong> {scores.r2_score}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="card">
                <h4 style={{ marginBottom: '14px' }}>Raw Records Explorer</h4>
                <RecordsTable dataset={selectedDataset} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
