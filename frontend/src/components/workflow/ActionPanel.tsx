import { Sparkles, Copy, Send, Info, AlertCircle } from 'lucide-react'
import type { ArtifactTreeNode } from './types'
import { cn } from '../../lib/utils'

interface ActionPanelProps {
  selectedNode: ArtifactTreeNode | null
  onGeneratePrompt: () => void
  onCopyPrompt: () => void
  onSendToChat: () => void
  className?: string
}

export function ActionPanel({
  selectedNode,
  onGeneratePrompt,
  onCopyPrompt,
  onSendToChat,
  className
}: ActionPanelProps) {
  const isMissing = selectedNode?.status === 'missing'
  const isPlaceholder = selectedNode?.type === 'placeholder'
  
  return (
    <div className={cn('flex flex-col h-full', className)}>
      <div className="px-6 py-4 border-b border-zinc-800">
        <h3 className="text-sm font-medium text-zinc-400">ACTIONS</h3>
      </div>
      
      <div className="flex-1 p-6 space-y-4">
        {!selectedNode ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <AlertCircle size={32} className="text-zinc-600 mb-3" />
            <p className="text-sm text-zinc-500">
              Select a node from the tree to see available actions
            </p>
          </div>
        ) : (
          <>
            {/* Node info */}
            <div className="p-4 bg-zinc-900 rounded-lg space-y-2">
              <div className="flex items-center gap-2">
                <Info size={14} className="text-zinc-500" />
                <span className="text-xs text-zinc-500 uppercase">Selected Node</span>
              </div>
              <h4 className="font-medium">{selectedNode.title}</h4>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <span>Type: {selectedNode.type}</span>
                <span>•</span>
                <span>Status: {selectedNode.status}</span>
              </div>
              {selectedNode.filePath && (
                <div className="text-xs text-zinc-600 mt-2 font-mono truncate">
                  {selectedNode.filePath}
                </div>
              )}
            </div>
            
            {/* Actions for missing nodes */}
            {(isMissing || isPlaceholder) && (
              <div className="space-y-3">
                <p className="text-sm text-zinc-400">
                  This artifact doesn't exist yet. Generate a prompt to create it:
                </p>
                
                <button
                  onClick={onGeneratePrompt}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                >
                  <Sparkles size={18} />
                  Generate Prompt
                </button>
                
                <div className="flex gap-2">
                  <button
                    onClick={onCopyPrompt}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors text-sm"
                  >
                    <Copy size={16} />
                    Copy to Clipboard
                  </button>
                  
                  <button
                    onClick={onSendToChat}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm"
                  >
                    <Send size={16} />
                    Send to Chat
                  </button>
                </div>
              </div>
            )}
            
            {/* Actions for existing nodes */}
            {!isMissing && !isPlaceholder && (
              <div className="space-y-3">
                <p className="text-sm text-zinc-400">
                  This artifact already exists. You can:
                </p>
                
                <button
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors text-sm"
                >
                  View in Editor
                </button>
                
                <button
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors text-sm"
                >
                  Create Child Artifact
                </button>
              </div>
            )}
            
            {/* Tips */}
            <div className="mt-6 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
              <div className="flex items-start gap-2">
                <span className="text-xs">💡</span>
                <div className="text-xs text-zinc-500">
                  {isMissing || isPlaceholder ? (
                    <>
                      <strong>Tip:</strong> Generate a prompt for this artifact, then paste it into your AI assistant to create the content automatically.
                    </>
                  ) : (
                    <>
                      <strong>Tip:</strong> Double-click a node in the tree to open it in the editor.
                    </>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
      
      {/* Auto-discovery status */}
      <div className="px-6 py-3 border-t border-zinc-800">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-500">Auto-Discovery</span>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-500">Active</span>
          </div>
        </div>
      </div>
    </div>
  )
}
