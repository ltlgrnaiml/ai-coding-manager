import { useState, useEffect } from 'react'
import { X, FileText, Plus, Eye } from 'lucide-react'
import type { ArtifactSummary } from './types'
import { cn } from '../../lib/utils'

interface AutoDiscoveryNotificationProps {
  newArtifacts: ArtifactSummary[]
  onAddToWorkflow: (artifact: ArtifactSummary) => void
  onIgnore: (artifactId: string) => void
  onViewDetails?: (artifact: ArtifactSummary) => void
  className?: string
}

export function AutoDiscoveryNotification({
  newArtifacts,
  onAddToWorkflow,
  onIgnore,
  onViewDetails,
  className
}: AutoDiscoveryNotificationProps) {
  const [visible, setVisible] = useState(true)
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())
  
  // Show notification when new artifacts arrive
  useEffect(() => {
    if (newArtifacts.length > 0) {
      setVisible(true)
    }
  }, [newArtifacts])
  
  const visibleArtifacts = newArtifacts.filter(a => !dismissed.has(a.id))
  
  if (!visible || visibleArtifacts.length === 0) {
    return null
  }
  
  const handleIgnore = (artifactId: string) => {
    setDismissed(prev => new Set(prev).add(artifactId))
    onIgnore(artifactId)
  }
  
  return (
    <div className={cn(
      'fixed bottom-4 right-4 z-50 max-w-md animate-in slide-in-from-bottom-2 fade-in duration-300',
      className
    )}>
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-zinc-700">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="font-medium text-sm">New Artifacts Detected!</span>
          </div>
          <button
            onClick={() => setVisible(false)}
            className="p-1 hover:bg-zinc-700 rounded transition-colors"
          >
            <X size={14} />
          </button>
        </div>
        
        {/* Artifact list */}
        <div className="max-h-64 overflow-y-auto">
          {visibleArtifacts.map(artifact => (
            <div
              key={artifact.id}
              className="flex items-center justify-between gap-3 px-4 py-3 border-b border-zinc-800 last:border-0"
            >
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <FileText size={16} className="text-zinc-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {artifact.id}: {artifact.title}
                  </p>
                  <p className="text-xs text-zinc-500 truncate">
                    {artifact.file_path}
                  </p>
                  {/* Show inferred parent if available */}
                  <p className="text-xs text-blue-400 mt-1">
                    Parent: {extractParentFromPath(artifact.file_path)}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-1 flex-shrink-0">
                {onViewDetails && (
                  <button
                    onClick={() => onViewDetails(artifact)}
                    className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-700 rounded transition-colors"
                    title="View details"
                  >
                    <Eye size={14} />
                  </button>
                )}
                <button
                  onClick={() => {
                    onAddToWorkflow(artifact)
                    handleIgnore(artifact.id)
                  }}
                  className="p-1.5 text-green-400 hover:text-green-300 hover:bg-green-600/20 rounded transition-colors"
                  title="Add to workflow"
                >
                  <Plus size={14} />
                </button>
                <button
                  onClick={() => handleIgnore(artifact.id)}
                  className="p-1.5 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-700 rounded transition-colors"
                  title="Ignore"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
        
        {/* Footer */}
        {visibleArtifacts.length > 1 && (
          <div className="px-4 py-2 bg-zinc-900/50 border-t border-zinc-800 text-center">
            <button
              onClick={() => {
                visibleArtifacts.forEach(a => {
                  onAddToWorkflow(a)
                })
                setVisible(false)
              }}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              Add all to workflow
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Helper function to extract parent reference from file path or content
function extractParentFromPath(path: string): string {
  // Try to find DISC/ADR reference in path
  const match = path.match(/(?:DISC|ADR|SPEC|PLAN)-\d+/i)
  if (match) {
    return match[0]
  }
  
  // Check if it's in a known directory that implies parent
  if (path.includes('.adrs/')) {
    return 'Inferred from ADRs directory'
  }
  if (path.includes('.discussions/')) {
    return 'Inferred from Discussions directory'
  }
  
  return 'Unknown'
}
