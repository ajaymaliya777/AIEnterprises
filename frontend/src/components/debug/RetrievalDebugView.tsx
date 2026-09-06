import React, { useState } from 'react';
import {
  SlidersHorizontal,
  Search,
  Zap,
  Clock,
  Layers,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Loader2
} from 'lucide-react';
import { RetrievalDebugResult, RetrievedChunk } from '../../types';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

export const RetrievalDebugView: React.FC = () => {
  const [query, setQuery] = useState('revenue growth in the third quarter');
  const [topK, setTopK] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [debugData, setDebugData] = useState<RetrievalDebugResult | null>(null);

  const handleRunDebug = async () => {
    if (!query.trim() || isLoading) return;
    setIsLoading(true);
    try {
      const res = await api.debugRetrieval(query, undefined, topK);
      setDebugData(res);
    } catch (err: any) {
      alert(`Debug retrieval error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Header & Description */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-sky-400" />
          <span>Multi-Stage Retrieval Diagnostic Panel</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Inspect lexical keyword search (BM25), dense semantic search (FAISS), reciprocal rank fusion (RRF), and cross-encoder reranking side-by-side independently of LLM generation.
        </p>
      </div>

      {/* Query Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Enter test query for retrieval inspection..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRunDebug()}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <span className="text-slate-400">Top-K:</span>
            <input
              type="range"
              min="3"
              max="15"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-24 accent-sky-500 cursor-pointer"
            />
            <span className="font-mono font-bold text-sky-400">{topK}</span>
          </div>

          <button
            onClick={handleRunDebug}
            disabled={isLoading || !query.trim()}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              isLoading || !query.trim()
                ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                : 'bg-sky-600 hover:bg-sky-500 text-white shadow-md shadow-sky-600/20'
            }`}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            <span>Inspect Pipeline</span>
          </button>
        </div>
      </div>

      {/* Latency Breakdown & Intent Card */}
      {debugData && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-3">
              <span className="text-slate-400">ML Intent Classification:</span>
              <Badge label={debugData.intent} variant="purple" />
              <span className="font-mono text-slate-400">Confidence: {(debugData.intent_confidence * 100).toFixed(1)}%</span>
            </div>

            <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
              <span>Dense: <strong className="text-sky-400">{debugData.timings_ms?.dense_search_ms ?? 0}ms</strong></span>
              <span>•</span>
              <span>Sparse: <strong className="text-amber-400">{debugData.timings_ms?.sparse_search_ms ?? 0}ms</strong></span>
              <span>•</span>
              <span>RRF: <strong className="text-indigo-400">{debugData.timings_ms?.rrf_fusion_ms ?? 0}ms</strong></span>
              <span>•</span>
              <span>Rerank: <strong className="text-emerald-400">{debugData.timings_ms?.reranking_ms ?? 0}ms</strong></span>
              <span>•</span>
              <span>Total: <strong className="text-slate-200">{debugData.timings_ms?.total_retrieval_ms ?? 0}ms</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* 4-Column Side-by-Side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. BM25 Lexical */}
        <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <h3 className="font-semibold text-xs text-white">1. Lexical (BM25)</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Keyword Index</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5 max-h-[600px]">
            {debugData && debugData.sparse_results.length > 0 ? (
              debugData.sparse_results.map((chunk, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 text-[11px] space-y-1">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-semibold text-amber-400 truncate max-w-[120px]">
                      #{idx + 1} {chunk.document_name}
                    </span>
                    <span className="font-mono text-amber-300 font-bold">
                      BM25: {chunk.sparse_score?.toFixed(2) ?? 'N/A'}
                    </span>
                  </div>
                  <p className="text-slate-300 font-mono text-[10px] line-clamp-3">
                    {chunk.content}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-slate-400 text-xs text-center py-12">
                {isLoading ? 'Searching...' : 'Run query to inspect BM25 hits.'}
              </div>
            )}
          </div>
        </div>

        {/* 2. FAISS Dense Vector */}
        <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              <h3 className="font-semibold text-xs text-white">2. Vector (FAISS)</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Cosine FlatIP</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5 max-h-[600px]">
            {debugData && debugData.dense_results.length > 0 ? (
              debugData.dense_results.map((chunk, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 text-[11px] space-y-1">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-semibold text-sky-400 truncate max-w-[120px]">
                      #{idx + 1} {chunk.document_name}
                    </span>
                    <span className="font-mono text-sky-300 font-bold">
                      Cos: {chunk.dense_score?.toFixed(3) ?? 'N/A'}
                    </span>
                  </div>
                  <p className="text-slate-300 font-mono text-[10px] line-clamp-3">
                    {chunk.content}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-slate-400 text-xs text-center py-12">
                {isLoading ? 'Searching...' : 'Run query to inspect FAISS hits.'}
              </div>
            )}
          </div>
        </div>

        {/* 3. Hybrid Fusion (RRF) */}
        <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-400" />
              <h3 className="font-semibold text-xs text-white">3. Hybrid (RRF)</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">k=60 Fusion</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5 max-h-[600px]">
            {debugData && debugData.hybrid_results.length > 0 ? (
              debugData.hybrid_results.map((chunk, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 text-[11px] space-y-1">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-semibold text-indigo-400 truncate max-w-[120px]">
                      #{idx + 1} {chunk.document_name}
                    </span>
                    <span className="font-mono text-indigo-300 font-bold">
                      RRF: {chunk.hybrid_score?.toFixed(4) ?? 'N/A'}
                    </span>
                  </div>
                  <p className="text-slate-300 font-mono text-[10px] line-clamp-3">
                    {chunk.content}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-slate-400 text-xs text-center py-12">
                {isLoading ? 'Merging...' : 'Run query to inspect fused ranks.'}
              </div>
            )}
          </div>
        </div>

        {/* 4. Cross-Encoder Reranked */}
        <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <h3 className="font-semibold text-xs text-white">4. Reranked (ms-marco)</h3>
            </div>
            <span className="text-[10px] font-mono text-emerald-400">Final Top-K</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5 max-h-[600px]">
            {debugData && debugData.reranked_results.length > 0 ? (
              debugData.reranked_results.map((chunk, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-emerald-500/30 text-[11px] space-y-1 shadow-sm">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-semibold text-emerald-400 truncate max-w-[120px]">
                      #{idx + 1} {chunk.document_name}
                    </span>
                    <span className="font-mono text-emerald-300 font-bold">
                      Score: {chunk.rerank_score?.toFixed(4) ?? 'N/A'}
                    </span>
                  </div>
                  <p className="text-slate-300 font-mono text-[10px] line-clamp-3">
                    {chunk.content}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-slate-400 text-xs text-center py-12">
                {isLoading ? 'Reranking...' : 'Run query to inspect final reranked top-K.'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
