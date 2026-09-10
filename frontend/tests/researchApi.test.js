import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import { once } from 'node:events'
import { test } from 'node:test'
import { createChatApi, createResearchApi, escalateToHuman, mapCitations, transcribeAudio } from '../src/lib/api.js'

async function serverFor(t, handler) {
  const server = createServer(handler)
  server.listen(0, '127.0.0.1')
  await once(server, 'listening')
  t.after(() => { server.closeAllConnections(); server.close() })
  return `http://127.0.0.1:${server.address().port}`
}

test('all research endpoints preserve their HTTP method, filters and query parameters', async (t) => {
  const received = []
  const base = await serverFor(t, async (req, res) => {
    let body = ''
    for await (const chunk of req) body += chunk
    received.push({ method: req.method, url: req.url, body: body ? JSON.parse(body) : null })
    res.setHeader('Content-Type', 'application/json')
    res.end('{}')
  })
  const api = createResearchApi(base)
  await api.info(); await api.languages(); await api.rags()
  for (const corpus of ['knowledge', 'legal']) {
    await api.health(corpus)
    await api.search(corpus, { query: 'TKDL', mode: 'bm25', domain: 'PATENT', top_k: 7 })
    await api.query(corpus, { query: 'patent', jurisdiction: 'INDIA', language: 'hi', top_k: 2 })
  }
  await api.historical({ query: 'patent', requested_date: '2015-01-01', category: 'patents_act', top_k: 3 })
  await api.document('document with spaces')
  await api.route('  Patent & Ayurveda?  ')
  await api.register({ rag_id: 'remote', endpoint_url: 'https://example.com', role: 'domain_context', name: 'Remote' })
  assert.deepEqual(received.map(({ method, url }) => [method, url.split('?')[0]]), [
    ['GET', '/api/info'], ['GET', '/api/v1/languages'], ['GET', '/api/v1/orchestrator/rags'],
    ['GET', '/api/v1/rag/knowledge/health'], ['POST', '/api/v1/rag/knowledge/search'], ['POST', '/api/v1/rag/knowledge/query'],
    ['GET', '/api/v1/rag/legal/health'], ['POST', '/api/v1/rag/legal/search'], ['POST', '/api/v1/rag/legal/query'],
    ['POST', '/api/v1/rag/legal/historical'], ['GET', '/api/v1/rag/legal/documents/document%20with%20spaces'],
    ['POST', '/api/v1/orchestrator/route'], ['POST', '/api/v1/orchestrator/rags/register'],
  ])
  assert.equal(received[4].body.mode, 'bm25')
  assert.equal(received[8].body.jurisdiction, 'INDIA')
  assert.equal(received[9].body.requested_date, '2015-01-01')
  assert.equal(new URL(received[11].url, base).searchParams.get('query'), 'Patent & Ayurveda?')
  assert.equal(received[11].body, null)
})

test('chat options and all answer provenance survive mapping', async (t) => {
  let payload
  const base = await serverFor(t, async (req, res) => {
    let body = ''; for await (const chunk of req) body += chunk
    payload = JSON.parse(body)
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ synthesized_answer: 'Answer', citations: [], connected_rags_responded: ['remote'],
      route_decision: { target_rags: ['remote'], intent: 'user_specified_target' }, domain_context: 'Domain', legal_evidence_context: 'Law', graph: { nodes: [] }, agentic_reasoning: { intent: 'review' } }))
  })
  const result = await createChatApi(base)({ query: 'patent', targetRags: ['remote'], topK: 10 })
  assert.deepEqual(payload.target_rags, ['remote'])
  assert.equal(payload.top_k_per_rag, 10)
  assert.equal(result.routeDecision.intent, 'user_specified_target')
  assert.equal(result.domainContext, 'Domain')
  assert.equal(result.legalContext, 'Law')
  assert.deepEqual(result.respondedRags, ['remote'])
})

test('escalation retains original citation identity and more than ten sources without truncating the answer', async (t) => {
  let payload
  const base = await serverFor(t, async (req, res) => {
    let body = ''; for await (const chunk of req) body += chunk
    payload = JSON.parse(body)
    res.setHeader('Content-Type', 'application/json'); res.end('{"case_id":"test"}')
  })
  const citations = mapCitations(Array.from({ length: 20 }, (_, index) => ({ document_id: 'DOC', chunk_id: `chunk-${index}`, title: 'Source', source_name: 'Authority', source_url: 'https://example.com/', rag_source: 'RAG2', authority_tier: 'TIER_1_AUTHORITATIVE', domain: 'PATENT', score: 0.8, text: 'Evidence' })))
  const answer = 'a'.repeat(13000)
  await escalateToHuman({ baseURL: base, query: 'Question', jurisdiction: 'international', language: 'ta', answer, confidence: 0.6, citations, userNote: 'Note' })
  assert.equal(payload.answer, answer)
  assert.equal(payload.citations.length, 20)
  assert.deepEqual(payload.citations[0], { document_id: 'DOC', chunk_id: 'chunk-0', title: 'Source', source_name: 'Authority', source_url: 'https://example.com/', text: 'Evidence', domain: 'PATENT', score: 0.8, authority_tier: 'TIER_1_AUTHORITATIVE', rag_source: 'RAG2' })
  assert.equal(payload.jurisdiction, 'INTERNATIONAL')
  assert.equal(payload.language, 'ta')
})

test('citation markers do not shift when malformed entries are skipped', () => {
  const citations = mapCitations([null, { title: 'Second', chunk_id: '2' }])
  assert.equal(citations[0].ref, 'S2')
})

test('voice sends a real multipart boundary and matching audio filename', async (t) => {
  let received
  const base = await serverFor(t, async (req, res) => {
    let body = ''; for await (const chunk of req) body += chunk
    received = { body, type: req.headers['content-type'] }
    res.setHeader('Content-Type', 'application/json'); res.end('{"text":"hello"}')
  })
  const result = await transcribeAudio({ baseURL: base, audioBlob: new Blob(['test-audio'], { type: 'audio/mp4' }), language: 'ta' })
  assert.equal(result.text, 'hello')
  assert.match(received.type, /multipart\/form-data; boundary=/)
  assert.match(received.body, /filename="recording.m4a"/)
  assert.match(received.body, /name="language"\r\n\r\nta/)
})

test('research errors handle validation arrays and cancellation', async (t) => {
  const base = await serverFor(t, (_req, res) => { res.writeHead(422, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ detail: [{ loc: ['body', 'requested_date'], msg: 'Invalid date' }] })) })
  await assert.rejects(createResearchApi(base).historical({}), /requested_date: Invalid date/)
  const pendingBase = await serverFor(t, () => {})
  const controller = new AbortController()
  const pending = createResearchApi(pendingBase).search('legal', { query: 'test' }, controller.signal)
  controller.abort()
  await assert.rejects(pending, { code: 'ERR_CANCELED' })
})
