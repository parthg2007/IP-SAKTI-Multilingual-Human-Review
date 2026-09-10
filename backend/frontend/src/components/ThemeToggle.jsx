export default function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label="Dark mode"
      aria-pressed={isDark}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="fixed top-4 right-3 z-20 grid size-11 cursor-pointer place-items-center rounded-full border border-[var(--lp-strong-line)] bg-[var(--lp-surface)] text-[var(--lp-accent)] transition-colors duration-200 hover:bg-[var(--lp-card)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lp-accent)] motion-reduce:transition-none md:top-7 md:right-6"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={`transition-transform duration-300 motion-reduce:transition-none ${isDark ? 'rotate-90' : 'rotate-0'}`}>
        {isDark ? (
          <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></>
        ) : (
          <path d="M20.8 13.2A9 9 0 0 1 10.8 3.2a9 9 0 1 0 10 10Z" />
        )}
      </svg>
    </button>
  )
}
