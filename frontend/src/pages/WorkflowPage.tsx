import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CloudRain,
  ChevronRight,
  ChevronDown,
  Plus,
  Check,
  Circle,
  AlertCircle,
  Loader2,
  Copy,
  ExternalLink,
  RefreshCw,
  FileText,
  MessageSquare,
  FileJson,
  Code2,
  ListTodo,
  Sparkles,
  Eye,
  Link2,
  Search,
  FolderOpen,
  Zap,
  ArrowRight,
  CheckCircle2,
  Clock,
  HelpCircle,
} from 'lucide-react'
import { cn } from '../lib/utils'
import { 
  parseDisc, 
  buildArtifactTree, 
  generateArtifactPrompt,
  type ParsedDisc,
  type ArtifactTreeNode,
  type ArtifactReference,
} from '../lib/discParser'

const API_BASE = '/api/devtools'

// Artifact type configuration
const TYPE_CONFIG: Record<string, {
  label: string
  icon: React.ElementType
  color: string
  bgColor: string
  borderColor: string
  description: string
}> = {
  disc: {
    label: 'Discussion',
    icon: MessageSquare,
    color: 'text-purple-400',
    bgColor: 'bg-purple-600/20',
    borderColor: 'border-purple-500',
    description: 'Capture design conversations and requirements',
  },
  adr: {
    label: 'ADR',
    icon: FileJson,
    color: 'text-blue-400',
    bgColor: 'bg-blue-600/20',
    borderColor: 'border-blue-500',
    description: 'Architecture Decision Record',
  },
  spec: {
    label: 'SPEC',
    icon: FileText,
    color: 'text-green-400',
    bgColor: 'bg-green-600/20',
    borderColor: 'border-green-500',
    description: 'Functional specification and API contracts',
  },
  contract: {
    label: 'Contract',
    icon: Code2,
    color: 'text-pink-400',
    bgColor: 'bg-pink-600/20',
    borderColor: 'border-pink-500',
    description: 'Pydantic data schemas',
  },
  plan: {
    label: 'Plan',
    icon: ListTodo,
    color: 'text-amber-400',
    bgColor: 'bg-amber-600/20',
    borderColor: 'border-amber-500',
    description: 'Execution milestones and tasks',
  },
  sprompt: {
    label: 'SPROMPT',
    icon: Zap,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-600/20',
    borderColor: 'border-cyan-500',
    description: 'Super Prompt for AI execution',
  },
  fragment: {
    label: 'Fragment',
    icon: FileText,
    color: 'text-orange-400',
    bgColor: 'bg-orange-600/20',
    borderColor: 'border-orange-500',
    description: 'Atomic execution unit',
  },
}

interface DiscSummary {
  id: string
  title: string
  filePath: string
  status?: string
}

