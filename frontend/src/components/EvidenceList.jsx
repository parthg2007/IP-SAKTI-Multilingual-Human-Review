import { useEffect, useState } from 'react'
import { researchApi, safeSourceUrl } from '../lib/api.js'

function DocumentDetails({ documentId }) {
  const [state, setState] = useState({ loading: true })
  useEffect(() => {
    const controller = new AbortController()
    researchApi.document(documentId, controller.signal).then(
      (data) => setState({ data }),
      (error) => { if (!controller.signal.aborted) setState({ error: error.message }) },
    )
    return () => controller.abort()
  }, [documentId])
  if (state.loading) return <p role="status">Loading document…</p>
  if (state.error) return <p role="alert">{state.error}</p>
  const doc = state.data
  return <div className="research-document">
    <strong>{doc.title}</strong>
    <p>{doc.jurisdiction} · {doc.authority_tier} · {doc.total_chunks} indexed passages</p>
    <p>{doc.category} · {doc.domain}</p>
    <p className="research-excerpt">{doc.sample_chunk?.text}</p>
  </div>
}

export default function EvidenceList({ items = [], legal = false }) {
  const [openDocument, setOpenDocument] = useState(null)
  return <div className="research-evidence" aria-label="Sources">
    {items.map((item, index) => {
      const url = safeSourceUrl(item.source_url || item.url)
      const id = item.chunk_id || item.id || index
      const documentId = item.document_id || item.documentId
      return <details key={`${id}:${index}`} className="research-source">
        <summary><span className="research-ref">[{item.ref || `S${index + 1}`}]</span> {item.title}</summary>
        <div className="research-source-body">
          <p>{item.source_name || item.sourceName || item.authority_tier} {item.domain && `· ${item.domain}`}</p>
          {item.jurisdiction && <p>Jurisdiction: {item.jurisdiction}</p>}
          {(item.section || item.rule || item.article) && <p>{[item.section && `Section ${item.section}`, item.rule && `Rule ${item.rule}`, item.article && `Article ${item.article}`].filter(Boolean).join(' · ')}</p>}
          {item.version && <p>Version {item.version}{item.effective_from && ` · Effective from ${item.effective_from}`}</p>}
          <p className="research-excerpt">{item.text || item.excerpt}</p>
          <p className="research-muted">{item.chunk_id}{typeof item.score === 'number' && ` · Retrieval score ${item.score.toFixed(4)}`}{item.retrieval_method && ` · ${item.retrieval_method}`}</p>
          <div className="research-actions">
            {url && <a href={url} target="_blank" rel="noopener noreferrer">Open source ↗</a>}
            {documentId && (legal || item.rag_source === 'RAG2') && <button type="button" onClick={() => setOpenDocument(openDocument === id ? null : id)}>{openDocument === id ? 'Hide document' : 'Document details'}</button>}
          </div>
          {openDocument === id && documentId && <DocumentDetails key={documentId} documentId={documentId} />}
        </div>
      </details>
    })}
  </div>
}
