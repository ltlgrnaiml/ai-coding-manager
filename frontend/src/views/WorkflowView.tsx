import { useState, useEffect } from 'react'
import {
  FileText,
  GitBranch,
  ClipboardList,
  MessageSquare,
  HelpCircle,
  RefreshCw,
  ChevronRight,
  Clock,
  Search,
} from 'lucide-react'

interface WorkflowStats {
  discussions: number
  adrs: number
  plans: number
  sessions: number
  questions: number
}

interface Artifact {
  id: string
  type: string
  title: string
  status: string
  file_path: string
  updated_at: string | null
}

const typeIcons: Record<string, React.ElementType> = {
  discussion: MessageSquare,
  adr: GitBranch,
  plan: ClipboardList,
  session: Clock,
  question: HelpCircle,
}

const typeColors: Record<string, string> = {
  discussion: 'text-purple-400 bg-purple-500/10',
  adr: 'text-cyan-400 bg-cyan-500/10',
  plan: 'text-green-400 bg-green-500/10',
  session: 'text-yellow-400 bg-yellow-500/10',
  question: 'text-orange-400 bg-orange-500/10',
}

export default function WorkflowView() {
  const [stats, setStats] = useState<WorkflowStats | null>(null)
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [artifactContent, setArtifactContent] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Load stats
  useEffect(() => {
    fetch('/api/workflow/stats')
      .then(res => res.json())
      .then(setStats)
      .catch(console.error)
  }, [])

  // Load artifacts
  useEffect(() => {
    setIsLoading(true)
    const url = selectedType
      ? `/api/workflow/artifacts?artifact_type=${selectedType}`
      : '/api/workflow/artifacts'
    fetch(url)
      .then(res => res.json())
      .then(data => {
        setArtifacts(data)
        setIsLoading(false)
      })
      .catch(err => {
        console.error(err)
        setIsLoading(false)
      })
  }, [selectedType])

  // Load artifact content
  useEffect(() => {
    if (!selectedArtifact) {
      setArtifactContent(null)
      return
    }
    fetch(`/api/workflow/artifact/${selectedArtifact.type}/${selectedArtifact.id}`)
      .then(res => res.json())
      .then(data => {
        if (data.type === 'json') {
          setArtifactContent(JSON.stringify(data.data, null, 2))
        } else {
          setArtifactContent(data.content)
        }
      })
      .catch(console.error)
  }, [selectedArtifact])

  const filteredArtifacts = artifacts.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="flex-1 flex h-full">
      {/* Left Panel - Stats & Filter */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-white">Workflow</h2>
          <p className="text-sm text-gray-400">Manage artifacts</p>
        </div>

        {/* Stats Cards */}
        <div className="p-4 space-y-2">
          {stats && Object.entries(stats).map(([type, count]) => {
            const Icon = typeIcons[type] || FileText
            const colorClass = typeColors[type] || 'text-gray-400 bg-gray-500/10'
            const isSelected = selectedType === type
            return (
              <button
                key={type}
                onClick={() => setSelectedType(isSelected ? null : type)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isSelected
                    ? 'bg-cyan-500/20 text-cyan-400'
                    : 'hover:bg-gray-800 text-gray-300'
                }`}
              >
                <div className={`p-2 rounded-lg ${colorClass}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="flex-1 text-left capitalize">{type}</span>
                <span className="text-sm font-medium">{count}</span>
              </button>
            )
          })}
        </div>

        {/* Refresh */}
        <div className="mt-auto p-4 border-t border-gray-800">
          <button
            onClick={() => {
              fetch('/api/workflow/stats').then(res => res.json()).then(setStats)
              setSelectedType(null)
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </aside>

      {/* Middle Panel - Artifact List */}
      <div className="w-80 border-r border-gray-800 flex flex-col">
        {/* Search */}
        <div className="p-4 border-b border-gray-800">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search artifacts..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading...</div>
          ) : filteredArtifacts.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No artifacts found</div>
          ) : (
            <div className="divide-y divide-gray-800">
              {filteredArtifacts.map(artifact => {
                const Icon = typeIcons[artifact.type] || FileText
                const colorClass = typeColors[artifact.type] || 'text-gray-400'
                const isSelected = selectedArtifact?.id === artifact.id
                return (
                  <button
                    key={artifact.id}
                    onClick={() => setSelectedArtifact(artifact)}
                    className={`w-full p-4 text-left hover:bg-gray-800/50 transition-colors ${
                      isSelected ? 'bg-gray-800' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Icon className={`w-5 h-5 mt-0.5 ${colorClass.split(' ')[0]}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-200 truncate">
                          {artifact.title}
                        </p>
                        <p className="text-xs text-gray-500 truncate">{artifact.id}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs px-2 py-0.5 rounded ${colorClass}`}>
                            {artifact.status}
                          </span>
                          <span className="text-xs text-gray-600">
                            {formatDate(artifact.updated_at)}
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-600" />
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Content Viewer */}
      <div className="flex-1 flex flex-col">
        {selectedArtifact ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-gray-800">
              <div className="flex items-center gap-3">
                {(() => {
                  const Icon = typeIcons[selectedArtifact.type] || FileText
                  const colorClass = typeColors[selectedArtifact.type] || 'text-gray-400 bg-gray-500/10'
                  return (
                    <div className={`p-2 rounded-lg ${colorClass}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                  )
                })()}
                <div>
                  <h2 className="text-lg font-semibold text-white">{selectedArtifact.title}</h2>
                  <p className="text-sm text-gray-400">{selectedArtifact.file_path}</p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-4">
              {artifactContent ? (
                <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap bg-gray-900 rounded-lg p-4">
                  {artifactContent}
                </pre>
              ) : (
                <div className="text-gray-500 text-center">Loading content...</div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <FileText className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p className="text-lg">Select an artifact to view</p>
              <p className="text-sm">Choose from the list on the left</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
