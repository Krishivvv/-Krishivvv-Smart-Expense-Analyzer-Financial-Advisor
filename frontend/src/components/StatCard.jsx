import { ArrowUp, ArrowDown } from 'lucide-react'

export default function StatCard({ icon: Icon, label, value, change, prefix = '', accent = 'brand' }) {
  const isUp = typeof change === 'number' && change > 0
  const isDown = typeof change === 'number' && change < 0

  const accentColors = {
    brand: 'from-brand-600/30 to-purple-700/20 text-brand-300',
    green: 'from-emerald-600/30 to-emerald-700/20 text-emerald-300',
    red: 'from-rose-600/30 to-rose-700/20 text-rose-300',
    amber: 'from-amber-600/30 to-orange-700/20 text-amber-300',
  }

  return (
    <div className="card animate-slide-up">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-400">{label}</div>
          <div className="text-2xl font-bold text-white mt-1">
            {prefix}
            {value}
          </div>
          {typeof change === 'number' && (
            <div
              className={`flex items-center gap-1 mt-2 text-xs ${
                isUp ? 'text-rose-400' : isDown ? 'text-emerald-400' : 'text-gray-400'
              }`}
            >
              {isUp ? <ArrowUp className="w-3 h-3" /> : isDown ? <ArrowDown className="w-3 h-3" /> : null}
              <span>{Math.abs(change).toFixed(1)}% vs last month</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${accentColors[accent]} flex items-center justify-center`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </div>
  )
}
