import { useState, useEffect } from 'react'
import { Copy, Send, FileText, Sparkles } from 'lucide-react'
import type { ArtifactType } from './types'
import { cn } from '../../lib/utils'

interface PromptGeneratorProps {
  targetType: ArtifactType
  parentContext: {
    title: string
    path: string
    content: string
    openQuestions?: string[]
  }
  onCopy: () => void
  onSendToChat?: () => void
  className?: string
}

export function PromptGenerator({
  targetType,
  parentContext,
  onCopy,
  onSendToChat,
  className
}: PromptGeneratorProps) {
  const [prompt, setPrompt] = useState('')
  const [copied, setCopied] = useState(false)
  
  useEffect(() => {
    // Generate prompt from template
    generatePrompt()
  }, [targetType, parentContext])
  
  const generatePrompt = () => {
    // Template variables
    const vars = {
      artifact_type: targetType.toUpperCase(),
      number: 'NNNN', // Would be generated from backend
      title: `[Generated from ${parentContext.title}]`,
      parent_title: parentContext.title,
      parent_file_path: parentContext.path,
      parent_context: parentContext.content.slice(0, 500) + '...',
      key_questions: parentContext.openQuestions?.join('\n- ') || '[No specific questions]',
      date: new Date().toISOString().split('T')[0],
      parent_id: parentContext.path.match(/([A-Z]+-\d+)/)?.[1] || 'Unknown',
      filename: parentContext.title.replace(/[^a-zA-Z0-9]/g, '-')
    }
    
    // Basic template (would load from .prompts/ in real implementation)
    const template = `# Create ${vars.artifact_type}-${vars.number}: ${vars.title}

## Context
You are helping build the AI Coding Manager (AICM).

**Parent Document**: ${vars.parent_title}
**Parent Path**: ${vars.parent_file_path}

**Relevant Context**:
${vars.parent_context}

## Task
Create a new ${targetType.toUpperCase()} document that addresses:
${vars.key_questions}

## Requirements
1. Follow the standard ${targetType.toUpperCase()} format
2. Status should be "active"
3. Reference the parent document: ${vars.parent_id}
4. Include all required sections per the template

## File Location
Save to: .${getArtifactDir(targetType)}/${vars.artifact_type}-${vars.number}_${vars.filename}.md
`
    
    setPrompt(template)
  }
  
  const getArtifactDir = (type: ArtifactType): string => {
    const dirs: Record<ArtifactType, string> = {
      discussion: 'discussions',
      adr: 'adrs',
      spec: 'specs',
      plan: 'plans',
      contract: 'contracts',
      session: 'sessions',
      bug: 'bugs',
      guide: 'guides',
      chatlog: 'chat_logs',
      trace: 'traces'
    }
    return dirs[type] || type + 's'
  }
  
  const handleCopy = () => {
    navigator.clipboard.writeText(prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    onCopy()
  }
  
  return (
    <div className={cn('flex flex-col h-full bg-zinc-950', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-purple-400" />
          <h3 className="font-medium">Prompt Generator</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <FileText size={14} />
          <span>Target: {targetType.toUpperCase()}</span>
        </div>
      </div>
      
      {/* Prompt preview */}
      <div className="flex-1 overflow-y-auto p-4">
        <pre className="whitespace-pre-wrap font-mono text-xs text-zinc-300 bg-zinc-900 rounded-lg p-4">
          {prompt}
        </pre>
      </div>
      
      {/* Actions */}
      <div className="flex gap-2 p-4 border-t border-zinc-800">
        <button
          onClick={handleCopy}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors',
            copied 
              ? 'bg-green-600 text-white' 
              : 'bg-zinc-700 hover:bg-zinc-600'
          )}
        >
          <Copy size={16} />
          {copied ? 'Copied!' : 'Copy to Clipboard'}
        </button>
        
        {onSendToChat && (
          <button
            onClick={onSendToChat}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Send size={16} />
            Send to Chat
          </button>
        )}
      </div>
    </div>
  )
}
