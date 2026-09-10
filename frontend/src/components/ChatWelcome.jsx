import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import Icon from './LandingIcon.jsx'
import logo from '../assets/landing-logo.webp'

const starters = [
  { icon: 'grid', label: 'Protect an idea', subtext: 'IP classification & strategy', text: 'What kind of IP could be relevant to my Ayurvedic product?' },
  { icon: 'balance', label: 'Understand ABS', subtext: 'Access & benefit sharing', text: 'What should I consider when sourcing a medicinal plant?' },
  { icon: 'search', label: 'Explore prior art', subtext: 'Prior-art exploration', text: 'How do I begin a prior-art search for a herbal formulation?' },
]

export default function ChatWelcome({ onPromptSelect }) {
  const welcomeRef = useRef(null)

  useEffect(() => {
    const media = gsap.matchMedia()
    media.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.from('[data-welcome-part]', { y: 22, opacity: 0, duration: 0.75, stagger: 0.1, ease: 'power3.out' })
    }, welcomeRef)
    return () => media.revert()
  }, [])

  return (
    <section ref={welcomeRef} aria-label="Suggested questions" className="mx-auto flex min-h-full w-full max-w-[880px] flex-col justify-center px-5 py-10 sm:px-8 sm:py-14">

      {/* Logo + headline — mirrors landing hero typography */}
      <div data-welcome-part className="mb-10 text-center">
        <div className="mb-6 flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-[var(--lp-accent)]/10 blur-xl scale-150" aria-hidden="true" />
            <img src={logo} alt="" className="relative size-16 rounded-full bg-[#F7F4ED] object-contain p-1 shadow-lg ring-1 ring-[var(--lp-line)]" />
          </div>
        </div>
        <p className="mb-3 flex items-center justify-center gap-3 text-xs font-medium tracking-[0.18em] text-[var(--lp-gold)] uppercase">
          <span className="h-px w-6 shrink-0 bg-current" />
          Ancient knowledge. New possibilities.
          <span className="h-px w-6 shrink-0 bg-current" />
        </p>
        <h1 className="font-['Merriweather',serif] text-3xl font-normal tracking-[-0.04em] sm:text-4xl">
          Your ideas.<br />
          <span className="italic text-[var(--lp-accent)]">Your rights.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-[480px] font-['Source_Sans_3',sans-serif] text-lg leading-relaxed text-[var(--lp-muted)]">
          Ask about IP categories, prior-art research, access & benefit sharing, or regulatory considerations.
        </p>
      </div>

      {/* Starter cards — elevated from landing toolkit style */}
      <div data-welcome-part className="grid gap-3 sm:grid-cols-3">
        {starters.map((starter) => (
          <button
            key={starter.label}
            type="button"
            onClick={() => onPromptSelect(starter.text)}
            className="group flex cursor-pointer flex-col rounded-2xl border border-[var(--lp-line)] bg-[var(--lp-card)]/80 p-5 text-left transition-[border-color,background-color,transform,box-shadow] duration-200 hover:border-[var(--lp-accent)] hover:bg-[var(--lp-card)] hover:shadow-lg hover:shadow-[var(--lp-accent)]/5 focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-[var(--lp-accent)] motion-safe:hover:-translate-y-1 motion-reduce:transition-none"
          >
            <span className="mb-4 flex w-full items-center justify-between">
              <span className="grid size-9 place-items-center rounded-xl bg-[var(--lp-surface)] text-[var(--lp-accent)] ring-1 ring-[var(--lp-line)]">
                <Icon name={starter.icon} className="size-[18px]" />
              </span>
              <Icon name="diagonal" className="size-4 text-[var(--lp-muted)] opacity-40 transition-opacity group-hover:opacity-100 group-hover:text-[var(--lp-accent)]" />
            </span>
            <span className="text-sm font-semibold tracking-[-0.01em] text-[var(--lp-ink)]">{starter.label}</span>
            <span className="mt-0.5 text-xs text-[var(--lp-gold)]">{starter.subtext}</span>
            <span className="mt-3 font-['Source_Sans_3',sans-serif] text-[15px] leading-snug text-[var(--lp-muted)]">{starter.text}</span>
          </button>
        ))}
      </div>

      {/* Bottom trust indicators — matches landing footer vibe */}
      <div data-welcome-part className="mt-8 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-[var(--lp-muted)]">
        <span className="flex items-center gap-1.5">
          <Icon name="book" className="size-3.5 text-[var(--lp-gold)]" />
          Source-grounded exploration
        </span>
        <span aria-hidden="true" className="hidden sm:block">·</span>
        <span className="flex items-center gap-1.5">
          <Icon name="globe" className="size-3.5 text-[var(--lp-accent)]" />
          Multilingual responses
        </span>
        <span aria-hidden="true" className="hidden sm:block">·</span>
        <span className="flex items-center gap-1.5">
          <Icon name="shield" className="size-3.5 text-[var(--lp-accent)]" />
          Human review path available
        </span>
      </div>
    </section>
  )
}
