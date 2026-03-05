import { Link } from 'react-router-dom'
import {
    BrainCircuit, Upload, Zap, Shield, BarChart3, Lightbulb,
    ArrowRight, CheckCircle2, FileSearch
} from 'lucide-react'

const features = [
    {
        icon: Upload,
        title: 'PDF Resume Parsing',
        desc: 'Upload any PDF resume. We extract skills, years of experience, and domain classification automatically.',
        color: 'text-brand-400',
        bg: 'bg-brand-500/10',
    },
    {
        icon: BarChart3,
        title: 'Weighted Match Scoring',
        desc: 'Explainable score: 50% skill overlap + 30% experience match + 20% domain alignment.',
        color: 'text-success-400',
        bg: 'bg-success-500/10',
    },
    {
        icon: Shield,
        title: 'Bias-Free Evaluation',
        desc: 'Toggle to strip names, gender, location, and college — judge purely on merit.',
        color: 'text-accent-400',
        bg: 'bg-accent-500/10',
    },
    {
        icon: Lightbulb,
        title: 'Career Recommendations',
        desc: 'If score < 60%, get 3 better-fit domains and a 5-step skill acquisition roadmap.',
        color: 'text-warn-400',
        bg: 'bg-warn-500/10',
    },
    {
        icon: Zap,
        title: 'Fully Offline',
        desc: 'No external APIs. No data sent anywhere. Everything runs locally on your machine.',
        color: 'text-success-400',
        bg: 'bg-success-500/10',
    },
    {
        icon: BrainCircuit,
        title: 'Smart Skill Taxonomy',
        desc: '200+ skills across 15+ technology domains, with intelligent domain classification.',
        color: 'text-brand-400',
        bg: 'bg-brand-500/10',
    },
]

const steps = [
    { n: '01', title: 'Upload Resume', desc: 'Drag & drop a PDF resume into the dashboard.' },
    { n: '02', title: 'Paste Job Description', desc: 'Enter the job requirements text.' },
    { n: '03', title: 'Set Preferences', desc: 'Enable bias-free mode if needed.' },
    { n: '04', title: 'Get Results', desc: 'View explainable scores, gaps, and roadmap.' },
]

export default function Home() {
    return (
        <div className="animate-fade-in">
            {/* Hero Section */}
            <section className="relative overflow-hidden py-24 px-4">
                {/* Background blobs */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl animate-pulse-slow" />
                    <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
                </div>

                <div className="relative max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-semibold mb-6">
                        <Zap className="w-3.5 h-3.5" />
                        Fully Offline · No External APIs · Privacy First
                    </div>

                    <h1 className="text-5xl sm:text-6xl font-extrabold text-white leading-tight mb-6">
                        AI Resume Screening &{' '}
                        <span className="text-gradient">Skill Matching</span>{' '}
                        Platform
                    </h1>

                    <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mb-10">
                        Upload a resume, paste a job description, and get an explainable weighted match score
                        with skill gap analysis, bias-free evaluation, and career recommendations — all running locally.
                    </p>

                    <div className="flex items-center justify-center gap-4 flex-wrap">
                        <Link to="/dashboard" id="hero-cta-screen" className="btn-primary text-base px-8 py-3">
                            <FileSearch className="w-5 h-5" />
                            Start Screening
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                        <Link to="/dashboard" id="hero-cta-dashboard" className="btn-secondary text-base px-8 py-3">
                            View Dashboard
                        </Link>
                    </div>

                    {/* Score preview */}
                    <div className="mt-16 grid grid-cols-3 gap-4 max-w-md mx-auto">
                        {[
                            { label: 'Skill Match', val: '72%', color: 'text-brand-400' },
                            { label: 'Experience', val: '85%', color: 'text-success-400' },
                            { label: 'Domain', val: '100%', color: 'text-accent-400' },
                        ].map(({ label, val, color }) => (
                            <div key={label} className="card px-4 py-3 text-center">
                                <p className={`text-2xl font-extrabold ${color}`}>{val}</p>
                                <p className="text-xs text-gray-500 mt-1">{label}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="py-20 px-4 border-t border-surface-700/40">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold text-white mb-3">Everything you need</h2>
                        <p className="text-gray-400 max-w-xl mx-auto">
                            A complete recruitment evaluation toolkit built for fairness, transparency, and accuracy.
                        </p>
                    </div>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {features.map(({ icon: Icon, title, desc, color, bg }) => (
                            <div key={title} className="card p-5 group hover:border-surface-500/80 transition-colors duration-200">
                                <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center mb-4`}>
                                    <Icon className={`w-5 h-5 ${color}`} />
                                </div>
                                <h3 className="font-bold text-white mb-2">{title}</h3>
                                <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How it works */}
            <section className="py-20 px-4 border-t border-surface-700/40">
                <div className="max-w-4xl mx-auto">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold text-white mb-3">How it works</h2>
                        <p className="text-gray-400">From upload to insight in under 5 seconds.</p>
                    </div>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {steps.map(({ n, title, desc }, i) => (
                            <div key={n} className="relative card p-5">
                                <span className="text-4xl font-extrabold text-surface-600 leading-none">{n}</span>
                                <h3 className="font-bold text-white mt-2 mb-1">{title}</h3>
                                <p className="text-sm text-gray-400">{desc}</p>
                                {i < steps.length - 1 && (
                                    <ArrowRight className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 text-surface-600" />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Banner */}
            <section className="py-16 px-4 border-t border-surface-700/40">
                <div className="max-w-2xl mx-auto card p-10 text-center bg-brand-gradient border-0 shadow-glow-brand">
                    <CheckCircle2 className="w-10 h-10 text-white/80 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-3">Ready to screen resumes?</h2>
                    <p className="text-white/70 mb-6 text-sm">
                        No account needed. No API keys. Just upload and screen.
                    </p>
                    <Link to="/dashboard" id="bottom-cta" className="inline-flex items-center gap-2 bg-white text-brand-600 font-bold px-8 py-3 rounded-lg hover:bg-gray-100 transition-colors">
                        <FileSearch className="w-5 h-5" />
                        Open Dashboard
                    </Link>
                </div>
            </section>
        </div>
    )
}
