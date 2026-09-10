export default function ConfidenceBadge({ confidence }) {
  if (!confidence) return null
  const pct = Math.round((confidence.score || 0) * 100)
  const level = confidence.level || 'moderate'
  const label = level === 'high' ? 'High confidence' : level === 'low' ? 'Low confidence' : 'Moderate confidence'
  return (
    <div className="mt-4 rounded-xl border border-[var(--lp-line)] bg-[var(--lp-surface)] px-3 py-2.5" aria-label={`${label}, ${pct}%`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium tracking-wide text-[var(--lp-muted)]">
          <span className={`grid size-2.5 rounded-full ${level === 'high' ? 'bg-[var(--lp-action)]' : level === 'low' ? 'bg-[var(--lp-gold)]' : 'bg-[var(--lp-accent)]'}`} />
          {label}
        </div>
        <span className="text-xs font-semibold text-[var(--lp-ink)]">{pct}%</span>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-[var(--lp-line)]">
        <div className="h-full rounded-full bg-[var(--lp-accent)]" style={{ width: `${pct}%` }} />
      </div>
      {confidence.basis && <p className="mt-2 text-[11px] leading-4 text-[var(--lp-muted)]">{confidence.basis}</p>}
    </div>
  )
}
