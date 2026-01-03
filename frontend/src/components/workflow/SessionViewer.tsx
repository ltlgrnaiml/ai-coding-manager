import { useState, useEffect } from 'react'
import { ScrollText, Calendar, Hash, CheckSquare, Lightbulb, ArrowRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import { MarkdownRenderer } from './MarkdownRenderer'

interface SessionViewerProps {
  artifactId: string
  filePath: string
  className?: string
}

interface SessionMetadata {
  sessionId: string
  title: string
  date: string | null
  topics: string[]
  decisions: string[]
  nextSteps: string[]
}

export function SessionViewer({ artifactId, filePath, className }: SessionViewerProps) {
  const [content, setContent] = useState<string>('')
  const [metadata, setMetadata] = useState<SessionMetadata | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'full'>('overview')

  useEffect(() => {
    const fetchSession = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/devtools/artifacts/${artifactId}`)
        if (!res.ok) throw new Error('Failed to fetch session')
        const data = await res.json()
        const rawContent = typeof data.content === 'string' ? data.content : JSON.stringify(data.content, null, 2)
        setContent(rawContent)
        
        // Extract metadata from session content
        const meta = extractSessionMetadata(rawContent, artifactId)
        setMetadata(meta)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    if (artifactId) fetchSession()
  }, [artifactId])

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="text-zinc-400">Loading session...</div>
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

  return (
    <div className={cn('flex flex-col h-full bg-zinc-900', className)}>
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2 mb-2">
          <ScrollText size={20} className="text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">{metadata?.title || artifactId}</h2>
        </div>
        <div className="flex items-center gap-4 text-sm text-zinc-400">
          <div className="flex items-center gap-1">
            <Hash size={14} />
            {metadata?.sessionId || artifactId}
          </div>
          {metadata?.date && (
            <div className="flex items-center gap-1">
              <Calendar size={14} />
              {metadata.date}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 flex border-b border-zinc-800">
        {[
          { id: 'overview', label: 'Overview', icon: Lightbulb },
          { id: 'full', label: 'Full Content', icon: ScrollText }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as 'overview' | 'full')}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === id
                ? 'text-cyan-400 border-b-2 border-cyan-400 bg-zinc-800/50'
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
        {activeTab === 'overview' && metadata && (
          <div className="p-4 space-y-6">
            {/* Topics */}
            {metadata.topics.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2">Topics Discussed</h3>
                <div className="flex flex-wrap gap-2">
                  {metadata.topics.map((topic, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-cyan-900/30 text-cyan-300 text-xs rounded-md"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Decisions */}
            {metadata.decisions.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <CheckSquare size={16} />
                  Decisions Made
                </h3>
                <ul className="space-y-1">
                  {metadata.decisions.map((decision, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-green-400 mt-1">✓</span>
                      {decision}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next Steps */}
            {metadata.nextSteps.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <ArrowRight size={16} />
                  Next Steps
                </h3>
                <ul className="space-y-1">
                  {metadata.nextSteps.map((step, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-blue-400 mt-1">→</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Fallback if no metadata extracted */}
            {metadata.topics.length === 0 && metadata.decisions.length === 0 && metadata.nextSteps.length === 0 && (
              <div className="text-zinc-500 text-sm">
                No structured metadata found. View full content for details.
              </div>
            )}
          </div>
        )}

        {activeTab === 'full' && (
          <div className="p-4">
            <MarkdownRenderer content={content} />
          </div>
        )}
      </div>
    </div>
  )
}

function extractSessionMetadata(content: string, artifactId: string): SessionMetadata {
  // Extract session ID from artifact ID (SESSION_001 -> SESSION_001)
  const sessionId = artifactId

  // Extract title from first heading
  const titleMatch = content.match(/^#\s+(.+)$/m)
  const title = titleMatch ? titleMatch[1].replace(/^SESSION_\d+:\s*/, '') : artifactId

  // Extract date from content
  const dateMatch = content.match(/(\d{4}-\d{2}-\d{2})/)
  const date = dateMatch ? dateMatch[1] : null

  // Extract topics from "Topics Discussed" section or bullet points
  const topics: string[] = []
  const topicsMatch = content.match(/(?:topics discussed|topics):?\s*\n((?:[-*]\s*.+\n?)+)/i)
  if (topicsMatch) {
    const topicLines = topicsMatch[1].match(/[-*]\s*(.+)/g)
    if (topicLines) {
      topics.push(...topicLines.map(l => l.replace(/^[-*]\s*/, '').trim()).slice(0, 10))
    }
  }

  // Extract decisions from "Decisions" section
  const decisions: string[] = []
  const decisionsMatch = content.match(/(?:decisions made|decisions|key decisions):?\s*\n((?:[-*]\s*.+\n?)+)/i)
  if (decisionsMatch) {
    const decisionLines = decisionsMatch[1].match(/[-*]\s*(.+)/g)
    if (decisionLines) {
      decisions.push(...decisionLines.map(l => l.replace(/^[-*]\s*/, '').trim()).slice(0, 10))
    }
  }

  // Extract next steps from "Next Steps" section
  const nextSteps: string[] = []
  const nextMatch = content.match(/(?:next steps|remaining work|todo):?\s*\n((?:[-*]\s*.+\n?)+)/i)
  if (nextMatch) {
    const nextLines = nextMatch[1].match(/[-*]\s*(.+)/g)
    if (nextLines) {
      nextSteps.push(...nextLines.map(l => l.replace(/^[-*]\s*/, '').trim()).slice(0, 10))
    }
  }

  return { sessionId, title, date, topics, decisions, nextSteps }
}
