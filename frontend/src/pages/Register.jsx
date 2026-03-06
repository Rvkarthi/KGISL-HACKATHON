import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Mail, Lock, User, Loader2, ArrowRight, BrainCircuit, Briefcase, Building2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function Register() {
    const [role, setRole] = useState('normal') // 'normal' or 'hr'
    const [formData, setFormData] = useState({
        email: '',
        full_name: '',
        password: '',
        confirm_password: '',
        company_name: '',
        department: '',
        job_title: '',
    })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const { registerNormal, registerHR } = useAuth()
    const navigate = useNavigate()

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
            if (formData.password !== formData.confirm_password) {
                setError('Passwords do not match.')
                setLoading(false)
                return
            }
            if (role === 'normal') {
                await registerNormal({
                    email: formData.email,
                    full_name: formData.full_name,
                    password: formData.password,
                    confirm_password: formData.confirm_password,
                })
            } else {
                await registerHR(formData)
            }
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed. Email might already exist.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 py-12">
            <div className="max-w-xl w-full animate-slide-up">
                <div className="card p-8 relative overflow-hidden">
                    {/* Decorative Background */}
                    <div className="absolute top-0 right-0 w-48 h-48 bg-brand-500/10 rounded-full blur-3xl -mr-24 -mt-24"></div>
                    <div className="absolute bottom-0 left-0 w-48 h-48 bg-accent-500/10 rounded-full blur-3xl -ml-24 -mb-24"></div>

                    <div className="relative">
                        <div className="flex flex-col items-center mb-8">
                            <div className="w-12 h-12 rounded-xl bg-brand-gradient flex items-center justify-center shadow-glow-brand mb-4">
                                <BrainCircuit className="w-7 h-7 text-white" />
                            </div>
                            <h1 className="text-2xl font-bold text-white">Create Account</h1>
                            <p className="text-gray-400 text-sm mt-1">Join ResumeAI to supercharge your recruitment</p>
                        </div>

                        {/* Role Selector */}
                        <div className="flex p-1 bg-surface-800 rounded-xl border border-surface-600 mb-8 max-w-xs mx-auto">
                            <button
                                onClick={() => setRole('normal')}
                                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${role === 'normal' ? 'bg-surface-600 text-white shadow-lg' : 'text-gray-500 hover:text-gray-300'
                                    }`}
                            >
                                <User className="w-3.5 h-3.5" />
                                Candidate
                            </button>
                            <button
                                onClick={() => setRole('hr')}
                                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${role === 'hr' ? 'bg-brand-500 text-white shadow-glow-brand' : 'text-gray-500 hover:text-gray-300'
                                    }`}
                            >
                                <Briefcase className="w-3.5 h-3.5" />
                                Recruiter / HR
                            </button>
                        </div>

                        {error && (
                            <div className="mb-6 p-4 rounded-lg bg-danger-500/10 border border-danger-500/30 text-danger-400 text-sm animate-fade-in">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                        Full Name
                                    </label>
                                    <div className="relative">
                                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            name="full_name"
                                            type="text"
                                            required
                                            value={formData.full_name}
                                            onChange={handleChange}
                                            className="input-field pl-11"
                                            placeholder="John Doe"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                        Email Address
                                    </label>
                                    <div className="relative">
                                        <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            name="email"
                                            type="email"
                                            required
                                            value={formData.email}
                                            onChange={handleChange}
                                            className="input-field pl-11"
                                            placeholder="john@example.com"
                                        />
                                    </div>
                                </div>
                            </div>

                            {role === 'hr' && (
                                <>
                                    <div className="grid md:grid-cols-2 gap-4 animate-fade-in">
                                        <div>
                                            <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                                Company Name
                                            </label>
                                            <div className="relative">
                                                <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                                <input
                                                    name="company_name"
                                                    type="text"
                                                    required={role === 'hr'}
                                                    value={formData.company_name}
                                                    onChange={handleChange}
                                                    className="input-field pl-11"
                                                    placeholder="TechCorp Inc."
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                                Job Title
                                            </label>
                                            <div className="relative">
                                                <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                                <input
                                                    name="job_title"
                                                    type="text"
                                                    required={role === 'hr'}
                                                    value={formData.job_title}
                                                    onChange={handleChange}
                                                    className="input-field pl-11"
                                                    placeholder="Talent Acquisition"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}

                            <div className="grid md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                        Password
                                    </label>
                                    <div className="relative">
                                        <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            name="password"
                                            type="password"
                                            required
                                            value={formData.password}
                                            onChange={handleChange}
                                            className="input-field pl-11"
                                            placeholder="••••••••"
                                        />
                                    </div>
                                    <p className="text-[10px] text-gray-500 mt-1 ml-1">Min. 8 characters</p>
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                        Confirm Password
                                    </label>
                                    <div className="relative">
                                        <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            name="confirm_password"
                                            type="password"
                                            required
                                            value={formData.confirm_password}
                                            onChange={handleChange}
                                            className="input-field pl-11"
                                            placeholder="••••••••"
                                        />
                                    </div>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="btn-primary w-full py-3 mt-4"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Creating Account...
                                    </>
                                ) : (
                                    <>
                                        Get Started
                                        <ArrowRight className="w-4 h-4" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-8 text-center border-t border-surface-600 pt-6">
                            <p className="text-gray-500 text-sm">
                                Already have an account?{' '}
                                <Link to="/login" className="text-brand-400 font-bold hover:text-brand-300 transition-colors">
                                    Sign In
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
