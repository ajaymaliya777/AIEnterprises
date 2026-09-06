import {
  DocumentItem,
  DocumentDetail,
  QueryResponse,
  RetrievalDebugResult,
  QueryHistoryItem,
  EvaluationItem,
  TraceItem,
  SystemHealth
} from '../types';

const API_BASE = 'https://aienterprises.onrender.com';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...(options?.headers || {})
    }
  });

  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errData.message || errorMsg;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export const api = {
  getHealth: () => fetchJson<SystemHealth>('/health'),

  getDocuments: () => fetchJson<DocumentItem[]>('/documents'),

  getDocument: (id: string) => fetchJson<DocumentDetail>(`/documents/${id}`),

  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || 'Failed to upload document');
    }
    return response.json();
  },

  deleteDocument: (id: string) =>
    fetchJson<{ message: string }>(`/documents/${id}`, { method: 'DELETE' }),

  executeQuery: (
    query: string,
    documentIds?: string[],
    topK: number = 5,
    enableReranking: boolean = true,
    includeDebug: boolean = true
  ) =>
    fetchJson<QueryResponse>('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
        top_k: topK,
        enable_reranking: enableReranking,
        include_debug: includeDebug
      })
    }),

  debugRetrieval: (query: string, documentIds?: string[], topK: number = 5) =>
    fetchJson<RetrievalDebugResult>('/query/retrieval-debug', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
        top_k: topK,
        enable_reranking: true
      })
    }),

  getQueryHistory: () => fetchJson<QueryHistoryItem[]>('/query/history'),

  runEvaluation: (sampleSize: number = 5) =>
    fetchJson<EvaluationItem>('/evaluations/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample_size: sampleSize })
    }),

  getEvaluations: () => fetchJson<EvaluationItem[]>('/evaluations'),

  getTraces: () => fetchJson<TraceItem[]>('/observability/traces'),

  getObservabilityStats: () => fetchJson<any>('/observability/stats')
};
