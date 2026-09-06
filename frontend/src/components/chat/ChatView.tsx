import React, { useState } from 'react';
import {
  Send,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Info,
  Clock,
  Cpu,
  Layers,
  FileText,
  AlertTriangle,
  Loader2,
  X
} from 'lucide-react';
import { QueryResponse, Citation, RetrievedChunk, DocumentItem } from '../../types';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  responseObj?: QueryResponse;
  timestamp: string;
}

interface ChatViewProps {
  documents: DocumentItem[];
}

export const ChatView: React.FC<ChatViewProps> = ({ documents }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: "Hello! I am your EnterpriseDoc AI assistant. Ask any question about your indexed contracts, financial reports, or technical manuals. All answers are strictly grounded in retrieved evidence with verifiable source citations.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [activeDebugChunks, setActiveDebugChunks] = useState<string | null>(null);

  const sampleQuestions = [
    "What was the total revenue in the third quarter?",
    "What is the limitation of liability under the contract?",
    "What is the maximum allowed query latency and throughput?",
    "Summarize the key takeaways and financial highlights."
  ];

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isLoading) return;

    setInputQuery('');
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const resp = await api.executeQuery(q, undefined, 5, true, true);
      const aiMsg: ChatMessage = {
        id: resp.query_id || `ai-${Date.now()}`,
        sender: 'ai',
        text: resp.answer,
        responseObj: resp,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text: `Error processing query: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
  className="flex h-[calc(100vh-4rem)] max-w-7xl mx-auto overflow-hidden"
  style={{ transform: 'scale(0.9)', transformOrigin: 'top left', width: '111.11%' }}
>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-slate-950 border-r border-slate-800/80">
        {/* Messages Scroll Area */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.map((msg) => {
            const isAi = msg.sender === 'ai';
            const resp = msg.responseObj;
            const isInsufficient = resp && !resp.is_grounded;

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isAi ? 'items-start' : 'items-end'} max-w-3xl ${isAi ? 'mr-auto' : 'ml-auto'}`}
              >
                <div className="flex items-center gap-2 mb-1.5 px-1">
                  <span className="text-[11px] font-medium text-slate-400">
                    {isAi ? 'EnterpriseDoc AI' : 'You'}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{msg.timestamp}</span>
                  {resp && (
                    <Badge label={resp.intent} variant="purple" size="sm" />
                  )}
                </div>

                <div
                  className={`p-4 rounded-2xl text-xs leading-relaxed ${
                    isAi
                      ? 'bg-slate-900 border border-slate-800 text-slate-200 shadow-sm'
                      : 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                  }`}
                >
                  {isInsufficient && (
                    <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                      <span>Notice: Grounding guardrails detected insufficient context in the knowledge base.</span>
                    </div>
                  )}

                  <div className="whitespace-pre-wrap font-sans text-[13px] leading-relaxed">
                    {msg.text}
                  </div>

                  {/* Citations List if available */}
                  {resp && resp.citations && resp.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80">
                      <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Verified Source Citations ({resp.citations.length}):</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {resp.citations.map((c, i) => (
                          <button
                            key={i}
                            onClick={() => setSelectedCitation(c)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950 border border-slate-700/80 hover:border-sky-500 text-[11px] text-slate-300 hover:text-white transition-all cursor-pointer"
                          >
                            <FileText className="w-3 h-3 text-sky-400" />
                            <span className="font-medium truncate max-w-[160px]">{c.document_name}</span>
                            <span className="text-slate-400 font-mono">p.{c.page_number}</span>
                            <span className="text-[10px] px-1 rounded bg-sky-500/20 text-sky-300 font-mono">
                              {(c.relevance_score * 100).toFixed(0)}%
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Retrieved Chunks Accordion */}
                  {resp && resp.retrieved_chunks && resp.retrieved_chunks.length > 0 && (
                    <div className="mt-3">
                      <button
                        onClick={() => setActiveDebugChunks(activeDebugChunks === msg.id ? null : msg.id)}
                        className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        {activeDebugChunks === msg.id ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        <span>{activeDebugChunks === msg.id ? 'Hide' : 'Inspect'} {resp.retrieved_chunks.length} Retrieved Context Chunks</span>
                      </button>

                      {activeDebugChunks === msg.id && (
                        <div className="mt-2.5 space-y-2 border-t border-slate-800/60 pt-2">
                          {resp.retrieved_chunks.map((chunk, cIdx) => (
                            <div
                              key={cIdx}
                              className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] space-y-1"
                            >
                              <div className="flex items-center justify-between text-slate-400">
                                <span className="font-semibold text-sky-400">
                                  #{cIdx + 1} {chunk.document_name} (Page {chunk.page_number})
                                </span>
                                <div className="font-mono text-[10px] space-x-2">
                                  {chunk.rerank_score !== undefined && chunk.rerank_score !== null && (
                                    <span>Rerank: <strong className="text-emerald-400">{chunk.rerank_score.toFixed(3)}</strong></span>
                                  )}
                                  {chunk.hybrid_score !== undefined && chunk.hybrid_score !== null && (
                                    <span>RRF: <strong className="text-slate-300">{chunk.hybrid_score.toFixed(3)}</strong></span>
                                  )}
                                </div>
                              </div>
                              <p className="text-slate-300 font-mono text-[10px] leading-relaxed line-clamp-3">
                                {chunk.content}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {resp && (
                  <div className="mt-1 px-2 flex items-center gap-3 text-[10px] text-slate-400 font-mono">
                    <span>Latency: {resp.latency_ms}ms</span>
                    <span>•</span>
                    <span>Model: {resp.model_used}</span>
                    <span>•</span>
                    <span>Trace: {resp.trace_id?.slice(0, 8)}...</span>
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 max-w-md animate-pulse">
              <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
              <span>Searching FAISS & BM25 indexes and synthesizing grounded answer...</span>
            </div>
          )}
        </div>

        {/* Input Bar & Suggestion Chips */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60">
          {/* Sample Prompts */}
          <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1 text-xs">
            <span className="text-[11px] text-slate-400 font-medium whitespace-nowrap">Try:</span>
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                className="px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] whitespace-nowrap border border-slate-700/60 transition-colors cursor-pointer"
              >
                {q}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              placeholder="Ask a question grounded in your enterprise knowledge base..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 shadow-inner"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isLoading}
              className={`p-2.5 rounded-xl transition-all cursor-pointer ${
                !inputQuery.trim() || isLoading
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                  : 'bg-sky-600 hover:bg-sky-500 text-white shadow-md shadow-sky-600/30'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Citation Inspector Drawer */}
      {selectedCitation && (
        <div className="w-80 lg:w-96 bg-slate-900 border-l border-slate-800 flex flex-col shadow-xl animate-in slide-in-from-right-5 duration-150">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <h3 className="font-semibold text-xs text-white">Source Citation Details</h3>
            </div>
            <button
              onClick={() => setSelectedCitation(null)}
              className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 p-4 space-y-4 overflow-y-auto text-xs">
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Document</span>
                <p className="font-medium text-slate-200 truncate mt-0.5">{selectedCitation.document_name}</p>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Page Number</span>
                  <p className="font-mono text-slate-200 font-bold">Page {selectedCitation.page_number}</p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Relevance Score</span>
                  <p className="font-mono text-emerald-400 font-bold">{(selectedCitation.relevance_score * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block mb-1.5">
                Exact Verbatim Evidence
              </span>
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                {selectedCitation.snippet}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-sky-950/20 border border-sky-900/40 text-[11px] text-sky-300">
              <Info className="w-3.5 h-3.5 inline mr-1 text-sky-400" />
              This citation was matched directly from the indexed document and verified via cross-attention.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
