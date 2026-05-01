import { NavLink } from 'react-router-dom'
import { useState } from 'react'
import { LayoutDashboard, Receipt, BarChart3, Sparkles, Upload, Wallet, Menu, X } from 'lucide-react'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/expenses', label: 'Expenses', icon: Receipt },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/advisor', label: 'Advisor', icon: Sparkles },
  { to: '/upload', label: 'Upload CSV', icon: Upload },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden flex items-center justify-between bg-gray-900 border-b border-gray-800 p-4">
        <div className="flex items-center gap-2">
          <Wallet className="w-6 h-6 text-brand-400" />
          <span className="font-semibold">Smart Expense</span>
        </div>
        <button onClick={() => setOpen(!open)} className="text-gray-400 hover:text-white">
          {open ? <X /> : <Menu />}
        </button>
      </div>

      <aside
        className={`${open ? 'block' : 'hidden'} md:block w-full md:w-64 bg-gray-900 border-r border-gray-800 md:min-h-screen p-4`}
      >
        <div className="hidden md:flex items-center gap-2 px-2 py-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
            <Wallet className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-white">Smart Expense</div>
            <div className="text-xs text-gray-500">AI Financial Coach</div>
          </div>
        </div>

        <nav className="space-y-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-brand-600/20 text-brand-300 border border-brand-700/40'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="hidden md:block absolute bottom-6 left-4 right-4 max-w-[14rem]">
          <div className="card bg-gradient-to-br from-brand-900/40 to-purple-900/30 border-brand-800/40">
            <div className="text-xs text-brand-300 font-semibold mb-1">AI Powered</div>
            <div className="text-xs text-gray-400">Categorization, anomaly detection & forecasts using your data.</div>
          </div>
        </div>
      </aside>
    </>
  )
}
