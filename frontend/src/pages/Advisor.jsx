import { useEffect, useState } from 'react'
import api from '../api/client.js'
import AdviceCard from '../components/AdviceCard.jsx'
import BudgetMeter from '../components/BudgetMeter.jsx'
import { Loader2, RefreshCw, TrendingUp, Sparkles } from 'lucide-react'

const CATEGORIES = [
  'Food', 'Transport', 'Shopping', 'Utilities', 'Entertainment',
  'Health', 'Education', 'Rent', 'Groceries', 'Others',
]

function HealthRing({ score }) {
  const safe = Math.max(0, Math.min(100, Number(score) || 0))
  const r = 70
  const c = 2 * Math.PI * r
  const offset = c - (safe / 100) * c
  const color = safe >= 70 ? '#34d399' : safe >= 40 ? '#fbbf24' : '#f87171'

  return (
    <div className="relative w-48 h-48 mx-auto">
      <svg width="192" height="192" className="-rotate-90">
        <circle cx="96" cy="96" r={r} stroke="#1f2937" strokeWidth="14" fill="none" />
        <circle
          cx="96" cy="96" r={r}
          stroke={color} strokeWidth="14" fill="none"
          strokeDasharray={c} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-5xl font-bold" style={{ color }}>{safe}</div>
        <div className="text-xs uppercase tracking-widest text-gray-400 mt-1">Health Score</div>
      </div>
    </div>
  )
}

export default function Advisor() {
  const [data, setData] = useState(null)
  const [budgets, setBudgets] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const monthStr = () => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  }

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [adv, bud, sum] = await Promise.all([
        api.get('/advisor/advice'),
        api.get('/advisor/budgets', { params: { month: monthStr() } }),
        api.get('/analytics/summary'),
      ])
      setData(adv.data)
      setBudgets(bud.data || [])
      setSummary(sum.data)
    } catch (e) {
      setError(e.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const updateBudget = async (category, monthly_limit) => {
    try {
      await api.post('/advisor/set-budget', { category, monthly_limit, month: monthStr() })
      await load()
    } catch (e) {
      alert('Failed to update budget')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading advisor...
      </div>
    )
  }
  if (error) {
    return (
      <div className="card max-w-lg">
        <p className="text-rose-400 mb-3">⚠ {error}</p>
        <button className="btn-primary inline-flex items-center gap-2" onClick={load}>
          <RefreshCw className="w-4 h-4" /> Retry
        </button>
      </div>
    )
  }

  const score = data?.overall_health_score || 0
  const advice = data?.advice || []
  const insights = data?.top_insights || []
  const summaryRow = data?.monthly_summary || {}

  // Budgets map (existing)
  const budgetMap = Object.fromEntries(budgets.map((b) => [b.category, b.monthly_limit]))
  const byCat = summary?.by_category || {}

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-brand-400" /> Financial Advisor
        </h1>
        <p className="text-gray-400 text-sm">AI-powered insights into your spending</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card">
          <HealthRing score={score} />
          <div className="text-center mt-3">
            <div className="text-lg font-semibold">{data?.health_label || ''}</div>
            <div className="text-xs text-gray-400 mt-1">
              {summaryRow.transaction_count || 0} transactions · ₹{Math.round(summaryRow.total_spent || 0).toLocaleString('en-IN')} this month
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="card bg-gradient-to-br from-emerald-900/30 to-emerald-800/10 border-emerald-800/40">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-6 h-6 text-emerald-400" />
              <div>
                <div className="text-sm text-emerald-300">Savings potential</div>
                <div className="text-2xl font-bold text-white">
                  ₹{Math.round(data?.savings_potential || 0).toLocaleString('en-IN')}
                  <span className="text-sm text-gray-400 font-normal ml-1">/ month</span>
                </div>
                <div className="text-xs text-emerald-300/80 mt-1">
                  Cut spend in over-trending categories to reach this.
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">Top insights</h3>
            <ul className="space-y-1.5 text-sm text-gray-400">
              {insights.length === 0 ? <li>No insights yet.</li> : insights.map((i, idx) => <li key={idx}>• {i}</li>)}
            </ul>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Personalised advice</h3>
        {advice.length === 0 ? (
          <div className="card text-gray-500 text-sm">No advice yet — add more expenses.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {advice.map((a, i) => <AdviceCard key={i} advice={a} />)}
          </div>
        )}
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Budgets — current month</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {CATEGORIES.map((cat) => {
            const limit = budgetMap[cat] ?? 0
            const spent = byCat[cat]?.total ?? 0
            return (
              <BudgetMeter
                key={cat}
                category={cat}
                spent={spent}
                limit={limit}
                editable
                onChange={(v) => updateBudget(cat, v)}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}
