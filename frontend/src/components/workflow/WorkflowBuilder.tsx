import { useState } from 'react'
import { RefreshCw, FileText, Copy, Send, Settings } from 'lucide-react'
import { ArtifactTree } from './ArtifactTree'
import { ActionPanel } from './ActionPanel'
import type { UmbrellaDisc, ArtifactTreeNode, ArtifactType } from './types'
import { cn } from '../../lib/utils'

interface WorkflowBuilderProps {
  umbrella: UmbrellaDisc
  tree: ArtifactTreeNode[]
  onNodeSelect: (node: ArtifactTreeNode) => void
  onCreateNode: (parentId: string, type: ArtifactType) => void
  onRefresh: () => void
  className?: string
}

export function WorkflowBuilder({
  umbrella,
  tree,
  onNodeSelect,
  onCreateNode,
  onRefresh,
  className
}: WorkflowBuilderProps) {
  const [selectedNode, setSelectedNode] = useState<ArtifactTreeNode | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set([umbrella.id]))
  
  const handleNodeSelect = (node: ArtifactTreeNode) => {
    setSelectedNode(node)
    onNodeSelect(node)
  }
  
  const handleToggleExpand = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId)
      } else {
        newSet.add(nodeId)
      }
      return newSet
    })
  }
  
  return (
    <div className={cn('flex flex-col h-full bg-zinc-950', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm text-zinc-500">WORKFLOW BUILDER</span>
            <span className="text-2xl">☂️</span>
          </div>
          <h2 className="text-xl font-semibold mt-1">{umbrella.title}</h2>
          {umbrella.splanId && (
            <div className="flex items-center gap-2 mt-1">
              <FileText size={14} className="text-blue-400" />
              <span className="text-sm text-blue-400">SPLAN: {umbrella.splanId}</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
            title="Refresh artifact tree"
          >
            <RefreshCw size={18} />
          </button>
          <button
            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings size={18} />
          </button>
        </div>
      </div>
      
      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Tree panel */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <div className="mb-4 px-3 py-2 bg-zinc-900 rounded-lg border border-zinc-800">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">ARTIFACT TREE</h3>
              <ArtifactTree
                nodes={tree}
                selectedId={selectedNode?.id}
                expandedIds={expandedNodes}
                onSelect={handleNodeSelect}
                onCreate={onCreateNode}
                onToggleExpand={handleToggleExpand}
              />
            </div>
          </div>
        </div>
        
        {/* Action panel */}
        <div className="w-96 border-l border-zinc-800 overflow-y-auto">
          <ActionPanel
            selectedNode={selectedNode}
            onGeneratePrompt={() => {
              if (selectedNode) {
                console.log('Generate prompt for:', selectedNode)
                // TODO: Implement prompt generation
              }
            }}
            onCopyPrompt={() => {
              if (selectedNode) {
                console.log('Copy prompt for:', selectedNode)
                // TODO: Implement copy prompt
              }
            }}
            onSendToChat={() => {
              if (selectedNode) {
                console.log('Send to chat:', selectedNode)
                // TODO: Implement send to chat
              }
            }}
          />
        </div>
      </div>
      
      {/* Status bar */}
      <div className="flex items-center justify-between px-6 py-2 border-t border-zinc-800 text-xs text-zinc-500">
        <div className="flex items-center gap-4">
          <span>{tree.length} artifacts</span>
          <span>Status: {umbrella.status}</span>
          <span>Created: {new Date(umbrella.createdAt).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Auto-discovery enabled</span>
        </div>
      </div>
    </div>
  )
}
