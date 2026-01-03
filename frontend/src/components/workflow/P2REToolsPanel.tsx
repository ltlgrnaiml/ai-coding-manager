import { useState } from 'react'
import { 
  Activity, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Layers,
  ExternalLink,
  RefreshCw,
  ChevronDown
} from 'lucide-react'
import { cn } from '../../lib/utils'

type P2RETool = 'phoenix' | 'prompt-optimizer' | 'quality-grader' | 'hallucination-detector' | 'context-optimizer'

interface ToolConfig {
  id: P2RETool
  name: string
  description: string
  icon: React.ReactNode
  url?: string
  available: boolean
}

const TOOLS: ToolConfig[] = [
  {
    id: 'phoenix',
    name: 'Phoenix Traces',
    description: 'View and inspect LLM traces',
    icon: <Activity size={16} />,
    url: 'http://localhost:6006',
    available: true,
  },
  {
    id: 'prompt-optimizer',
    name: 'Prompt Optimizer',
    description: 'Analyze and improve prompts',
    icon: <Sparkles size={16} />,
    available: false,
  },
  {
    id: 'quality-grader',
    name: 'Quality Grader',
    description: 'Score response quality',
    icon: <CheckCircle2 size={16} />,
    available: false,
  },
  {
    id: 'hallucination-detector',
    name: 'Hallucination Detector',
    description: 'Flag potentially hallucinated content',
    icon: <AlertTriangle size={16} />,
    available: false,
  },
  {
    id: 'context-optimizer',
    name: 'Context Optimizer',
    description: 'Optimize RAG context relevance',
    icon: <Layers size={16} />,
    available: false,
  },
]

export function P2REToolsPanel() {
  const [selectedTool, setSelectedTool] = useState<P2RETool>('phoenix')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [iframeKey, setIframeKey] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  const currentTool = TOOLS.find(t => t.id === selectedTool) || TOOLS[0]

  const handleRefresh = () => {
    setIsLoading(true)
    setIframeKey(prev => prev + 1)
  }

  const handleOpenExternal = () => {
    if (currentTool.url) {
      window.open(currentTool.url, '_blank')
    }
  }

  return (
    <div className="flex flex-col h-full bg-zinc-900">
      {/* Tool Selector Header */}
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        {/* Dropdown Selector */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 rounded-md hover:bg-zinc-700 transition-colors"
          >
            {currentTool.icon}
            <span className="text-sm font-medium">{currentTool.name}</span>
            <ChevronDown size={14} className={cn(
              'transition-transform',
              isDropdownOpen && 'rotate-180'
            )} />
          </button>

          {isDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-zinc-800 border border-zinc-700 rounded-md shadow-lg z-50">
              {TOOLS.map(tool => (
                <button
                  key={tool.id}
                  onClick={() => {
                    if (tool.available) {
                      setSelectedTool(tool.id)
                      setIsLoading(true)
                    }
                    setIsDropdownOpen(false)
                  }}
                  disabled={!tool.available}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-zinc-700 transition-colors',
                    tool.id === selectedTool && 'bg-zinc-700',
                    !tool.available && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <div className={cn(
                    'p-1.5 rounded',
                    tool.available ? 'bg-blue-500/20 text-blue-400' : 'bg-zinc-700 text-zinc-500'
                  )}>
                    {tool.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium flex items-center gap-2">
                      {tool.name}
                      {!tool.available && (
                        <span className="text-xs text-zinc-500">(Coming Soon)</span>
                      )}
                    </div>
                    <div className="text-xs text-zinc-400 truncate">{tool.description}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleRefresh}
            className="p-1.5 hover:bg-zinc-800 rounded transition-colors"
            title="Refresh"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
          {currentTool.url && (
            <button
              onClick={handleOpenExternal}
              className="p-1.5 hover:bg-zinc-800 rounded transition-colors"
              title="Open in new tab"
            >
              <ExternalLink size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Tool Content Area */}
      <div className="flex-1 relative">
        {currentTool.available && currentTool.url ? (
          <>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-zinc-900 z-10">
                <div className="flex flex-col items-center gap-3">
                  <RefreshCw size={24} className="animate-spin text-blue-500" />
                  <span className="text-sm text-zinc-400">Loading {currentTool.name}...</span>
                </div>
              </div>
            )}
            <iframe
              key={iframeKey}
              src={currentTool.url}
              className="w-full h-full border-0"
              onLoad={() => setIsLoading(false)}
              onError={() => setIsLoading(false)}
              title={currentTool.name}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
            />
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="p-4 bg-zinc-800 rounded-full mb-4">
              {currentTool.icon}
            </div>
            <h3 className="text-lg font-medium mb-2">{currentTool.name}</h3>
            <p className="text-sm text-zinc-400 max-w-md mb-4">
              {currentTool.description}
            </p>
            <span className="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-full text-xs">
              Coming Soon
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
