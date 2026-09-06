export interface DocumentItem {
  id: string;
  filename: string;
  original_name: string;
  mime_type: string;
  file_size: number;
  category: string;
  ocr_applied: boolean;
  status: string;
  error_message?: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunkItem {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  content: string;
  token_count: number;
  char_start: number;
  char_end: number;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface DocumentDetail extends DocumentItem {
  chunks: DocumentChunkItem[];
}

export interface Citation {
  document_id: string;
  document_name: string;
  chunk_id: string;
  page_number: number;
  snippet: string;
  relevance_score: number;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  content: string;
  dense_score?: number | null;
  sparse_score?: number | null;
  hybrid_score?: number | null;
  rerank_score?: number | null;
}

export interface RetrievalDebugResult {
  query: string;
  intent: string;
  intent_confidence: number;
  dense_results: RetrievedChunk[];
  sparse_results: RetrievedChunk[];
  hybrid_results: RetrievedChunk[];
  reranked_results: RetrievedChunk[];
  timings_ms: Record<string, number>;
}

export interface QueryResponse {
  query_id: string;
  query: string;
  intent: string;
  intent_confidence: number;
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  is_grounded: boolean;
  model_used: string;
  latency_ms: number;
  trace_id?: string | null;
  debug?: RetrievalDebugResult | null;
}

export interface QueryHistoryItem {
  id: string;
  query_text: string;
  intent: string;
  answer_text: string;
  latency_ms: number;
  is_grounded: boolean;
  model_used: string;
  created_at: string;
  citations: Citation[];
}

export interface EvaluationItem {
  id: string;
  run_name: string;
  dataset_name: string;
  sample_count: number;
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  context_recall: number;
  overall_score: number;
  details: any[];
  created_at: string;
}

export interface TraceSpan {
  name: string;
  duration_ms: number;
  status: string;
  metadata: Record<string, any>;
}

export interface TraceItem {
  id: string;
  query_id?: string | null;
  trace_id: string;
  query_text: string;
  total_latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  status: string;
  error_message?: string | null;
  spans: TraceSpan[];
  created_at: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  environment: string;
  database: string;
  vector_store_chunks: number;
  bm25_chunks: number;
  embedding_model: string;
  reranker_model: string;
  gemini_model: string;
  ocr_enabled: boolean;
}
