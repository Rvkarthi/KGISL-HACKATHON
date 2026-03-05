import { Shield, ShieldOff, Info } from 'lucide-react'
import { useState } from 'react'

/**
 * Toggle for enabling/disabling bias-free evaluation mode.
 * Shows an explanation tooltip when the (i) icon is clicked.
 */
export default function BiasFreeToggle({ enabled, onChange }) {
    const [showInfo, setShowInfo] = useState(false)

    return (
        <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between p-4 rounded-xl border border-surface-600 bg-surface-800/50">
                <div className="flex items-center gap-3">
                    {enabled ? (
                        <Shield className="w-5 h-5 text-accent-400" />
                    ) : (
                        <ShieldOff className="w-5 h-5 text-gray-500" />
                    )}
                    <div>
                        <p className="text-sm font-semibold text-white">Bias-Free Evaluation</p>
                        <p className="text-xs text-gray-500">
                            {enabled ? 'Personal identifiers removed from analysis' : 'Standard evaluation mode'}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => setShowInfo(!showInfo)}
                        className="text-gray-500 hover:text-gray-300 transition-colors"
                        aria-label="Bias-free mode information"
                    >
                        <Info className="w-4 h-4" />
                    </button>
                    {/* Toggle switch */}
                    <button
                        id="bias-free-toggle"
                        type="button"
                        role="switch"
                        aria-checked={enabled}
                        onClick={() => onChange(!enabled)}
                        className={`
              relative inline-flex h-6 w-11 items-center rounded-full
              transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2 focus:ring-offset-surface-800
              ${enabled ? 'bg-accent-600' : 'bg-surface-600'}
            `}
                    >
                        <span
                            className={`
                inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200
                ${enabled ? 'translate-x-6' : 'translate-x-1'}
              `}
                        />
                    </button>
                </div>
            </div>

            {showInfo && (
                <div className="px-4 py-3 rounded-lg bg-accent-500/10 border border-accent-500/20 text-xs text-gray-300 space-y-1 animate-fade-in">
                    <p className="font-semibold text-accent-300 mb-1">What gets removed in Bias-Free mode:</p>
                    <ul className="space-y-0.5 list-disc list-inside text-gray-400">
                        <li>Candidate name and title (Mr/Mrs/Dr)</li>
                        <li>Gender-indicating pronouns (he/she/his/her)</li>
                        <li>College and university names</li>
                        <li>Geographic location (city, state, country)</li>
                        <li>Contact details (email, phone)</li>
                    </ul>
                    <p className="text-gray-500 mt-2 italic">
                        Evaluation focuses purely on skills, experience, and domain expertise.
                    </p>
                </div>
            )}
        </div>
    )
}
