import { useRef, useState } from 'react'
import Icon from './LandingIcon.jsx'
import { apiError, escalateToHuman } from '../lib/api.js'
import Modal from './Modal.jsx'

export default function EscalationModal({ message, jurisdiction, language, onClose, onCreated }) {
  const [note, setNote] = useState('')
  const [state, setState] = useState({ status: message.escalation ? 'complete' : 'idle', data: message.escalation || null, error: '' })
  const submitting = useRef(false)

  if (!message) return null
  async function submit() {
    if (submitting.current) return
    submitting.current = true
    setState({ status: 'loading', data: null, error: '' })
    try {
      const data = await escalateToHuman({
        query: message.query || '', answer: message.status === 'error' ? undefined : message.content || '', confidence: message.confidence?.score,
        citations: message.citations || [], jurisdiction: message.jurisdiction || jurisdiction, language: message.language || language, userNote: note.trim(),
      })
      setState({ status: 'complete', data, error: '' })
      onCreated?.(data)
    } catch (error) {
      setState({ status: 'error', data: null, error: apiError(error) })
    } finally {
      submitting.current = false
    }
  }

  return (
    <Modal label="Escalate to human IP facilitator" onClose={onClose} busy={state.status === 'loading'}>
      <section>
        {state.status === 'complete' ? (
          <>
            <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.2em] text-[var(--lp-gold)]">Human review</p><h2 className="mt-2 text-2xl font-semibold">Case created</h2></div><button type="button" onClick={onClose} disabled={state.status === 'loading'} aria-label="Close human review" className="grid size-10 place-items-center rounded-full border border-[var(--lp-line)]"><Icon name="close" /></button></div>
            <p className="mt-5 text-sm leading-6 text-[var(--lp-muted)]">Your question and evidence trail have been queued for a human IP facilitator.</p>
            <div className="mt-5 rounded-2xl border border-[var(--lp-line)] bg-[var(--lp-surface)] p-4"><p className="text-xs text-[var(--lp-muted)]">Case ID</p><p className="mt-1 font-mono text-sm font-semibold text-[var(--lp-ink)]">{state.data.case_id}</p>{state.data.facilitator_email && <p className="mt-3 text-xs text-[var(--lp-muted)]">Facilitator: {state.data.facilitator_email}</p>}</div>
            <button type="button" onClick={onClose} className="mt-5 w-full rounded-full bg-[var(--lp-action)] px-4 py-3 text-sm font-semibold text-[var(--lp-on-action)]">Done</button>
          </>
        ) : (
          <>
            <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.2em] text-[var(--lp-gold)]">Human escalation</p><h2 className="mt-2 text-2xl font-semibold">Talk to an IP facilitator</h2></div><button type="button" onClick={onClose} disabled={state.status === 'loading'} aria-label="Close human review" className="grid size-10 place-items-center rounded-full border border-[var(--lp-line)]"><Icon name="close" /></button></div>
            <p className="mt-3 text-sm leading-6 text-[var(--lp-muted)]">We will pass the question, current answer, confidence signal, and cited sources to the human-review queue.</p>
            <textarea aria-label="Context for the facilitator" disabled={state.status === 'loading'} value={note} onChange={(event) => setNote(event.target.value)} maxLength={2000} rows={4} placeholder="Add context for the facilitator (optional)…" className="mt-5 w-full resize-y rounded-2xl border border-[var(--lp-line)] bg-[var(--lp-surface)] p-4 text-sm text-[var(--lp-ink)] outline-none focus:border-[var(--lp-accent)]" />
            {state.error && <p role="alert" className="mt-3 rounded-xl border border-[var(--lp-gold)]/60 bg-[var(--lp-surface)] p-3 text-sm text-[var(--lp-ink)]">{state.error}</p>}
            <div className="mt-5 flex gap-3"><button type="button" onClick={onClose} disabled={state.status === 'loading'} className="flex-1 rounded-full border border-[var(--lp-strong-line)] px-4 py-3 text-sm">Cancel</button><button type="button" onClick={submit} disabled={state.status === 'loading'} className="flex-1 rounded-full bg-[var(--lp-action)] px-4 py-3 text-sm font-semibold text-[var(--lp-on-action)] disabled:opacity-50">{state.status === 'loading' ? 'Creating case…' : 'Send to facilitator'}</button></div>
          </>
        )}
      </section>
    </Modal>
  )
}
