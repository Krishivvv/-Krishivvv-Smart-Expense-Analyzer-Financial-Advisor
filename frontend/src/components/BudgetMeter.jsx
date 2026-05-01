export default function BudgetMeter({ category, spent, limit, editable = false, onChange }) {
  const pct = limit > 0 ? Math.min((spent / limit) * 100, 150) : 0
  const color = pct >= 100 ? 'bg-rose-500' : pct >= 85 ? 'bg-amber-500' : 'bg-emerald-500'
  const label = pct >= 100 ? 'over budget' : pct >= 85 ? 'close' : 'on track'

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium">{category}</div>
        <div className={`text-xs ${pct >= 100 ? 'text-rose-400' : pct >= 85 ? 'text-amber-400' : 'text-emerald-400'}`}>
          {label}
        </div>
      </div>
      <div className="h-3 bg-gray-800 rounded-full overflow-hidden mb-2">
        <div
          className={`${color} h-full rounded-full transition-all`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-400">
          ₹{Math.round(spent).toLocaleString('en-IN')} of{' '}
          {editable ? (
            <input
              type="number"
              defaultValue={limit}
              onBlur={(e) => onChange?.(Number(e.target.value))}
              onKeyDown={(e) => e.key === 'Enter' && e.target.blur()}
              className="bg-gray-800 border border-gray-700 rounded px-1 py-0.5 w-20 text-right text-gray-200 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          ) : (
            <>₹{Math.round(limit).toLocaleString('en-IN')}</>
          )}
        </span>
        <span className="text-gray-500">{pct.toFixed(0)}%</span>
      </div>
    </div>
  )
}
