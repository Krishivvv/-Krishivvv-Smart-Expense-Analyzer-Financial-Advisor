import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function SpendingChart({ data }) {
  const safe = (data || []).map((d) => ({ ...d, day: d.date?.slice(5) || d.date }))

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Daily Spending — last 30 days</h3>
        <span className="text-xs text-gray-500">{safe.length} days with activity</span>
      </div>
      <div className="w-full h-64">
        <ResponsiveContainer>
          <BarChart data={safe} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="bargrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" stopOpacity={0.95} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0.3} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
            <XAxis dataKey="day" stroke="#6b7280" fontSize={11} />
            <YAxis stroke="#6b7280" fontSize={11} />
            <Tooltip
              cursor={{ fill: '#1f2937' }}
              formatter={(v) => [`₹${Number(v).toLocaleString('en-IN')}`, 'Spent']}
            />
            <Bar dataKey="amount" fill="url(#bargrad)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
