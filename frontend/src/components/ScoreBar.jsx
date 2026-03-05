/**
 * Horizontal progress bar with label and value.
 */
export default function ScoreBar({ label, value, max = 100, color = 'brand' }) {
    const pct = Math.min(100, Math.max(0, (value / max) * 100))

    const colorClasses = {
        brand: 'from-brand-500 to-accent-500',
        success: 'from-success-500 to-success-400',
        warn: 'from-warn-500 to-warn-400',
        danger: 'from-danger-500 to-danger-400',
    }

    const getBarColor = (pct) => {
        if (pct >= 80) return colorClasses.success
        if (pct >= 60) return colorClasses.brand
        if (pct >= 40) return colorClasses.warn
        return colorClasses.danger
    }

    const barColor = getBarColor(pct)
    const displayValue = typeof value === 'number' ? `${Math.round(value)}%` : value

    return (
        <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400 font-medium">{label}</span>
                <span className="text-white font-bold">{displayValue}</span>
            </div>
            <div className="h-2 w-full bg-surface-700 rounded-full overflow-hidden">
                <div
                    className={`h-full bg-gradient-to-r ${barColor} rounded-full transition-all duration-700 ease-out`}
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    )
}
