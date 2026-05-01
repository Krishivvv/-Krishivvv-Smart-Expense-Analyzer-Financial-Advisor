import { useEffect, useState, useMemo } from 'react'
import api from '../api/client.js'
import CategoryBadge from '../components/CategoryBadge.jsx'
import { useExpenses } from '../hooks/useExpenses.js'
import { Plus, Pencil, Trash2, AlertTriangle, X, Loader2, Sparkles } from 'lucide-react'

const CATEGORIES = [
  'Food', 'Transport', 'Shopping', 'Utilities', 'Entertainment',
  'Health', 'Education', 'Rent', 'Groceries', 'Others',
]

const PAYMENT_METHODS = ['upi', 'card', 'cash']

function ExpenseModal({ open, onClose, onSave, initial }) {
  const [form, setForm] = useState({
    description: '',
    amount: '',
    category: '',
    payment_method: 'upi',
    date: new Date().toISOString().slice(0, 10),
    notes: '',
  })
  const [suggestion, setSuggestion] = useState(null)
  const [warning, setWarning] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (initial) {
      setForm({
        description: initial.description || '',
        amount: initial.amount || '',
        category: initial.category || '',
        payment_method: initial.payment_method || 'upi',
        date: initial.date ? initial.date.slice(0, 10) : new Date().toISOString().slice(0, 10),
        notes: initial.notes || '',
      })
    } else {
      setForm({
        description: '',
        amount: '',
        category: '',
        payment_method: 'upi',
        date: new Date().toISOString().slice(0, 10),
        notes: '',
      })
    }
    setSuggestion(null)
    setWarning(null)
  }, [initial, open])

  // Debounced auto-categorize
  useEffect(() => {
    if (!form.description || form.description.length < 3) {
      setSuggestion(null)
      return
    }
    const t = setTimeout(async () => {
      try {
        const r = await api.get('/analytics/categorize', { params: { description: form.description } })
        setSuggestion(r.data)
        if (!form.category && r.data?.category) {
          setForm((f) => ({ ...f, category: r.data.category }))
        }
      } catch (e) {
        // silent fail
      }
    }, 500)
    return () => clearTimeout(t)
  }, [form.description])

  // Subtle anomaly hint when amount entered
  useEffect(() => {
    setWarning(null)
    if (!form.amount || !form.category) return
    const amount = Number(form.amount)
    if (!amount || amount <= 0) return
    api.get('/analytics/summary').then((r) => {
      const cat = r.data?.by_category?.[form.category]
      if (cat?.avg && amount > cat.avg * 2.5) {
        setWarning(`This seems higher than usual for ${form.category} (avg ₹${Math.round(cat.avg).toLocaleString('en-IN')})`)
      }
    }).catch(() => {})
  }, [form.amount, form.category])

  const submit = async (e) => {
    e.preventDefault()
    if (!form.description || !form.amount) return
    setSaving(true)
    try {
      const payload = {
        description: form.description.trim(),
        amount: Number(form.amount),
        category: form.category || null,
        payment_method: form.payment_method,
        date: new Date(form.date).toISOString(),
        notes: form.notes || null,
      }
      await onSave(payload)
      onClose()
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="card w-full max-w-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{initial ? 'Edit expense' : 'Add expense'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="label">Description</label>
            <input
              required
              className="input w-full"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="e.g. Lunch at cafe"
            />
            {suggestion && (
              <div className="text-xs text-brand-300 mt-1 inline-flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> AI suggested: <strong>{suggestion.category}</strong>
                <span className="text-gray-500">({Math.round(suggestion.confidence * 100)}%)</span>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Amount (₹)</label>
              <input
                required
                type="number"
                step="0.01"
                className="input w-full"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
              />
              {warning && <div className="text-xs text-amber-400 mt-1">⚠ {warning}</div>}
            </div>
            <div>
              <label className="label">Category</label>
              <select className="input w-full" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                <option value="">Auto</option>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Date</label>
              <input type="date" className="input w-full" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            </div>
            <div>
              <label className="label">Payment</label>
              <select className="input w-full" value={form.payment_method} onChange={(e) => setForm({ ...form, payment_method: e.target.value })}>
                {PAYMENT_METHODS.map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Notes</label>
            <input className="input w-full" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary inline-flex items-center gap-2">
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              {initial ? 'Update' : 'Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Expenses() {
  const [month, setMonth] = useState('')
  const { data, loading, error, reload, create, update, remove } = useExpenses(month || undefined)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)

  const months = useMemo(() => {
    const set = new Set()
    data.forEach((e) => {
      if (e.date) set.add(e.date.slice(0, 7))
    })
    return Array.from(set).sort().reverse()
  }, [data])

  const onAdd = () => { setEditing(null); setModalOpen(true) }
  const onEdit = (exp) => { setEditing(exp); setModalOpen(true) }
  const onDelete = async (exp) => {
    if (!confirm(`Delete "${exp.description}"?`)) return
    await remove(exp.id)
  }
  const onSave = async (payload) => {
    if (editing) await update(editing.id, payload)
    else await create(payload)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Expenses</h1>
          <p className="text-gray-400 text-sm">All your tracked transactions</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={month} onChange={(e) => setMonth(e.target.value)} className="input">
            <option value="">All months</option>
            {months.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <button onClick={onAdd} className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card flex items-center gap-2 text-gray-400">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading...
        </div>
      ) : error ? (
        <div className="card text-rose-400">
          {error} <button onClick={reload} className="underline ml-2">Retry</button>
        </div>
      ) : data.length === 0 ? (
        <div className="card text-center text-gray-500 py-12">
          No expenses yet. <button onClick={onAdd} className="text-brand-400 underline">Add your first expense</button>.
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800">
                <th className="py-2 pr-3">Date</th>
                <th className="py-2 pr-3">Description</th>
                <th className="py-2 pr-3">Category</th>
                <th className="py-2 pr-3">Payment</th>
                <th className="py-2 pr-3 text-right">Amount</th>
                <th className="py-2 pr-3"></th>
              </tr>
            </thead>
            <tbody>
              {data.map((e) => (
                <tr
                  key={e.id}
                  className={`border-b border-gray-800/60 ${e.is_anomaly ? 'bg-rose-950/20' : ''}`}
                >
                  <td className="py-3 pr-3 text-gray-400 whitespace-nowrap">
                    {e.date ? new Date(e.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : ''}
                  </td>
                  <td className="py-3 pr-3">
                    <div className="flex items-center gap-2">
                      {e.is_anomaly && <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />}
                      <span>{e.description}</span>
                    </div>
                  </td>
                  <td className="py-3 pr-3"><CategoryBadge category={e.category} /></td>
                  <td className="py-3 pr-3 text-gray-400 uppercase tracking-wider text-xs">{e.payment_method || '—'}</td>
                  <td className="py-3 pr-3 text-right font-medium">₹{Number(e.amount).toLocaleString('en-IN')}</td>
                  <td className="py-3 pr-3 text-right whitespace-nowrap">
                    <button onClick={() => onEdit(e)} className="text-gray-400 hover:text-white p-1"><Pencil className="w-4 h-4" /></button>
                    <button onClick={() => onDelete(e)} className="text-gray-400 hover:text-rose-400 p-1"><Trash2 className="w-4 h-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ExpenseModal open={modalOpen} onClose={() => setModalOpen(false)} onSave={onSave} initial={editing} />
    </div>
  )
}
