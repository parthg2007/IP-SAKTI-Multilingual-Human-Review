import { useEffect, useRef, useState } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import Sidebar from '../components/Sidebar.jsx'
import InputBar from '../components/InputBar.jsx'
import ChatMessages from '../components/ChatMessages.jsx'
import ChatWelcome from '../components/ChatWelcome.jsx'
import InteractiveBackground from '../components/InteractiveBackground.jsx'
import Icon from '../components/LandingIcon.jsx'
import useChat from '../hooks/useChat.js'
import EscalationModal from '../components/EscalationModal.jsx'
import ResearchTools from '../components/ResearchTools.jsx'
import { researchApi } from '../lib/api.js'
import '../components/research.css'

const toolPrompts = {
  Classify: 'What kind of IP could be relevant to my Ayurvedic product?',
  ABS: 'What should I consider when sourcing a medicinal plant?',
  'Prior Art': 'How do I begin a prior-art search for a herbal formulation?',
}

const Chat = () => {
  const { messages, isGenerating, chats, activeChatId, jurisdiction, language, setJurisdiction, setLanguage,
    sendMessage, retryMessage, newChat, selectChat, cancelRequest, queryOptions, setQueryOptions, saveEscalation } = useChat()
  const mobileSidebarRef = useRef(null)
  const form = useForm({ defaultValues: { message: '' } })
  const isEmpty = !messages.length && !isGenerating
  const [escalationMessage, setEscalationMessage] = useState(null)
  const [toolsOpen, setToolsOpen] = useState(false)
  const [inputRevision, setInputRevision] = useState(0)
  const [capabilities, setCapabilities] = useState(null)
  const [rags, setRags] = useState([])
  const [serviceError, setServiceError] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    researchApi.languages(controller.signal).then(setCapabilities, () => {})
    researchApi.rags(controller.signal).then((data) => { setRags(data); setServiceError('') }, (error) => { if (!controller.signal.aborted) setServiceError(error.message) })
    return () => controller.abort()
  }, [revision])

  const languages = [
    ['en', 'English'], ['hi', 'हिन्दी'], ['bn', 'বাংলা'], ['gu', 'ગુજરાતી'],
    ['kn', 'ಕನ್ನಡ'], ['ml', 'മലയാളം'], ['mr', 'मराठी'], ['or', 'ଓଡ଼ିଆ'],
    ['pa', 'ਪੰਜਾਬੀ'], ['ta', 'தமிழ்'], ['te', 'తెలుగు'], ['ur', 'اردو'],
  ]

  useEffect(() => {
    const desktop = window.matchMedia('(min-width: 768px)')
    const closeOnDesktop = () => {
      if (desktop.matches) mobileSidebarRef.current?.close()
    }
    desktop.addEventListener('change', closeOnDesktop)
    return () => desktop.removeEventListener('change', closeOnDesktop)
  }, [])

  const preparePrompt = (prompt) => {
    mobileSidebarRef.current?.close()
    form.setValue('message', prompt, { shouldDirty: true })
    form.setFocus('message')
  }

  const sidebarProps = {
    chats,
    activeChatId,
    onChatSelect: (chat) => {
      mobileSidebarRef.current?.close()
      selectChat(chat)
      form.reset({ message: '' })
    },
    onNewQuery: () => {
      setInputRevision((value) => value + 1)
      mobileSidebarRef.current?.close()
      form.reset({ message: '' })
      form.setFocus('message')
      newChat()
    },
    onToolSelect: (tool) => {
      if (tool === 'Research tools') { mobileSidebarRef.current?.close(); setToolsOpen(true); return }
      preparePrompt(toolPrompts[tool])
    },
  }

  return (
    <FormProvider {...form}>
      <div className="relative isolate flex h-dvh overflow-hidden bg-[var(--lp-bg)] font-['Inter',sans-serif] text-[var(--lp-ink)]">
        {isEmpty && <div className="pointer-events-none absolute inset-0 opacity-40"><InteractiveBackground /></div>}
        <div className="relative z-10 hidden md:block"><Sidebar {...sidebarProps} /></div>
        <dialog
          ref={mobileSidebarRef}
          id="mobile-sidebar"
          aria-label="Navigation menu"
          className="fixed inset-y-0 left-0 m-0 h-dvh max-h-none w-fit max-w-none translate-x-0 border-0 bg-[var(--lp-sidebar)] p-0 text-[var(--lp-ink)] transition-[translate,display,overlay] transition-discrete duration-250 ease-out not-open:-translate-x-full starting:open:-translate-x-full backdrop:bg-[#111B15]/60 backdrop:opacity-100 backdrop:transition-[opacity,display,overlay] backdrop:transition-discrete backdrop:duration-250 not-open:backdrop:opacity-0 starting:open:backdrop:opacity-0 motion-reduce:transition-none motion-reduce:backdrop:transition-none"
          onClick={(event) => {
            if (event.target === event.currentTarget) mobileSidebarRef.current?.close()
          }}
        >
          <Sidebar {...sidebarProps} mobile onClose={() => mobileSidebarRef.current?.close()} />
        </dialog>

        <main className="relative z-0 flex min-h-0 min-w-0 flex-1 flex-col" aria-label="Chat">
          {/* Header — editorial, matches landing navbar */}
          <header className="shrink-0 border-b border-[var(--lp-line)] bg-[var(--lp-bg)]/90 backdrop-blur-sm">
            <div className="grid grid-cols-[44px_minmax(0,1fr)_44px] items-center gap-2 px-3 py-3 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] md:px-6 md:py-4">

              {/* Left — mobile menu | desktop brand label */}
              <button
                type="button"
                aria-label="Open sidebar"
                aria-haspopup="dialog"
                aria-controls="mobile-sidebar"
                onClick={() => mobileSidebarRef.current?.showModal()}
                className="grid size-10 cursor-pointer place-items-center rounded-full border border-[var(--lp-strong-line)] bg-[var(--lp-surface)] text-[var(--lp-accent)] transition-colors hover:bg-[var(--lp-card)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lp-accent)] md:hidden"
              >
                <Icon name="menu" />
              </button>
              <div className="hidden min-w-0 md:block">
                <p className="font-['Merriweather',serif] text-base font-bold tracking-[-0.03em] text-[var(--lp-ink)]">
                  IP-SAKTI<span className="text-[var(--lp-gold)]">.</span>
                </p>
                <p className="mt-0.5 flex items-center gap-1.5 text-xs text-[var(--lp-muted)]">
                  <span className="size-1.5 rounded-full bg-[var(--lp-accent)]" />
                  Your research space · <span className="italic text-[var(--lp-gold)]">A little clarity goes a long way.</span>
                </p>
              </div>

              {/* Center — jurisdiction + language */}
              <div className="flex min-w-0 items-center justify-center gap-2">
                <div
                  className="relative grid w-[180px] max-w-full grid-cols-2 rounded-full border border-[var(--lp-strong-line)] bg-[var(--lp-surface)] p-1 sm:w-[224px]"
                  role="group"
                  aria-label="Jurisdiction"
                >
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none absolute inset-y-1 left-1 w-[calc(50%-8px)] rounded-full bg-[var(--lp-action)] transition-transform duration-250 ease-in-out motion-reduce:transition-none ${jurisdiction === 'international' ? 'translate-x-[calc(100%+8px)]' : 'translate-x-0'}`}
                  />
                  <span aria-hidden="true" className="pointer-events-none absolute top-1/2 left-1/2 h-5 w-px -translate-y-1/2 bg-[var(--lp-strong-line)]" />
                  {['india', 'international'].map((option) => (
                    <button
                      key={option}
                      type="button"
                      aria-pressed={jurisdiction === option}
                      onClick={() => setJurisdiction(option)}
                      className={`relative min-h-9 min-w-0 cursor-pointer rounded-full border-0 px-1 py-2 text-xs font-medium transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lp-accent)] motion-reduce:transition-none sm:text-sm ${jurisdiction === option ? 'text-[var(--lp-on-action)]' : 'text-[var(--lp-muted)] hover:text-[var(--lp-ink)]'}`}
                    >
                      {option === 'india' ? 'India' : 'International'}
                    </button>
                  ))}
                </div>
                <label className="flex items-center rounded-full border border-[var(--lp-strong-line)] bg-[var(--lp-surface)] px-2 py-1.5 text-xs text-[var(--lp-muted)] sm:px-3">
                  <span className="sr-only">Response language</span>
                  <select
                    value={language}
                    onChange={(event) => setLanguage(event.target.value)}
                    className="w-[74px] cursor-pointer bg-transparent font-medium text-[var(--lp-ink)] outline-none sm:w-auto"
                  >
                    {(capabilities?.languages?.map(({ code, name }) => [code, name]) || languages).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
                  </select>
                </label>
              </div>

              {/* Right — AYUSH badge (desktop only) */}
              <div className="hidden items-center justify-end gap-2 md:flex">
                <span className="flex items-center gap-2 rounded-full border border-[var(--lp-line)] bg-[var(--lp-surface)] px-3 py-1.5 text-xs tracking-[0.1em] text-[var(--lp-muted)] uppercase">
                  <span className="size-1.5 rounded-full bg-[var(--lp-accent)]" />
                  Made for AYUSH
                </span>
              </div>
              {/* Mobile right spacer */}
              <div className="md:hidden" />
            </div>
          </header>

          <details className="research-options">
            <summary>Answer settings · {queryOptions.targetRags.length ? 'Selected sources' : 'Automatic routing'} · {queryOptions.topK} passages per source</summary>
            <fieldset disabled={isGenerating}>
              <legend className="sr-only">Answer settings</legend>
              <label>Evidence per source<select aria-label="Evidence per source" value={queryOptions.topK} onChange={(event) => setQueryOptions((current) => ({ ...current, topK: Number(event.target.value) }))}>{Array.from({ length: 10 }, (_, index) => <option key={index + 1}>{index + 1}</option>)}</select></label>
              <label><input type="checkbox" checked={!queryOptions.targetRags.length} onChange={() => setQueryOptions((current) => ({ ...current, targetRags: [] }))} />Automatic routing</label>
              {rags.map((rag) => <label key={rag.rag_id}><input type="checkbox" checked={queryOptions.targetRags.includes(rag.rag_id)} onChange={(event) => setQueryOptions((current) => ({ ...current, targetRags: event.target.checked ? [...current.targetRags, rag.rag_id] : current.targetRags.filter((id) => id !== rag.rag_id) }))} />{rag.name}{!rag.is_healthy && ' (unavailable)'}</label>)}
            </fieldset>
            {serviceError && <p role="status">{serviceError} <button type="button" onClick={() => setRevision((value) => value + 1)}>Retry status</button></p>}
          </details>

          <ChatMessages key={activeChatId || 'new'} messages={messages} isGenerating={isGenerating} onRetry={retryMessage} onEscalate={setEscalationMessage} emptyState={<ChatWelcome onPromptSelect={preparePrompt} />} />

          {/* Input area */}
          <div className="border-t border-[var(--lp-line)] bg-[var(--lp-bg)]/80 backdrop-blur-sm">
            <div className="mx-auto w-full max-w-[880px] px-4 pt-4 pb-5 sm:px-8 sm:pb-6">
              <InputBar key={`${activeChatId || 'new'}:${inputRevision}`} jurisdiction={jurisdiction} language={language} isGenerating={isGenerating} onStop={cancelRequest} onSend={(message) => {
                if (sendMessage(message)) form.reset({ message: '' })
              }} />
              <p className="mt-3 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-center text-xs text-[var(--lp-muted)]">
                <span className="inline-flex items-center gap-1.5"><Icon name="book" className="size-3.5 text-[var(--lp-gold)]" />Source-grounded</span>
                <span aria-hidden="true">·</span>
                <span className="inline-flex items-center gap-1.5"><Icon name="globe" className="size-3.5 text-[var(--lp-accent)]" />{capabilities?.bhashini_enabled ? 'BHASHINI translation enabled' : 'Multilingual responses'}</span>
                <span aria-hidden="true">·</span>
                <span className="inline-flex items-center gap-1.5"><Icon name="shield" className="size-3.5 text-[var(--lp-accent)]" />Human review path</span>
              </p>
            </div>
          </div>
        </main>
      </div>
      {escalationMessage && <EscalationModal message={escalationMessage} jurisdiction={jurisdiction} language={language} onCreated={(data) => saveEscalation(escalationMessage.id, data)} onClose={() => setEscalationMessage(null)} />}
      {toolsOpen && <ResearchTools jurisdiction={jurisdiction} language={language} onClose={() => setToolsOpen(false)} onRegistered={() => setRevision((value) => value + 1)} />}
    </FormProvider>
  )
}

export default Chat
