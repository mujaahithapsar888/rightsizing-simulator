import React, { Component, ErrorInfo, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Enterprise React Error Boundary.
 * Catches uncaught runtime exceptions anywhere in the child component tree,
 * logs error telemetry, and presents a graceful, glassmorphic fallback UI.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log exception to local telemetry and console
    console.error('[ErrorBoundary caught error]:', error, errorInfo)
    this.setState({ errorInfo })
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.reload()
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div
          style={{
            minHeight: '60vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '640px',
              width: '100%',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              background: 'rgba(239, 68, 68, 0.05)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
              textAlign: 'center',
              padding: '36px 28px',
            }}
          >
            <div
              style={{
                fontSize: '2.5rem',
                marginBottom: '16px',
                lineHeight: 1,
              }}
            >
              ⚠️
            </div>
            <h2
              style={{
                fontSize: '1.4rem',
                fontWeight: 700,
                color: 'var(--color-rose, #ef4444)',
                marginBottom: '8px',
              }}
            >
              Application Error Encountered
            </h2>
            <p
              className="text-sm text-secondary"
              style={{ marginBottom: '20px', lineHeight: 1.6 }}
            >
              A client-side runtime exception was intercepted by the Error Boundary.
              Your data and session state are preserved. You can refresh the view to recover.
            </p>

            {this.state.error && (
              <div
                style={{
                  textAlign: 'left',
                  background: 'rgba(0, 0, 0, 0.5)',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md, 8px)',
                  marginBottom: '20px',
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  color: '#fca5a5',
                  maxHeight: '160px',
                  overflowY: 'auto',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                }}
              >
                <strong>{this.state.error.name}:</strong> {this.state.error.message}
                {this.state.errorInfo && (
                  <pre style={{ marginTop: '8px', fontSize: '0.75rem', opacity: 0.8 }}>
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={this.handleReset}
              >
                ↺ Reload Application
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => (window.location.href = '/')}
              >
                ⌂ Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
