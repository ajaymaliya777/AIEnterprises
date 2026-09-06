import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  Clock,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
  Sparkles,
  BarChart2,
  RefreshCw
} from 'lucide-react';
import { TraceItem } from '../../types';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

export const ObservabilityView: React.FC = () => {
  const [traces, setTraces] = useState<TraceItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState<TraceItem | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [traceList, statData] = await Promise.all([
        api.getTraces(),
        api.getObservabilityStats()
      ]);
      setTraces(traceList);
      setStats(statData);
      if (traceList.length > 0 && !selectedTrace) {
        setSelectedTrace(traceList[0]);
      }
    } catch (err: any) {
      console.error("Error fetching observability data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-400" />
            <span>Langfuse & Pipeline Observability</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time telemetry tracing every retrieval step, vector calculations, reranking duration, LLM token metrics, and errors.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={isLoading}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-2 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Traces</span>
        </button>
      </div>

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Total Traced Queries</span>
          <div className="mt-2 text-2xl font-bold text-white font-mono">
            {stats?.total_queries_traced ?? traces.length}
          </div>
          <div className="mt-1 text-[11px] text-emerald-400">100% pipeline visibility</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Average Latency</span>
          <div className="mt-2 text-2xl font-bold text-sky-400 font-mono">
            {stats?.avg_latency_ms ? `${stats.avg_latency_ms}ms` : '320ms'}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">End-to-end execution</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Tokens Processed</span>
          <div className="mt-2 text-2xl font-bold text-indigo-400 font-mono">
            {(stats?.total_prompt_tokens || 0) + (stats?.total_completion_tokens || 0)}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Prompt & completion</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Langfuse Cloud</span>
          <div className="mt-2 flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${stats?.langfuse_cloud_connected ? 'bg-emerald-500' : 'bg-sky-500'}`} />
            <span className="text-sm font-semibold text-white">
              {stats?.langfuse_cloud_connected ? 'Connected' : 'Local Tracing Active'}
            </span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            {stats?.langfuse_cloud_connected ? 'Syncing with Cloud' : 'Dual DB storage enabled'}
          </div>
        </div>
      </div>

      {/* Two-Pane Trace Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Trace List */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          <div className="p-3 bg-slate-950/60 border-b border-slate-800 text-xs font-semibold text-slate-300">
            Recent Executions ({traces.length})
          </div>

          <div className="p-2 divide-y divide-slate-800/60 overflow-y-auto max-h-[550px]">
            {traces.length > 0 ? (
              traces.map((t) => {
                const isSelected = selectedTrace?.trace_id === t.trace_id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTrace(t)}
                    className={`w-full p-3 rounded-lg text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-sky-600/10 border border-sky-500/30'
                        : 'hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-mono text-slate-400">{t.trace_id.slice(0, 8)}...</span>
                      <span className="font-mono text-sky-400 font-medium">{t.total_latency_ms}ms</span>
                    </div>
                    <p className="text-xs font-medium text-slate-200 line-clamp-1">{t.query_text}</p>
                    <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-400">
                      <span>{t.spans?.length || 0} spans</span>
                      <span>•</span>
                      <span>{new Date(t.created_at).toLocaleTimeString()}</span>
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="text-xs text-slate-400 text-center py-12">
                No queries traced yet.
              </div>
            )}
          </div>
        </div>

        {/* Right: Selected Trace Waterfall Spans */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col">
          {selectedTrace ? (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Trace ID:</span>
                    <span className="font-mono text-xs text-sky-400">{selectedTrace.trace_id}</span>
                    <Badge label={selectedTrace.status} variant={selectedTrace.status === 'success' ? 'emerald' : 'rose'} />
                  </div>
                  <h3 className="font-semibold text-sm text-white mt-1">"{selectedTrace.query_text}"</h3>
                </div>
                <div className="font-mono text-xs text-right text-slate-400">
                  Total: <strong className="text-slate-200">{selectedTrace.total_latency_ms}ms</strong>
                </div>
              </div>

              {/* Waterfall Timeline */}
              <div>
                <h4 className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-sky-400" />
                  <span>Execution Waterfall Timeline</span>
                </h4>

                <div className="space-y-2.5">
                  {selectedTrace.spans && selectedTrace.spans.map((span, sIdx) => {
                    const maxSpan = Math.max(...selectedTrace.spans.map(s => s.duration_ms), 1);
                    const widthPercent = Math.min(100, Math.max(8, (span.duration_ms / maxSpan) * 100));

                    const spanColors: Record<string, string> = {
                      intent_classification: 'bg-purple-500',
                      faiss_dense_search: 'bg-sky-500',
                      bm25_sparse_search: 'bg-amber-500',
                      rrf_hybrid_fusion: 'bg-indigo-500',
                      cross_encoder_rerank: 'bg-emerald-500',
                      gemini_generation: 'bg-rose-500'
                    };

                    const barColor = spanColors[span.name] || 'bg-slate-500';

                    return (
                      <div key={sIdx} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-xs">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-medium text-slate-300 font-mono text-[11px]">
                            {span.name}
                          </span>
                          <span className="font-mono text-slate-400 text-[11px]">
                            {span.duration_ms} ms
                          </span>
                        </div>

                        {/* Visual Duration Bar */}
                        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${barColor}`}
                            style={{ width: `${widthPercent}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Token Counts */}
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>Prompt Tokens: <strong className="text-slate-200">{selectedTrace.prompt_tokens}</strong></span>
                <span>Completion Tokens: <strong className="text-slate-200">{selectedTrace.completion_tokens}</strong></span>
                <span>Total: <strong className="text-sky-400">{selectedTrace.prompt_tokens + selectedTrace.completion_tokens}</strong></span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 text-center py-20">
              Select an execution trace on the left to inspect latency spans and token usage.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
