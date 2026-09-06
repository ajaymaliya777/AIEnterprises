import React, { useState } from 'react';
import {
  Files,
  Upload,
  Trash2,
  Eye,
  CheckCircle2,
  Clock,
  Scan,
  FileText,
  FileCode,
  AlertCircle,
  X,
  Search
} from 'lucide-react';
import { DocumentItem, DocumentDetail, DocumentChunkItem } from '../../types';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

interface DocumentManagerViewProps {
  documents: DocumentItem[];
  onRefresh: () => void;
  onOpenUploadModal: () => void;
}

export const DocumentManagerView: React.FC<DocumentManagerViewProps> = ({
  documents,
  onRefresh,
  onOpenUploadModal
}) => {
  const [selectedDocDetail, setSelectedDocDetail] = useState<DocumentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  const handleInspectChunks = async (docId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await api.getDocument(docId);
      setSelectedDocDetail(detail);
    } catch (err: any) {
      alert(`Error fetching document details: ${err.message}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDelete = async (docId: string, docName: string) => {
    if (!window.confirm(`Are you sure you want to delete '${docName}'? This will remove all vectors from FAISS and BM25 indexes.`)) {
      return;
    }
    setIsDeleting(docId);
    try {
      await api.deleteDocument(docId);
      onRefresh();
      if (selectedDocDetail?.id === docId) {
        setSelectedDocDetail(null);
      }
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message}`);
    } finally {
      setIsDeleting(null);
    }
  };

  const filteredDocs = documents.filter((d) =>
    d.original_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Files className="w-5 h-5 text-sky-400" />
            <span>Document Knowledge Base</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Manage enterprise files, inspect parsed chunks, and monitor OCR status.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search documents or categories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>
          <button
            onClick={onOpenUploadModal}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/20 transition-all cursor-pointer whitespace-nowrap"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload</span>
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Document</th>
                <th className="py-3 px-4">ML Domain Category</th>
                <th className="py-3 px-4">OCR Status</th>
                <th className="py-3 px-4">Size</th>
                <th className="py-3 px-4">Chunks Indexed</th>
                <th className="py-3 px-4">Date Added</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredDocs.length > 0 ? (
                filteredDocs.map((doc) => {
                  const sizeKB = (doc.file_size / 1024).toFixed(1);
                  const isPdf = doc.original_name.toLowerCase().endsWith('.pdf');
                  const isDocx = doc.original_name.toLowerCase().endsWith('.docx');

                  return (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-slate-800 text-sky-400 flex items-center justify-center flex-shrink-0">
                            {isPdf ? <FileText className="w-4 h-4" /> : <FileCode className="w-4 h-4" />}
                          </div>
                          <div>
                            <p className="font-medium text-slate-200 truncate max-w-xs">{doc.original_name}</p>
                            <p className="text-[10px] text-slate-400 font-mono">{doc.id.slice(0, 8)}...</p>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <Badge label={doc.category} variant="sky" />
                      </td>

                      <td className="py-3.5 px-4">
                        {doc.ocr_applied ? (
                          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <Scan className="w-3 h-3" /> OCR Applied
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                            Digital Native
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 font-mono text-slate-400">
                        {sizeKB} KB
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center gap-1 font-mono font-medium text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                          {doc.chunk_count}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>

                      <td className="py-3.5 px-4 text-right space-x-2">
                        <button
                          onClick={() => handleInspectChunks(doc.id)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors cursor-pointer"
                          title="Inspect chunks"
                        >
                          <Eye className="w-3.5 h-3.5 inline mr-1" />
                          Chunks
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.original_name)}
                          disabled={isDeleting === doc.id}
                          className="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 transition-colors cursor-pointer"
                          title="Delete document"
                        >
                          <Trash2 className="w-3.5 h-3.5 inline" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    {searchQuery ? 'No documents matched your search.' : 'No documents indexed yet. Upload your first document to begin.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Chunks Inspector Drawer / Modal */}
      {selectedDocDetail && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl max-h-[85vh] bg-slate-900 border border-slate-800 rounded-2xl flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-base text-white flex items-center gap-2">
                  <Eye className="w-4 h-4 text-sky-400" />
                  <span>Chunk Inspector: {selectedDocDetail.original_name}</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Total {selectedDocDetail.chunks.length} chunks indexed with 384-dimensional dense vectors and BM25 tokens.
                </p>
              </div>
              <button
                onClick={() => setSelectedDocDetail(null)}
                className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chunks Scrollable Content */}
            <div className="flex-1 p-5 overflow-y-auto space-y-4">
              {selectedDocDetail.chunks.map((chunk, idx) => (
                <div
                  key={chunk.id}
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-slate-400 border-b border-slate-800/80 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-sky-400">Chunk #{chunk.chunk_index + 1}</span>
                      <span className="text-slate-400">• Page {chunk.page_number}</span>
                      {chunk.metadata_json?.is_ocr && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">OCR</span>
                      )}
                    </div>
                    <div className="font-mono text-slate-400">
                      Tokens: <strong className="text-slate-200">{chunk.token_count}</strong> | Offset: {chunk.char_start}..{chunk.char_end}
                    </div>
                  </div>

                  <div className="text-slate-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap bg-slate-900/80 p-3 rounded-lg border border-slate-800/60">
                    {chunk.content}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-right">
              <button
                onClick={() => setSelectedDocDetail(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
