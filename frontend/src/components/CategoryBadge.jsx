const COLORS = {
  Food: 'bg-orange-900/40 text-orange-300 border-orange-800/50',
  Transport: 'bg-blue-900/40 text-blue-300 border-blue-800/50',
  Shopping: 'bg-pink-900/40 text-pink-300 border-pink-800/50',
  Utilities: 'bg-cyan-900/40 text-cyan-300 border-cyan-800/50',
  Entertainment: 'bg-purple-900/40 text-purple-300 border-purple-800/50',
  Health: 'bg-emerald-900/40 text-emerald-300 border-emerald-800/50',
  Education: 'bg-yellow-900/40 text-yellow-300 border-yellow-800/50',
  Rent: 'bg-red-900/40 text-red-300 border-red-800/50',
  Groceries: 'bg-lime-900/40 text-lime-300 border-lime-800/50',
  Others: 'bg-gray-800 text-gray-300 border-gray-700',
}

export const CATEGORY_HEX = {
  Food: '#fb923c',
  Transport: '#60a5fa',
  Shopping: '#f472b6',
  Utilities: '#22d3ee',
  Entertainment: '#c084fc',
  Health: '#34d399',
  Education: '#facc15',
  Rent: '#f87171',
  Groceries: '#a3e635',
  Others: '#9ca3af',
}

export default function CategoryBadge({ category }) {
  const cls = COLORS[category] || COLORS.Others
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {category || 'Others'}
    </span>
  )
}
