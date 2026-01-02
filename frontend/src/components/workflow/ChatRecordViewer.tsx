import { useState, useEffect } from 'react'
import { Copy, MessageSquare, Clock, Users, Lightbulb, CheckSquare, FileText } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ChatMessage {
  role: string
  content: string
  timestamp?: string
}

interface ChatSession {
  session_id: string
  title: string
  date: string
  messages: ChatMessage[]
  total_messages: number
  user_messages: number
  assistant_messages: number
}

interface ConversationInsights {
  topics_discussed: string[]
  key_insights: string[]
  action_items: string[]
  decisions_made: string[]
  technical_concepts: string[]
  summary: string
}

interface DiscLogEntry {
  date: string
  session_id: string | null
  topics_discussed: string[]
  key_insights: string[]
  action_items: string[]
}

interface CopyableSnippets {
  summary?: string
  requirements?: string
  technical_concepts?: string
  action_items?: string
  decisions?: string
  conversation_excerpt?: string
}

interface ChatRecordData {
  chat_session: ChatSession
  conversation_insights: ConversationInsights
  disc_log_entry: DiscLogEntry
  copyable_snippets: CopyableSnippets
}

interface ChatRecordViewerProps {
  artifactId: string
  className?: string
}

export function ChatRecordViewer({ artifactId, className }: ChatRecordViewerProps) {
  const [data, setData] = useState<ChatRecordData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'conversation' | 'snippets' | 'disc'>('overview')
  const [copiedSnippet, setCopiedSnippet] = useState<string | null>(null)

  useEffect(() => {
    const fetchChatData = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/devtools/artifacts/${artifactId}/chat-analysis`)
        if (!res.ok) throw new Error('Failed to fetch chat analysis')
        const chatData = await res.json()
        setData(chatData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    if (artifactId) fetchChatData()
  }, [artifactId])

  const handleCopySnippet = async (snippetType: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedSnippet(snippetType)
      setTimeout(() => setCopiedSnippet(null), 2000)
    } catch (err) {
      console.error('Failed to copy snippet:', err)
    }
  }

  const handleCopyDiscEntry = async () => {
    if (!data?.disc_log_entry) return
    
    const entry = data.disc_log_entry
    const discFormat = `{
  "date": "${entry.date}",
  "session_id": ${entry.session_id ? `"${entry.session_id}"` : 'null'},
  "topics_discussed": ${JSON.stringify(entry.topics_discussed, null, 2)},
  "key_insights": ${JSON.stringify(entry.key_insights, null, 2)},
  "action_items": ${JSON.stringify(entry.action_items, null, 2)}
}`
    
    await handleCopySnippet('disc_entry', discFormat)
  }

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="text-zinc-400">Loading chat analysis...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="text-red-400">Error: {error}</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="text-zinc-400">No chat data available</div>
      </div>
    )
  }

  const { chat_session, conversation_insights, copyable_snippets } = data

  return (
    <div className={cn('flex flex-col h-full bg-zinc-900', className)}>
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2 mb-2">
          <MessageSquare size={20} className="text-blue-400" />
          <h2 className="text-lg font-semibold text-white">{chat_session.title}</h2>
        </div>
        <div className="flex items-center gap-4 text-sm text-zinc-400">
          <div className="flex items-center gap-1">
            <Clock size={14} />
            {chat_session.date}
          </div>
          <div className="flex items-center gap-1">
            <Users size={14} />
            {chat_session.total_messages} messages
          </div>
          <div className="text-zinc-500">
            {chat_session.user_messages} user • {chat_session.assistant_messages} assistant
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 flex border-b border-zinc-800">
        {[
          { id: 'overview', label: 'Overview', icon: Lightbulb },
          { id: 'conversation', label: 'Messages', icon: MessageSquare },
          { id: 'snippets', label: 'Copy Snippets', icon: Copy },
          { id: 'disc', label: 'DISC Entry', icon: FileText }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as any)}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === id
                ? 'text-blue-400 border-b-2 border-blue-400 bg-zinc-800/50'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800/30'
            )}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'overview' && (
          <div className="p-4 space-y-6">
            {/* Summary */}
            {conversation_insights.summary && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2">Summary</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  {conversation_insights.summary}
                </p>
              </div>
            )}

            {/* Topics */}
            {conversation_insights.topics_discussed.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2">Topics Discussed</h3>
                <div className="flex flex-wrap gap-2">
                  {conversation_insights.topics_discussed.map((topic, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-blue-900/30 text-blue-300 text-xs rounded-md"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Key Insights */}
            {conversation_insights.key_insights.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <Lightbulb size={16} />
                  Key Insights
                </h3>
                <ul className="space-y-1">
                  {conversation_insights.key_insights.map((insight, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-yellow-400 mt-1">•</span>
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Items */}
            {conversation_insights.action_items.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <CheckSquare size={16} />
                  Action Items
                </h3>
                <ul className="space-y-1">
                  {conversation_insights.action_items.map((item, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-green-400 mt-1">□</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Decisions */}
            {conversation_insights.decisions_made.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2">Decisions Made</h3>
                <ul className="space-y-1">
                  {conversation_insights.decisions_made.map((decision, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-purple-400 mt-1">→</span>
                      {decision}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'conversation' && (
          <div className="p-4 space-y-4">
            {chat_session.messages.map((message, i) => (
              <div
                key={i}
                className={cn(
                  'p-3 rounded-lg',
                  message.role === 'user'
                    ? 'bg-blue-900/20 border-l-2 border-blue-400'
                    : 'bg-zinc-800/50 border-l-2 border-zinc-600'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={cn(
                    'text-xs font-medium px-2 py-1 rounded',
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-zinc-600 text-zinc-200'
                  )}>
                    {message.role === 'user' ? 'User' : 'Assistant'}
                  </span>
                  {message.timestamp && (
                    <span className="text-xs text-zinc-500">{message.timestamp}</span>
                  )}
                </div>
                <div className="text-sm text-zinc-300 whitespace-pre-wrap">
                  {message.content}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'snippets' && (
          <div className="p-4 space-y-4">
            {Object.entries(copyable_snippets).map(([type, content]) => (
              <div key={type} className="border border-zinc-700 rounded-lg">
                <div className="flex items-center justify-between p-3 border-b border-zinc-700">
                  <h3 className="text-sm font-medium text-zinc-300 capitalize">
                    {type.replace('_', ' ')}
                  </h3>
                  <button
                    onClick={() => handleCopySnippet(type, content)}
                    className={cn(
                      'flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors',
                      copiedSnippet === type
                        ? 'bg-green-600 text-white'
                        : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
                    )}
                  >
                    <Copy size={12} />
                    {copiedSnippet === type ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="p-3">
                  <pre className="text-xs text-zinc-400 whitespace-pre-wrap font-mono">
                    {content}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'disc' && (
          <div className="p-4">
            <div className="border border-zinc-700 rounded-lg">
              <div className="flex items-center justify-between p-3 border-b border-zinc-700">
                <h3 className="text-sm font-medium text-zinc-300">
                  DISC Conversation Log Entry
                </h3>
                <button
                  onClick={handleCopyDiscEntry}
                  className={cn(
                    'flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors',
                    copiedSnippet === 'disc_entry'
                      ? 'bg-green-600 text-white'
                      : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
                  )}
                >
                  <Copy size={12} />
                  {copiedSnippet === 'disc_entry' ? 'Copied!' : 'Copy JSON'}
                </button>
              </div>
              <div className="p-3">
                <div className="text-xs text-zinc-400 space-y-2">
                  <div><strong>Date:</strong> {data.disc_log_entry.date}</div>
                  <div><strong>Session ID:</strong> {data.disc_log_entry.session_id || 'None'}</div>
                  <div>
                    <strong>Topics:</strong>
                    <ul className="mt-1 ml-4">
                      {data.disc_log_entry.topics_discussed.map((topic, i) => (
                        <li key={i}>• {topic}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <strong>Key Insights:</strong>
                    <ul className="mt-1 ml-4">
                      {data.disc_log_entry.key_insights.map((insight, i) => (
                        <li key={i}>• {insight}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <strong>Action Items:</strong>
                    <ul className="mt-1 ml-4">
                      {data.disc_log_entry.action_items.map((item, i) => (
                        <li key={i}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
