import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Platform Overview & Key Metrics' },
  '/upload': { title: 'Upload Data', subtitle: 'Import Historical Metrics' },
  '/simulator': { title: 'Rightsizing Simulator', subtitle: 'Model Resource Downsizing' },
  '/experiments': { title: 'Experiments', subtitle: 'A/B Scenario Comparison' },
  '/reports': { title: 'Reports', subtitle: 'Analysis & Export' },
  '/settings': { title: 'Settings', subtitle: 'Preferences & Configuration' },
}

export default function Navbar() {
  const { pathname } = useLocation()
  const { user } = useAuth()
  const page = pageTitles[pathname] ?? { title: 'Page', subtitle: '' }

  return (
    <header className="navbar">
      <div>
        <div className="navbar-title">{page.title}</div>
        <div className="navbar-breadcrumb">{page.subtitle}</div>
      </div>

      <div className="navbar-actions">
        {/* Live indicator */}
        <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>
          <span
            className="status-dot completed"
            style={{ margin: 0, display: 'inline-block' }}
          />
          <span>System Healthy</span>
        </div>

        {/* User avatar */}
        <div className="user-avatar" title={user?.email}>
          {user?.username?.charAt(0).toUpperCase() ?? 'A'}
        </div>
      </div>
    </header>
  )
}
