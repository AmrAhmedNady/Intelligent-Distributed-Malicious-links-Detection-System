// ResultsTable.jsx — Filterable results table with risk bars
import { useState } from 'react'
import { ExternalLink, Trash2, Search, ShieldAlert, ShieldCheck } from 'lucide-react'

function RiskBar({ score }) {
  const pct = Math.round((score || 0) * 100)
  const cls = pct >= 70 ? 'high' : pct >= 40 ? 'medium' : 'low'
  return (
    <div className="risk-bar-wrap">
      <div className="risk-bar-track">
        <div className="risk-bar-fill" style={{ width: `${pct}%` }} data-cls={cls}
          ref={el => { if (el) el.className = `risk-bar-fill ${cls}` }} />
      </div>
      <span className="risk-pct">{pct}%</span>
    </div>
  )
}

function Badge({ label, trusted }) {
  if (!label) return <span className="badge queued"><span className="badge-dot"/>Processing</span>
  if (trusted) return <span className="badge benign"><ShieldCheck size={10}/> Trusted</span>
  return label === 'malicious'
    ? <span className="badge malicious"><ShieldAlert size={10}/> Malicious</span>
    : <span className="badge benign"><ShieldCheck size={10}/> Benign</span>
}

function formatTime(ts) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString([], { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' })
}

export default function ResultsTable({ results = [], onClear, compact = false }) {
  const [search, setSearch]   = useState('')
  const [filter, setFilter]   = useState('all')

  const filtered = results.filter(r => {
    const matchSearch = !search || r.url?.toLowerCase().includes(search.toLowerCase())
    const matchFilter =
      filter === 'all' ? true :
      filter === 'malicious' ? r.label === 'malicious' :
      filter === 'benign'    ? r.label === 'benign'    : true
    return matchSearch && matchFilter
  })

  return (
    <div>
      {!compact && (
        <div className="results-toolbar mb-4">
          <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
            <Search size={14} style={{ position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', color:'var(--text-muted)' }}/>
            <input
              className="search-input"
              style={{ paddingLeft: 32, width: '100%' }}
              placeholder="Filter by URL…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button className={`filter-btn ${filter==='all'?'active':''}`}       onClick={() => setFilter('all')}>All ({results.length})</button>
          <button className={`filter-btn danger ${filter==='malicious'?'active danger':''}`} onClick={() => setFilter('malicious')}>
            Malicious ({results.filter(r=>r.label==='malicious').length})
          </button>
          <button className={`filter-btn success ${filter==='benign'?'active success':''}`} onClick={() => setFilter('benign')}>
            Benign ({results.filter(r=>r.label==='benign').length})
          </button>
          {onClear && (
            <button className="btn btn-danger" onClick={onClear} style={{ marginLeft: 'auto' }}>
              <Trash2 size={14} /> Clear All
            </button>
          )}
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="empty-state">
          <ShieldCheck size={40} />
          <p>{results.length === 0 ? 'No scans yet. Go to "Scan URLs" to begin.' : 'No results match your filter.'}</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="results-table">
            <thead>
              <tr>
                <th>URL</th>
                <th>Label</th>
                <th>Risk Score</th>
                {!compact && <th>Confidence</th>}
                {!compact && <th>Scanned</th>}
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(r => (
                <tr key={r.job_id} className="fade-in">
                  <td>
                    <div className="url-cell" title={r.url}>
                      <a href={r.url} target="_blank" rel="noopener noreferrer">{r.url}</a>
                    </div>
                  </td>
                  <td><Badge label={r.label} trusted={r.trusted} /></td>
                  <td><RiskBar score={r.risk_score} /></td>
                  {!compact && <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {r.confidence ? `${(r.confidence * 100).toFixed(1)}%` : '—'}
                  </td>}
                  {!compact && <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatTime(r.updated_at)}</td>}
                  <td>
                    <a href={r.url} target="_blank" rel="noopener noreferrer"
                       style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
                      <ExternalLink size={13} />
                    </a>
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
