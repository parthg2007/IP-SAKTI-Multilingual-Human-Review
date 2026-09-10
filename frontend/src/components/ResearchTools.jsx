import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { researchApi, safeSourceUrl } from '../lib/api.js'
import EvidenceList from './EvidenceList.jsx'
import Modal from './Modal.jsx'

const tabs = [['search', 'Evidence search'], ['query', 'Source query'], ['historical', 'Legal history'], ['route', 'Routing preview'], ['services', 'Services']]
const markdownComponents = {
  a: ({ href, children }) => { const url = safeSourceUrl(href); return url ? <a href={url} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span> },
  img: ({ alt }) => <span>{alt}</span>,
}

function Services({ onRegistered, onBusyChange }) {
  const [state, setState] = useState({ loading: true })
  const [revision, setRevision] = useState(0)
  const [registration, setRegistration] = useState({})
  const submitting = useRef(false)
  useEffect(() => {
    const controller = new AbortController()
    const requests = { info: researchApi.info, rags: researchApi.rags, knowledge: (signal) => researchApi.health('knowledge', signal), legal: (signal) => researchApi.health('legal', signal) }
    Promise.all(Object.entries(requests).map(async ([key, load]) => {
      try { return [key, { data: await load(controller.signal) }] } catch (error) { return [key, { error: error.message }] }
    })).then((entries) => { if (!controller.signal.aborted) setState(Object.fromEntries(entries)) })
    return () => controller.abort()
  }, [revision])
  async function register(event) {
    event.preventDefault()
    if (submitting.current) return
    const form = event.currentTarget
    const payload = Object.fromEntries(new FormData(form))
    if (!safeSourceUrl(payload.endpoint_url)) { setRegistration({ error: 'Use an HTTP or HTTPS service URL.' }); return }
    submitting.current = true
    onBusyChange(true)
    setRegistration({ loading: true })
    try {
      const data = await researchApi.register(payload)
      setRegistration({ data })
      form.reset()
      setRevision((value) => value + 1)
      onRegistered()
    } catch (error) { setRegistration({ error: error.message }) }
    finally { submitting.current = false; onBusyChange(false) }
  }
  return <>
    <div className="research-actions"><button type="button" onClick={() => { setState({ loading: true }); setRevision((value) => value + 1) }}>Refresh status</button></div>
    {state.loading ? <p role="status">Checking services…</p> : <>
      {state.info?.data && <p className="research-muted">{state.info.data.service} · Version {state.info.data.version}</p>}
      {Object.entries(state).filter(([, value]) => value.error).map(([key, value]) => <p className="research-error" role="alert" key={key}>{key}: {value.error}</p>)}
      <div className="research-service-grid">{['knowledge', 'legal'].map((key) => state[key]?.data && <section className="research-status" key={key}>
        <h3>{key === 'knowledge' ? 'Ayurveda & IP knowledge' : 'Legal & regulatory evidence'}</h3>
        <p>Status: {state[key].data.status} · {state[key].data.total_chunks} passages</p>
        {state[key].data.total_sources != null && <p>{state[key].data.total_sources} sources</p>}
        <p>Domains: {state[key].data.domains_indexed?.join(', ')}</p>
        <p>Retrievers: {state[key].data.retrievers_active?.join(', ')}</p>
      </section>)}</div>
      <div className="research-service-grid">{state.rags?.data?.map((rag) => <section className="research-status" key={rag.rag_id}>
        <h3>{rag.name}</h3><p>{rag.is_healthy ? 'Healthy' : 'Unavailable'} · {rag.connector_type}</p>
        <p>{rag.role} · {rag.authority_tier}</p><p className="research-muted">{rag.rag_id}</p><p>{rag.description}</p>
        {rag.endpoint_url && <p>{rag.endpoint_url}</p>}
      </section>)}</div>
    </>}
    <details className="research-result"><summary>Connect an external RAG service</summary>
      <p className="research-muted">Registers a service for this backend process. It must implement the compatible query and health API. Registration lasts until the backend restarts.</p>
      <form onSubmit={register} className="research-form">
        <fieldset disabled={registration.loading} className="research-fields">
          <label>Service ID<input name="rag_id" required maxLength={100} pattern="[a-zA-Z0-9_-]+" /></label>
          <label>Display name<input name="name" required maxLength={150} /></label>
          <label>Role<select name="role"><option value="authoritative_legal">Legal evidence</option><option value="domain_context">Domain context</option><option value="prior_art">Prior art</option></select></label>
          <label>Authority tier<input name="authority_tier" defaultValue="authoritative" required /></label>
          <label>Service URL<input name="endpoint_url" type="url" required placeholder="https://service.example" /></label>
          <label>Description<input name="description" maxLength={500} /></label>
        </fieldset>
        {registration.error && <p role="alert" className="research-error">{registration.error}</p>}
        {registration.data && <p role="status">{registration.data.message}</p>}
        <div className="research-actions"><button className="research-primary" disabled={registration.loading}>{registration.loading ? 'Connecting…' : 'Register service'}</button></div>
      </form>
    </details>
  </>
}

