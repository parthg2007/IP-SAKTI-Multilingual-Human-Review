import axios from 'axios'

export function safeSourceUrl(value) {
  try {
    const url = new URL(value)
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null
  } catch {
    return null
  }
}

export function createChatApi(baseURL = '') {
  const client = axios.create({ baseURL: baseURL.replace(/\/+$/, ''), timeout: 120_000 })

  return async function queryKnowledge({ query, jurisdiction = 'india', signal }) {
    try {
      const { data } = await client.post('/api/v1/orchestrator/query', {
        query: query.trim(),
        jurisdiction: jurisdiction.toUpperCase(),
        top_k_per_rag: 4,
      }, { signal })

      if (!data || typeof data.synthesized_answer !== 'string' || !data.synthesized_answer.trim()
        || !Array.isArray(data.citations) || !Array.isArray(data.connected_rags_responded)) {
        throw new Error('The server returned an unreadable answer. Please try again.')
      }
      if (!data.connected_rags_responded.length) {
        throw new Error('The knowledge service is unavailable. Please try again shortly.')
      }

      return {
        content: data.synthesized_answer,
        citations: data.citations.filter((item) => item && typeof item.title === 'string').map((item) => ({
          id: `${item.rag_source || ''}:${item.chunk_id}`,
          title: item.title,
          sourceName: item.source_name,
          url: safeSourceUrl(item.source_url),
          excerpt: item.text,
        })),
        disclaimer: typeof data.legal_disclaimer === 'string' ? data.legal_disclaimer : '',
      }
    } catch (error) {
      if (axios.isCancel(error) || signal?.aborted) throw error
      if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
        throw new Error('The answer took too long. Please try again with a shorter question.', { cause: error })
      }
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 422) {
          throw new Error('Please enter a question of 1–4,000 characters and select a jurisdiction.', { cause: error })
        }
        if (error.response?.status === 429) {
          throw new Error('The service is busy. Please wait a moment, then try again.', { cause: error })
        }
        throw new Error(error.response
          ? 'The server could not answer your question. Please try again shortly.'
          : 'Unable to reach the backend. Check that it is running and try again.', { cause: error })
      }
      throw error
    }
  }
}

export const queryKnowledge = createChatApi(import.meta.env?.VITE_API_BASE_URL || '')
