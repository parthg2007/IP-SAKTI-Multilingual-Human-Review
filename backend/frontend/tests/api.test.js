import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import { once } from 'node:events'
import { test } from 'node:test'
import { createChatApi, safeSourceUrl } from '../src/lib/api.js'

async function withServer(t, handler) {
  const server = createServer(handler)
  server.listen(0, '127.0.0.1')
  await once(server, 'listening')
  t.after(() => { server.closeAllConnections(); server.close() })
  return createChatApi(`http://127.0.0.1:${server.address().port}/`)
}

test('sends the chat API contract and maps answer/source fields', async (t) => {
  let received
  const query = await withServer(t, async (request, response) => {
    let body = ''
    for await (const chunk of request) body += chunk
    received = { method: request.method, url: request.url, body: JSON.parse(body) }
    response.setHeader('Content-Type', 'application/json')
    response.end(JSON.stringify({
      synthesized_answer: '**Treaty evidence**', connected_rags_responded: ['rag2_legal_regulatory'],
      legal_disclaimer: 'Check the relevant jurisdiction.',
      citations: [{ chunk_id: '123', rag_source: 'RAG2', title: 'TRIPS', source_name: 'WTO', source_url: 'https://www.wto.org/', text: 'Article 27' }],
    }))
  })
  const answer = await query({ query: '  What is TRIPS?  ', jurisdiction: 'international' })
  assert.deepEqual(received, { method: 'POST', url: '/api/v1/orchestrator/query', body: { query: 'What is TRIPS?', jurisdiction: 'INTERNATIONAL', top_k_per_rag: 4 } })
  assert.equal(answer.content, '**Treaty evidence**')
  assert.equal(answer.citations[0].url, 'https://www.wto.org/')
  assert.equal(answer.citations[0].id, 'RAG2:123')
  assert.equal(answer.disclaimer, 'Check the relevant jurisdiction.')
})

test('handles API validation, rate limiting, and server errors', async (t) => {
  for (const [status, expected] of [[422, /1–4,000/], [429, /busy/], [503, /try again shortly/]]) {
    const query = await withServer(t, (_request, response) => { response.writeHead(status); response.end() })
    await assert.rejects(query({ query: 'TKDL' }), expected)
  }
})

test('rejects HTML responses and unavailable knowledge services', async (t) => {
  const htmlQuery = await withServer(t, (_request, response) => response.end('<html>SPA fallback</html>'))
  await assert.rejects(htmlQuery({ query: 'TKDL' }), /unreadable answer/)
  const unavailable = await withServer(t, (_request, response) => {
    response.setHeader('Content-Type', 'application/json')
    response.end(JSON.stringify({ synthesized_answer: 'Unavailable', citations: [], connected_rags_responded: [] }))
  })
  await assert.rejects(unavailable({ query: 'TKDL' }), /knowledge service is unavailable/)
})

test('aborts pending requests so stopped answers cannot replace a new chat', async (t) => {
  const query = await withServer(t, () => {})
  const controller = new AbortController()
  const pending = query({ query: 'TKDL', signal: controller.signal })
  controller.abort()
  await assert.rejects(pending, { code: 'ERR_CANCELED' })
})

test('only permits public HTTP(S) link protocols', () => {
  assert.equal(safeSourceUrl('https://example.com/source'), 'https://example.com/source')
  for (const value of ['javascript:alert(1)', 'data:text/html,hello', 'file:///secret', '/relative', null]) {
    assert.equal(safeSourceUrl(value), null)
  }
})
