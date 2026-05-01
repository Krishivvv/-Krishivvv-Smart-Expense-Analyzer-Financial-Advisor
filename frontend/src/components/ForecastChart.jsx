import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

export default function ForecastChart({ data, title = 'Forecast — Next Month' }) {
  const safe = (data || []).map((d) => ({
    day: d.date?.slice(5) || d.date,
    predicted: d.predicted_amount ?? d.predicted,
  }))

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <span className="text-xs text-gray-500">{safe.length} days projected</span>
      </div>
      <div className="w-full h-72">
        <ResponsiveContainer>
          <LineChart data={safe} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
            <XAxis dataKey="day" stroke="#6b7280" fontSize={11} />
            <YAxis stroke="#6b7280" fontSize={11} />
            <Tooltip formatter={(v) => `₹${Number(v).toLocaleString('en-IN')}`} />
            <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#a78bfa"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={{ r: 2 }}
              name="Predicted"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
