import { Link, useLocation } from 'react-router-dom'
import { BrainCircuit, LayoutDashboard, Home, FileSearch, LogOut, User as UserIcon } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const navItems = [
    { to: '/', label: 'Home', icon: Home },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/history', label: 'History', icon: FileSearch },
]

export default function Navbar() {
    const { pathname } = useLocation()
    const { user, logout } = useAuth()

    return (
        <header className="sticky top-0 z-50 border-b border-surface-700/60 bg-surface-900/80 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2.5 group">
                        <div className="w-8 h-8 rounded-lg bg-brand-gradient flex items-center justify-center shadow-glow-brand group-hover:shadow-glow-accent transition-all duration-300">
                            <BrainCircuit className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-bold text-lg text-white tracking-tight">
                            Resume<span className="text-gradient">AI</span>
                        </span>
                    </Link>

                    {/* Nav links */}
                    <nav className="flex items-center gap-1">
                        {navItems.map(({ to, label, icon: Icon }) => (
                            <Link
                                key={to}
                                to={to}
                                className={pathname === to ? 'nav-link-active' : 'nav-link'}
                            >
                                <span className="flex items-center gap-1.5">
                                    <Icon className="w-4 h-4" />
                                    {label}
                                </span>
                            </Link>
                        ))}
                    </nav>

                    {/* Auth & CTAs */}
                    <div className="flex items-center gap-3">
                        {user ? (
                            <>
                                <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-surface-800 border border-surface-700">
                                    <Link to="/profile" className="w-6 h-6 rounded-full bg-brand-500/20 flex items-center justify-center border border-brand-500/30 hover:bg-brand-500/30 transition-all">
                                        <UserIcon className="w-3 h-3 text-brand-400" />
                                    </Link>
                                    <span className="text-xs font-semibold text-gray-200">{user.full_name}</span>
                                    <button
                                        onClick={logout}
                                        className="p-1 text-gray-500 hover:text-danger-400 transition-colors"
                                        title="Logout"
                                    >
                                        <LogOut className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                                <Link to="/dashboard" className="btn-primary text-xs px-4 py-2">
                                    <FileSearch className="w-4 h-4" />
                                    Screen Resume
                                </Link>
                            </>
                        ) : (
                            <>
                                <Link to="/login" className="nav-link">Sign In</Link>
                                <Link to="/register" className="btn-primary text-xs px-4 py-2">
                                    Get Started
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    )
}
