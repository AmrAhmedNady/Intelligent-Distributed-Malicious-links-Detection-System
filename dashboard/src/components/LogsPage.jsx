// LogsPage.jsx — Terminal-style system log viewer
import { useEffect, useRef } from 'react'
import { ScrollText, RefreshCw } from 'lucide-react'

function formatTs(ts) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString([], {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function statusLabel(log) {
  if (log.status === 'completed') return log.label === 'malicious' ? '[MALICIOUS]' : '[BENIGN]   '
  if (log.status === 'processing') return '[SCANNING] '
  if (log.status === 'queued')    return '[QUEUED]   '
  if (log.status === 'failed')    return '[FAILED]   '
  return `[${log.status?.toUpperCase()}]`
}

function statusClass(log) {
  if (log.status === 'processing') return 'processing'
  if (log.status === 'failed')    return 'failed'
  if (log.status === 'queued')    return 'queued'
  if (log.status === 'completed') return `completed ${log.label || ''}`
  return ''
}

export default function LogsPage({ logs = [], onRefresh }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">System Logs</h1>
        <p className="page-subtitle">Live feed of all scan activity and job states</p>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title"><ScrollText size={16} className="card-title-icon" /> Activity Terminal</span>
          <button className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '6px 12px' }} onClick={onRefresh}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <div className="logs-terminal">
            <div className="logs-terminal-header">
              <span className="terminal-dot red"/>
              <span className="terminal-dot yellow"/>
              <span className="terminal-dot green"/>
              <span className="terminal-label">novashield@system — scan log — {logs.length} entries</span>
            </div>

            {logs.length === 0 ? (
              <div className="logs-empty">
                <ScrollText size={32} style={{ opacity: 0.3 }} />
                <span>No activity yet. Scan some URLs to see logs.</span>
              </div>
            ) : (
              <>
                {logs.map(log => (
                  <div key={log.job_id} className="log-entry">
                    <span className="log-time">{formatTs(log.updated_at)}</span>
                    <span className={`log-status ${statusClass(log)}`}>{statusLabel(log)}</span>
                    <span className="log-url" title={log.url}>
                      {log.url}
                      {log.confidence && (
                        <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>
                          ({(log.confidence * 100).toFixed(1)}% confidence)
                        </span>
                      )}
                      {log.error_msg && (
                        <span style={{ color: '#fb923c', marginLeft: 8 }}>— {log.error_msg}</span>
                      )}
                    </span>
                  </div>
                ))}
                <div ref={bottomRef} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
