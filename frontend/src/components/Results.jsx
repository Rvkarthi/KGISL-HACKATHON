import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import {
    ArrowLeft, Shield, CheckCircle2, XCircle,
    Briefcase, Clock, Globe2, TrendingUp
} from 'lucide-react'
import ScoreRing from '../components/ScoreRing'
import ScoreBar from '../components/ScoreBar'
import SkillGrid from '../components/SkillGrid'
import RecommendationPanel from '../components/RecommendationPanel'

export default function Results() {
    const { state } = useLocation()
    const navigate = useNavigate()
    const result = state?.result

    useEffect(() => {
        if (!result) {
            navigate('/dashboard')
        }
    }, [result, navigate])

    if (!result) return null

    const {
        filename,
        candidate_name,
        email,
        phone,
        final_score,
        skill_score,
        experience_score,
        domain_score,
        matched_skills,
        missing_skills,
        experience_gap,
        domain_match,
        candidate_domain,
        job_domain,
        candidate_experience,
        required_experience,
        bias_free_mode,
        learning_roadmap,
        recommended_domains,
        top_skills_to_gain,
    } = result

    const getScoreVerdict = (s) => {
        if (s >= 80) return { label: 'Strong Match', color: 'text-success-400', bg: 'bg-success-500/10 border-success-500/30' }
        if (s >= 60) return { label: 'Good Match', color: 'text-warn-400', bg: 'bg-warn-500/10 border-warn-500/30' }
        if (s >= 40) return { label: 'Partial Match', color: 'text-warn-500', bg: 'bg-warn-500/10 border-warn-500/20' }
        return { label: 'Low Match', color: 'text-danger-400', bg: 'bg-danger-500/10 border-danger-500/30' }
    }

    const verdict = getScoreVerdict(final_score)

    return (
        <div className="max-w-6xl mx-auto px-4 py-10 animate-slide-up space-y-8">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        id="back-to-dashboard"
                        onClick={() => navigate('/dashboard')}
                        className="btn-secondary text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Screen Another
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-white leading-tight">
                            {candidate_name || 'Anonymous Candidate'}
                        </h1>
                        <p className="text-xs text-gray-500 font-mono mt-0.5">
                            {filename} {email && `• ${email}`} {phone && `• ${phone}`}
                        </p>
                    </div>
                </div>

                {bias_free_mode && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-500/10 border border-accent-500/30 text-accent-300 text-xs font-semibold">
                        <Shield className="w-3.5 h-3.5" />
                        Bias-Free Mode Active
                    </div>
                )}
            </div>

            {/* Score Summary Hero */}
            <div className="card p-8">
                <div className="flex flex-col md:flex-row items-center gap-8">
                    {/* Big Score Ring */}
                    <div className="flex-shrink-0">
                        <ScoreRing score={final_score} size={160} strokeWidth={12} label="Final Score" />
                    </div>

                    {/* Verdict + sub-bars */}
                    <div className="flex-1 w-full">
                        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-bold border mb-4 ${verdict.bg} ${verdict.color}`}>
                            <TrendingUp className="w-4 h-4" />
                            {verdict.label}
                        </div>

                        <div className="space-y-4">
                            <ScoreBar label="Skill Match Score (50% weight)" value={skill_score} />
                            <ScoreBar label="Experience Match Score (30% weight)" value={experience_score} />
                            <ScoreBar label="Domain Alignment Score (20% weight)" value={domain_score} />
                        </div>

                        <p className="text-xs text-gray-500 mt-4 font-mono">
                            Final = 0.5×Skill + 0.3×Experience + 0.2×Domain = {final_score.toFixed(1)}%
                        </p>
                    </div>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card p-4 text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <Briefcase className="w-4 h-4 text-brand-400" />
                        <span className="text-xs text-gray-500 font-medium">Candidate Domain</span>
                    </div>
                    <p className="text-sm font-bold text-white">{candidate_domain || '—'}</p>
                </div>

                <div className="card p-4 text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <Globe2 className="w-4 h-4 text-accent-400" />
                        <span className="text-xs text-gray-500 font-medium">Job Domain</span>
                    </div>
                    <p className="text-sm font-bold text-white">{job_domain || '—'}</p>
                </div>

                <div className="card p-4 text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <Clock className="w-4 h-4 text-success-400" />
                        <span className="text-xs text-gray-500 font-medium">Experience</span>
                    </div>
                    <p className="text-sm font-bold text-white">
                        {candidate_experience}y <span className="text-gray-500 font-normal">of</span> {required_experience}y required
                    </p>
                </div>

                <div className="card p-4 text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        {domain_match ? (
                            <CheckCircle2 className="w-4 h-4 text-success-400" />
                        ) : (
                            <XCircle className="w-4 h-4 text-danger-400" />
                        )}
                        <span className="text-xs text-gray-500 font-medium">Domain Match</span>
                    </div>
                    <p className={`text-sm font-bold ${domain_match ? 'text-success-400' : 'text-danger-400'}`}>
                        {domain_match ? 'Aligned' : 'Misaligned'}
                    </p>
                </div>
            </div>

            {/* Experience Gap Alert */}
            {experience_gap > 0 && (
                <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-warn-500/10 border border-warn-500/30">
                    <Clock className="w-5 h-5 text-warn-400 flex-shrink-0" />
                    <p className="text-sm text-warn-300">
                        <span className="font-bold">Experience Gap: </span>
                        Candidate has {candidate_experience} years; role requires {required_experience} years
                        — gap of <span className="font-bold">{experience_gap.toFixed(1)} years</span>.
                    </p>
                </div>
            )}

            {/* Skill Grid */}
            <div>
                <h2 className="section-title mb-4">Skill Analysis</h2>
                <SkillGrid matchedSkills={matched_skills} missingSkills={missing_skills} />
            </div>

            {/* Recommendations */}
            {(learning_roadmap?.length > 0 || top_skills_to_gain?.length > 0 || recommended_domains?.length > 0) && (
                <div>
                    <h2 className="section-title mb-4">Recommendations & Learning Roadmap</h2>
                    <RecommendationPanel
                        roadmap={learning_roadmap}
                        recommendedDomains={recommended_domains}
                        topSkills={top_skills_to_gain}
                        score={final_score}
                    />
                </div>
            )}

            {/* Bias Free Summary */}
            {bias_free_mode && (
                <div className="card p-5 border-accent-500/30">
                    <div className="flex items-start gap-3">
                        <Shield className="w-5 h-5 text-accent-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-semibold text-white text-sm mb-1">Bias-Free Evaluation Active</h3>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                This result was computed with personal identifiers removed — name, gender indicators,
                                college/university names, and location data were stripped before analysis.
                                Scores reflect only skills, experience, and domain alignment.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