function ResearchForm({ mode, jurisdiction, language }) {
  const [corpus, setCorpus] = useState('legal')
  const [health, setHealth] = useState(null)
  const [state, setState] = useState({})
  const request = useRef(null)
  useEffect(() => {
    const controller = new AbortController()
    researchApi.health(corpus, controller.signal).then(setHealth, () => {})
    return () => controller.abort()
  }, [corpus])
  useEffect(() => () => request.current?.abort(), [])
  async function submit(event) {
    event.preventDefault()
    if (request.current) return
    const fields = Object.fromEntries(new FormData(event.currentTarget))
    const query = fields.query.trim()
    if (!query) { setState({ error: 'Enter a question or search terms.' }); return }
    const controller = new AbortController()
    request.current = controller
    setState({ loading: true })
    try {
      let data
      const top_k = Number(fields.top_k || 5)
      const domain = fields.domain || undefined
      const category = fields.category || undefined
      if (mode === 'route') data = await researchApi.route(query, controller.signal)
      else if (mode === 'historical') data = await researchApi.historical({ query, requested_date: fields.date, category, top_k }, controller.signal)
      else if (mode === 'search') data = await researchApi.search(corpus, { query, top_k, mode: fields.retrieval, domain, ...(corpus === 'legal' ? { category, jurisdiction: fields.jurisdiction } : {}) }, controller.signal)
      else data = await researchApi.query(corpus, { query, top_k, language, jurisdiction: fields.jurisdiction,
        ...(corpus === 'legal' ? { domains: domain ? [domain] : undefined, categories: category ? [category] : undefined, as_of_date: fields.date || undefined } : { domain }),
      }, controller.signal)
      if (!controller.signal.aborted) setState({ data })
    } catch (error) { if (!controller.signal.aborted) setState({ error: error.message }) }
    finally { if (request.current === controller) request.current = null }
  }
  const data = state.data
  const legal = corpus === 'legal' || mode === 'historical'
  const evidence = data?.results || data?.evidence || []
  const legalCitations = data?.citations || data?.applicable_provisions || []
  const enriched = evidence.map((item) => ({ ...item, ...legalCitations.find((citation) => citation.chunk_id === item.chunk_id) }))
  return <>
    <form onSubmit={submit} className="research-form">
      <fieldset disabled={state.loading} className="research-form">
        <label>{mode === 'search' ? 'Search terms' : 'Question'}<textarea name="query" required maxLength={4000} placeholder="Search formulations, statutory sections, or regulatory requirements" /></label>
        <div className="research-fields">
          {['search', 'query'].includes(mode) && <label>Knowledge source<select value={corpus} onChange={(event) => { setCorpus(event.target.value); setHealth(null); setState({}) }}><option value="legal">Legal & regulatory evidence</option><option value="knowledge">Ayurveda & IP knowledge</option></select></label>}
          {(mode === 'query' || (mode === 'search' && legal)) && <label>Jurisdiction<select name="jurisdiction" defaultValue={jurisdiction.toUpperCase()}><option value="INDIA">India</option><option value="INTERNATIONAL">International</option></select></label>}
          {mode === 'search' && <label>Search method<select name="retrieval"><option value="hybrid">Hybrid</option><option value="bm25">Keyword (BM25)</option><option value="vector">Vector similarity</option></select></label>}
          {mode !== 'route' && <label>Results<input name="top_k" type="number" min={1} max={mode === 'search' ? 50 : 20} defaultValue={5} required /></label>}
          {['search', 'query'].includes(mode) && <label>Domain<select key={`domain-${corpus}`} name="domain"><option value="">All domains</option>{health?.domains_indexed?.map((domain) => <option key={domain}>{domain}</option>)}</select></label>}
          {legal && mode !== 'route' && <label>Legal category<select name="category"><option value="">All categories</option>{health?.categories_indexed?.map((category) => <option key={category}>{category}</option>)}</select></label>}
          {(mode === 'historical' || (mode === 'query' && legal)) && <label>{mode === 'historical' ? 'Historical date' : 'As of date (optional)'}<input type="date" name="date" required={mode === 'historical'} /></label>}
        </div>
      </fieldset>
      {mode === 'historical' && <p className="research-muted">Checks the indexed provisions against their recorded effective dates. This endpoint searches across jurisdictions; each result shows its jurisdiction.</p>}
      {mode === 'search' && !legal && <p className="research-muted">The domain search endpoint covers the Ayurveda and IP corpus and has no jurisdiction filter.</p>}
      {mode === 'query' && <p className="research-muted">Returns retrieved source context. The chat combines sources into a generated answer.</p>}
      {mode === 'route' && <p className="research-muted">Previews intent routing for the text you enter. Chat may adjust routing after translation or for the selected jurisdiction.</p>}
      <div className="research-actions"><button className="research-primary" disabled={state.loading}>{state.loading ? 'Working…' : mode === 'route' ? 'Preview routing' : mode === 'historical' ? 'Look up legal history' : 'Run search'}</button>
        {state.loading && <button type="button" onClick={() => { request.current?.abort(); request.current = null; setState({}) }}>Cancel</button>}
      </div>
    </form>
    {state.error && <p role="alert" className="research-error">{state.error}</p>}
    {data && <section className="research-result" aria-label="Research results">
      {mode === 'route' ? <><h3>{data.intent}</h3><p>{data.explanation}</p><p className="research-muted">Primary: {data.primary_rag} · Routing confidence: {Math.round(data.confidence * 100)}%</p><p>Targets: {data.target_rags?.join(', ')}</p></> : <>
        <h3>{mode === 'historical' ? `Legal evidence as of ${data.requested_date}` : `${evidence.length} evidence passage${evidence.length === 1 ? '' : 's'}`}</h3>
        {data.explanation && <p>{data.explanation}</p>}
        {data.conflict_detected && <p role="status" className="research-error">Statutory conflict / qualification: {data.conflict_details}</p>}
        {data.answer_context && <div dir="auto" className="chat-answer"><Markdown skipHtml remarkPlugins={[remarkGfm]} components={markdownComponents}>{data.answer_context}</Markdown></div>}
        {data.retrieval_metadata && <p className="research-muted">Method: {data.retrieval_metadata.method} · Candidates: {data.retrieval_metadata.total_candidates} · Matched concepts: {data.retrieval_metadata.matched_concepts?.join(', ') || 'None'}</p>}
        {typeof data.retrieval_score === 'number' && <p className="research-muted">Retrieval score: {data.retrieval_score.toFixed(4)}</p>}
        {!evidence.length && <p>No matching evidence found. Try broader terms or fewer filters.</p>}
        <EvidenceList items={enriched} legal={legal} />
        {data.disclaimer && <p className="research-muted">{data.disclaimer}</p>}
      </>}
    </section>}
  </>
}

export default function ResearchTools({ jurisdiction, language, onClose, onRegistered }) {
  const [tab, setTab] = useState('search')
  const [registering, setRegistering] = useState(false)
  return <Modal label="Research tools" onClose={onClose} busy={registering} wide>
    <header className="research-header"><div><h2>Research tools</h2><p>Explore the evidence behind your research.</p></div><button type="button" disabled={registering} className="research-close" onClick={onClose} aria-label="Close research tools">Close</button></header>
    <nav className="research-tabs" aria-label="Research tools">{tabs.map(([id, label]) => <button type="button" disabled={registering} key={id} aria-pressed={tab === id} onClick={() => setTab(id)}>{label}</button>)}</nav>
    {tab === 'services' ? <Services onRegistered={onRegistered} onBusyChange={setRegistering} /> : <ResearchForm key={tab} mode={tab} jurisdiction={jurisdiction} language={language} />}
  </Modal>
}
