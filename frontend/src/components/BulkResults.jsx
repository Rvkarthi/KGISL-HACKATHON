import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { ArrowLeft, Mail, Phone, ExternalLink, Trophy, Filter } from 'lucide-react'

export default function BulkResults() {
    const { state } = useLocation()
    const navigate = useNavigate()
    const results = state?.results || []

    useEffect(() => {
        if (!results.length) {
            navigate('/dashboard')
        }
    }, [results, navigate])

    if (!results.length) return null

    return (
        <div className="max-w-6xl mx-auto px-4 py-10 animate-slide-up space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <button
                        id="back-btn"
                        onClick={() => navigate('/dashboard')}
                        className="btn-secondary w-10 h-10 rounded-full flex items-center justify-center p-0"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
                            Ranked Recruitment List
                            <Trophy className="w-6 h-6 text-accent-400" />
                        </h1>
                        <p className="text-gray-400 text-sm mt-1">
                            Analyzed {results.length} resumes against your job description.
                        </p>
                    </div>
                </div>

                <div className="bg-surface-800 border border-surface-600 rounded-xl px-4 py-3 flex items-center gap-4 shadow-xl">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-brand-400" />
                        <span className="text-xs text-gray-500 font-medium">Sort Strategy:</span>
                        <span className="text-xs text-white font-bold bg-brand-500/20 px-2 py-0.5 rounded border border-brand-500/30">
                            Highest Score First
                        </span>
                    </div>
                </div>
            </div>

            {/* Results Table */}
            <div className="card overflow-hidden shadow-2xl border-surface-600/50">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-surface-700/40 border-b border-surface-600">
                                <th className="px-6 py-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Rank</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Candidate Info</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Contact Details</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Experience / Domain</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest text-right">Match Score</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-700">
                            {results.map((res, index) => (
                                <tr key={index} className="hover:bg-brand-500/[0.03] transition-colors group">
                                    <td className="px-6 py-5">
                                        <div className={`
                                            inline-flex items-center justify-center w-8 h-8 rounded-lg text-xs font-black
                                            ${index === 0 ? 'bg-accent-500 text-white shadow-glow-accent scale-110' :
                                                index === 1 ? 'bg-brand-500/80 text-white' :
                                                    index === 2 ? 'bg-brand-500/60 text-white' :
                                                        'bg-surface-600 text-gray-400'}
                                        `}>
                                            #{index + 1}
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div>
                                            <p className="font-bold text-white group-hover:text-brand-400 transition-colors">
                                                {res.candidate_name || 'Unknown Candidate'}
                                            </p>
                                            <p className="text-[10px] text-gray-500 font-mono mt-1 flex items-center gap-1">
                                                <span className="w-1 h-1 rounded-full bg-surface-500"></span>
                                                {res.filename}
                                            </p>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="space-y-1.5">
                                            <div className="flex items-center gap-2 group/contact">
                                                <Mail className="w-3.5 h-3.5 text-brand-400/70" />
                                                <span className={`text-xs ${res.email ? 'text-gray-300' : 'text-gray-600 italic font-mono'}`}>
                                                    {res.email || 'null'}
                                                </span>
                                            </div>
                                            {res.phone && (
                                                <div className="flex items-center gap-2">
                                                    <Phone className="w-3.5 h-3.5 text-accent-400/70" />
                                                    <span className="text-xs text-gray-300">{res.phone}</span>
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="space-y-1">
                                            <div className="text-xs text-white font-semibold">
                                                {res.candidate_experience} Years <span className="text-[10px] text-gray-500 font-normal ml-1">of Experience</span>
                                            </div>
                                            <div className="text-[10px] text-brand-400 uppercase tracking-tighter bg-brand-500/10 inline-block px-1.5 py-0.5 rounded border border-brand-500/20">
                                                {res.candidate_domain}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 text-right">
                                        <div className="flex flex-col items-end">
                                            <div className={`text-xl font-black ${res.final_score >= 80 ? 'text-success-400' :
                                                    res.final_score >= 60 ? 'text-warn-400' :
                                                        res.final_score >= 40 ? 'text-warn-500' : 'text-danger-400'
                                                }`}>
                                                {res.final_score.toFixed(1)}%
                                            </div>
                                            <div className="w-20 h-1 bg-surface-700 rounded-full mt-1.5 overflow-hidden">
                                                <div
                                                    className={`h-full ${res.final_score >= 80 ? 'bg-success-500' :
                                                            res.final_score >= 60 ? 'bg-warn-500' :
                                                                res.final_score >= 40 ? 'bg-warn-600' : 'bg-danger-500'
                                                        }`}
                                                    style={{ width: `${res.final_score}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 text-right">
                                        <button
                                            id={`view-details-${index + 1}`}
                                            onClick={() => navigate('/results', { state: { result: res } })}
                                            className="inline-flex items-center gap-2 text-xs font-bold text-brand-400 hover:text-white bg-brand-500/10 hover:bg-brand-500 px-3 py-1.5 rounded-lg transition-all"
                                        >
                                            Analyze Detail
                                            <ExternalLink className="w-3 h-3" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Footer Tip */}
            <div className="flex items-center justify-center gap-2 grayscale opacity-50">
                <p className="text-xs text-gray-400 italic">
                    Click "Analyze Detail" for full skill mapping and learning roadmaps for any candidate.
                </p>
            </div>
        </div>
    )
}
