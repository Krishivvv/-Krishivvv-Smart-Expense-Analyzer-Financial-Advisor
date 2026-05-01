import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Expenses from './pages/Expenses.jsx'
import Analytics from './pages/Analytics.jsx'
import Advisor from './pages/Advisor.jsx'
import Upload from './pages/Upload.jsx'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <Navbar />
      <main className="flex-1 p-4 md:p-8 overflow-x-hidden">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/advisor" element={<Advisor />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}