export function WorkflowPage() {
  const navigate = useNavigate()
  
  // State
  const [discs, setDiscs] = useState<DiscSummary[]>([])
  const [selectedDiscIds, setSelectedDiscIds] = useState<string[]>([])
  const [parsedDiscs, setParsedDiscs] = useState<Record<string, ParsedDisc>>({})
  const [loading, setLoading] = useState(true)
  const [loadingDisc, setLoadingDisc] = useState<string | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [selectedNode, setSelectedNode] = useState<ArtifactTreeNode | null>(null)
  const [copiedPrompt, setCopiedPrompt] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showDiscSelector, setShowDiscSelector] = useState(true)

  // Fetch all DISCs on mount
  useEffect(() => {
    const fetchDiscs = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE}/artifacts?type=discussion`)
        const data = await res.json()
        const items = data.items || []
        setDiscs(items.map((item: any) => ({
          id: item.id,
          title: item.title || item.id,
          filePath: item.file_path,
          status: item.status,
        })))
      } catch (err) {
        console.error('Failed to fetch DISCs:', err)
      }
      setLoading(false)
    }
    fetchDiscs()
  }, [])

  // Load and parse a DISC
  const loadDisc = useCallback(async (discId: string) => {
    const disc = discs.find(d => d.id === discId)
    if (!disc || parsedDiscs[discId]) return

    setLoadingDisc(discId)
    try {
      // Fetch the DISC content - correct endpoint is /artifacts/{id}
      const res = await fetch(`${API_BASE}/artifacts/${discId}`)
      if (!res.ok) {
        throw new Error(`Failed to fetch: ${res.status}`)
      }
      const data = await res.json()
      // Content can be string (markdown) or object
      const content = typeof data.content === 'string' ? data.content : JSON.stringify(data.content, null, 2)
      
      console.log(`Loaded DISC ${discId}, content length: ${content.length}`)

      // Parse the DISC
      const parsed = parseDisc(content, discId)
      parsed.title = data.title || disc.title
      parsed.status = data.status || parsed.status
      
      setParsedDiscs(prev => ({ ...prev, [discId]: parsed }))
      setExpandedNodes(prev => new Set([...prev, discId]))
    } catch (err) {
      console.error('Failed to load DISC:', err)
    }
    setLoadingDisc(null)
  }, [discs, parsedDiscs])

  // Toggle DISC selection
  const toggleDiscSelection = useCallback((discId: string) => {
    setSelectedDiscIds(prev => {
      if (prev.includes(discId)) {
        return prev.filter(id => id !== discId)
      } else {
        // Load the DISC if not already loaded
        if (!parsedDiscs[discId]) {
          loadDisc(discId)
        }
        return [...prev, discId]
      }
    })
  }, [parsedDiscs, loadDisc])

  // Build combined artifact tree
  const artifactTrees = useMemo(() => {
    return selectedDiscIds
      .filter(id => parsedDiscs[id])
      .map(id => buildArtifactTree(parsedDiscs[id]))
  }, [selectedDiscIds, parsedDiscs])

  // Copy AI prompt
  const copyPrompt = useCallback((node: ArtifactTreeNode) => {
    const discId = selectedDiscIds[0]
    const parsed = parsedDiscs[discId]
    if (!parsed) return

    const existingArtifacts = parsed.references
      .filter(r => r.status === 'exists')
      .map(r => r.id)

    const prompt = generateArtifactPrompt(parsed, node.type as ArtifactReference['type'], existingArtifacts)
    navigator.clipboard.writeText(prompt)
    setCopiedPrompt(node.id)
    setTimeout(() => setCopiedPrompt(null), 2000)
  }, [selectedDiscIds, parsedDiscs])

  // Filter DISCs by search
  const filteredDiscs = useMemo(() => {
    if (!searchQuery) return discs
    const query = searchQuery.toLowerCase()
    return discs.filter(d => 
      d.id.toLowerCase().includes(query) ||
      d.title.toLowerCase().includes(query)
    )
  }, [discs, searchQuery])

  // Render artifact node in tree
  const renderArtifactNode = (node: ArtifactTreeNode, depth: number = 0) => {
    const config = TYPE_CONFIG[node.type] || TYPE_CONFIG.disc
    const Icon = config.icon
    const isExpanded = expandedNodes.has(node.id)
    const isSelected = selectedNode?.id === node.id
    const hasChildren = node.children.length > 0

    const statusIcon = {
      exists: <CheckCircle2 size={14} className="text-green-400" />,
      planned: <Clock size={14} className="text-amber-400" />,
      missing: <HelpCircle size={14} className="text-zinc-500" />,
    }[node.status]

    return (
      <div key={node.id} className="select-none">
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all',
            isSelected ? 'bg-zinc-700 ring-1 ring-zinc-500' : 'hover:bg-zinc-800',
            depth > 0 && 'ml-6'
          )}
          onClick={() => setSelectedNode(isSelected ? null : node)}
        >
          {/* Expand toggle */}
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setExpandedNodes(prev => {
                  const next = new Set(prev)
                  if (next.has(node.id)) next.delete(node.id)
                  else next.add(node.id)
                  return next
                })
              }}
              className="p-0.5 hover:bg-zinc-700 rounded"
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          ) : (
            <span className="w-5" />
          )}

          {/* Icon */}
          <div className={cn('p-1.5 rounded', config.bgColor)}>
            <Icon size={14} className={config.color} />
          </div>

          {/* Label */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={cn(
                'font-medium text-sm truncate',
                node.status === 'missing' ? 'text-zinc-500' : 'text-white'
              )}>
                {node.id}
              </span>
              {statusIcon}
            </div>
            {node.title && (
              <div className="text-xs text-zinc-500 truncate">{node.title}</div>
            )}
          </div>
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {node.children.map(child => renderArtifactNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  // Render action panel for selected node
  const renderActionPanel = () => {
    if (!selectedNode) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center p-8">
          <FileText size={48} className="text-zinc-700 mb-4" />
          <h3 className="text-lg font-medium text-zinc-400 mb-2">Select an Artifact</h3>
          <p className="text-sm text-zinc-600 max-w-sm">
            Click on an artifact in the tree to view details and actions
          </p>
        </div>
      )
    }

    const config = TYPE_CONFIG[selectedNode.type] || TYPE_CONFIG.disc
    const Icon = config.icon
    const discId = selectedDiscIds[0]
    const parsed = discId ? parsedDiscs[discId] : null

    return (
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start gap-4 mb-6">
          <div className={cn('p-3 rounded-xl', config.bgColor)}>
            <Icon size={24} className={config.color} />
          </div>
          <div className="flex-1">
            <h2 className={cn('text-xl font-bold', config.color)}>{selectedNode.id}</h2>
            {selectedNode.title && (
              <p className="text-zinc-400 mt-1">{selectedNode.title}</p>
            )}
            <p className="text-sm text-zinc-500 mt-2">{config.description}</p>
          </div>
        </div>

        {/* Status badge */}
        <div className="mb-6">
          <div className={cn(
            'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm',
            selectedNode.status === 'exists' && 'bg-green-600/20 text-green-400',
            selectedNode.status === 'planned' && 'bg-amber-600/20 text-amber-400',
            selectedNode.status === 'missing' && 'bg-zinc-700 text-zinc-400',
          )}>
            {selectedNode.status === 'exists' && <CheckCircle2 size={14} />}
            {selectedNode.status === 'planned' && <Clock size={14} />}
            {selectedNode.status === 'missing' && <HelpCircle size={14} />}
            {selectedNode.status === 'exists' ? 'Artifact Exists' : 
             selectedNode.status === 'planned' ? 'Planned in DISC' : 'Not Yet Created'}
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          {selectedNode.status === 'exists' ? (
            <>
              <button 
                onClick={() => navigate(`/artifacts?id=${selectedNode.id}`)}
                className="w-full flex items-center gap-3 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
              >
                <Eye size={18} className="text-zinc-400" />
                <div className="text-left">
                  <div className="font-medium">View Artifact</div>
                  <div className="text-xs text-zinc-500">Open in Artifact Manager</div>
                </div>
                <ExternalLink size={14} className="ml-auto text-zinc-500" />
              </button>
              <button
                onClick={() => copyPrompt(selectedNode)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  copiedPrompt === selectedNode.id
                    ? 'bg-green-600 text-white'
                    : 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-300'
                )}
              >
                {copiedPrompt === selectedNode.id ? (
                  <>
                    <Check size={18} />
                    <div className="text-left">
                      <div className="font-medium">Copied!</div>
                      <div className="text-xs opacity-80">Paste into AI chat</div>
                    </div>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <div className="text-left">
                      <div className="font-medium">Copy Update Prompt</div>
                      <div className="text-xs text-purple-400">Generate AI prompt to update this artifact</div>
                    </div>
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => copyPrompt(selectedNode)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  copiedPrompt === selectedNode.id
                    ? 'bg-green-600 text-white'
                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                )}
              >
                {copiedPrompt === selectedNode.id ? (
                  <>
                    <Check size={18} />
                    <div className="text-left">
                      <div className="font-medium">Copied!</div>
                      <div className="text-xs opacity-80">Paste into AI chat</div>
                    </div>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <div className="text-left">
                      <div className="font-medium">Copy AI Prompt</div>
                      <div className="text-xs opacity-80">Generate this artifact with AI assistance</div>
                    </div>
                  </>
                )}
              </button>
              <button className="w-full flex items-center gap-3 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors">
                <Plus size={18} className="text-zinc-400" />
                <div className="text-left">
                  <div className="font-medium">Create Manually</div>
                  <div className="text-xs text-zinc-500">Open editor with template</div>
                </div>
              </button>
              <button className="w-full flex items-center gap-3 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors">
                <Link2 size={18} className="text-zinc-400" />
                <div className="text-left">
                  <div className="font-medium">Link Existing</div>
                  <div className="text-xs text-zinc-500">Connect to existing artifact</div>
                </div>
              </button>
            </>
          )}
        </div>

        {/* Context from DISC */}
        {parsed && selectedNode.type !== 'disc' && (
          <div className="mt-8 pt-6 border-t border-zinc-800">
            <h3 className="text-sm font-medium text-zinc-400 mb-3">Context from Discussion</h3>
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-xs text-zinc-500 mb-1">Source: {parsed.id}</div>
              {parsed.summary && (
                <p className="text-sm text-zinc-300 line-clamp-3">{parsed.summary}</p>
              )}
              {parsed.requirements.functional.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs text-zinc-500 mb-1">Requirements:</div>
                  <ul className="text-xs text-zinc-400 space-y-1">
                    {parsed.requirements.functional.slice(0, 3).map((req, i) => (
                      <li key={i} className="truncate">• {req}</li>
                    ))}
                    {parsed.requirements.functional.length > 3 && (
                      <li className="text-zinc-500">+{parsed.requirements.functional.length - 3} more</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <CloudRain className="text-blue-400" size={28} />
          <div>
            <h1 className="text-xl font-bold">The Rainstorm</h1>
            <p className="text-sm text-zinc-500">Guided artifact creation workflow</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowDiscSelector(!showDiscSelector)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
              showDiscSelector ? 'bg-purple-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-white'
            )}
          >
            <FolderOpen size={16} />
            Select DISCs
          </button>
          <button
            onClick={() => {
              setSelectedDiscIds([])
              setParsedDiscs({})
              setSelectedNode(null)
            }}
            className="flex items-center gap-2 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-white transition-colors"
          >
            <RefreshCw size={16} />
            Reset
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* DISC Selector Panel */}
        {showDiscSelector && (
          <div className="w-80 border-r border-zinc-800 flex flex-col">
            <div className="p-4 border-b border-zinc-800">
              <h2 className="text-sm font-medium text-zinc-400 mb-3">Select Discussions to Work On</h2>
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                <input
                  type="text"
                  placeholder="Search DISCs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none focus:border-zinc-600"
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="animate-spin text-zinc-500" size={24} />
                </div>
              ) : filteredDiscs.length === 0 ? (
                <div className="text-center py-8 text-zinc-500 text-sm">
                  No discussions found
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredDiscs.map(disc => {
                    const isSelected = selectedDiscIds.includes(disc.id)
                    const isLoading = loadingDisc === disc.id
                    return (
                      <button
                        key={disc.id}
                        onClick={() => toggleDiscSelection(disc.id)}
                        disabled={isLoading}
                        className={cn(
                          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                          isSelected 
                            ? 'bg-purple-600/20 border border-purple-500/50' 
                            : 'hover:bg-zinc-800 border border-transparent'
                        )}
                      >
                        <div className={cn(
                          'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                          isSelected ? 'bg-purple-600 border-purple-600' : 'border-zinc-600'
                        )}>
                          {isSelected && <Check size={12} className="text-white" />}
                          {isLoading && <Loader2 size={12} className="animate-spin text-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{disc.id}</div>
                          <div className="text-xs text-zinc-500 truncate">{disc.title}</div>
                        </div>
                        {disc.status && (
                          <span className={cn(
                            'text-xs px-1.5 py-0.5 rounded',
                            disc.status === 'active' ? 'bg-green-600/20 text-green-400' : 'bg-zinc-700 text-zinc-400'
                          )}>
                            {disc.status}
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
            {selectedDiscIds.length > 0 && (
              <div className="p-3 border-t border-zinc-800 bg-zinc-900">
                <div className="text-xs text-zinc-500 mb-2">
                  {selectedDiscIds.length} discussion{selectedDiscIds.length !== 1 ? 's' : ''} selected
                </div>
                <button
                  onClick={() => setShowDiscSelector(false)}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Continue to Workflow
                  <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Artifact Tree Panel */}
        <div className="w-96 border-r border-zinc-800 flex flex-col">
          <div className="p-4 border-b border-zinc-800">
            <h2 className="text-sm font-medium text-zinc-400 mb-1">Artifact Chain</h2>
            <p className="text-xs text-zinc-600">
              {selectedDiscIds.length === 0 
                ? 'Select a DISC to begin'
                : `Building from ${selectedDiscIds.length} discussion${selectedDiscIds.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            {selectedDiscIds.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-4">
                <MessageSquare size={40} className="text-zinc-700 mb-3" />
                <p className="text-sm text-zinc-500">
                  Select one or more discussions from the left panel to see their artifact chains
                </p>
              </div>
            ) : artifactTrees.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin text-zinc-500" size={24} />
              </div>
            ) : (
              <div className="space-y-4">
                {artifactTrees.map(tree => (
                  <div key={tree.id}>
                    {renderArtifactNode(tree)}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Progress summary */}
          {artifactTrees.length > 0 && (
            <div className="p-4 border-t border-zinc-800 bg-zinc-900">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-zinc-500">Workflow Progress</span>
                <span className="text-xs text-zinc-400">
                  {artifactTrees.reduce((acc, tree) => 
                    acc + tree.children.filter(c => c.status === 'exists').length, 0
                  )} / {artifactTrees.reduce((acc, tree) => 
                    acc + tree.children.filter(c => c.type !== 'contract').length, 0
                  )} required
                </span>
              </div>
              <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all"
                  style={{ 
                    width: `${
                      (artifactTrees.reduce((acc, tree) => 
                        acc + tree.children.filter(c => c.status === 'exists').length, 0
                      ) / Math.max(1, artifactTrees.reduce((acc, tree) => 
                        acc + tree.children.filter(c => c.type !== 'contract').length, 0
                      ))) * 100
                    }%` 
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Action Panel */}
        <div className="flex-1 bg-zinc-900/50 overflow-y-auto">
          {renderActionPanel()}
        </div>
      </div>
    </div>
  )
}
