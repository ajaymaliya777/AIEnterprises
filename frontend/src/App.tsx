import React, { useState, useEffect } from 'react';
import { Sidebar, TabType } from './components/common/Sidebar';
import { Navbar } from './components/common/Navbar';
import { DashboardView } from './components/dashboard/DashboardView';
import { DocumentManagerView } from './components/documents/DocumentManagerView';
import { DocumentUploadModal } from './components/documents/DocumentUploadModal';
import { ChatView } from './components/chat/ChatView';
import { RetrievalDebugView } from './components/debug/RetrievalDebugView';
import { EvaluationView } from './components/evaluation/EvaluationView';
import { ObservabilityView } from './components/observability/ObservabilityView';
import { DocumentItem, QueryHistoryItem, EvaluationItem, SystemHealth } from './types';
import { api } from './api/client';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationItem[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const loadData = async () => {
    try {
      const [h, docs, history, evals] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getDocuments().catch(() => []),
        api.getQueryHistory().catch(() => []),
        api.getEvaluations().catch(() => [])
      ]);
      if (h) setHealth(h);
      setDocuments(docs);
      setQueryHistory(history);
      setEvaluations(evals);
    } catch (e) {
      console.error("Initial load failed:", e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 antialiased font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        documentCount={documents.length}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar
          health={health}
          onOpenUpload={() => setIsUploadModalOpen(true)}
        />

        <main className="flex-1 overflow-y-auto">
          {activeTab === 'dashboard' && (
            <DashboardView
              documents={documents}
              queryHistory={queryHistory}
              evaluations={evaluations}
              health={health}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === 'documents' && (
            <DocumentManagerView
              documents={documents}
              onRefresh={loadData}
              onOpenUploadModal={() => setIsUploadModalOpen(true)}
            />
          )}

          {activeTab === 'chat' && (
            <ChatView documents={documents} />
          )}

          {activeTab === 'debug' && (
            <RetrievalDebugView />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationView
              evaluations={evaluations}
              onRefresh={loadData}
            />
          )}

          {activeTab === 'observability' && (
            <ObservabilityView />
          )}
        </main>
      </div>

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}

export default App;
