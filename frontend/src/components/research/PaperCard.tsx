import { useState } from 'react';
import { FileText, Copy, ExternalLink, ChevronDown, ChevronUp, Check } from 'lucide-react';
import { Paper } from '../../hooks/useResearch';

interface PaperCardProps {
  paper: Paper;
  onCopyBibtex: (paperId: string) => Promise<boolean>;
  onInsertReference?: (paper: Paper) => void;
  onViewDetails?: (paper: Paper) => void;
  compact?: boolean;
}

export function PaperCard({ 
  paper, 
  onCopyBibtex, 
  onInsertReference,
  onViewDetails,
  compact = false 
}: PaperCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyBibtex = async () => {
    const success = await onCopyBibtex(paper.paper_id);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const similarityPercent = paper.similarity 
    ? Math.round(paper.similarity * 100) 
    : null;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 hover:border-cyan-500/50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-cyan-500/10 rounded-lg shrink-0">
          <FileText className="w-4 h-4 text-cyan-400" />
        </div>
        
        <div className="flex-1 min-w-0">
          <h4 
            className="font-medium text-white text-sm leading-tight cursor-pointer hover:text-cyan-400 transition-colors line-clamp-2"
            onClick={() => onViewDetails?.(paper)}
          >
            {paper.title || 'Untitled Paper'}
          </h4>
          
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
            {paper.arxiv_id && (
              <span className="bg-slate-700 px-1.5 py-0.5 rounded">
                arXiv:{paper.arxiv_id}
              </span>
            )}
            {similarityPercent !== null && (
              <span className="text-cyan-400">
                {similarityPercent}% match
              </span>
            )}
          </div>

          {!compact && (
            <>
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1 mt-2 text-xs text-slate-400 hover:text-white transition-colors"
              >
                {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {expanded ? 'Less' : 'More'}
              </button>

              {expanded && paper.abstract && (
                <p className="mt-2 text-xs text-slate-300 leading-relaxed line-clamp-4">
                  {paper.abstract}
                </p>
              )}
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 mt-3 pt-2 border-t border-slate-700/50">
        <button
          onClick={handleCopyBibtex}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded transition-colors"
          title="Copy BibTeX"
        >
          {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Copied!' : 'Cite'}
        </button>
        
        {onInsertReference && (
          <button
            onClick={() => onInsertReference(paper)}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded transition-colors"
            title="Insert reference"
          >
            <ExternalLink className="w-3 h-3" />
            Insert
          </button>
        )}
        
        {onViewDetails && (
          <button
            onClick={() => onViewDetails(paper)}
            className="px-2 py-1 text-xs bg-cyan-600 hover:bg-cyan-500 rounded transition-colors ml-auto"
          >
            View
          </button>
        )}
      </div>
    </div>
  );
}
