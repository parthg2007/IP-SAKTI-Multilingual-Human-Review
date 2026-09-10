import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import Icon from './LandingIcon.jsx'

const starters = [
  { icon: 'grid', label: 'Protect an idea', text: 'What kind of IP could be relevant to my Ayurvedic product?' },
  { icon: 'balance', label: 'Understand ABS', text: 'What should I consider when sourcing a medicinal plant?' },
  { icon: 'search', label: 'Explore prior art', text: 'How do I begin a prior-art search for a herbal formulation?' },
]

export default function ChatWelcome({ onPromptSelect }) {
  const welcomeRef = useRef(null)

  useEffect(() => {
    const media = gsap.matchMedia()
    media.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.from('[data-welcome-part]', { y: 18, opacity: 0, duration: 0.7, stagger: 0.09, ease: 'power3.out' })
    }, welcomeRef)
    return () => media.revert()
  }, [])

  return (
    <section ref={welcomeRef} aria-label="Suggested questions" className="mx-auto flex min-h-full w-full max-w-[880px] flex-col justify-center px-5 py-9 text-center sm:px-8 sm:py-12">
      <div data-welcome-part className="mt-9 grid gap-3 text-left sm:grid-cols-3">
        {starters.map((starter) => (
          <button key={starter.label} type="button" onClick={() => onPromptSelect(starter.text)} className="group flex cursor-pointer flex-col rounded-2xl border border-[var(--lp-line)] bg-[var(--lp-card)]/70 p-4 text-left transition-[border-color,background-color,transform] duration-200 hover:border-[var(--lp-accent)] hover:bg-[var(--lp-card)] focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-[var(--lp-accent)] motion-safe:hover:-translate-y-1 motion-reduce:transition-none sm:p-5">
            <span className="mb-3 flex w-full items-center justify-between text-[var(--lp-accent)]"><Icon name={starter.icon} className="size-[18px]" /><Icon name="diagonal" className="size-4 opacity-40 transition-opacity group-hover:opacity-100" /></span>
            <span className="text-sm font-medium text-[var(--lp-ink)]">{starter.label}</span>
            <span className="mt-2 font-['Source_Sans_3',sans-serif] text-base leading-snug text-[var(--lp-muted)]">{starter.text}</span>
          </button>
        ))}
      </div>
    </section>
  )
}
