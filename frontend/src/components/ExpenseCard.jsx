import CategoryBadge from './CategoryBadge.jsx'
import { AlertTriangle, Pencil, Trash2 } from 'lucide-react'

export default function ExpenseCard({ expense, onEdit, onDelete }) {
  const date = expense.date ? new Date(expense.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : ''

  return (
    <div className={`card flex items-center justify-between gap-4 ${expense.is_anomaly ? 'border-rose-700/40' : ''}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium truncate">{expense.description}</span>
          {expense.is_anomaly && (
            <span className="inline-flex items-center gap-1 text-xs text-rose-400">
              <AlertTriangle className="w-3 h-3" /> anomaly
            </span>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-1 flex gap-2 items-center">
          <span>{date}</span>
          <CategoryBadge category={expense.category} />
          {expense.payment_method && <span className="uppercase tracking-wider">{expense.payment_method}</span>}
        </div>
      </div>

      <div className="text-right">
        <div className="font-semibold">₹{Number(expense.amount).toLocaleString('en-IN')}</div>
      </div>

      {(onEdit || onDelete) && (
        <div className="flex items-center gap-2">
          {onEdit && <button onClick={() => onEdit(expense)} className="text-gray-400 hover:text-white"><Pencil className="w-4 h-4" /></button>}
          {onDelete && <button onClick={() => onDelete(expense)} className="text-gray-400 hover:text-rose-400"><Trash2 className="w-4 h-4" /></button>}
        </div>
      )}
    </div>
  )
}
