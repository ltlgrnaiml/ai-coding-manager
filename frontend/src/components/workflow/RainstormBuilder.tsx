import { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  CloudRain, 
  RefreshCw, 
  Sparkles, 
  Plus, 
  Link2, 
  Eye,
  Edit3,
  ChevronRight,
  Check,
  Circle,
  AlertCircle,
  Loader2,
  Copy,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  Maximize2
} from 'lucide-react'
import { cn } from '../../lib/utils'
import type { ArtifactSummary } from './types'

const API_BASE = '/api/devtools'

// Artifact type configuration
type ArtifactType = 'discussion' | 'adr' | 'spec' | 'contract' | 'plan'

interface ArtifactNode {
  id: string
  type: ArtifactType
  label: string
  artifact: ArtifactSummary | null
  status: 'completed' | 'current' | 'pending' | 'optional'
  children: ArtifactNode[]
  x?: number
  y?: number
}

interface RainstormBuilderProps {
  selectedDiscId: string | null
  onSelectArtifact: (artifact: ArtifactSummary) => void
  onViewArtifact: (artifact: ArtifactSummary) => void
  onEditArtifact: (artifact: ArtifactSummary) => void
  onReset: () => void
  className?: string
}

const TYPE_CONFIG: Record<ArtifactType, { 
  label: string
  color: string
  bgColor: string
  borderColor: string
  required: boolean
  prompt: string
}> = {
  discussion: { 
    label: 'DISC', 
    color: 'text-purple-400', 
    bgColor: 'bg-purple-600/20',
    borderColor: 'border-purple-500',
    required: true,
    prompt: `Create a Discussion document that captures the design conversation.

Template:
# DISC-XXX: [Title]

**Status**: draft
**Created**: [Date]

## Summary
[One paragraph describing the topic]

## Problem Statement
[What problem are we solving?]

## Requirements
### Functional Requirements
- [ ] **FR-1**: [Requirement]

## Open Questions
| ID | Question | Status |
|----|----------|--------|
| Q-1 | [Question] | open |`
  },
  adr: { 
    label: 'ADR', 
    color: 'text-blue-400', 
    bgColor: 'bg-blue-600/20',
    borderColor: 'border-blue-500',
    required: true,
    prompt: `Create an Architecture Decision Record (ADR) documenting the key architectural decisions.

Template:
# ADR-XXX: [Decision Title]

**Status**: proposed
**Created**: [Date]
**Decision Makers**: [Names]

## Context
[What is the situation that requires a decision?]

## Decision
[What is the decision that was made?]

## Consequences
### Positive
- [Benefit 1]

### Negative
- [Tradeoff 1]

## Alternatives Considered
1. [Alternative]: Rejected because [reason]`
  },
  spec: { 
    label: 'SPEC', 
    color: 'text-green-400', 
    bgColor: 'bg-green-600/20',
    borderColor: 'border-green-500',
    required: true,
    prompt: `Create a Specification (SPEC) defining the functional requirements and API contracts.

Template:
# SPEC-XXX: [Feature Name]

**Status**: draft
**Created**: [Date]
**Source**: [Related DISC/ADR]

## Overview
[Brief description of the feature]

## Functional Requirements
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-1 | [Requirement] | must | pending |

## API Contracts
### Endpoint: [Name]
- **Method**: POST/GET
- **Path**: /api/...
- **Request**: [Schema]
- **Response**: [Schema]

## Acceptance Criteria
- [ ] [Criterion 1]`
  },
  contract: { 
    label: 'Contract', 
    color: 'text-pink-400', 
    bgColor: 'bg-pink-600/20',
    borderColor: 'border-pink-500',
    required: false,
    prompt: `Create Pydantic contracts (data schemas) for this feature.

Template:
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class [Name]Request(BaseModel):
    """Request schema for [operation]."""
    field: str = Field(..., description="[Description]")

class [Name]Response(BaseModel):
    """Response schema for [operation]."""
    id: str
    created_at: datetime
    data: dict`
  },
  plan: { 
    label: 'Plan', 
    color: 'text-amber-400', 
    bgColor: 'bg-amber-600/20',
    borderColor: 'border-amber-500',
    required: true,
    prompt: `Create a Plan breaking this work into milestones and tasks.

Template (JSON):
{
  "plan_id": "PLAN-XXX",
  "title": "[Plan Title]",
  "status": "active",
  "source_discussions": ["DISC-XXX"],
  "milestones": [
    {
      "id": "M01",
      "title": "[Milestone Name]",
      "tasks": [
        {
          "id": "T01",
          "description": "[Task description]",
          "acceptance_criteria": [
            {
              "id": "AC-01",
              "description": "[Criterion]",
              "verification_command": "[command]"
            }
          ]
        }
      ]
    }
  ]
}`
  },
}

