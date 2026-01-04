import { useState, useEffect } from 'react'
import { 
  MessageSquare, 
  Sparkles, 
  Plus, 
  FolderOpen, 
  Check, 
  ChevronRight,
  FileJson,
  FileText,
  ListTodo,
  Code2,
  RefreshCw
} from 'lucide-react'
import { cn } from '../../lib/utils'
import type { ArtifactSummary } from './types'

const API_BASE = '/api/devtools'

// Artifact types in the Rainstorm workflow chain
const ARTIFACT_CHAIN = [
  { id: 'discussion', label: 'Discussion', icon: MessageSquare, color: 'text-purple-400' },
  { id: 'adr', label: 'ADR', icon: FileJson, color: 'text-blue-400' },
  { id: 'spec', label: 'SPEC', icon: FileText, color: 'text-green-400' },
  { id: 'contract', label: 'Contract', icon: Code2, color: 'text-pink-400' },
  { id: 'plan', label: 'Plan', icon: ListTodo, color: 'text-amber-400' },
]

interface RainstormStep1Props {
  onSelectDisc: (disc: ArtifactSummary) => void
  onCreateNew: () => void
  onCopyPrompt: () => void
  onReset: () => void
  className?: string
}

export function RainstormStep1({ 
  onSelectDisc, 
  onCreateNew, 
  onCopyPrompt,
  onReset,
  className 
}: RainstormStep1Props) {
  const [discussions, setDiscussions] = useState<ArtifactSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDisc, setSelectedDisc] = useState<ArtifactSummary | null>(null)
  const [showSelector, setShowSelector] = useState(false)

  // Fetch existing discussions
  useEffect(() => {
    fetch(`${API_BASE}/artifacts?type=discussion`)
      .then(res => res.json())
      .then(data => {
        setDiscussions(data.items || [])
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch discussions:', err)
        setLoading(false)
      })
  }, [])

  const handleSelectDisc = (disc: ArtifactSummary) => {
    setSelectedDisc(disc)
  }

  const handleConfirmSelection = () => {
    if (selectedDisc) {
      onSelectDisc(selectedDisc)
    }
  }

  return (
    <div className={cn('flex flex-col items-center justify-center h-full p-8', className)}>
      {/* Header */}
      <div className="mb-6 px-4 py-2 bg-blue-600/20 border border-blue-500/30 rounded-full text-blue-400 text-sm flex items-center gap-2">
        <span>The Rainstorm ⛈️</span>
        <span className="text-blue-500">•</span>
        <span>Step 1 of 6</span>
      </div>

      <MessageSquare size={48} className="text-purple-400 mb-4" />
      
      <h2 className="text-2xl font-bold mb-2">Choose Your Starting Point</h2>
      <p className="text-zinc-400 text-center max-w-lg mb-8">
        Every Rainstorm begins with a Discussion (DISC). You can create a new one 
        or select an existing DISC to continue working on.
      </p>

      {/* Three options */}
      <div className="flex flex-col sm:flex-row items-stretch gap-4 w-full max-w-2xl mb-8">
        {/* Option 1: Select Existing */}
        <button
          onClick={() => setShowSelector(true)}
          className="flex-1 flex flex-col items-center gap-3 p-6 bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 hover:border-purple-500/50 rounded-xl transition-all group"
        >
          <FolderOpen size={32} className="text-purple-400 group-hover:scale-110 transition-transform" />
          <div className="text-center">
            <div className="font-semibold">Select Existing DISC</div>
            <div className="text-sm text-zinc-500">
              {discussions.length} discussions available
            </div>
          </div>
        </button>

        {/* Option 2: Copy AI Prompt */}
        <button
          onClick={onCopyPrompt}
          className="flex-1 flex flex-col items-center gap-3 p-6 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 hover:border-purple-500 rounded-xl transition-all group"
        >
          <Sparkles size={32} className="text-purple-400 group-hover:scale-110 transition-transform" />
          <div className="text-center">
            <div className="font-semibold text-purple-300">Copy AI Prompt</div>
            <div className="text-sm text-zinc-500">
              Generate a new DISC with AI
            </div>
          </div>
        </button>

        {/* Option 3: Create Manually */}
        <button
          onClick={onCreateNew}
          className="flex-1 flex flex-col items-center gap-3 p-6 bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 hover:border-zinc-500 rounded-xl transition-all group"
        >
          <Plus size={32} className="text-zinc-400 group-hover:scale-110 transition-transform" />
          <div className="text-center">
            <div className="font-semibold">Create Manually</div>
            <div className="text-sm text-zinc-500">
              Write a new DISC yourself
            </div>
          </div>
        </button>
      </div>

      {/* Reset button */}
      <button
        onClick={onReset}
        className="flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors"
      >
        <RefreshCw size={14} />
        Reset Workflow
      </button>

      {/* Artifact Chain Preview */}
      <div className="mt-8 pt-8 border-t border-zinc-800 w-full max-w-2xl">
        <div className="text-xs text-zinc-500 mb-4 text-center">
          The Rainstorm guides you through this artifact chain:
        </div>
        <div className="flex items-center justify-center gap-2">
          {ARTIFACT_CHAIN.map((artifact, i) => (
            <div key={artifact.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <artifact.icon size={20} className={artifact.color} />
                <span className="text-xs text-zinc-500 mt-1">{artifact.label}</span>
              </div>
              {i < ARTIFACT_CHAIN.length - 1 && (
                <ChevronRight size={16} className="text-zinc-600 mx-2" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* DISC Selector Modal */}
      {showSelector && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-zinc-800">
              <h3 className="text-lg font-semibold">Select a Discussion</h3>
              <button 
                onClick={() => { setShowSelector(false); setSelectedDisc(null); }}
                className="text-zinc-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* DISC List */}
            <div className="p-4 max-h-[50vh] overflow-y-auto">
              {loading ? (
                <div className="text-center text-zinc-500 py-8">Loading discussions...</div>
              ) : discussions.length === 0 ? (
                <div className="text-center text-zinc-500 py-8">
                  No discussions found. Create one to get started.
                </div>
              ) : (
                <div className="space-y-2">
                  {discussions.map(disc => (
                    <button
                      key={disc.id}
                      onClick={() => handleSelectDisc(disc)}
                      className={cn(
                        'w-full text-left p-4 rounded-lg border transition-all',
                        selectedDisc?.id === disc.id
                          ? 'bg-purple-600/20 border-purple-500'
                          : 'bg-zinc-800/50 border-zinc-700 hover:border-zinc-600'
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium">{disc.id}</div>
                          <div className="text-sm text-zinc-400 truncate max-w-md">
                            {disc.title || disc.file_path}
                          </div>
                        </div>
                        {selectedDisc?.id === disc.id && (
                          <Check size={20} className="text-purple-400" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-4 border-t border-zinc-800">
              <button
                onClick={() => { setShowSelector(false); setSelectedDisc(null); }}
                className="px-4 py-2 text-zinc-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmSelection}
                disabled={!selectedDisc}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                  selectedDisc
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                )}
              >
                <ChevronRight size={16} />
                Continue with {selectedDisc?.id || 'Selection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
