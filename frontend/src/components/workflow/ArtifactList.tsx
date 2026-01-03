import { Search, Loader2 } from 'lucide-react'
import { useRef, useEffect, useCallback } from 'react'
import { cn } from '../../lib/utils'
import { useArtifacts, useChatLogs } from '../../hooks/useWorkflowApi'
import type { ArtifactType, ArtifactSummary } from './types'

interface ArtifactListProps {
  type: ArtifactType
  searchQuery: string
  onSearchChange: (query: string) => void
  onSelect: (artifact: ArtifactSummary) => void
  selectedId?: string
  onNavigateList?: (direction: 'left' | 'right') => void
}

export function ArtifactList({
  type,
  searchQuery,
  onSearchChange,
  onSelect,
  selectedId,
  onNavigateList,
}: ArtifactListProps) {
  // Use different hooks for chatlogs vs other artifacts
  const isChatLog = type === 'chatlog'
  const { data: artifacts, loading: artifactsLoading, error: artifactsError } = useArtifacts(
    isChatLog ? undefined : type, 
    isChatLog ? undefined : searchQuery
  )
  const { data: chatLogs, loading: chatLogsLoading, error: chatLogsError } = useChatLogs(
    isChatLog ? searchQuery : undefined
  )
  
  // Normalize data for display
  const items = isChatLog 
    ? chatLogs?.map(cl => ({ 
        id: String(cl.id), 
        title: cl.title || cl.filename,
        type: 'chatlog' as ArtifactType,
        status: 'active',
        file_path: cl.filename,
        turn_count: cl.turn_count,
        word_count: cl.word_count,
      })) || []
    : artifacts || []
  
  const loading = isChatLog ? chatLogsLoading : artifactsLoading
  const error = isChatLog ? chatLogsError : artifactsError
  
  const listRef = useRef<HTMLDivElement>(null)
  const selectedIndex = items.findIndex(a => a.id === selectedId)

  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!items.length) return
    
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      const nextIndex = selectedIndex < items.length - 1 ? selectedIndex + 1 : 0
      onSelect(items[nextIndex] as ArtifactSummary)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const prevIndex = selectedIndex > 0 ? selectedIndex - 1 : items.length - 1
      onSelect(items[prevIndex] as ArtifactSummary)
    } else if (e.key === 'ArrowLeft' && onNavigateList) {
      e.preventDefault()
      onNavigateList('left')
    } else if (e.key === 'ArrowRight' && onNavigateList) {
      e.preventDefault()
      onNavigateList('right')
    }
  }, [items, selectedIndex, onSelect, onNavigateList])

  useEffect(() => {
    const listEl = listRef.current
    if (listEl) {
      listEl.addEventListener('keydown', handleKeyDown)
      return () => listEl.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  // Scroll selected item into view
  useEffect(() => {
    if (selectedId && listRef.current) {
      const selectedEl = listRef.current.querySelector(`[data-id="${selectedId}"]`)
      selectedEl?.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedId])

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Search input */}
      <div className="p-2 border-b border-zinc-800">
        <div className="relative">
          <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-7 pr-2 py-1 text-sm bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* List */}
      <div 
        ref={listRef}
        tabIndex={0}
        className="flex-1 overflow-y-auto focus:outline-none"
      >
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="animate-spin text-zinc-500" />
          </div>
        )}
        
        {error && (
          <div className="p-4 text-red-400 text-sm">{error.message}</div>
        )}
        
        {!loading && !error && items.map((item) => (
          <button
            key={item.id}
            data-id={item.id}
            onClick={() => onSelect(item as ArtifactSummary)}
            className={cn(
              'w-full text-left px-3 py-2 text-sm hover:bg-zinc-800 border-b border-zinc-800/50',
              selectedId === item.id && 'bg-zinc-800 ring-1 ring-blue-500/50'
            )}
          >
            <div className="font-medium truncate">{item.id}</div>
            <div className="text-xs text-zinc-500 truncate">{item.title}</div>
            {isChatLog && 'turn_count' in item && (
              <div className="text-xs text-zinc-600 mt-0.5">
                {item.turn_count} turns · {item.word_count?.toLocaleString()} words
              </div>
            )}
          </button>
        ))}
        
        {!loading && !error && items.length === 0 && (
          <div className="p-4 text-zinc-500 text-sm text-center">No artifacts found</div>
        )}
      </div>
    </div>
  )
}
