// ScanPage.jsx — URL submission panel
import { useState } from 'react'
import { Search, Zap, Network } from 'lucide-react'
import { api } from '../api.js'

const PLACEHOLDER = `https://www.example.com
https://suspicious-site.xyz/login
http://paypal-verify.tk/account`

export default function ScanPage({ onRefresh }) {
  const [input, setInput]   = useState('')
  const [mode, setMode]     = useState('direct')   // 'direct' | 'distributed'
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  const handleScan = async () => {
    const urls = input.split('\n').map(u => u.trim()).filter(Boolean)
    if (!urls.length) {
      setMessage({ type: 'error', text: 'Please enter at least one URL.' })
      return
    }
    setLoading(true)
    setMessage({ type: 'info', text: `Scanning ${urls.length} URL(s)…` })
    try {
      if (mode === 'direct') {
        const res = await api.scanDirect(urls)
        const malicious = res.results.filter(r => r.label === 'malicious').length
        const benign    = res.results.filter(r => r.label === 'benign').length
        const errors    = res.results.filter(r => r.error).length
        setMessage({
          type: 'success',
          text: `Scan complete: ${malicious} malicious, ${benign} benign${errors ? `, ${errors} error(s)` : ''}.`,
        })
      } else {
        const res = await api.scanDistributed(urls)
        setMessage({
          type: 'success',
          text: `Queued ${res.queued} job(s) to distributed workers${res.failed ? `. ${res.failed} failed.` : '.'}`,
        })
      }
      await onRefresh()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Scan failed.' })
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => { setInput(''); setMessage(null) }

  const EXAMPLE_LEGIT  = 'https://www.google.com\nhttps://www.python.org\nhttps://github.com'
  const EXAMPLE_PHISH  = 'https://paypal-secure-verify.tk/login\nhttp://192.168.1.1/confirm\nhttps://amazon-billing-update.xyz/verify'

  return (
    <div className="fade-in scan-panel">
      <div className="page-header">
        <h1 className="page-title">Scan URLs</h1>
        <p className="page-subtitle">Enter URLs to classify — one per line, up to 20</p>
      </div>

      {/* Mode selector */}
      <div className="card mb-4">
        <div className="card-header">
          <span className="card-title"><Search size={16} className="card-title-icon" /> Scan Mode</span>
        </div>
        <div className="card-body" style={{ display: 'flex', gap: 12 }}>
          <button
            className={`btn ${mode === 'direct' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setMode('direct')}
          >
            <Zap size={15} /> Direct (In-Process)
          </button>
          <button
            className={`btn ${mode === 'distributed' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setMode('distributed')}
          >
            <Network size={15} /> Distributed (Celery)
          </button>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', alignSelf: 'center', marginLeft: 4 }}>
            {mode === 'direct'
              ? 'Runs in FastAPI process — works without Redis'
              : 'Dispatches to Celery workers — requires Redis'}
          </span>
        </div>
      </div>

      {/* URL input */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Search size={16} className="card-title-icon" /> URLs to Scan</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" style={{ fontSize: '0.75rem', padding: '5px 10px' }}
              onClick={() => setInput(EXAMPLE_LEGIT)}>Load Legit Examples</button>
            <button className="btn btn-ghost" style={{ fontSize: '0.75rem', padding: '5px 10px' }}
              onClick={() => setInput(EXAMPLE_PHISH)}>Load Phishing Examples</button>
          </div>
        </div>
        <div className="card-body">
          <textarea
            className="scan-textarea"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={PLACEHOLDER}
            spellCheck={false}
          />
          <p className="scan-hint">
            One URL per line. http:// is added automatically if omitted. Max 20 per scan.
          </p>
          <div className="scan-actions">
            <button className="btn btn-primary" onClick={handleScan} disabled={loading}>
              {loading ? <><span className="spinner" /> Scanning…</> : <><Search size={15} /> Run Scan</>}
            </button>
            <button className="btn btn-ghost" onClick={handleClear} disabled={loading}>
              Clear
            </button>
          </div>

          {message && (
            <div className={`scan-message ${message.type}`}>
              {loading && <span className="spinner" />}
              {message.text}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
