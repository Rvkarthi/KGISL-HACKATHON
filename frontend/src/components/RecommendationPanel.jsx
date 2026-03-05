import { BookOpen, ArrowRight, Target, Lightbulb } from 'lucide-react'

/**
 * Displays a learning roadmap and domain/skill recommendations.
 */
export default function RecommendationPanel({ roadmap = [], recommendedDomains = [], topSkills = [], score = 0 }) {
    const showDomainRecs = score < 60 && recommendedDomains.length > 0

    return (
        <div className="space-y-4">
            {/* Learning Roadmap */}
            {roadmap.length > 0 && (
                <div className="card p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-brand-500/20 flex items-center justify-center">
                            <BookOpen className="w-4 h-4 text-brand-400" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white">Learning Roadmap</h3>
                            <p className="text-xs text-gray-500">Steps to close your skill gaps</p>
                        </div>
                    </div>
                    <ol className="space-y-2.5">
                        {roadmap.map((step, i) => (
                            <li key={i} className="flex items-start gap-3">
                                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-500/20 border border-brand-500/40 text-brand-400 text-xs font-bold flex items-center justify-center mt-0.5">
                                    {i + 1}
                                </span>
                                <span className="text-sm text-gray-300 leading-relaxed">{step}</span>
                            </li>
                        ))}
                    </ol>
                </div>
            )}

            {/* Top skills to gain */}
            {topSkills.length > 0 && (
                <div className="card p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-warn-500/20 flex items-center justify-center">
                            <Target className="w-4 h-4 text-warn-400" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white">Top Skills to Acquire</h3>
                            <p className="text-xs text-gray-500">Highest-impact skills for this role</p>
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {topSkills.map((skill) => (
                            <span
                                key={skill}
                                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-warn-500/10 text-warn-400 border border-warn-500/20"
                            >
                                <ArrowRight className="w-3 h-3" />
                                {skill}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Domain Recommendations (only when score < 60%) */}
            {showDomainRecs && (
                <div className="card p-5 border-accent-500/30">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-accent-500/20 flex items-center justify-center">
                            <Lightbulb className="w-4 h-4 text-accent-400" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white">Better-Fit Domains</h3>
                            <p className="text-xs text-gray-500">
                                Your current score is below 60% — consider these roles instead
                            </p>
                        </div>
                    </div>
                    <div className="grid gap-2">
                        {recommendedDomains.map((domain, i) => (
                            <div
                                key={domain}
                                className="flex items-center gap-3 px-4 py-3 rounded-lg bg-surface-700/60 border border-surface-600/50"
                            >
                                <span className="text-accent-400 font-bold text-sm">#{i + 1}</span>
                                <span className="text-gray-200 text-sm font-medium">{domain}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {roadmap.length === 0 && topSkills.length === 0 && !showDomainRecs && (
                <div className="card p-5 text-center">
                    <p className="text-gray-400 text-sm">No additional recommendations — excellent match!</p>
                </div>
            )}
        </div>
    )
}
