import { useState, useEffect } from 'react'
import { MessagesSquare, User, Bot, Calendar, FileText, Terminal, Search } from 'lucide-react'
import { cn } from '../../lib/utils'
import { MarkdownRenderer } from './MarkdownRenderer'

interface ChatLogViewerProps {
  chatlogId: number
  className?: string
}

interface ChatTurn {
  id: number
  turn_index: number
  role: 'user' | 'assistant'
  content: string
  word_count: number
  has_code_blocks: boolean
  has_file_refs: boolean
  has_commands: boolean
}

interface ChatLogData {
  id: number
  filename: string
  title: string | null
  file_path: string
  turn_count: number
  word_count: number
  modified_date: string | null
  projects_referenced: string | null
  turns: ChatTurn[]
  file_refs: { file_path: string; project_name: string | null }[]
  commands: { command: string; was_accepted: boolean }[]
}

export function ChatLogViewer({ chatlogId, className }: ChatLogViewerProps) {
  const [data, setData] = useState<ChatLogData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'conversation' | 'files' | 'commands'>('conversation')

  useEffect(() => {
    const fetchChatLog = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/chatlogs/${chatlogId}`)
        if (!res.ok) throw new Error('Failed to fetch chat log')
        const json = await res.json()
        setData(json)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    if (chatlogId) fetchChatLog()
  }, [chatlogId])

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="text-zinc-400">Loading chat log...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="text-red-400">Error: {error || 'No data'}</div>
      </div>
    )
  }

  const filteredTurns = searchQuery
    ? data.turns.filter(t => t.content.toLowerCase().includes(searchQuery.toLowerCase()))
    : data.turns

  const projects = data.projects_referenced ? JSON.parse(data.projects_referenced) : []

  return (
    <div className={cn('flex flex-col h-full bg-zinc-900', className)}>
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2 mb-2">
          <MessagesSquare size={20} className="text-indigo-400" />
          <h2 className="text-lg font-semibold text-white truncate">{data.title || data.filename}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-zinc-400">
          <div className="flex items-center gap-1">
            <Calendar size={14} />
            {data.modified_date?.split('T')[0] || 'Unknown'}
          </div>
          <div>{data.turn_count} turns</div>
          <div>{data.word_count.toLocaleString()} words</div>
          {projects.length > 0 && (
            <div className="flex items-center gap-1">
              {projects.map((p: string) => (
                <span key={p} className="px-1.5 py-0.5 bg-indigo-900/30 text-indigo-300 text-xs rounded">
                  {p}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 flex border-b border-zinc-800">
        {[
          { id: 'conversation', label: 'Conversation', icon: MessagesSquare, count: data.turns.length },
          { id: 'files', label: 'Files', icon: FileText, count: data.file_refs.length },
          { id: 'commands', label: 'Commands', icon: Terminal, count: data.commands.length },
        ].map(({ id, label, icon: Icon, count }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as typeof activeTab)}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === id
                ? 'text-indigo-400 border-b-2 border-indigo-400 bg-zinc-800/50'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800/30'
            )}
          >
            <Icon size={16} />
            {label}
            <span className="text-xs text-zinc-500">({count})</span>
          </button>
        ))}
      </div>

      {/* Search (for conversation tab) */}
      {activeTab === 'conversation' && (
        <div className="flex-shrink-0 p-2 border-b border-zinc-800">
          <div className="relative">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="Search in conversation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-7 pr-2 py-1.5 text-sm bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'conversation' && (
          <div className="p-4 space-y-4">
            {filteredTurns.map((turn) => (
              <div
                key={turn.id}
                className={cn(
                  'flex gap-3',
                  turn.role === 'user' ? 'flex-row-reverse' : ''
                )}
              >
                <div className={cn(
                  'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
                  turn.role === 'user' ? 'bg-blue-600' : 'bg-zinc-700'
                )}>
                  {turn.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className={cn(
                  'flex-1 max-w-[85%] rounded-lg p-3',
                  turn.role === 'user' 
                    ? 'bg-blue-600/20 border border-blue-600/30' 
                    : 'bg-zinc-800 border border-zinc-700'
                )}>
                  <div className="text-xs text-zinc-500 mb-1">
                    {turn.role === 'user' ? 'You' : 'Assistant'} · Turn {turn.turn_index + 1}
                  </div>
                  <div className="text-sm text-zinc-200 prose prose-invert prose-sm max-w-none">
                    <MarkdownRenderer content={turn.content} />
                  </div>
                </div>
              </div>
            ))}
            {filteredTurns.length === 0 && (
              <div className="text-center text-zinc-500 py-8">
                {searchQuery ? 'No matching turns found' : 'No conversation turns'}
              </div>
            )}
          </div>
        )}

        {activeTab === 'files' && (
          <div className="p-4 space-y-2">
            {data.file_refs.length > 0 ? (
              data.file_refs.map((ref, i) => (
                <div key={i} className="flex items-center gap-2 text-sm p-2 bg-zinc-800/50 rounded">
                  <FileText size={14} className="text-zinc-500" />
                  <code className="text-zinc-300 text-xs truncate flex-1">{ref.file_path}</code>
                  {ref.project_name && (
                    <span className="px-1.5 py-0.5 bg-indigo-900/30 text-indigo-300 text-xs rounded">
                      {ref.project_name}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-zinc-500 py-8">No file references found</div>
            )}
          </div>
        )}

        {activeTab === 'commands' && (
          <div className="p-4 space-y-2">
            {data.commands.length > 0 ? (
              data.commands.map((cmd, i) => (
                <div key={i} className="flex items-center gap-2 text-sm p-2 bg-zinc-800/50 rounded">
                  <Terminal size={14} className={cmd.was_accepted ? 'text-green-400' : 'text-red-400'} />
                  <code className="text-zinc-300 text-xs truncate flex-1">{cmd.command}</code>
                  <span className={cn(
                    'px-1.5 py-0.5 text-xs rounded',
                    cmd.was_accepted ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'
                  )}>
                    {cmd.was_accepted ? 'Accepted' : 'Rejected'}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center text-zinc-500 py-8">No commands found</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
