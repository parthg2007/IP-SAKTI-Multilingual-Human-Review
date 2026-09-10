import { useFormContext, useWatch } from 'react-hook-form'
import Icon from './LandingIcon.jsx'

export default function InputBar({ jurisdiction = 'india', isGenerating = false, onSend, onStop }) {
  const { register, control, handleSubmit } = useFormContext()
  const hasMessage = Boolean(useWatch({ control, name: 'message' })?.trim())
  const submit = handleSubmit(({ message }) => {
    if (!isGenerating && message.trim()) onSend(message)
  })

  return (
    <form onSubmit={submit} className="rounded-2xl border border-[var(--lp-strong-line)] bg-[var(--lp-card)] p-4 shadow-[0_8px_36px_-20px_#00000030] transition-[border-color,box-shadow] duration-200 focus-within:border-[var(--lp-accent)] focus-within:ring-2 focus-within:ring-[var(--lp-accent)]/10 motion-reduce:transition-none sm:rounded-3xl sm:p-5">
      <textarea
        {...register('message')}
        aria-label="Message"
        placeholder="Tell me about your idea, research, or next step…"
        rows={2}
        maxLength={4000}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault()
            void submit()
          }
        }}
        className="block max-h-40 min-h-14 w-full resize-y border-0 bg-transparent font-['Source_Sans_3',sans-serif] text-lg leading-7 text-[var(--lp-ink)] outline-none placeholder:text-[var(--lp-muted)]"
      />
      <div className="mt-3 flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-2 rounded-full border border-[var(--lp-line)] bg-[var(--lp-surface)] px-3 py-1.5 text-xs text-[var(--lp-muted)]"><Icon name="globe" className="size-3.5" />{jurisdiction === 'india' ? 'India' : 'International'} context</span>
        <button type={isGenerating ? 'button' : 'submit'} onClick={isGenerating ? onStop : undefined} disabled={!isGenerating && !hasMessage} aria-label={isGenerating ? 'Stop response' : 'Send message'} title={isGenerating ? 'Stop response' : 'Send message (Enter; Shift+Enter for a new line)'} className="group relative grid size-11 shrink-0 cursor-pointer place-items-center rounded-full border border-[var(--lp-action)] bg-[var(--lp-action)] text-[var(--lp-on-action)] transition-[filter,transform] duration-200 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-[var(--lp-accent)] motion-safe:active:scale-95 motion-reduce:transition-none">
          {hasMessage && !isGenerating && <span aria-hidden="true" className="pointer-events-none absolute inset-0 rounded-full border border-[var(--lp-accent)]/40 motion-safe:animate-[ping_1.8s_ease-out_2] motion-reduce:hidden" />}
          {isGenerating ? <span aria-hidden="true" className="size-3.5 rounded-sm bg-current" /> : <Icon name="up" className="transition-transform duration-200 motion-safe:group-hover:-translate-y-0.5 motion-reduce:transition-none" />}
        </button>
      </div>
    </form>
  )
}
