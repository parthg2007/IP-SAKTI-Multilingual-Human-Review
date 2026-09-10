import { useEffect, useRef, useState } from 'react'
import { transcribeAudio } from '../lib/api.js'

export default function VoiceInputButton({ onTranscript, onBusyChange, language = 'en', disabled = false }) {
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const session = useRef(null)
  const mounted = useRef(false)
  const callbacks = useRef({ onTranscript, onBusyChange })
  useEffect(() => { callbacks.current = { onTranscript, onBusyChange } }, [onTranscript, onBusyChange])
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
      const active = session.current
      session.current = null
      active?.controller.abort()
      active?.stream?.getTracks().forEach((track) => track.stop())
      if (active?.recorder?.state === 'recording') active.recorder.stop()
      active?.recognition?.abort()
      clearTimeout(active?.timer)
    }
  }, [])

  function finish(active, message = '') {
    if (session.current !== active || !mounted.current) return
    clearTimeout(active.timer)
    active.stream?.getTracks().forEach((track) => track.stop())
    session.current = null
    setError(message)
    setStatus('idle')
    callbacks.current.onBusyChange?.(false)
  }

  function browserSpeech(active) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Recognition) { finish(active, 'Voice input is unavailable in this browser. You can type your question.'); return }
    try {
      const recognition = new Recognition()
      active.recognition = recognition
      recognition.lang = language === 'hi-Latn' ? 'hi-IN' : `${language}-IN`
      recognition.interimResults = false
      recognition.onstart = () => { if (session.current === active) setStatus('recording') }
      recognition.onresult = (event) => {
        if (session.current !== active) return
        const text = event.results[0]?.[0]?.transcript
        if (text) callbacks.current.onTranscript(text)
      }
      recognition.onerror = () => finish(active, 'Speech was not recognized. Please try again.')
      recognition.onend = () => finish(active)
      recognition.start()
    } catch { finish(active, 'Speech recognition is unavailable. Please type your question.') }
  }

  async function start() {
    if (session.current || disabled) return
    const active = { controller: new AbortController() }
    session.current = active
    setError('')
    setStatus('starting')
    callbacks.current.onBusyChange?.(true)
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { browserSpeech(active); return }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (session.current !== active || !mounted.current) { stream.getTracks().forEach((track) => track.stop()); return }
      active.stream = stream
      const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/webm'].find((type) => MediaRecorder.isTypeSupported(type))
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      active.recorder = recorder
      const chunks = []
      recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data) }
      recorder.onerror = () => finish(active, 'Recording failed. Please try again.')
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop())
        clearTimeout(active.timer)
        if (session.current !== active || !mounted.current) return
        const audioBlob = new Blob(chunks, { type: recorder.mimeType || mimeType || 'audio/webm' })
        if (audioBlob.size < 100) { finish(active, 'No audio captured. Please record again.'); return }
        setStatus('transcribing')
        try {
          const data = await transcribeAudio({ audioBlob, language: language === 'hi-Latn' ? 'hi' : language, signal: active.controller.signal })
          if (session.current !== active || !mounted.current) return
          if (data.text?.trim()) callbacks.current.onTranscript(data.text.trim())
          finish(active, data.text?.trim() ? '' : 'No speech detected. Please try again.')
        } catch {
          if (!active.controller.signal.aborted) finish(active, 'Audio transcription is unavailable. Please try again or type your question.')
        }
      }
      recorder.start(250)
      setStatus('recording')
      active.timer = setTimeout(() => { if (recorder.state === 'recording') recorder.stop() }, 60_000)
    } catch {
      active.stream?.getTracks().forEach((track) => track.stop())
      finish(active, 'Microphone access failed. Allow microphone access in your browser and try again.')
    }
  }

  function stop() {
    const active = session.current
    if (active?.recorder?.state === 'recording') active.recorder.stop()
    active?.recognition?.stop()
  }

  return <div className="relative inline-flex items-center">
    <button type="button" onClick={status === 'recording' ? stop : start}
      disabled={status === 'starting' || status === 'transcribing' || (disabled && status !== 'recording')}
      aria-label={status === 'recording' ? 'Stop recording voice' : 'Dictate with voice'}
      title={status === 'recording' ? 'Stop recording' : status === 'transcribing' ? 'Transcribing audio?' : 'Voice input'}
      className={`grid size-11 shrink-0 cursor-pointer place-items-center rounded-full border focus-visible:outline-2 focus-visible:outline-[var(--lp-accent)] disabled:opacity-50 ${status === 'recording' ? 'border-red-500 text-red-500' : 'border-[var(--lp-line)] bg-[var(--lp-surface)] text-[var(--lp-muted)]'}`}>
      {status === 'recording' ? <span className="size-3 rounded-sm bg-current" /> : status === 'transcribing' || status === 'starting' ? <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" /> :
        <svg className="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="9" y="2" width="6" height="13" rx="3" /><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3" /></svg>}
    </button>
    {status !== 'idle' && <span className="sr-only" role="status">{status === 'recording' ? 'Recording. Press stop when finished.' : status === 'starting' ? 'Waiting for microphone access.' : 'Transcribing audio.'}</span>}
    {error && <span role="alert" className="absolute right-0 bottom-full z-50 mb-2 w-64 rounded-lg border border-[var(--lp-line)] bg-[var(--lp-card)] p-3 text-xs text-[var(--lp-ink)] shadow-lg">{error}</span>}
  </div>
}
