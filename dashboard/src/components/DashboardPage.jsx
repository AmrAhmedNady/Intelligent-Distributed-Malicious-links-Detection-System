// DashboardPage.jsx — Main dashboard with stats + charts
import { Globe, ShieldAlert, ShieldCheck, BarChart3 } from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import ResultsTable from './ResultsTable.jsx'

function StatCard({ label, value, sub, colorClass, Icon }) {
  return (
    <div className={`stat-card ${colorClass}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value ?? '—'}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      <Icon className="stat-icon" />
    </div>
  )
}

const PIE_COLORS = ['#ef4444', '#22c55e']
const CUSTOM_TOOLTIP = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'rgba(5,5,16,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 14px', fontSize: 13 }}>
      <span style={{ color: payload[0].payload.fill }}>{payload[0].name}: </span>
      <strong style={{ color: '#f1f5f9' }}>{payload[0].value}</strong>
    </div>
  )
}

export default function DashboardPage({ stats, results }) {
  const pieData = stats ? [
    { name: 'Malicious', value: stats.malicious, fill: '#ef4444' },
    { name: 'Benign',    value: stats.benign,    fill: '#22c55e' },
  ] : []

  // Build trend from last 20 results
  const trendData = results.slice(0, 20).reverse().map((r, i) => ({
    i, risk: Math.round((r.risk_score || 0) * 100),
  }))

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Threat Intelligence Dashboard</h1>
        <p className="page-subtitle">Real-time monitoring of malicious website detection</p>
      </div>

      {/* Stats */}
      <div className="stats-grid mb-6">
        <StatCard
          label="Total Scanned"    value={stats?.total_scanned ?? 0}
          sub="all time"           colorClass="primary" Icon={Globe}
        />
        <StatCard
          label="Malicious"        value={stats?.malicious ?? 0}
          sub={`${stats?.malicious_pct ?? 0}% of total`}
          colorClass="danger"      Icon={ShieldAlert}
        />
        <StatCard
          label="Benign"           value={stats?.benign ?? 0}
          sub="safe websites"      colorClass="success" Icon={ShieldCheck}
        />
        <StatCard
          label="Avg Confidence"   value={stats ? `${(stats.avg_confidence * 100).toFixed(0)}%` : '—'}
          sub="analysis certainty"    colorClass="secondary"   Icon={BarChart3}
        />
      </div>

      {/* Charts */}
      {results.length > 0 && (
        <div className="charts-grid mb-6">
          {/* Trend */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Risk Score Trend</span>
              <span className="text-sm text-muted">Last {trendData.length} scans</span>
            </div>
            <div className="card-body" style={{ paddingTop: 10 }}>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={trendData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#7c3aed" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="i" hide />
                  <YAxis domain={[0, 100]} tick={{ fill: '#475569', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: 'rgba(5,5,16,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                    labelStyle={{ display: 'none' }}
                    formatter={(v) => [`${v}%`, 'Risk']}
                  />
                  <Area type="monotone" dataKey="risk" stroke="#7c3aed" strokeWidth={2} fill="url(#riskGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pie */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Threat Distribution</span>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={72} paddingAngle={4} dataKey="value">
                    {pieData.map((d, i) => <Cell key={i} fill={d.fill} stroke="none"/>)}
                  </Pie>
                  <Tooltip content={<CUSTOM_TOOLTIP />} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 20, marginTop: 8 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444', display: 'inline-block' }}/>
                  Malicious ({stats?.malicious ?? 0})
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}/>
                  Benign ({stats?.benign ?? 0})
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Results */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Scans</span>
          <span className="text-sm text-muted">{results.length} results</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <ResultsTable results={results.slice(0, 10)} compact />
        </div>
      </div>
    </div>
  )
}
