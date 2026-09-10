import { useEffect, useRef } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import Sidebar from '../components/Sidebar.jsx'
import InputBar from '../components/InputBar.jsx'
import ChatMessages from '../components/ChatMessages.jsx'
import ChatWelcome from '../components/ChatWelcome.jsx'
import InteractiveBackground from '../components/InteractiveBackground.jsx'
import Icon from '../components/LandingIcon.jsx'
import useChat from '../hooks/useChat.js'

const toolPrompts = {
  Classify: 'What kind of IP could be relevant to my Ayurvedic product?',
  ABS: 'What should I consider when sourcing a medicinal plant?',
  'Prior Art': 'How do I begin a prior-art search for a herbal formulation?',
}

const Chat = () => {
  const { messages, isGenerating, chats, activeChatId, jurisdiction, setJurisdiction,
    sendMessage, retryMessage, newChat, selectChat, cancelRequest } = useChat()
  const mobileSidebarRef = useRef(null)
  const form = useForm({ defaultValues: { message: '' } })
  const isEmpty = !messages.length && !isGenerating

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
      mobileSidebarRef.current?.close()
      form.reset({ message: '' })
      form.setFocus('message')
      newChat()
    },
    onToolSelect: (tool) => {
      preparePrompt(toolPrompts[tool])
    },
  }

  return (
    <FormProvider {...form}>
      <div className="relative isolate flex h-dvh overflow-hidden bg-[var(--lp-bg)] font-['Inter',sans-serif] text-[var(--lp-ink)]">
        {isEmpty && <div className="pointer-events-none absolute inset-0 opacity-35"><InteractiveBackground /></div>}
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
          <header className="grid shrink-0 grid-cols-[44px_minmax(0,1fr)_44px] items-center gap-1 border-b border-[var(--lp-line)] bg-[var(--lp-bg)]/85 px-3 pt-4 pb-4 md:min-h-24 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] md:px-6 md:py-6">
            <button type="button" aria-label="Open sidebar" aria-haspopup="dialog" aria-controls="mobile-sidebar" onClick={() => mobileSidebarRef.current?.showModal()} className="grid size-11 cursor-pointer place-items-center rounded-full border border-[var(--lp-strong-line)] bg-[var(--lp-surface)] text-[var(--lp-accent)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lp-accent)] md:hidden"><Icon name="menu" /></button>
            <div className="hidden min-w-0 md:block"><p className="truncate text-sm text-[var(--lp-muted)]">Your research space</p><p className="mt-1 hidden text-xs text-[var(--lp-gold)] xl:block">A little clarity goes a long way.</p></div>
            <div className="flex min-w-0 justify-center">
              <div className="relative grid w-[224px] max-w-full grid-cols-2 rounded-full border border-[var(--lp-strong-line)] bg-[var(--lp-surface)] p-1" role="group" aria-label="Jurisdiction">
                <span aria-hidden="true" className={`pointer-events-none absolute inset-y-1 left-1 w-[calc(50%-8px)] rounded-full bg-[var(--lp-action)] transition-transform duration-250 ease-in-out motion-reduce:transition-none ${jurisdiction === 'international' ? 'translate-x-[calc(100%+8px)]' : 'translate-x-0'}`} />
                <span aria-hidden="true" className="pointer-events-none absolute top-1/2 left-1/2 h-5 w-px -translate-y-1/2 bg-[var(--lp-strong-line)]" />
                {['india', 'international'].map((option) => (
                  <button key={option} type="button" aria-pressed={jurisdiction === option} onClick={() => setJurisdiction(option)} className={`relative min-h-9 min-w-0 cursor-pointer rounded-full border-0 px-1 py-2 text-xs font-medium transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lp-accent)] motion-reduce:transition-none sm:text-sm ${jurisdiction === option ? 'text-[var(--lp-on-action)]' : 'text-[var(--lp-muted)] hover:text-[var(--lp-ink)]'}`}>
                    {option === 'india' ? 'India' : 'International'}
                  </button>
                ))}
              </div>
            </div>
          </header>

          <ChatMessages key={activeChatId || 'new'} messages={messages} isGenerating={isGenerating} onRetry={retryMessage} emptyState={<ChatWelcome onPromptSelect={preparePrompt} />} />
          <div className="mx-auto w-full max-w-[880px] shrink-0 px-4 pt-4 pb-4 sm:px-8 sm:pb-6">
            <InputBar jurisdiction={jurisdiction} isGenerating={isGenerating} onStop={cancelRequest} onSend={(message) => {
              if (sendMessage(message)) form.reset({ message: '' })
            }} />
            <p className="mt-3 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-center text-xs text-[var(--lp-muted)]"><span className="inline-flex items-center gap-1.5"><Icon name="book" className="size-3.5 text-[var(--lp-gold)]" />Source-grounded exploration</span><span aria-hidden="true">·</span><span>Rooted in Ayurveda. Guided by context.</span></p>
          </div>
        </main>
      </div>
    </FormProvider>
  )
}

export default Chat
