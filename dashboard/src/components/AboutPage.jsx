// AboutPage.jsx — Project info, architecture & ML metrics
import { Shield, Cpu, Database } from 'lucide-react'

const METRICS = [
  { name: 'Accuracy',  value: '94.4%', pct: 94.4 },
  { name: 'F1-Score',  value: '94.4%', pct: 94.4 },
  { name: 'ROC-AUC',   value: '98.6%', pct: 98.6 },
  { name: 'Precision', value: '94.4%', pct: 94.4 },
]



const FEATURES = [
  'having_IP_Address', 'URL_Length', 'Shortining_Service', 'having_At_Symbol',
  'Prefix_Suffix', 'having_Sub_Domain', 'SSLfinal_State', 'Favicon',
  'port', 'HTTPS_token', 'Request_URL', 'URL_of_Anchor',
  'Links_in_tags', 'SFH', 'Submitting_to_email', 'on_mouseover',
  'popUpWidnow',
]

export default function AboutPage({ stats }) {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">About NovaShield</h1>
        <p className="page-subtitle">Detection of Malicious Websites Using Distributed Crawlers</p>
      </div>

      <div className="about-grid">
        {/* Core Performance */}
        <div className="card">
          <div className="card-header">
            <span className="card-title"><Cpu size={16} className="card-title-icon"/> Core Performance</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>UCI Dataset — 11,055 URLs</span>
          </div>
          <div className="card-body">
            <div className="metric-list">
              {METRICS.map(m => (
                <div key={m.name} className="metric-item">
                  <span className="metric-name">{m.name}</span>
                  <div className="metric-bar-wrap">
                    <div className="metric-bar-track">
                      <div className="metric-bar-fill" style={{ width: `${m.pct}%` }} />
                    </div>
                    <span className="metric-value">{m.value}</span>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: '10px 14px', background: 'rgba(124,58,237,0.08)', borderRadius: 8, fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--primary-light)' }}>Ensemble</strong>: RandomForest + GradientBoosting + LogisticRegression (soft-voting)<br/>
              <strong style={{ color: 'var(--primary-light)' }}>Feature Selection</strong>: dropped legacy WHOIS, traffic, and low-signal browser-era fields<br/>
              <strong style={{ color: 'var(--primary-light)' }}>NLP</strong>: Keyword scoring across 4 phishing signal categories
            </div>
          </div>
        </div>

        {/* Live stats */}
        <div className="card">
          <div className="card-header">
            <span className="card-title"><Shield size={16} className="card-title-icon"/> Live Session Stats</span>
          </div>
          <div className="card-body">
            {stats ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  ['Total Scanned', stats.total_scanned],
                  ['Malicious Detected', stats.malicious],
                  ['Benign Classified', stats.benign],
                  ['Detection Rate', `${stats.malicious_pct}%`],
                  ['Avg Confidence', `${(stats.avg_confidence * 100).toFixed(1)}%`],
                  ['Queued / Failed', `${stats.queued} / ${stats.failed}`],
                ].map(([label, val]) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{label}</span>
                    <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--primary-light)' }}>{val}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No scans yet. Run a scan to see statistics.</p>
            )}
          </div>
        </div>
      </div>

        {/* Feature list */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Database size={16} className="card-title-icon"/> Runtime Feature Set ({FEATURES.length} features)</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '6px 16px' }}>
            {FEATURES.map((f, i) => (
              <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: 'var(--text-secondary)', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', minWidth: 22 }}>{String(i+1).padStart(2,'0')}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{f}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            All features use UCI encoding: <strong style={{ color: '#86efac' }}>+1 = legitimate</strong> · <strong style={{ color: '#fca5a5' }}>-1 = phishing</strong> · <strong style={{ color: '#fde68a' }}>0 = uncertain</strong>
          </div>
        </div>
      </div>
    </div>
  )
}
