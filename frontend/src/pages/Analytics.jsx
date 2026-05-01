import { useEffect, useState, useMemo } from 'react'
import api from '../api/client.js'
import ForecastChart from '../components/ForecastChart.jsx'
import AnomalyAlert from '../components/AnomalyAlert.jsx'
import { CATEGORY_HEX } from '../components/CategoryBadge.jsx'
import { Loader2, RefreshCw, BarChart3 } from 'lucide-react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from 'recharts'

export default function Analytics() {
  const [summary, setSummary] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [forecasts, setForecasts] = useState([])
  const [selectedCat, setSelectedCat] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, a, f] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/analytics/anomalies'),
        api.get('/analytics/forecast'),
      ])
      setSummary(s.data)
      setAnomalies(a.data?.anomalies || [])
      setForecasts(f.data?.forecasts || [])
      if (f.data?.forecasts?.length && !selectedCat) {
        setSelectedCat(f.data.forecasts[0].category)
      }
    } catch (e) {
      setError(e.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const selectedForecast = useMemo(
    () => forecasts.find((f) => f.category === selectedCat),
    [forecasts, selectedCat]
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading analytics...
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

  const catBars = Object.entries(summary?.by_category || {}).map(([cat, v]) => ({
    category: cat,
    total: v.total,
    avg: v.avg,
    count: v.count,
  }))

  const pmData = Object.entries(summary?.payment_method_split || {}).map(([k, v]) => ({
    name: k.toUpperCase(),
    value: v,
  }))
  const pmColors = { CASH: '#fbbf24', CARD: '#60a5fa', UPI: '#a78bfa' }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-brand-400" /> Analytics
        </h1>
        <p className="text-gray-400 text-sm">Forecasts, anomalies, and breakdowns</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card mb-2 flex flex-wrap items-center gap-3">
            <span className="text-sm text-gray-400">Forecast for:</span>
            <select className="input" value={selectedCat || ''} onChange={(e) => setSelectedCat(e.target.value)}>
              {forecasts.map((f) => <option key={f.category} value={f.category}>{f.category}</option>)}
            </select>
            {selectedForecast && (
              <div className="ml-auto text-sm text-gray-400">
                Predicted: <span className="text-white font-semibold">₹{Math.round(selectedForecast.predicted_next_month).toLocaleString('en-IN')}</span>
                <span className={`ml-3 ${selectedForecast.trend === 'increasing' ? 'text-rose-400' : selectedForecast.trend === 'decreasing' ? 'text-emerald-400' : 'text-gray-400'}`}>
                  Trend: {selectedForecast.trend}
                </span>
              </div>
            )}
          </div>
          <ForecastChart data={selectedForecast?.predicted_daily_breakdown} title={`Forecast — ${selectedCat || ''}`} />
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Payment methods</h3>
          {pmData.every((d) => d.value === 0) ? (
            <p className="text-gray-500 text-sm">No data this month.</p>
          ) : (
            <div className="w-full h-64">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pmData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={85} paddingAngle={3}>
                    {pmData.map((d, i) => <Cell key={i} fill={pmColors[d.name] || '#9ca3af'} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Spending by category (this month)</h3>
        {catBars.length === 0 ? (
          <p className="text-gray-500 text-sm">No spending this month.</p>
        ) : (
          <div className="w-full h-72">
            <ResponsiveContainer>
              <BarChart data={catBars}>
                <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                <XAxis dataKey="category" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} />
                <Tooltip formatter={(v, name) => [name === 'total' ? `₹${Number(v).toLocaleString('en-IN')}` : v, name]} />
                <Bar dataKey="total" radius={[6, 6, 0, 0]}>
                  {catBars.map((d, i) => <Cell key={i} fill={CATEGORY_HEX[d.category] || '#9ca3af'} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Anomalies detected</h3>
        {anomalies.length === 0 ? (
          <div className="card text-gray-500 text-sm">No anomalies. You're spending consistently.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {anomalies.map((a) => <AnomalyAlert key={a.id} anomaly={a} />)}
          </div>
        )}
      </div>
    </div>
  )
}
