import { useState } from 'react'
import { Activity, RefreshCw, ExternalLink, ChevronDown } from 'lucide-react'

interface P2RETool {
  id: string
  name: string
  description: string
  url?: string
  available: boolean
}

const TOOLS: P2RETool[] = [
  {
    id: 'phoenix',
    name: 'Phoenix Traces',
    description: 'View and analyze LLM traces, spans, and observability data',
    url: 'http://localhost:6006',
    available: true,
  },
  {
    id: 'prompt-optimizer',
    name: 'Prompt Optimizer',
    description: 'Analyze and improve prompt effectiveness',
    available: false,
  },
  {
    id: 'quality-grader',
    name: 'Quality Grader',
    description: 'Score and evaluate response quality',
    available: false,
  },
  {
    id: 'hallucination-detector',
    name: 'Hallucination Detector',
    description: 'Identify potentially hallucinated content',
    available: false,
  },
  {
    id: 'context-optimizer',
    name: 'Context Optimizer',
    description: 'Optimize RAG context relevance and retrieval',
    available: false,
  },
]

export function P2REPage() {
  const [selectedTool, setSelectedTool] = useState<P2RETool>(TOOLS[0])
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [iframeKey, setIframeKey] = useState(0)

  const handleRefresh = () => {
    setIsLoading(true)
    setIframeKey(prev => prev + 1)
  }

  const handleOpenExternal = () => {
    if (selectedTool.url) {
      window.open(selectedTool.url, '_blank')
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">P2RE Tools</h1>
            <p className="text-xs text-gray-400">Prompts to Response Ecosystem</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Tool Selector */}
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <span className="text-sm text-white">{selectedTool.name}</span>
              <ChevronDown size={16} className={`text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {isDropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
                {TOOLS.map((tool) => (
                  <button
                    key={tool.id}
                    onClick={() => {
                      if (tool.available) {
                        setSelectedTool(tool)
                        setIsLoading(true)
                      }
                      setIsDropdownOpen(false)
                    }}
                    disabled={!tool.available}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg transition-colors ${
                      !tool.available ? 'opacity-50 cursor-not-allowed' : ''
                    } ${selectedTool.id === tool.id ? 'bg-gray-700' : ''}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">{tool.name}</span>
                      {!tool.available && (
                        <span className="text-xs text-gray-500 bg-gray-900 px-2 py-0.5 rounded">Coming Soon</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{tool.description}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw size={18} />
          </button>
          <button
            onClick={handleOpenExternal}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Open in new tab"
          >
            <ExternalLink size={18} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 relative">
        {selectedTool.available && selectedTool.url ? (
          <>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-gray-400">Loading {selectedTool.name}...</span>
                </div>
              </div>
            )}
            <iframe
              key={iframeKey}
              src={selectedTool.url}
              className="w-full h-full border-0"
              onLoad={() => setIsLoading(false)}
              title={selectedTool.name}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Activity className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">{selectedTool.name}</h2>
              <p className="text-gray-400 mb-4">{selectedTool.description}</p>
              <span className="text-sm text-emerald-400 bg-emerald-500/10 px-4 py-2 rounded-lg">
                Coming Soon
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
