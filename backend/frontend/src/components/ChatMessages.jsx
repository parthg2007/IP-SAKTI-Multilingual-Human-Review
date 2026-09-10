import { useEffect, useRef } from 'react'
import Icon from './LandingIcon.jsx'
import Markdown from 'react-markdown'
import { safeSourceUrl } from '../lib/api.js'

const emptyMessages = []

const markdownComponents = {
  a: ({ href, children }) => {
    const url = safeSourceUrl(href)
    return url ? <a href={url} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>
  },
  img: ({ alt }) => <span>{alt}</span>,
}

export default function ChatMessages({ messages = emptyMessages, isGenerating = false, citationsLoading = false, emptyState, onRetry }) {
  const scrollRef = useRef(null)
  const followLatestRef = useRef(true)
  const firstRenderRef = useRef(true)
  const isEmpty = messages.length === 0 && !isGenerating && !citationsLoading

  useEffect(() => {
    const container = scrollRef.current
    if (isEmpty) {
      followLatestRef.current = true
      firstRenderRef.current = true
      return
    }
    if (followLatestRef.current) {
      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      container.scrollTo({
        top: container.scrollHeight,
        behavior: firstRenderRef.current || reduceMotion ? 'instant' : 'smooth',
      })
    }
    firstRenderRef.current = false
  }, [messages, isGenerating, citationsLoading, isEmpty])

  return (
    <div
      ref={scrollRef}
      className="min-h-0 flex-1 overflow-y-auto overscroll-contain"
      onScroll={() => {
        if (isEmpty) return
        const container = scrollRef.current
        followLatestRef.current = container.scrollHeight - container.scrollTop - container.clientHeight < 96
      }}
    >
      {isEmpty ? emptyState : (
      <div className="mx-auto w-full max-w-[880px] space-y-7 px-4 py-7 sm:px-8" role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions text">
        {messages.filter((message) => message.status !== 'loading').map((message) => (
          <article key={message.id} className={`flex items-start gap-3 motion-safe:animate-message-in ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.role !== 'user' && <span aria-hidden="true" className="mt-1 hidden size-9 shrink-0 place-items-center rounded-full border border-[var(--lp-line)] bg-[var(--lp-surface)] text-[var(--lp-gold)] sm:grid"><Icon name="spark" className="size-4" /></span>}
            <div className={`min-w-0 max-w-full rounded-2xl border border-[var(--lp-line)] px-5 py-4 sm:max-w-[85%] ${message.role === 'user' ? 'rounded-tr-md bg-[var(--lp-surface)]' : 'rounded-tl-md bg-[var(--lp-card)]'}`}>
              <p className="mb-2 text-xs font-medium tracking-wide text-[var(--lp-muted)]">{message.role === 'user' ? 'You' : 'IP-SAKTI'}{message.jurisdiction && ` · ${message.jurisdiction === 'international' ? 'International' : 'India'}`}</p>
              {message.role === 'user' || message.status === 'error' ? (
                <p role={message.status === 'error' ? 'alert' : undefined} className="whitespace-pre-wrap font-['Source_Sans_3',sans-serif] text-lg leading-8 wrap-anywhere">{message.content}</p>
              ) : (
                <div className="chat-answer font-['Source_Sans_3',sans-serif] text-lg leading-8 wrap-anywhere"><Markdown skipHtml components={markdownComponents}>{message.content}</Markdown></div>
              )}
              {message.status === 'error' && message.query && <button type="button" onClick={() => onRetry?.(message)} disabled={isGenerating} className="mt-3 cursor-pointer rounded-full border border-[var(--lp-strong-line)] px-4 py-2 text-sm text-[var(--lp-accent)] disabled:cursor-not-allowed disabled:opacity-40">Retry answer</button>}
              {message.citations?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2 border-t border-[var(--lp-line)] pt-3" aria-label="Sources">
                  {message.citations.map((citation, index) => {
                    const url = safeSourceUrl(citation.url)
                    const className = 'rounded-lg border border-[var(--lp-gold)]/60 bg-[var(--lp-surface)] px-2 py-1 font-[Inter,sans-serif] text-xs text-[var(--lp-muted)]'
                    return url ? <a key={citation.id ?? index} href={url} target="_blank" rel="noopener noreferrer" title={citation.sourceName} className={`${className} hover:text-[var(--lp-accent)] focus-visible:outline-2 focus-visible:outline-[var(--lp-accent)]`}>{citation.title}<span className="sr-only"> (opens in a new tab)</span></a>
                      : <span key={citation.id ?? index} className={className}>{citation.title}</span>
                  })}
                </div>
              )}
              {message.disclaimer && <p className="mt-4 border-t border-[var(--lp-line)] pt-3 text-xs leading-relaxed text-[var(--lp-muted)]">{message.disclaimer}</p>}
            </div>
          </article>
        ))}
        {isGenerating && (
          <div role="status" className="flex items-center gap-3 py-3 text-[var(--lp-muted)] motion-safe:animate-message-in">
            <span className="flex items-center gap-1.5" aria-hidden="true">
              <span className="size-1.5 rounded-full bg-[var(--lp-accent)] motion-safe:animate-[bounce_1.2s_infinite]" />
              <span className="size-1.5 rounded-full bg-[var(--lp-accent)] motion-safe:animate-[bounce_1.2s_150ms_infinite]" />
              <span className="size-1.5 rounded-full bg-[var(--lp-accent)] motion-safe:animate-[bounce_1.2s_300ms_infinite]" />
            </span>
            <span className="font-['Source_Sans_3',sans-serif] text-sm">Preparing your answer…</span>
          </div>
        )}
        {citationsLoading && (
          <div role="status" className="space-y-2 motion-safe:animate-message-in">
            <span className="font-['Source_Sans_3',sans-serif] text-sm text-[var(--lp-muted)]">Loading sources…</span>
            <div className="flex flex-wrap gap-2" aria-hidden="true">
              {[0, 1, 2].map((item) => (
                <div key={item} className="relative h-8 w-32 overflow-hidden rounded-lg border border-[var(--lp-gold)]/40 bg-[var(--lp-surface)]">
                  <span className="absolute inset-0 bg-linear-to-r from-transparent via-[var(--lp-accent)]/15 to-transparent motion-safe:animate-citation-shimmer motion-reduce:hidden" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      )}
    </div>
  )
}
