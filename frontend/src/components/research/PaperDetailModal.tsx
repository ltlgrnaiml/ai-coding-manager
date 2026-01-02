import { useState, useEffect } from 'react';
import { X, Copy, Download, ExternalLink, Check, FileText, Tag, Link2 } from 'lucide-react';
import { Paper, useResearch } from '../../hooks/useResearch';

interface PaperDetailModalProps {
  paper: Paper;
  onClose: () => void;
  onInsertReference?: (paper: Paper) => void;
}

export function PaperDetailModal({ paper, onClose, onInsertReference }: PaperDetailModalProps) {
  const { getBibtex } = useResearch();
  const [bibtex, setBibtex] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'abstract' | 'bibtex' | 'related'>('abstract');

  useEffect(() => {
    getBibtex(paper.paper_id).then(result => {
      if (result) setBibtex(result.bibtex);
    });
  }, [paper.paper_id, getBibtex]);

  const handleCopy = async () => {
    if (bibtex) {
      await navigator.clipboard.writeText(bibtex);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-slate-700">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg">
              <FileText className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white leading-tight">
                {paper.title || 'Untitled Paper'}
              </h2>
              <div className="flex items-center gap-2 mt-1 text-sm text-slate-400">
                {paper.arxiv_id && (
                  <a 
                    href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 hover:text-cyan-400 transition-colors"
                  >
                    arXiv:{paper.arxiv_id}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                {paper.authors && (
                  <span className="truncate max-w-xs">{paper.authors}</span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-700 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-700">
          {(['abstract', 'bibtex', 'related'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'abstract' && (
            <div className="space-y-4">
              {paper.abstract ? (
                <p className="text-slate-300 leading-relaxed">{paper.abstract}</p>
              ) : (
                <p className="text-slate-500 italic">No abstract available</p>
              )}
              
              {paper.similarity && (
                <div className="flex items-center gap-2 p-3 bg-slate-800 rounded-lg">
                  <Tag className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm text-slate-300">
                    Relevance: <span className="text-cyan-400 font-medium">
                      {Math.round(paper.similarity * 100)}%
                    </span>
                  </span>
                </div>
              )}
            </div>
          )}

          {activeTab === 'bibtex' && (
            <div className="space-y-3">
              {bibtex ? (
                <>
                  <pre className="bg-slate-800 p-3 rounded-lg text-xs text-slate-300 overflow-x-auto font-mono">
                    {bibtex}
                  </pre>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-2 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors text-sm"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied!' : 'Copy BibTeX'}
                  </button>
                </>
              ) : (
                <p className="text-slate-500 italic">Loading BibTeX...</p>
              )}
            </div>
          )}

          {activeTab === 'related' && (
            <div className="space-y-3">
              <p className="text-slate-400 text-sm">
                Related papers based on citation network and semantic similarity.
              </p>
              <div className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-lg text-slate-500">
                <Link2 className="w-4 h-4" />
                <span className="text-sm">Citation graph integration coming soon</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center gap-2 p-4 border-t border-slate-700 bg-slate-800/30">
          {onInsertReference && (
            <button
              onClick={() => {
                onInsertReference(paper);
                onClose();
              }}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Insert Reference
            </button>
          )}
          
          {paper.arxiv_id && (
            <a
              href={`https://arxiv.org/pdf/${paper.arxiv_id}.pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Download PDF
            </a>
          )}
          
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-400 hover:text-white transition-colors ml-auto"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
