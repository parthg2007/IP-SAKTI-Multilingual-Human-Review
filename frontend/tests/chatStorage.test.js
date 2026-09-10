import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readChatHistory, writeChatHistory } from '../src/lib/chatStorage.js'

function memoryStorage(value) {
  return { getItem: () => value, setItem: (_key, next) => { value = next } }
}

test('restores history and converts interrupted answers to retryable errors', () => {
  const storage = memoryStorage()
  writeChatHistory(storage, { activeChatId: 'chat1', chats: [{ id: 'chat1', title: 'TRIPS', jurisdiction: 'international', messages: [
    { id: 'q1', role: 'user', content: 'TRIPS?' },
    { id: 'a1', role: 'assistant', status: 'loading', content: '', query: 'TRIPS?', jurisdiction: 'international' },
  ] }] })
  const state = readChatHistory(storage)
  assert.equal(state.activeChatId, 'chat1')
  assert.equal(state.chats[0].jurisdiction, 'international')
  assert.equal(state.chats[0].messages[1].status, 'error')
  assert.equal(state.chats[0].messages[1].query, 'TRIPS?')
})

test('survives corrupt or disabled storage', () => {
  for (const value of ['{broken', 'null', '{}', '{"chats":[null,{}],"activeChatId":"missing"}']) {
    assert.deepEqual(readChatHistory(memoryStorage(value)), { chats: [], activeChatId: null })
  }
  const blocked = { getItem() { throw new Error('disabled') }, setItem() { throw new Error('full') } }
  assert.deepEqual(readChatHistory(blocked), { chats: [], activeChatId: null })
  assert.doesNotThrow(() => writeChatHistory(blocked, { chats: [], activeChatId: null }))
})

test('caps persisted history to avoid unbounded browser storage', () => {
  const storage = memoryStorage()
  const chats = Array.from({ length: 40 }, (_, index) => ({ id: `c${index}`, title: 'Query', messages: Array.from({ length: 120 }, (_, message) => ({ id: `m${message}`, role: 'user', content: 'Question' })) }))
  writeChatHistory(storage, { chats, activeChatId: 'c0' })
  const saved = readChatHistory(storage)
  assert.equal(saved.chats.length, 30)
  assert.equal(saved.chats[0].messages.length, 100)
})
