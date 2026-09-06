import React, { useState } from 'react';
import {
  BarChart3,
  Play,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  Layers,
  Sparkles,
  Loader2
} from 'lucide-react';
import { EvaluationItem } from '../../types';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

interface EvaluationViewProps {
  evaluations: EvaluationItem[];
  onRefresh: () => void;
}

export const EvaluationView: React.FC<EvaluationViewProps> = ({
  evaluations,
  onRefresh
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [selectedEval, setSelectedEval] = useState<EvaluationItem | null>(
    evaluations.length > 0 ? evaluations[0] : null
  );

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    try {
      const newEval = await api.runEvaluation(5);
      onRefresh();
      setSelectedEval(newEval);
    } catch (err: any) {
      alert(`Benchmark execution failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const activeEval = selectedEval || (evaluations.length > 0 ? evaluations[0] : null);

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-sky-400" />
            <span>RAGAS Benchmark & Quality Evaluation</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated RAG metrics evaluating Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={isRunning}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
            isRunning
              ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
              : 'bg-sky-600 hover:bg-sky-500 text-white shadow-md shadow-sky-600/20'
          }`}
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Evaluating Test Suite...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Run RAGAS Benchmark</span>
            </>
          )}
        </button>
      </div>

      {activeEval ? (
        <>
          {/* Main Metric Gauges Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Overall */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900 to-sky-950/40 border border-sky-500/30">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Overall Quality</span>
              <div className="mt-3 text-3xl font-bold text-white font-mono">
                {(activeEval.overall_score * 100).toFixed(1)}%
              </div>
              <div className="mt-2 text-[11px] text-sky-400">Harmonic RAGAS index</div>
            </div>

            {/* Faithfulness */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Faithfulness</span>
              <div className="mt-3 text-3xl font-bold text-emerald-400 font-mono">
                {(activeEval.faithfulness * 100).toFixed(1)}%
              </div>
              <div className="mt-2 text-[11px] text-slate-400">Groundedness in context</div>
            </div>

            {/* Answer Relevancy */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Answer Relevancy</span>
              <div className="mt-3 text-3xl font-bold text-sky-400 font-mono">
                {(activeEval.answer_relevancy * 100).toFixed(1)}%
              </div>
              <div className="mt-2 text-[11px] text-slate-400">Semantic query alignment</div>
            </div>

            {/* Context Precision */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Context Precision</span>
              <div className="mt-3 text-3xl font-bold text-indigo-400 font-mono">
                {(activeEval.context_precision * 100).toFixed(1)}%
              </div>
              <div className="mt-2 text-[11px] text-slate-400">Signal-to-noise ratio</div>
            </div>

            {/* Context Recall */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Context Recall</span>
              <div className="mt-3 text-3xl font-bold text-purple-400 font-mono">
                {(activeEval.context_recall * 100).toFixed(1)}%
              </div>
              <div className="mt-2 text-[11px] text-slate-400">Ground truth coverage</div>
            </div>
          </div>

          {/* Sample Scenario Drill-down */}
          <div className="p-6 rounded-xl bg-slate-900 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm text-white">
                Benchmark Sample Inspection ({activeEval.run_name})
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                {activeEval.sample_count} Scenarios Evaluated
              </span>
            </div>

            <div className="space-y-4">
              {activeEval.details && activeEval.details.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sky-400">#{idx + 1}</span>
                      <Badge label={item.domain || 'Domain Scenario'} variant="sky" />
                      <span className="font-medium text-slate-200">{item.question}</span>
                    </div>
                    <div className="flex items-center gap-3 font-mono text-[11px]">
                      <span>Faith: <strong className="text-emerald-400">{(item.faithfulness * 100).toFixed(0)}%</strong></span>
                      <span>•</span>
                      <span>Rel: <strong className="text-sky-400">{(item.answer_relevancy * 100).toFixed(0)}%</strong></span>
                      <span>•</span>
                      <span>Prec: <strong className="text-indigo-400">{(item.context_precision * 100).toFixed(0)}%</strong></span>
                      <span>•</span>
                      <span>Recall: <strong className="text-purple-400">{(item.context_recall * 100).toFixed(0)}%</strong></span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                    <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                        Synthesized Answer
                      </span>
                      <p className="text-slate-200 font-sans leading-relaxed">{item.answer}</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                        Ground Truth Reference
                      </span>
                      <p className="text-slate-300 font-sans leading-relaxed">
                        {item.ground_truth || 'N/A (Sufficient context verification)'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="p-12 rounded-xl bg-slate-900 border border-slate-800 text-center space-y-3">
          <BarChart3 className="w-10 h-10 text-slate-500 mx-auto" />
          <h3 className="font-semibold text-slate-200 text-sm">No Evaluations Run Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Click "Run RAGAS Benchmark" above to test faithfulness, answer relevancy, and context retrieval against curated enterprise scenarios.
          </p>
        </div>
      )}
    </div>
  );
};
