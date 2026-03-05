import { CheckCircle2, XCircle } from 'lucide-react'

/**
 * Displays two columns: matched skills (green) and missing skills (red).
 * Includes counts and a loading skeleton state.
 */
export default function SkillGrid({ matchedSkills = [], missingSkills = [], loading = false }) {
    if (loading) {
        return (
            <div className="grid md:grid-cols-2 gap-4">
                {[0, 1].map((col) => (
                    <div key={col} className="card p-4 space-y-3">
                        <div className="h-4 bg-surface-600 rounded w-1/3 animate-pulse" />
                        {Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="h-6 bg-surface-700 rounded animate-pulse" />
                        ))}
                    </div>
                ))}
            </div>
        )
    }

    return (
        <div className="grid md:grid-cols-2 gap-4">
            {/* Matched Skills */}
            <div className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                    <CheckCircle2 className="w-4 h-4 text-success-400" />
                    <h3 className="text-sm font-semibold text-white">
                        Matched Skills
                        <span className="ml-2 badge bg-success-500/20 text-success-400 border-success-500/30">
                            {matchedSkills.length}
                        </span>
                    </h3>
                </div>
                {matchedSkills.length === 0 ? (
                    <p className="text-xs text-gray-500 italic">No matching skills found.</p>
                ) : (
                    <div className="flex flex-wrap gap-2">
                        {matchedSkills.map((skill) => (
                            <span key={skill} className="badge-skill-matched capitalize">{skill}</span>
                        ))}
                    </div>
                )}
            </div>

            {/* Missing Skills */}
            <div className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                    <XCircle className="w-4 h-4 text-danger-400" />
                    <h3 className="text-sm font-semibold text-white">
                        Missing Skills
                        <span className="ml-2 badge bg-danger-500/10 text-danger-400 border-danger-500/20">
                            {missingSkills.length}
                        </span>
                    </h3>
                </div>
                {missingSkills.length === 0 ? (
                    <p className="text-xs text-gray-500 italic">No skill gaps — great match!</p>
                ) : (
                    <div className="flex flex-wrap gap-2">
                        {missingSkills.map((skill) => (
                            <span key={skill} className="badge-skill-missing capitalize">{skill}</span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
