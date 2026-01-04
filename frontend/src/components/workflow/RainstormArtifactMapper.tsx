import { useState, useEffect } from 'react'
import { 
  MessageSquare, 
  FileJson, 
  FileText, 
  Code2, 
  ListTodo,
  Check,
  Circle,
  ChevronRight,
  Loader2
} from 'lucide-react'
import { cn } from '../../lib/utils'
import type { ArtifactSummary } from './types'

const API_BASE = '/api/devtools'

export type ArtifactStage = 'discussion' | 'adr' | 'spec' | 'contract' | 'plan'

export interface ArtifactMapping {
  stage: ArtifactStage
  label: string
  icon: React.ElementType
  color: string
  bgColor: string
  required: boolean
  artifact: ArtifactSummary | null
  status: 'completed' | 'current' | 'pending' | 'optional'
}

const STAGE_CONFIG: Record<ArtifactStage, { label: string; icon: React.ElementType; color: string; bgColor: string; required: boolean }> = {
  discussion: { label: 'Discussion', icon: MessageSquare, color: 'text-purple-400', bgColor: 'bg-purple-600/20', required: true },
  adr: { label: 'ADR', icon: FileJson, color: 'text-blue-400', bgColor: 'bg-blue-600/20', required: true },
  spec: { label: 'SPEC', icon: FileText, color: 'text-green-400', bgColor: 'bg-green-600/20', required: true },
  contract: { label: 'Contract', icon: Code2, color: 'text-pink-400', bgColor: 'bg-pink-600/20', required: false },
  plan: { label: 'Plan', icon: ListTodo, color: 'text-amber-400', bgColor: 'bg-amber-600/20', required: true },
}

const STAGES_ORDER: ArtifactStage[] = ['discussion', 'adr', 'spec', 'contract', 'plan']

interface RainstormArtifactMapperProps {
  selectedDiscId: string | null
  currentStage: ArtifactStage
  artifactIds: Record<ArtifactStage, string | null>
  onArtifactClick: (stage: ArtifactStage, artifact: ArtifactSummary | null) => void
  className?: string
}

export function RainstormArtifactMapper({
  selectedDiscId,
  currentStage,
  artifactIds,
  onArtifactClick,
  className
}: RainstormArtifactMapperProps) {
  const [artifacts, setArtifacts] = useState<Record<string, ArtifactSummary>>({})
  const [loading, setLoading] = useState(true)

  // Fetch all artifacts to check which ones exist
  useEffect(() => {
    const fetchArtifacts = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE}/artifacts`)
        const data = await res.json()
        const items: ArtifactSummary[] = data.items || []
        
        // Create lookup by ID
        const lookup: Record<string, ArtifactSummary> = {}
        items.forEach(a => {
          lookup[a.id] = a
        })
        setArtifacts(lookup)
      } catch (err) {
        console.error('Failed to fetch artifacts:', err)
      }
      setLoading(false)
    }
    fetchArtifacts()
  }, [])

  // Build artifact mappings
  const mappings: ArtifactMapping[] = STAGES_ORDER.map(stage => {
    const config = STAGE_CONFIG[stage]
    const artifactId = artifactIds[stage]
    const artifact = artifactId ? artifacts[artifactId] || null : null
    
    // Determine status
    let status: ArtifactMapping['status'] = 'pending'
    if (artifact) {
      status = 'completed'
    } else if (stage === currentStage) {
      status = 'current'
    } else if (!config.required) {
      status = 'optional'
    }

    return {
      stage,
      ...config,
      artifact,
      status,
    }
  })

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <Loader2 className="animate-spin text-zinc-500" size={24} />
      </div>
    )
  }

  return (
    <div className={cn('', className)}>
      {/* Horizontal artifact chain */}
      <div className="flex items-center justify-center gap-1 mb-6">
        {mappings.map((mapping, i) => {
          const Icon = mapping.icon
          const isCompleted = mapping.status === 'completed'
          const isCurrent = mapping.status === 'current'
          const isOptional = mapping.status === 'optional'
          
          return (
            <div key={mapping.stage} className="flex items-center">
              <button
                onClick={() => onArtifactClick(mapping.stage, mapping.artifact)}
                className={cn(
                  'flex flex-col items-center p-3 rounded-lg transition-all',
                  isCurrent && 'ring-2 ring-blue-500 bg-zinc-800',
                  isCompleted && 'bg-zinc-800/50',
                  !isCompleted && !isCurrent && 'opacity-50 hover:opacity-75',
                  'hover:bg-zinc-800'
                )}
              >
                <div className={cn(
                  'relative w-10 h-10 rounded-full flex items-center justify-center',
                  mapping.bgColor
                )}>
                  <Icon size={20} className={mapping.color} />
                  {isCompleted && (
                    <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                      <Check size={10} className="text-white" />
                    </div>
                  )}
                  {isCurrent && (
                    <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center">
                      <Circle size={8} className="text-white fill-white" />
                    </div>
                  )}
                </div>
                <span className={cn(
                  'text-xs mt-2',
                  isCurrent ? 'text-white font-medium' : 'text-zinc-500'
                )}>
                  {mapping.label}
                  {isOptional && ' (opt)'}
                </span>
                {mapping.artifact && (
                  <span className="text-[10px] text-zinc-600 truncate max-w-[80px]">
                    {mapping.artifact.id}
                  </span>
                )}
              </button>
              
              {i < mappings.length - 1 && (
                <ChevronRight size={16} className="text-zinc-700 mx-1" />
              )}
            </div>
          )
        })}
      </div>

      {/* Current stage details */}
      {currentStage && (
        <div className="text-center">
          <div className="text-xs text-zinc-500 mb-1">Currently working on:</div>
          <div className={cn(
            'inline-flex items-center gap-2 px-3 py-1.5 rounded-full',
            STAGE_CONFIG[currentStage].bgColor
          )}>
            {(() => {
              const Icon = STAGE_CONFIG[currentStage].icon
              return <Icon size={14} className={STAGE_CONFIG[currentStage].color} />
            })()}
            <span className={STAGE_CONFIG[currentStage].color}>
              {STAGE_CONFIG[currentStage].label}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
