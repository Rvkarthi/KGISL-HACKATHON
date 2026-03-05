import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    History as HistoryIcon, Trash2, Calendar, FileText,
    BarChart3, Shield, Search, RefreshCw, AlertCircle, ExternalLink
} from 'lucide-react'
import { fetchHistory, deleteRecord, clearAllRecords, fetchRecordDetail } from '../services/api'
import ScoreBar from '../components/ScoreBar'

export default function History() {
    const navigate = useNavigate()
    const [records, setRecords] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')

    const loadHistory = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await fetchHistory()
            setRecords(data)
        } catch (err) {
            setError('Failed to load screening history.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadHistory()
    }, [])

    const handleAnalyse = async (id) => {
        try {
            const result = await fetchRecordDetail(id)
            navigate('/results', { state: { result } })
        } catch (err) {
            alert('Failed to load analysis details.')
        }
    }

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this record?')) return
        try {
            await deleteRecord(id)
            setRecords(records.filter(r => r.id !== id))
        } catch (err) {
            alert('Failed to delete record.')
        }
    }

    const handleClearAll = async () => {
        if (!window.confirm('Are you sure you want to clear ALL screening history? This cannot be undone.')) return
        try {
            await clearAllRecords()
            setRecords([])
        } catch (err) {
            alert('Failed to clear history.')
        }
    }

    const filteredRecords = records.filter(r =>
        r.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.domain.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const formatDate = (dateStr) => {
        if (!dateStr) return 'N/A'
        return new Date(dateStr).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    return (
        <div className="max-w-6xl mx-auto px-4 py-10 animate-fade-in space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
                        <HistoryIcon className="w-8 h-8 text-brand-400" />
                        Recruiter History
                    </h1>
                    <p className="text-gray-400 mt-1">Review and manage past screening sessions.</p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={loadHistory}
                        className="btn-secondary"
                        title="Refresh history"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>

                    <button
                        onClick={handleClearAll}
                        disabled={records.length === 0}
                        className="btn-danger flex items-center gap-2"
                    >
                        <Trash2 className="w-4 h-4" />
                        Clear All
                    </button>
                </div>
            </div>

            {/* Search & Stats */}
            <div className="grid md:grid-cols-3 gap-6">
                <div className="md:col-span-2 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search by filename or domain..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="input-field pl-10"
                    />
                </div>
                <div className="card px-5 py-2.5 flex items-center justify-between bg-surface-800/50">
                    <span className="text-xs text-gray-400 font-medium">Total Records</span>
                    <span className="text-xl font-bold text-white">{records.length}</span>
                </div>
            </div>

            {loading ? (
                <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="card p-6 h-32 animate-pulse" />
                    ))}
                </div>
            ) : error ? (
                <div className="card p-12 text-center border-danger-500/20 bg-danger-500/5">
                    <AlertCircle className="w-10 h-10 text-danger-400 mx-auto mb-4" />
                    <p className="text-danger-300 font-medium">{error}</p>
                    <button onClick={loadHistory} className="btn-primary mt-4">Try Again</button>
                </div>
            ) : filteredRecords.length === 0 ? (
                <div className="card p-20 text-center border-surface-600/30">
                    <FileText className="w-12 h-12 text-surface-600 mx-auto mb-4" />
                    <p className="text-gray-400">No screening history found.</p>
                    {searchTerm && <p className="text-xs text-gray-600 mt-1">Try changing your search filters.</p>}
                </div>
            ) : (
                <div className="grid gap-4">
                    {filteredRecords.map((record) => (
                        <div key={record.id} className="card p-5 group hover:border-brand-500/40 transition-all duration-200">
                            <div className="flex flex-col lg:flex-row gap-6">
                                {/* Info */}
                                <div className="flex-1 space-y-3">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h3 className="text-lg font-bold text-white group-hover:text-brand-400 transition-colors">
                                                {record.filename}
                                            </h3>
                                            <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3.5 h-3.5" />
                                                    {formatDate(record.created_at)}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <BarChart3 className="w-3.5 h-3.5" />
                                                    {record.domain}
                                                </span>
                                                {record.bias_free_mode && (
                                                    <span className="flex items-center gap-1 text-accent-400">
                                                        <Shield className="w-3.5 h-3.5" />
                                                        Bias-Free
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleDelete(record.id)}
                                            className="p-2 rounded-lg text-gray-600 hover:text-danger-400 hover:bg-danger-500/10 transition-colors"
                                            title="Delete record"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>

                                    <div className="flex flex-wrap gap-1.5">
                                        {record.matched_skills.slice(0, 8).map(skill => (
                                            <span key={skill} className="badge-skill-matched text-[10px] capitalize">{skill}</span>
                                        ))}
                                        {record.matched_skills.length > 8 && (
                                            <span className="text-[10px] text-gray-500 px-1 mt-0.5">+{record.matched_skills.length - 8} more</span>
                                        )}
                                    </div>
                                </div>

                                {/* Score Column */}
                                <div className="lg:w-72 border-l border-surface-700/50 pl-6 flex flex-col justify-center space-y-4">
                                    <ScoreBar label="Match Score" value={record.final_score} />
                                    <button
                                        onClick={() => handleAnalyse(record.id)}
                                        className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-brand-500/10 hover:bg-brand-500 text-brand-400 hover:text-white rounded-lg font-bold text-xs transition-all border border-brand-500/20"
                                    >
                                        <ExternalLink className="w-3.5 h-3.5" />
                                        Detailed Analysis
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
