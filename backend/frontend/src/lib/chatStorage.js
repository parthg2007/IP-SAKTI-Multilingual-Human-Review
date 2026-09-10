const STORAGE_KEY = 'ip-sakti-chats-v1'
const MAX_CHATS = 30
const MAX_MESSAGES = 100

export function readChatHistory(storage) {
  try {
    const saved = JSON.parse(storage.getItem(STORAGE_KEY))
    if (!Array.isArray(saved?.chats)) return { chats: [], activeChatId: null }
    const chats = saved.chats.filter((chat) => chat && typeof chat.id === 'string'
      && typeof chat.title === 'string' && Array.isArray(chat.messages)).slice(0, MAX_CHATS).map((chat) => ({
      id: chat.id,
      title: chat.title,
      jurisdiction: chat.jurisdiction === 'international' ? 'international' : 'india',
      messages: chat.messages.filter((message) => message && typeof message.id === 'string'
        && ['user', 'assistant'].includes(message.role) && typeof message.content === 'string')
        .slice(-MAX_MESSAGES).map((message) => ({
          ...message,
          citations: Array.isArray(message.citations) ? message.citations.filter((citation) => citation && typeof citation.title === 'string') : [],
          ...(message.status === 'loading' ? { status: 'error', content: 'This answer was interrupted. Please retry.' } : {}),
        })),
    }))
    return { chats, activeChatId: chats.some((chat) => chat.id === saved.activeChatId) ? saved.activeChatId : null }
  } catch {
    return { chats: [], activeChatId: null }
  }
}

export function writeChatHistory(storage, state) {
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify({
      activeChatId: state.activeChatId,
      chats: state.chats.slice(0, MAX_CHATS).map((chat) => ({ ...chat, messages: chat.messages.slice(-MAX_MESSAGES) })),
    }))
  } catch {
    // The current conversation still works when browser storage is full or disabled.
  }
}
