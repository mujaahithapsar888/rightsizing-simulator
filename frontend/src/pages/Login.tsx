import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(username, password)
      navigate('/', { replace: true })
    } catch {
      setError('Invalid username or password. Try admin / admin123')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Background orbs */}
      <div className="login-bg-orb login-bg-orb-1" />
      <div className="login-bg-orb login-bg-orb-2" />

      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">⚡</div>
          <div>
            <div className="login-title">Rightsizing Simulator</div>
            <div className="login-subtitle">Cloud Media Platform · Performance &amp; Cost Intelligence</div>
          </div>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit} id="login-form">
          {error && <div className="login-error">{error}</div>}

          <div className="form-group">
            <label className="form-label" htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              className="form-input"
              placeholder="admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            style={{ marginTop: '8px' }}
            disabled={isLoading}
            id="login-submit-btn"
          >
            {isLoading ? (
              <>
                <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                <span>Authenticating…</span>
              </>
            ) : (
              '→ Sign In'
            )}
          </button>
        </form>

        {/* Hint */}
        <div
          className="text-xs text-center"
          style={{ color: 'var(--color-text-muted)', marginTop: '20px', lineHeight: '1.6' }}
        >
          Default credentials: <code style={{ color: 'var(--color-indigo-light)', fontFamily: 'var(--font-mono)' }}>admin</code> /{' '}
          <code style={{ color: 'var(--color-indigo-light)', fontFamily: 'var(--font-mono)' }}>admin123</code>
        </div>
      </div>
    </div>
  )
}
