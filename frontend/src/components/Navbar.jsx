import { Link, useLocation } from 'react-router-dom'
import { BrainCircuit, LayoutDashboard, Home, FileSearch } from 'lucide-react'

const navItems = [
    { to: '/', label: 'Home', icon: Home },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/history', label: 'History', icon: FileSearch },
]

export default function Navbar() {
    const { pathname } = useLocation()

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

                    {/* CTA */}
                    <Link to="/history" className="nav-link">
                        <span className="flex items-center gap-1.5">
                            <LayoutDashboard className="w-4 h-4" />
                            Recruiter Mode
                        </span>
                    </Link>
                    <Link to="/dashboard" className="btn-primary text-xs px-4 py-2">
                        <FileSearch className="w-4 h-4" />
                        Screen Resume
                    </Link>
                </div>
            </div>
        </header>
    )
}
