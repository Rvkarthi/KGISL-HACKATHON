import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Results from './pages/Results'
import BulkResults from './pages/BulkResults'
import History from './pages/History'

export default function App() {
  return (
    <div className="min-h-screen bg-surface-900 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/results" element={<Results />} />
          <Route path="/bulk-results" element={<BulkResults />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  )
}
