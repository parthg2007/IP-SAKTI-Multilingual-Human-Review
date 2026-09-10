import { useEffect, useRef, useState } from 'react'
import { queryKnowledge } from '../lib/api.js'
import { readChatHistory, writeChatHistory } from '../lib/chatStorage.js'

function loadHistory() {
  try {
    return readChatHistory(window.localStorage)
  } catch {
    return { chats: [], activeChatId: null }
  }
}

export default function useChat() {
  const [history, setHistory] = useState(loadHistory)
  const [draftJurisdiction, setDraftJurisdiction] = useState('india')
  const requestRef = useRef(null)
  const activeChat = history.chats.find((chat) => chat.id === history.activeChatId)
  const messages = activeChat?.messages || []
  const jurisdiction = activeChat?.jurisdiction || draftJurisdiction
  const isGenerating = messages.some((message) => message.status === 'loading')

  useEffect(() => {
    try {
      writeChatHistory(window.localStorage, history)
    } catch {
      // Storage may be disabled by the browser.
    }
  }, [history])

  useEffect(() => () => requestRef.current?.controller.abort(), [])

  function updateMessage(chatId, messageId, update) {
    setHistory((current) => ({ ...current, chats: current.chats.map((chat) => chat.id === chatId
      ? { ...chat, messages: chat.messages.map((message) => message.id === messageId ? { ...message, ...update } : message) }
      : chat) }))
  }

  function cancelRequest() {
    const pending = requestRef.current
    if (!pending) return
    requestRef.current = null
    pending.controller.abort()
    updateMessage(pending.chatId, pending.messageId, { status: 'error', content: 'This answer was stopped. You can retry it.' })
  }

  async function requestAnswer(chatId, messageId, query, context) {
    const pending = { chatId, messageId, controller: new AbortController() }
    requestRef.current = pending
    try {
      const answer = await queryKnowledge({ query, jurisdiction: context, signal: pending.controller.signal })
      if (requestRef.current === pending) updateMessage(chatId, messageId, { ...answer, status: 'complete' })
    } catch (error) {
      if (requestRef.current === pending && !pending.controller.signal.aborted) {
        updateMessage(chatId, messageId, { status: 'error', content: error.message || 'Something went wrong. Please try again.' })
      }
    } finally {
      if (requestRef.current === pending) requestRef.current = null
    }
  }

  function sendMessage(value) {
    const query = value.trim()
    if (!query || query.length > 4000 || requestRef.current) return false
    const chatId = activeChat?.id || crypto.randomUUID()
    const messageId = crypto.randomUUID()
    const additions = [
      { id: crypto.randomUUID(), role: 'user', content: query, jurisdiction },
      { id: messageId, role: 'assistant', content: '', status: 'loading', query, jurisdiction },
    ]
    setHistory((current) => ({
      activeChatId: chatId,
      chats: activeChat
        ? current.chats.map((chat) => chat.id === chatId ? { ...chat, messages: [...chat.messages, ...additions] } : chat)
        : [{ id: chatId, title: query.slice(0, 64), jurisdiction, messages: additions }, ...current.chats],
    }))
    void requestAnswer(chatId, messageId, query, jurisdiction)
    return true
  }

  function retryMessage(message) {
    if (requestRef.current || !activeChat || !message.query) return
    updateMessage(activeChat.id, message.id, { status: 'loading', content: '' })
    void requestAnswer(activeChat.id, message.id, message.query, message.jurisdiction)
  }

  function newChat() {
    cancelRequest()
    setHistory((current) => ({ ...current, activeChatId: null }))
  }

  function selectChat(chat) {
    if (chat.id === history.activeChatId) return
    cancelRequest()
    setHistory((current) => ({ ...current, activeChatId: chat.id }))
  }

  function setJurisdiction(value) {
    setDraftJurisdiction(value)
    if (activeChat) setHistory((current) => ({ ...current, chats: current.chats.map((chat) => chat.id === activeChat.id ? { ...chat, jurisdiction: value } : chat) }))
  }

  return { ...history, messages, jurisdiction, setJurisdiction, isGenerating, sendMessage, retryMessage, newChat, selectChat, cancelRequest }
}
