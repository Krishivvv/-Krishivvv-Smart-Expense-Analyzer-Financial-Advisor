import { useEffect, useState } from 'react'
import api from '../api/client.js'
import StatCard from '../components/StatCard.jsx'
import SpendingChart from '../components/SpendingChart.jsx'
import AdviceCard from '../components/AdviceCard.jsx'
import { CATEGORY_HEX } from '../components/CategoryBadge.jsx'
import { Wallet, TrendingUp, AlertTriangle, Calendar, Loader2, RefreshCw } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [advice, setAdvice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, a] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/advisor/advice'),
      ])
      setSummary(s.data)
      setAdvice(a.data)
    } catch (e) {
      setError(e.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading dashboard...
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

  const inr = (v) => `₹${Math.round(v || 0).toLocaleString('en-IN')}`

  const pieData = Object.entries(summary?.by_category || {}).map(([cat, v]) => ({
    name: cat,
    value: v.total,
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-400 text-sm">Your spending at a glance</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Wallet}
          label="Total this month"
          value={inr(summary?.total_this_month)}
          change={summary?.change_percent}
          accent="brand"
        />
        <StatCard
          icon={Calendar}
          label="Last month"
          value={inr(summary?.total_last_month)}
          accent="amber"
        />
        <StatCard
          icon={TrendingUp}
          label="Categories tracked"
          value={Object.keys(summary?.by_category || {}).length}
          accent="green"
        />
        <StatCard
          icon={AlertTriangle}
          label="Anomalies found"
          value={summary?.anomaly_count || 0}
          accent="red"
        />
      </div>

      <SpendingChart data={summary?.daily_totals} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Category breakdown</h3>
          {pieData.length === 0 ? (
            <p className="text-gray-500 text-sm">No spending this month yet.</p>
          ) : (
            <div className="w-full h-64">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={2}>
                    {pieData.map((d, i) => (
                      <Cell key={i} fill={CATEGORY_HEX[d.name] || '#9ca3af'} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => `₹${Number(v).toLocaleString('en-IN')}`} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Top advice</h3>
          {(advice?.advice || []).slice(0, 3).map((a, i) => <AdviceCard key={i} advice={a} />)}
          {(!advice?.advice || advice.advice.length === 0) && (
            <div className="card text-gray-500 text-sm">Add more expenses to get personalised tips.</div>
          )}
        </div>
      </div>
    </div>
  )
}
