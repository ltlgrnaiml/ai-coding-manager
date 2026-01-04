import { ChevronRight, ChevronDown, Plus, FileText, FileJson, ListTodo, Code2, MessageSquare } from 'lucide-react'
import type { ArtifactTreeNode, ArtifactType } from './types'
import { cn } from '../../lib/utils'

interface ArtifactTreeProps {
  nodes: ArtifactTreeNode[]
  selectedId?: string
  expandedIds: Set<string>
  onSelect: (node: ArtifactTreeNode) => void
  onCreate: (parentId: string, type: ArtifactType) => void
  onToggleExpand: (nodeId: string) => void
}

// Icon mapping for artifact types
const ARTIFACT_ICONS: Record<string, React.ReactNode> = {
  discussion: <MessageSquare size={16} className="text-purple-400" />,
  adr: <FileJson size={16} className="text-blue-400" />,
  spec: <FileText size={16} className="text-green-400" />,
  plan: <ListTodo size={16} className="text-amber-400" />,
  contract: <Code2 size={16} className="text-pink-400" />,
  placeholder: <Plus size={16} className="text-zinc-500" />,
}

export function ArtifactTree({
  nodes,
  selectedId,
  expandedIds,
  onSelect,
  onCreate,
  onToggleExpand
}: ArtifactTreeProps) {
  return (
    <div className="space-y-1">
      {nodes.map(node => (
        <TreeNode
          key={node.id}
          node={node}
          selectedId={selectedId}
          expandedIds={expandedIds}
          onSelect={onSelect}
          onCreate={onCreate}
          onToggleExpand={onToggleExpand}
        />
      ))}
    </div>
  )
}

interface TreeNodeProps {
  node: ArtifactTreeNode
  selectedId?: string
  expandedIds: Set<string>
  onSelect: (node: ArtifactTreeNode) => void
  onCreate: (parentId: string, type: ArtifactType) => void
  onToggleExpand: (nodeId: string) => void
}

function TreeNode({
  node,
  selectedId,
  expandedIds,
  onSelect,
  onCreate,
  onToggleExpand
}: TreeNodeProps) {
  const isExpanded = expandedIds.has(node.id)
  const isSelected = node.id === selectedId
  const hasChildren = node.children && node.children.length > 0
  const isPlaceholder = node.type === 'placeholder'
  const isMissing = node.status === 'missing'
  
  return (
    <div>
      {/* Node row */}
      <div
        className={cn(
          'flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors',
          isSelected ? 'bg-blue-600/20 text-blue-300' : 'hover:bg-zinc-800',
          isPlaceholder && 'opacity-60'
        )}
        style={{ paddingLeft: `${node.depth * 20 + 8}px` }}
        onClick={() => !isPlaceholder && onSelect(node)}
      >
        {/* Expand/collapse chevron */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onToggleExpand(node.id)
            }}
            className="p-0.5 hover:bg-zinc-700 rounded"
          >
            {isExpanded ? (
              <ChevronDown size={14} className="text-zinc-500" />
            ) : (
              <ChevronRight size={14} className="text-zinc-500" />
            )}
          </button>
        ) : (
          <div className="w-5" /> // Spacer for alignment
        )}
        
        {/* Icon */}
        <span className="flex-shrink-0">
          {node.isUmbrella ? '☂️' : (ARTIFACT_ICONS[node.type] || ARTIFACT_ICONS.placeholder)}
        </span>
        
        {/* Title */}
        <span className={cn(
          'flex-1 text-sm',
          isMissing && 'text-zinc-500'
        )}>
          {node.title}
        </span>
        
        {/* Status indicator */}
        {node.status === 'exists' && !isPlaceholder && (
          <span className="text-green-500 text-xs">✓</span>
        )}
        {node.status === 'in_progress' && (
          <span className="text-yellow-500 text-xs">⏳</span>
        )}
        
        {/* Create button for missing nodes */}
        {isMissing && !isPlaceholder && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              // Determine type from context
              const artifactType = node.type as ArtifactType
              onCreate(node.parentId || '', artifactType)
            }}
            className="px-2 py-0.5 text-xs bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            +Create
          </button>
        )}
      </div>
      
      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              selectedId={selectedId}
              expandedIds={expandedIds}
              onSelect={onSelect}
              onCreate={onCreate}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </div>
      )}
    </div>
  )
}
