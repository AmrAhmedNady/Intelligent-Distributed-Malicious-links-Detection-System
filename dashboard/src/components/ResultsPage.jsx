// ResultsPage.jsx — Full results page
import { Table2 } from 'lucide-react'
import ResultsTable from './ResultsTable.jsx'

export default function ResultsPage({ results, onClear }) {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Scan Results</h1>
        <p className="page-subtitle">All completed website classifications</p>
      </div>
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Table2 size={16} className="card-title-icon" /> Detection Log</span>
          <span className="text-sm text-muted">{results.length} entries</span>
        </div>
        <div className="card-body">
          <ResultsTable results={results} onClear={onClear} />
        </div>
      </div>
    </div>
  )
}