const WORKFLOW_ORDER: ArtifactType[] = ['discussion', 'adr', 'spec', 'contract', 'plan']

export function RainstormBuilder({
  selectedDiscId,
  onSelectArtifact,
  onViewArtifact,
  onEditArtifact,
  onReset,
  className
}: RainstormBuilderProps) {
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<ArtifactNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [copiedPrompt, setCopiedPrompt] = useState<string | null>(null)

  // Fetch all artifacts
  useEffect(() => {
    const fetchArtifacts = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE}/artifacts`)
        const data = await res.json()
        setArtifacts(data.items || [])
      } catch (err) {
        console.error('Failed to fetch artifacts:', err)
      }
      setLoading(false)
    }
    fetchArtifacts()
  }, [])

  // Find the selected DISC
  const selectedDisc = useMemo(() => {
    return artifacts.find(a => a.id === selectedDiscId) || null
  }, [artifacts, selectedDiscId])

  // Build the artifact tree from the selected DISC
  const artifactTree = useMemo((): ArtifactNode[] => {
    if (!selectedDisc) return []

    // Find related artifacts (simple heuristic: same prefix or referenced)
    const relatedArtifacts: Record<ArtifactType, ArtifactSummary[]> = {
      discussion: [selectedDisc],
      adr: artifacts.filter(a => a.type === 'adr'),
      spec: artifacts.filter(a => a.type === 'spec'),
      contract: artifacts.filter(a => a.type === 'contract'),
      plan: artifacts.filter(a => a.type === 'plan'),
    }

    // Build tree structure
    const tree: ArtifactNode[] = WORKFLOW_ORDER.map((type, index) => {
      const typeArtifacts = relatedArtifacts[type]
      const hasArtifact = type === 'discussion' ? true : typeArtifacts.length > 0
      const config = TYPE_CONFIG[type]

      // Determine status
      let status: ArtifactNode['status'] = 'pending'
      if (type === 'discussion') {
        status = 'completed'
      } else if (!config.required) {
        status = 'optional'
      }

      // For types with multiple artifacts, create children
      const children: ArtifactNode[] = type !== 'discussion' && typeArtifacts.length > 0
        ? typeArtifacts.map(a => ({
            id: a.id,
            type,
            label: a.id,
            artifact: a,
            status: 'completed' as const,
            children: [],
          }))
        : []

      return {
        id: type === 'discussion' ? selectedDisc.id : `${type}-placeholder`,
        type,
        label: config.label,
        artifact: type === 'discussion' ? selectedDisc : (children.length > 0 ? children[0].artifact : null),
        status: children.length > 0 ? 'completed' : status,
        children,
      }
    })

    return tree
  }, [selectedDisc, artifacts])

  // Copy prompt with context
  const copyPrompt = useCallback((type: ArtifactType) => {
    const config = TYPE_CONFIG[type]
    let prompt = config.prompt

    // Add context from selected DISC
    if (selectedDisc) {
      prompt = `Context: Working on "${selectedDisc.title || selectedDisc.id}"
Source Discussion: ${selectedDisc.id}
${selectedDisc.file_path ? `File: ${selectedDisc.file_path}` : ''}

---

${prompt}`
    }

    navigator.clipboard.writeText(prompt)
    setCopiedPrompt(type)
    setTimeout(() => setCopiedPrompt(null), 2000)
  }, [selectedDisc])

  // Render artifact node
  const renderNode = (node: ArtifactNode, depth: number = 0) => {
    const config = TYPE_CONFIG[node.type]
    const isSelected = selectedNode?.id === node.id
    const hasArtifact = node.artifact !== null
    const isOptional = node.status === 'optional'
    const isCompleted = node.status === 'completed'
    const isCurrent = node.status === 'current'

    return (
      <div key={node.id} className="relative">
        {/* Connection line */}
        {depth > 0 && (
          <div className="absolute left-0 top-1/2 w-8 h-px bg-zinc-700 -translate-x-full" />
        )}

        {/* Node */}
        <button
          onClick={() => setSelectedNode(isSelected ? null : node)}
          className={cn(
            'relative flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all min-w-[200px]',
            isSelected && 'ring-2 ring-white/20',
            hasArtifact 
              ? `${config.bgColor} ${config.borderColor}` 
              : 'bg-zinc-800/50 border-zinc-700 border-dashed',
            !hasArtifact && !isOptional && 'hover:border-zinc-500',
            isOptional && !hasArtifact && 'opacity-60'
          )}
        >
          {/* Status indicator */}
          <div className={cn(
            'absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center',
            isCompleted && 'bg-green-500',
            isCurrent && 'bg-blue-500',
            !isCompleted && !isCurrent && !isOptional && 'bg-zinc-700',
            isOptional && !hasArtifact && 'bg-zinc-800 border border-zinc-600'
          )}>
            {isCompleted && <Check size={12} className="text-white" />}
            {isCurrent && <Circle size={8} className="text-white fill-white" />}
            {!isCompleted && !isCurrent && !isOptional && <AlertCircle size={12} className="text-zinc-400" />}
            {isOptional && !hasArtifact && <span className="text-[8px] text-zinc-500">opt</span>}
          </div>

          {/* Content */}
          <div className="flex-1 text-left">
            <div className={cn('font-medium', config.color)}>
              {node.label}
            </div>
            {hasArtifact ? (
              <div className="text-xs text-zinc-400 truncate max-w-[150px]">
                {node.artifact!.id}
              </div>
            ) : (
              <div className="text-xs text-zinc-500">
                {isOptional ? 'Optional' : 'Not created'}
              </div>
            )}
          </div>

          {/* Expand indicator for multiple */}
          {node.children.length > 1 && (
            <div className="text-xs text-zinc-500 bg-zinc-700 px-1.5 py-0.5 rounded">
              +{node.children.length - 1}
            </div>
          )}
        </button>

        {/* Action panel when selected */}
        {isSelected && (
          <div className="absolute left-full top-0 ml-4 z-10">
            <div className="bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl p-3 min-w-[200px]">
              <div className="text-sm font-medium mb-3">{config.label} Actions</div>
              
              {hasArtifact ? (
                <div className="space-y-2">
                  <button
                    onClick={() => onViewArtifact(node.artifact!)}
                    className="w-full flex items-center gap-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded text-sm"
                  >
                    <Eye size={14} />
                    View
                  </button>
                  <button
                    onClick={() => onEditArtifact(node.artifact!)}
                    className="w-full flex items-center gap-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded text-sm"
                  >
                    <Edit3 size={14} />
                    Edit
                  </button>
                  {node.children.length > 1 && (
                    <div className="pt-2 border-t border-zinc-700">
                      <div className="text-xs text-zinc-500 mb-2">Related ({node.children.length})</div>
                      {node.children.map(child => (
                        <button
                          key={child.id}
                          onClick={() => child.artifact && onViewArtifact(child.artifact)}
                          className="w-full text-left px-2 py-1 hover:bg-zinc-700 rounded text-xs truncate"
                        >
                          {child.id}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={() => copyPrompt(node.type)}
                    className={cn(
                      'w-full flex items-center gap-2 px-3 py-2 rounded text-sm',
                      copiedPrompt === node.type 
                        ? 'bg-green-600 text-white' 
                        : 'bg-purple-600 hover:bg-purple-700'
                    )}
                  >
                    {copiedPrompt === node.type ? (
                      <>
                        <Check size={14} />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Sparkles size={14} />
                        Copy AI Prompt
                      </>
                    )}
                  </button>
                  <button
                    className="w-full flex items-center gap-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded text-sm"
                  >
                    <Plus size={14} />
                    Create Manually
                  </button>
                  <button
                    className="w-full flex items-center gap-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded text-sm"
                  >
                    <Link2 size={14} />
                    Link Existing
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center h-full', className)}>
        <Loader2 className="animate-spin text-zinc-500" size={32} />
      </div>
    )
  }

  if (!selectedDiscId) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-full p-8', className)}>
        <CloudRain size={64} className="text-blue-400 mb-4" />
        <h2 className="text-xl font-bold mb-2">No Umbrella DISC Selected</h2>
        <p className="text-zinc-400 text-center max-w-md">
          Select or create a Discussion to start mapping your artifact chain.
        </p>
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <CloudRain className="text-blue-400" size={24} />
          <div>
            <h2 className="font-semibold">Workflow Builder</h2>
            <div className="text-sm text-zinc-400">
              Building from: {selectedDisc?.id || selectedDiscId}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom controls */}
          <button
            onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}
            className="p-2 hover:bg-zinc-800 rounded"
            title="Zoom out"
          >
            <ZoomOut size={16} />
          </button>
          <span className="text-xs text-zinc-500 w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom(z => Math.min(2, z + 0.1))}
            className="p-2 hover:bg-zinc-800 rounded"
            title="Zoom in"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={() => setZoom(1)}
            className="p-2 hover:bg-zinc-800 rounded"
            title="Reset zoom"
          >
            <Maximize2 size={16} />
          </button>

          <div className="w-px h-6 bg-zinc-700 mx-2" />

          <button
            onClick={onReset}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded"
          >
            <RefreshCw size={14} />
            Reset
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div 
        className="flex-1 overflow-auto p-8"
        onClick={() => setSelectedNode(null)}
      >
        <div 
          className="min-w-max"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
          onClick={e => e.stopPropagation()}
        >
          {/* Horizontal flow layout */}
          <div className="flex items-start gap-8">
            {artifactTree.map((node, index) => (
              <div key={node.id} className="flex items-center">
                {renderNode(node)}
                
                {/* Arrow to next */}
                {index < artifactTree.length - 1 && (
                  <div className="flex items-center px-4">
                    <ChevronRight size={24} className="text-zinc-600" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="mt-12 flex items-center gap-6 text-xs text-zinc-500">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                <Check size={8} className="text-white" />
              </div>
              Completed
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-zinc-700 flex items-center justify-center">
                <AlertCircle size={8} className="text-zinc-400" />
              </div>
              Needs Creation
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-zinc-800 border border-zinc-600 flex items-center justify-center">
                <span className="text-[6px]">opt</span>
              </div>
              Optional
            </div>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="px-6 py-3 border-t border-zinc-800 bg-zinc-900">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-zinc-500">Workflow Progress</span>
          <span className="text-xs text-zinc-400">
            {artifactTree.filter(n => n.status === 'completed').length} / {artifactTree.filter(n => TYPE_CONFIG[n.type].required).length} required
          </span>
        </div>
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all"
            style={{ 
              width: `${(artifactTree.filter(n => n.status === 'completed').length / artifactTree.filter(n => TYPE_CONFIG[n.type].required).length) * 100}%` 
            }}
          />
        </div>
      </div>
    </div>
  )
}
