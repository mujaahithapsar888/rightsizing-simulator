import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navItems = [
  { icon: '⊞', label: 'Dashboard', to: '/' },
  { icon: '↑', label: 'Upload Data', to: '/upload' },
  { icon: '◈', label: 'Simulator', to: '/simulator' },
  { icon: '⚗', label: 'Experiments', to: '/experiments' },
  { icon: '📊', label: 'Reports', to: '/reports' },
]

const bottomItems = [
  { icon: '⚙', label: 'Settings', to: '/settings' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <div>
          <div className="sidebar-logo-text">Rightsizing</div>
          <div className="sidebar-logo-sub">Simulator v1.0</div>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-title">Navigation</div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `sidebar-item${isActive ? ' active' : ''}`
            }
          >
            <span className="sidebar-item-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        <div className="sidebar-section-title" style={{ marginTop: '16px' }}>
          System
        </div>
        {bottomItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-item${isActive ? ' active' : ''}`
            }
          >
            <span className="sidebar-item-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="flex items-center gap-3" style={{ marginBottom: '12px' }}>
          <div className="user-avatar" style={{ width: '32px', height: '32px', fontSize: '0.75rem' }}>
            {user?.username?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.username ?? 'Unknown'}
            </div>
            <div className="text-xs" style={{ color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>
              {user?.role ?? 'viewer'}
            </div>
          </div>
        </div>
        <button
          className="btn btn-ghost btn-sm"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleLogout}
        >
          <span>⎋</span> Logout
        </button>
      </div>
    </aside>
  )
}
