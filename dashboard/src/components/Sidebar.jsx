// Sidebar.jsx — Navigation sidebar with NovaShield logo
import { LayoutDashboard, Search, Table2, ScrollText, Info } from 'lucide-react'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard',  Icon: LayoutDashboard },
  { id: 'scan',      label: 'Scan URLs',  Icon: Search },
  { id: 'results',   label: 'Results',    Icon: Table2 },
  { id: 'logs',      label: 'System Logs',Icon: ScrollText },
  { id: 'about',     label: 'About',      Icon: Info },
]

function StatusDot({ online }) {
  const cls = online === true ? 'online' : online === false ? 'offline' : 'unknown'
  return <span className={`status-dot ${cls}`} />
}

export default function Sidebar({ page, onNavigate, sysStatus }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo" style={{ cursor: 'default' }}>
        <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
          <defs>
            <linearGradient id="nova" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FF0055"/>
              <stop offset="100%" stopColor="#00E5FF"/>
            </linearGradient>
          </defs>
          {/* Hexagon Shield */}
          <path d="M17 2 L31 9 L31 25 L17 32 L3 25 L3 9 Z" fill="url(#nova)" opacity="0.15"/>
          <path d="M17 2 L31 9 L31 25 L17 32 L3 25 L3 9 Z" stroke="url(#nova)" strokeWidth="1.5"/>
          {/* Inner Nova Star */}
          <path d="M17 9 L19 15 L25 17 L19 19 L17 25 L15 19 L9 17 L15 15 Z" fill="url(#nova)"/>
        </svg>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">NovaShield</span>
          <span className="sidebar-logo-tag">Threat Detection</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            className={`nav-item ${page === id ? 'active' : ''}`}
            onClick={() => onNavigate(id)}
          >
            <Icon className="nav-icon" size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      {/* System status */}
      <div className="sidebar-status">
        <div className="status-row">
          <StatusDot online={sysStatus?.broker_online} />
          <span>Redis Broker</span>
        </div>
        <div className="status-row">
          <StatusDot online={sysStatus?.worker_online} />
          <span>Celery Worker</span>
        </div>
        {sysStatus && (
          <div style={{ marginTop: 6, fontSize: '0.7rem', color: sysStatus.status === 'ok' ? 'var(--success)' : 'var(--warning)' }}>
            {sysStatus.status === 'ok' ? '● Distributed mode' : '● Direct mode (no Redis)'}
          </div>
        )}
      </div>
    </aside>
  )
}
