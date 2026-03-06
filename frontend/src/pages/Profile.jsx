import { useState } from 'react'
import { User, Mail, Briefcase, Building2, Shield, Calendar, Key, Loader2, Save } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import api from '../services/api'

export default function Profile() {
    const { user } = useAuth()
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState('')
    const [formData, setFormData] = useState({
        full_name: user?.full_name || '',
        company_name: user?.company || '',
        department: '',
        job_title: '',
    })

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value })
    }

    const handleUpdate = async (e) => {
        e.preventDefault()
        setLoading(true)
        setMessage('')
        try {
            await api.patch('/api/auth/me/profile', formData)
            setMessage('Profile updated successfully!')
        } catch (err) {
            setMessage('Failed to update profile.')
        } finally {
            setLoading(false)
        }
    }

    if (!user) return null

    return (
        <div className="max-w-4xl mx-auto px-4 py-10 animate-slide-up space-y-8">
            <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-brand-gradient flex items-center justify-center shadow-glow-brand">
                    <User className="w-8 h-8 text-white" />
                </div>
                <div>
                    <h1 className="text-3xl font-extrabold text-white">{user.full_name}</h1>
                    <p className="text-gray-400 flex items-center gap-2 mt-1">
                        <Shield className="w-4 h-4 text-brand-400" />
                        {user.is_hr ? 'HR / Recruiter Account' : 'Candidate Account'}
                    </p>
                </div>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
                {/* Info Sidebar */}
                <div className="space-y-4">
                    <div className="card p-5">
                        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Account Details</h2>
                        <div className="space-y-4">
                            <div className="flex items-start gap-3">
                                <Mail className="w-4 h-4 text-gray-500 mt-0.5" />
                                <div>
                                    <p className="text-[10px] text-gray-500 uppercase font-bold">Email</p>
                                    <p className="text-sm text-gray-200">{user.email}</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <Calendar className="w-4 h-4 text-gray-500 mt-0.5" />
                                <div>
                                    <p className="text-[10px] text-gray-500 uppercase font-bold">Member Since</p>
                                    <p className="text-sm text-gray-200">March 2026</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card p-5 bg-surface-800/50">
                        <div className="flex items-center gap-2 text-brand-400 mb-2">
                            <Key className="w-4 h-4" />
                            <h3 className="text-sm font-bold">Security</h3>
                        </div>
                        <p className="text-xs text-gray-500 mb-4">Keep your account secure by using a strong password.</p>
                        <button className="btn-secondary w-full text-xs py-2">Change Password</button>
                    </div>
                </div>

                {/* Main Form */}
                <div className="md:col-span-2 space-y-6">
                    <div className="card p-8">
                        <h2 className="section-title mb-6">Profile Settings</h2>

                        {message && (
                            <div className={`mb-6 p-4 rounded-lg text-sm animate-fade-in ${message.includes('success')
                                    ? 'bg-success-500/10 border border-success-500/30 text-success-400'
                                    : 'bg-danger-500/10 border border-danger-500/30 text-danger-400'
                                }`}>
                                {message}
                            </div>
                        )}

                        <form onSubmit={handleUpdate} className="space-y-6">
                            <div className="grid md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2 ml-1">
                                        Full Name
                                    </label>
                                    <div className="relative">
                                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            name="full_name"
                                            value={formData.full_name}
                                            onChange={handleChange}
                                            className="input-field pl-11"
                                        />
                                    </div>
                                </div>
                                {user.is_hr && (
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2 ml-1">
                                            Company Name
                                        </label>
                                        <div className="relative">
                                            <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                            <input
                                                name="company_name"
                                                value={formData.company_name}
                                                onChange={handleChange}
                                                className="input-field pl-11"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {user.is_hr && (
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2 ml-1">
                                            Department
                                        </label>
                                        <input
                                            name="department"
                                            value={formData.department}
                                            onChange={handleChange}
                                            className="input-field"
                                            placeholder="e.g. Engineering"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2 ml-1">
                                            Job Title
                                        </label>
                                        <input
                                            name="job_title"
                                            value={formData.job_title}
                                            onChange={handleChange}
                                            className="input-field"
                                            placeholder="e.g. Senior Recruiter"
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-end pt-4 border-t border-surface-700">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="btn-primary px-8"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="w-4 h-4" />
                                            Update Profile
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    )
}
