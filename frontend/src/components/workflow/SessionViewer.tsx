import { useState, useEffect, useRef } from 'react'
import { ScrollText, Calendar, Hash, Target, FileText, ArrowRight, List, ChevronRight } from 'lucide-react'
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
  status: string | null
  objective: string | null
  sections: { level: number; title: string; line: number }[]
  workCompleted: string[]
  filesModified: { file: string; action: string }[]
  nextSteps: string[]
}

export function SessionViewer({ artifactId, filePath, className }: SessionViewerProps) {
  const [content, setContent] = useState<string>('')
  const [metadata, setMetadata] = useState<SessionMetadata | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'outline' | 'full'>('overview')
  const contentRef = useRef<HTMLDivElement>(null)

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

  const scrollToSection = (sectionTitle: string) => {
    setActiveTab('full')
    setTimeout(() => {
      const headings = contentRef.current?.querySelectorAll('h1, h2, h3, h4')
      headings?.forEach(h => {
        if (h.textContent?.includes(sectionTitle)) {
          h.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      })
    }, 100)
  }

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

  const hasOverviewContent = metadata && (
    metadata.objective || 
    metadata.workCompleted.length > 0 || 
    metadata.filesModified.length > 0 || 
    metadata.nextSteps.length > 0
  )

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
          {metadata?.status && (
            <span className="px-2 py-0.5 bg-green-900/30 text-green-300 text-xs rounded">
              {metadata.status}
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 flex border-b border-zinc-800">
        {[
          { id: 'overview', label: 'Overview', icon: Target },
          { id: 'outline', label: 'Outline', icon: List },
          { id: 'full', label: 'Full Content', icon: ScrollText }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as 'overview' | 'outline' | 'full')}
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
            {/* Objective */}
            {metadata.objective && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <Target size={16} className="text-cyan-400" />
                  Objective
                </h3>
                <p className="text-zinc-400 text-sm bg-zinc-800/50 p-3 rounded-lg border border-zinc-700">
                  {metadata.objective}
                </p>
              </div>
            )}

            {/* Work Completed */}
            {metadata.workCompleted.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <FileText size={16} className="text-green-400" />
                  Work Completed
                </h3>
                <ul className="space-y-1">
                  {metadata.workCompleted.map((item, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-green-400 mt-1">✓</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Files Modified */}
            {metadata.filesModified.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <FileText size={16} className="text-blue-400" />
                  Files Modified ({metadata.filesModified.length})
                </h3>
                <div className="space-y-1 max-h-40 overflow-auto">
                  {metadata.filesModified.slice(0, 10).map((item, i) => (
                    <div key={i} className="text-xs flex items-center gap-2 text-zinc-400">
                      <span className={cn(
                        'px-1.5 py-0.5 rounded text-xs',
                        item.action === 'Created' ? 'bg-green-900/30 text-green-300' :
                        item.action === 'Modified' ? 'bg-yellow-900/30 text-yellow-300' :
                        'bg-zinc-700 text-zinc-300'
                      )}>
                        {item.action}
                      </span>
                      <code className="text-zinc-300">{item.file}</code>
                    </div>
                  ))}
                  {metadata.filesModified.length > 10 && (
                    <div className="text-xs text-zinc-500">
                      +{metadata.filesModified.length - 10} more files...
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Next Steps */}
            {metadata.nextSteps.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <ArrowRight size={16} className="text-purple-400" />
                  Next Steps
                </h3>
                <ul className="space-y-1">
                  {metadata.nextSteps.map((step, i) => (
                    <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
                      <span className="text-purple-400 mt-1">→</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Fallback */}
            {!hasOverviewContent && (
              <div className="text-zinc-500 text-sm">
                No structured metadata extracted. Use the Outline tab for navigation or view Full Content.
              </div>
            )}
          </div>
        )}

        {activeTab === 'outline' && metadata && (
          <div className="p-4">
            <h3 className="text-sm font-medium text-zinc-300 mb-3">Document Structure</h3>
            {metadata.sections.length > 0 ? (
              <nav className="space-y-1">
                {metadata.sections.map((section, i) => (
                  <button
                    key={i}
                    onClick={() => scrollToSection(section.title)}
                    className={cn(
                      'w-full text-left px-2 py-1.5 rounded text-sm hover:bg-zinc-800 transition-colors flex items-center gap-2',
                      section.level === 1 ? 'text-zinc-200 font-medium' :
                      section.level === 2 ? 'text-zinc-300 pl-4' :
                      'text-zinc-400 pl-6'
                    )}
                  >
                    <ChevronRight size={12} className="text-cyan-400" />
                    {section.title}
                  </button>
                ))}
              </nav>
            ) : (
              <div className="text-zinc-500 text-sm">No sections found in document.</div>
            )}
          </div>
        )}

        {activeTab === 'full' && (
          <div className="p-4" ref={contentRef}>
            <MarkdownRenderer content={content} />
          </div>
        )}
      </div>
    </div>
  )
}

function extractSessionMetadata(content: string, artifactId: string): SessionMetadata {
  const sessionId = artifactId

  // Extract title from first heading
  const titleMatch = content.match(/^#\s+(.+)$/m)
  const title = titleMatch ? titleMatch[1].replace(/^SESSION_\d+:\s*/, '') : artifactId

  // Extract date from front matter or content
  const dateMatch = content.match(/\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})/i) || 
                    content.match(/>\s*\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})/i) ||
                    content.match(/(\d{4}-\d{2}-\d{2})/)
  const date = dateMatch ? dateMatch[1] : null

  // Extract status from front matter
  const statusMatch = content.match(/\*\*Status\*\*:\s*(\w+)/i)
  const status = statusMatch ? statusMatch[1] : null

  // Extract objective from "## Objective" section
  let objective: string | null = null
  const objectiveMatch = content.match(/##\s*Objective\s*\n+([\s\S]*?)(?=\n##|\n---|\n\n\n|$)/)
  if (objectiveMatch) {
    objective = objectiveMatch[1].trim().split('\n')[0].replace(/^\d+\.\s*/, '').trim()
    if (objective.length > 200) objective = objective.substring(0, 200) + '...'
  }

  // Extract all headings for outline/tree view
  const sections: { level: number; title: string; line: number }[] = []
  const lines = content.split('\n')
  lines.forEach((line, idx) => {
    const h1 = line.match(/^#\s+(.+)$/)
    const h2 = line.match(/^##\s+(.+)$/)
    const h3 = line.match(/^###\s+(.+)$/)
    if (h1) sections.push({ level: 1, title: h1[1], line: idx })
    else if (h2) sections.push({ level: 2, title: h2[1], line: idx })
    else if (h3) sections.push({ level: 3, title: h3[1], line: idx })
  })

  // Extract work completed from numbered lists under "Work Completed" section
  const workCompleted: string[] = []
  const workMatch = content.match(/##\s*(?:Work Completed|Completed Work)\s*\n+([\s\S]*?)(?=\n##|\n---|\n\n\n|$)/i)
  if (workMatch) {
    const items = workMatch[1].match(/###\s*\d*\.?\s*(.+)/g)
    if (items) {
      workCompleted.push(...items.map(i => i.replace(/^###\s*\d*\.?\s*/, '').trim()).slice(0, 10))
    }
  }

  // Extract files modified from table
  const filesModified: { file: string; action: string }[] = []
  const tableMatch = content.match(/\|\s*File\s*\|\s*Action\s*\|[\s\S]*?\n((?:\|.+\|.+\|.+\|\n?)+)/i)
  if (tableMatch) {
    const rows = tableMatch[1].match(/\|\s*`?([^|`]+)`?\s*\|\s*(\w+)\s*\|/g)
    if (rows) {
      rows.forEach(row => {
        const match = row.match(/\|\s*`?([^|`]+)`?\s*\|\s*(\w+)\s*\|/)
        if (match && !match[1].includes('---')) {
          filesModified.push({ file: match[1].trim(), action: match[2].trim() })
        }
      })
    }
  }

  // Extract next steps
  const nextSteps: string[] = []
  const nextMatch = content.match(/##\s*(?:Next Steps|Remaining Work|TODO|Action Items)\s*\n+([\s\S]*?)(?=\n##|\n---|\n\n\n|$)/i)
  if (nextMatch) {
    const items = nextMatch[1].match(/[-*]\s*\[?\s*[x ]?\]?\s*(.+)/gi)
    if (items) {
      nextSteps.push(...items.map(i => i.replace(/^[-*]\s*\[?\s*[x ]?\]?\s*/, '').trim()).slice(0, 10))
    }
  }

  return { sessionId, title, date, status, objective, sections, workCompleted, filesModified, nextSteps }
}
