import { AlertTriangle, Lightbulb, Trophy } from 'lucide-react'

const TYPE_STYLES = {
  warning: {
    border: 'border-rose-700/50',
    bg: 'bg-rose-950/30',
    icon: AlertTriangle,
    iconColor: 'text-rose-400',
  },
  tip: {
    border: 'border-blue-700/50',
    bg: 'bg-blue-950/30',
    icon: Lightbulb,
    iconColor: 'text-blue-400',
  },
  achievement: {
    border: 'border-emerald-700/50',
    bg: 'bg-emerald-950/30',
    icon: Trophy,
    iconColor: 'text-emerald-400',
  },
}

const IMPACT_BADGE = {
  high: 'bg-rose-900/50 text-rose-300',
  medium: 'bg-amber-900/50 text-amber-300',
  low: 'bg-gray-800 text-gray-400',
}

export default function AdviceCard({ advice }) {
  const style = TYPE_STYLES[advice.type] || TYPE_STYLES.tip
  const Icon = style.icon

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-5`}>
      <div className="flex items-start gap-3">
        <div className={`${style.iconColor} mt-0.5 shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h4 className="font-semibold text-white">{advice.title}</h4>
            {advice.impact && (
              <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${IMPACT_BADGE[advice.impact]}`}>
                {advice.impact}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-300 mt-1.5 leading-relaxed">{advice.detail}</p>
        </div>
      </div>
    </div>
  )
}
