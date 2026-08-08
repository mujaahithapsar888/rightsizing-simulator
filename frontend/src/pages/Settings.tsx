import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { eventRecoveryApi } from '../api/eventRecovery'
import { formatDateTime } from '../utils/formatters'

export default function Settings() {
  const [email, setEmail] = useState('admin@example.com')
  const [theme] = useState('dark')
  const [refreshInterval, setRefreshInterval] = useState('300')
  const [maxSimulations, setMaxSimulations] = useState('100')
  const [saved, setSaved] = useState(false)

  // Event Recovery State
  const [recoveryResult, setRecoveryResult] = useState<any>(null)

  const recoveryMutation = useMutation({
    mutationFn: () => eventRecoveryApi.simulate(),
    onSuccess: (data) => {
      setRecoveryResult(data)
    },
    onError: (err) => {
      alert(`Simulation failed: ${err.message}`)
    }
  })

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>Settings & event verification</h1>
        <p>Preferences, System Configuration, and Event Ingestion Stream Recovery validation</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Event Ingestion processing validator card */}
        <div className="card" style={{ border: '1px solid var(--color-indigo)' }}>
          <div className="flex items-center justify-between">
            <div>
              <h3 style={{ margin: 0 }}>📡 Event Processing Simulator & State Recovery Validator</h3>
              <p className="text-sm text-secondary mt-1" style={{ margin: 0 }}>
                Injects out-of-order, duplicate, and delayed telemetry events, and runs recovery pipeline.
              </p>
            </div>
            <button
              className="btn btn-primary"
              disabled={recoveryMutation.isPending}
              onClick={() => recoveryMutation.mutate()}
            >
              {recoveryMutation.isPending ? 'Replaying Stream...' : '▶ Run Ingestion Test'}
            </button>
          </div>

          {recoveryResult && (
            <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="flex justify-between items-center" style={{ padding: '12px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <strong>Recovery Test Result:</strong>
                  <span className={`badge ${recoveryResult.test_status === 'PASS' ? 'badge-emerald' : 'badge-rose'}`} style={{ marginLeft: '10px', fontSize: '1rem', padding: '6px 12px' }}>
                    {recoveryResult.test_status}
                  </span>
                </div>
                <div className="text-xs text-muted">
                  Deduplicated & Ordered <strong>{recoveryResult.metrics?.final_count}</strong> events
                </div>
              </div>

              {/* Validation detail metrics */}
              <div className="grid grid-4 gap-4">
                <div style={{ padding: '10px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <div className="text-xs text-muted">Duplicates Rejected</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-cyan-light)', marginTop: '4px' }}>{recoveryResult.validation?.duplicates_rejected}</div>
                </div>
                <div style={{ padding: '10px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <div className="text-xs text-muted">Count match</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-emerald)', marginTop: '4px' }}>{recoveryResult.validation?.count_match ? 'PASS' : 'FAIL'}</div>
                </div>
                <div style={{ padding: '10px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <div className="text-xs text-muted">CPU State Integrity</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-emerald)', marginTop: '4px' }}>{recoveryResult.validation?.cpu_state_correct ? 'PASS' : 'FAIL'}</div>
                </div>
                <div style={{ padding: '10px', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <div className="text-xs text-muted">Memory State Integrity</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-emerald)', marginTop: '4px' }}>{recoveryResult.validation?.memory_state_correct ? 'PASS' : 'FAIL'}</div>
                </div>
              </div>

              {/* Event Timeline Before vs After Recovery */}
              <div className="grid grid-2 gap-6">
                <div>
                  <h4 style={{ marginBottom: '10px', color: 'var(--color-rose)' }}>Adversarial Stream (Before Recovery)</h4>
                  <div style={{ maxHeight: '200px', overflowY: 'auto', background: 'var(--color-bg-secondary)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
                    {recoveryResult.timeline_before?.map((e: any, idx: number) => (
                      <div key={idx} className="text-xs flex justify-between" style={{ padding: '4px 0', borderBottom: '1px solid var(--color-border)' }}>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>{e.event_id}</span>
                        <span className="text-muted">{new Date(e.timestamp).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 style={{ marginBottom: '10px', color: 'var(--color-emerald)' }}>Recovered Timeline (After Recovery)</h4>
                  <div style={{ maxHeight: '200px', overflowY: 'auto', background: 'var(--color-bg-secondary)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
                    {recoveryResult.timeline_after?.map((e: any, idx: number) => (
                      <div key={idx} className="text-xs flex justify-between" style={{ padding: '4px 0', borderBottom: '1px solid var(--color-border)' }}>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>{e.event_id}</span>
                        <span className="text-muted">{new Date(e.timestamp).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-2 gap-6">
          {/* Profile */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Profile</h3>
            <div className="flex flex-col gap-4">
              <div className="form-group">
                <label className="form-label" htmlFor="settings-email">Email</label>
                <input
                  id="settings-email"
                  type="email"
                  className="form-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* App Preferences */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Application Preferences</h3>
            <div className="flex flex-col gap-4">
              <div className="form-group">
                <label className="form-label" htmlFor="settings-theme">Theme</label>
                <select id="settings-theme" className="form-select" value={theme} disabled>
                  <option value="dark">Dark (Default)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="settings-refresh">Dashboard Refresh Interval (seconds)</label>
                <input
                  id="settings-refresh"
                  type="number"
                  min={30}
                  max={3600}
                  className="form-input"
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="settings-max-sims">Max Simulations to Display</label>
                <input
                  id="settings-max-sims"
                  type="number"
                  min={10}
                  max={1000}
                  className="form-input"
                  value={maxSimulations}
                  onChange={(e) => setMaxSimulations(e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end mt-6 gap-3">
        {saved && (
          <div className="flex items-center gap-2" style={{ color: 'var(--color-emerald-light)', fontSize: '0.875rem' }}>
            ✓ Settings saved
          </div>
        )}
        <button className="btn btn-primary" onClick={handleSave} id="settings-save-btn">
          Save Changes
        </button>
      </div>
    </div>
  )
}
