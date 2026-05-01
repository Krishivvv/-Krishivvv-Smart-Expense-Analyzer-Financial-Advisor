import { AlertTriangle } from 'lucide-react'
import CategoryBadge from './CategoryBadge.jsx'

const SEVERITY = {
  high: 'border-rose-700/60 bg-rose-950/40 text-rose-300',
  medium: 'border-amber-700/60 bg-amber-950/40 text-amber-300',
  low: 'border-yellow-700/60 bg-yellow-950/30 text-yellow-300',
}

export default function AnomalyAlert({ anomaly }) {
  const cls = SEVERITY[anomaly.severity] || SEVERITY.medium
  return (
    <div className={`border rounded-xl p-4 ${cls}`}>
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="font-semibold text-white truncate">{anomaly.description}</div>
            <div className="text-sm text-white whitespace-nowrap">
              ₹{Number(anomaly.amount).toLocaleString('en-IN')}
            </div>
          </div>
          <div className="text-xs mt-1 opacity-90">{anomaly.reason}</div>
          <div className="flex items-center gap-2 mt-2">
            <CategoryBadge category={anomaly.category} />
            <span className="text-xs uppercase tracking-wide opacity-75">Severity: {anomaly.severity}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
