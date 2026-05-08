// App.jsx — NovaShield main shell
import { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'
import Sidebar from './components/Sidebar.jsx'
import DashboardPage from './components/DashboardPage.jsx'
import ScanPage from './components/ScanPage.jsx'
import ResultsPage from './components/ResultsPage.jsx'
import LogsPage from './components/LogsPage.jsx'
import AboutPage from './components/AboutPage.jsx'

const POLL_INTERVAL = 5000

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [stats, setStats]     = useState(null)
  const [results, setResults] = useState([])
  const [logs, setLogs]       = useState([])
  const [sysStatus, setSysStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchAll = useCallback(async () => {
    try {
      const [s, r, l, ss] = await Promise.allSettled([
        api.stats(),
        api.results(),
        api.logs(),
        api.systemStatus(),
      ])
      if (s.status === 'fulfilled')  setStats(s.value)
      if (r.status === 'fulfilled')  setResults(r.value.results || [])
      if (l.status === 'fulfilled')  setLogs(l.value.logs || [])
      if (ss.status === 'fulfilled') setSysStatus(ss.value)
    } catch (_) {}
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [fetchAll])

  const handleClearResults = async () => {
    await api.clearResults()
    setResults([])
    fetchAll()
  }

  const pageProps = { stats, results, logs, sysStatus, loading, onRefresh: fetchAll }

  return (
    <div className="app-shell">
      <Sidebar page={page} onNavigate={setPage} sysStatus={sysStatus} />
      <main className="main-content fade-in">
        {page === 'dashboard' && <DashboardPage {...pageProps} />}
        {page === 'scan'      && <ScanPage onRefresh={fetchAll} />}
        {page === 'results'   && <ResultsPage results={results} onClear={handleClearResults} />}
        {page === 'logs'      && <LogsPage logs={logs} onRefresh={fetchAll} />}
        {page === 'about'     && <AboutPage stats={stats} />}
      </main>
    </div>
  )
}
