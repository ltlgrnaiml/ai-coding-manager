import { useState, useEffect, useRef } from 'react';
import { FileText, Tag, User, Search } from 'lucide-react';
import { useResearch, AutocompleteResult } from '../../hooks/useResearch';

interface AutocompletePopupProps {
  query: string;
  position: { top: number; left: number };
  onSelect: (result: AutocompleteResult) => void;
  onClose: () => void;
  filterType?: 'paper' | 'concept' | 'author';
}

export function AutocompletePopup({
  query,
  position,
  onSelect,
  onClose,
  filterType
}: AutocompletePopupProps) {
  const { autocomplete } = useResearch();
  const [results, setResults] = useState<AutocompleteResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    const timeoutId = setTimeout(async () => {
      const data = await autocomplete(query, filterType);
      setResults(data);
      setSelectedIndex(0);
      setLoading(false);
    }, 150); // Debounce

    return () => clearTimeout(timeoutId);
  }, [query, filterType, autocomplete]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(i => Math.min(i + 1, results.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(i => Math.max(i - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (results[selectedIndex]) {
            onSelect(results[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [results, selectedIndex, onSelect, onClose]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'paper': return <FileText className="w-4 h-4 text-cyan-400" />;
      case 'concept': return <Tag className="w-4 h-4 text-green-400" />;
      case 'author': return <User className="w-4 h-4 text-purple-400" />;
      default: return <Search className="w-4 h-4 text-slate-400" />;
    }
  };

  if (results.length === 0 && !loading) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className="fixed bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 w-80 max-h-64 overflow-hidden"
      style={{ top: position.top, left: position.left }}
    >
      {loading ? (
        <div className="p-3 text-sm text-slate-400 text-center">
          Searching...
        </div>
      ) : (
        <ul className="overflow-y-auto max-h-64">
          {results.map((result, index) => (
            <li
              key={`${result.type}-${result.value}`}
              className={`flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors ${
                index === selectedIndex 
                  ? 'bg-cyan-500/20 text-white' 
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
              onClick={() => onSelect(result)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              {getIcon(result.type)}
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate">{result.display}</div>
                {result.metadata?.frequency && (
                  <div className="text-xs text-slate-500">
                    {String(result.metadata.frequency)} occurrences
                  </div>
                )}
              </div>
              <span className="text-xs text-slate-500 uppercase">{result.type}</span>
            </li>
          ))}
        </ul>
      )}
      
      <div className="px-3 py-1.5 border-t border-slate-700 text-xs text-slate-500 flex items-center justify-between">
        <span>↑↓ Navigate</span>
        <span>↵ Select</span>
        <span>Esc Close</span>
      </div>
    </div>
  );
}

export function useAutocomplete() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [filterType, setFilterType] = useState<'paper' | 'concept' | 'author' | undefined>();

  const openAutocomplete = (
    searchQuery: string,
    pos: { top: number; left: number },
    type?: 'paper' | 'concept' | 'author'
  ) => {
    setQuery(searchQuery);
    setPosition(pos);
    setFilterType(type);
    setIsOpen(true);
  };

  const closeAutocomplete = () => {
    setIsOpen(false);
    setQuery('');
  };

  return {
    isOpen,
    query,
    position,
    filterType,
    openAutocomplete,
    closeAutocomplete
  };
}
