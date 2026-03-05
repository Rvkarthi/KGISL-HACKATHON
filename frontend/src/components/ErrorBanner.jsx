import { AlertCircle } from 'lucide-react'

/**
 * A styled error banner component.
 */
export default function ErrorBanner({ message }) {
    if (!message) return null
    return (
        <div
            role="alert"
            className="flex items-start gap-3 px-4 py-3 rounded-xl bg-danger-500/10 border border-danger-500/30 animate-fade-in"
        >
            <AlertCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-danger-300">{message}</p>
        </div>
    )
}
