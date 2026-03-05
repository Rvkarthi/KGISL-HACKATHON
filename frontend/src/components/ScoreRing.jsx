/**
 * Animated circular score ring component.
 * Renders an SVG ring with a percentage label.
 */
export default function ScoreRing({ score, size = 140, strokeWidth = 10, label = 'Match Score' }) {
    const radius = (size - strokeWidth) / 2
    const circumference = 2 * Math.PI * radius
    const clampedScore = Math.min(100, Math.max(0, score))
    const offset = circumference - (clampedScore / 100) * circumference

    const getColor = (s) => {
        if (s >= 80) return '#10b981'  // success green
        if (s >= 60) return '#f59e0b'  // warn amber
        return '#ef4444'               // danger red
    }

    const color = getColor(clampedScore)

    const getLabel = (s) => {
        if (s >= 80) return 'Excellent'
        if (s >= 60) return 'Good'
        if (s >= 40) return 'Fair'
        return 'Low'
    }

    return (
        <div className="flex flex-col items-center gap-2">
            <div className="relative" style={{ width: size, height: size }}>
                <svg width={size} height={size} className="-rotate-90">
                    {/* Track */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke="rgba(255,255,255,0.08)"
                        strokeWidth={strokeWidth}
                    />
                    {/* Progress */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke={color}
                        strokeWidth={strokeWidth}
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        strokeLinecap="round"
                        style={{
                            transition: 'stroke-dashoffset 1s ease-in-out, stroke 0.5s ease',
                            filter: `drop-shadow(0 0 6px ${color}80)`,
                        }}
                    />
                </svg>
                {/* Center label */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-extrabold text-white leading-none">
                        {Math.round(clampedScore)}
                    </span>
                    <span className="text-xs text-gray-400 mt-0.5">%</span>
                </div>
            </div>
            <div className="text-center">
                <p className="text-sm font-medium text-gray-300">{label}</p>
                <p className="text-xs font-semibold mt-0.5" style={{ color }}>
                    {getLabel(clampedScore)}
                </p>
            </div>
        </div>
    )
}
