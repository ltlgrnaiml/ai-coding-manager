import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Send, Bot, User, Loader2, Trash2, Copy, Check, Plus, MessageSquare, ChevronLeft, AlertCircle, ChevronDown, RefreshCw, BarChart3, X, Wrench, Zap, Eye, Globe, Code, Brain, DollarSign, Settings2, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isStreaming?: boolean
  model?: string
  provider?: string
  error?: {
    message: string
    details?: string
    status?: number
  }
}

interface ModelPricing {
  input_per_mtok: number
  output_per_mtok: number
  cache_read_per_mtok?: number
  batch_input_per_mtok?: number
}

interface ModelCapabilities {
  streaming: boolean
  tools: boolean
  vision: boolean
  audio: boolean
  video: boolean
  code_execution: boolean
  web_search: boolean
  caching: boolean
  batch: boolean
  reasoning: boolean
  json_mode: boolean
  mcp: boolean
}

interface Model {
  id: string
  name: string
  provider_id: string
  family?: string
  category?: string
  context_window: number
  pricing: ModelPricing
  capabilities: ModelCapabilities
}

interface ToolInfo {
  id: string
  name: string
  display_name: string
  description?: string
  price_per_use?: number
  price_per_1k?: number
  token_overhead: number
}

interface ModelAutocomplete {
  model_id: string
  model_name: string
  provider_id: string
  capabilities: ModelCapabilities
  enabled_capabilities: string[]
  tools: ToolInfo[]
  supports_tools: boolean
  supports_mcp: boolean
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  model?: string  // Current model for this conversation
}

interface ModelStats {
  modelId: string
  messageCount: number
  tokenEstimate: number
  errorCount: number
  lastUsed: Date
}

interface ChatStats {
  totalMessages: number
  modelUsage: Record<string, ModelStats>
  lastUsedModel: string
}

const STORAGE_KEY = 'ai-chat-conversations'
const ACTIVE_CONV_KEY = 'ai-chat-active-conversation'
const STATS_KEY = 'ai-chat-stats'
const LAST_MODEL_KEY = 'ai-chat-last-model'
const ENABLED_TOOLS_KEY = 'ai-chat-enabled-tools'
const DEFAULT_MODEL = 'grok-4-fast-reasoning'

const CAPABILITY_ICONS: Record<string, { icon: typeof Zap; color: string; label: string }> = {
  tools: { icon: Wrench, color: 'text-blue-400', label: 'Tools' },
  vision: { icon: Eye, color: 'text-purple-400', label: 'Vision' },
  web_search: { icon: Globe, color: 'text-green-400', label: 'Web' },
  code_execution: { icon: Code, color: 'text-yellow-400', label: 'Code' },
  reasoning: { icon: Brain, color: 'text-pink-400', label: 'Reasoning' },
  mcp: { icon: Sparkles, color: 'text-cyan-400', label: 'MCP' },
}

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: 'bg-orange-900/30 text-orange-300 border-orange-700',
  google: 'bg-blue-900/30 text-blue-300 border-blue-700',
  xai: 'bg-purple-900/30 text-purple-300 border-purple-700',
  openai: 'bg-green-900/30 text-green-300 border-green-700',
  local: 'bg-gray-900/30 text-gray-300 border-gray-700',
}

export default function ChatView() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [models, setModels] = useState<Model[]>([])
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const [expandedErrors, setExpandedErrors] = useState<Set<string>>(new Set())
  const [stats, setStats] = useState<ChatStats>({
    totalMessages: 0,
    modelUsage: {},
    lastUsedModel: DEFAULT_MODEL,
  })
  const [showStats, setShowStats] = useState(false)
  const [showToolPanel, setShowToolPanel] = useState(false)
  const [modelAutocomplete, setModelAutocomplete] = useState<ModelAutocomplete | null>(null)
  const [enabledTools, setEnabledTools] = useState<string[]>([])
  const [estimatedCost, setEstimatedCost] = useState<{ cost: number; breakdown: Record<string, number> } | null>(null)
  const [isLoadingModels, setIsLoadingModels] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load conversations and stats from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Conversation[]
        setConversations(parsed.map(c => ({
          ...c,
          createdAt: new Date(c.createdAt),
          updatedAt: new Date(c.updatedAt),
          messages: c.messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) }))
        })))
      }
      const activeId = localStorage.getItem(ACTIVE_CONV_KEY)
      if (activeId) setActiveConversationId(activeId)
      
      // Load stats
      const storedStats = localStorage.getItem(STATS_KEY)
      if (storedStats) {
        const parsedStats = JSON.parse(storedStats) as ChatStats
        // Convert date strings back to Date objects
        Object.values(parsedStats.modelUsage).forEach(s => {
          s.lastUsed = new Date(s.lastUsed)
        })
        setStats(parsedStats)
      }
      
      // Load last used model as default for new chats
      const lastModel = localStorage.getItem(LAST_MODEL_KEY)
      if (lastModel) {
        setSelectedModel(lastModel)
      }
    } catch (e) {
      console.error('Failed to load conversations:', e)
    }
  }, [])

  // Save conversations to localStorage when they change
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
    }
  }, [conversations])

  // Save stats to localStorage when they change
  useEffect(() => {
    localStorage.setItem(STATS_KEY, JSON.stringify(stats))
  }, [stats])

  // Save last used model
  useEffect(() => {
    localStorage.setItem(LAST_MODEL_KEY, selectedModel)
  }, [selectedModel])

  // Save active conversation ID
  useEffect(() => {
    if (activeConversationId) {
      localStorage.setItem(ACTIVE_CONV_KEY, activeConversationId)
    }
  }, [activeConversationId])

  // Sync messages and model with active conversation
  useEffect(() => {
    if (activeConversationId) {
      const conv = conversations.find(c => c.id === activeConversationId)
      if (conv) {
        setMessages(conv.messages)
        // Restore the model for this conversation, or use last used model
        if (conv.model) {
          setSelectedModel(conv.model)
        }
      }
    } else {
      setMessages([])
    }
  }, [activeConversationId, conversations])

  const generateId = () => Math.random().toString(36).substr(2, 9)

  const createNewConversation = useCallback(() => {
    const newConv: Conversation = {
      id: generateId(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      model: selectedModel,  // New chats inherit current model
    }
    setConversations(prev => [newConv, ...prev])
    setActiveConversationId(newConv.id)
    setMessages([])
  }, [selectedModel])

  const updateConversation = useCallback((convId: string, newMessages: Message[], model?: string) => {
    setConversations(prev => prev.map(c => {
      if (c.id === convId) {
        // Auto-generate title from first user message
        const title = c.title === 'New Chat' && newMessages.length > 0
          ? newMessages.find(m => m.role === 'user')?.content.slice(0, 40) + '...' || c.title
          : c.title
        return { ...c, messages: newMessages, updatedAt: new Date(), title, model: model || c.model }
      }
      return c
    }))
  }, [])

  // Update model for current conversation when changed
  const handleModelChange = useCallback((newModel: string) => {
    setSelectedModel(newModel)
    // Update the current conversation's model
    if (activeConversationId) {
      setConversations(prev => prev.map(c => 
        c.id === activeConversationId ? { ...c, model: newModel } : c
      ))
    }
    // Update stats
    setStats(prev => ({
      ...prev,
      lastUsedModel: newModel,
    }))
  }, [activeConversationId])

  // Track model usage statistics
  const trackModelUsage = useCallback((modelId: string, contentLength: number, isError: boolean = false) => {
    setStats(prev => {
      const existing = prev.modelUsage[modelId] || {
        modelId,
        messageCount: 0,
        tokenEstimate: 0,
        errorCount: 0,
        lastUsed: new Date(),
      }
      return {
        ...prev,
        totalMessages: prev.totalMessages + 1,
        lastUsedModel: modelId,
        modelUsage: {
          ...prev.modelUsage,
          [modelId]: {
            ...existing,
            messageCount: existing.messageCount + 1,
            tokenEstimate: existing.tokenEstimate + Math.ceil(contentLength / 4),
            errorCount: existing.errorCount + (isError ? 1 : 0),
            lastUsed: new Date(),
          }
        }
      }
    })
  }, [])

  const deleteConversation = useCallback((convId: string) => {
    setConversations(prev => prev.filter(c => c.id !== convId))
    if (activeConversationId === convId) {
      setActiveConversationId(null)
      setMessages([])
    }
  }, [activeConversationId])

  // Load models from registry on mount
  useEffect(() => {
    setIsLoadingModels(true)
    fetch('/api/models')
      .then(res => res.json())
      .then((data: Model[]) => {
        setModels(data)
        setIsLoadingModels(false)
      })
      .catch(err => {
        console.error('Failed to load models from registry:', err)
        // Fallback to old endpoint
        fetch('/api/chat/models')
          .then(res => res.json())
          .then(data => setModels(data.models?.map((m: { id: string; name: string; category: string }) => ({
            ...m,
            provider_id: 'unknown',
            context_window: 128000,
            pricing: { input_per_mtok: 0, output_per_mtok: 0 },
            capabilities: { streaming: true, tools: false, vision: false, audio: false, video: false, code_execution: false, web_search: false, caching: false, batch: false, reasoning: false, json_mode: false, mcp: false }
          })) || []))
          .catch(console.error)
          .finally(() => setIsLoadingModels(false))
      })
  }, [])

  // Fetch autocomplete data when model changes
  useEffect(() => {
    if (!selectedModel) return
    
    fetch(`/api/models/${selectedModel}/autocomplete`)
      .then(res => res.json())
      .then((data: ModelAutocomplete) => {
        setModelAutocomplete(data)
        // Reset enabled tools if they're no longer available
        setEnabledTools(prev => prev.filter(t => data.tools.some(tool => tool.name === t)))
      })
      .catch(err => {
        console.error('Failed to load model autocomplete:', err)
        setModelAutocomplete(null)
      })
  }, [selectedModel])

  // Load saved enabled tools from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(ENABLED_TOOLS_KEY)
      if (saved) {
        setEnabledTools(JSON.parse(saved))
      }
    } catch (e) {
      console.error('Failed to load enabled tools:', e)
    }
  }, [])

  // Save enabled tools to localStorage
  useEffect(() => {
    localStorage.setItem(ENABLED_TOOLS_KEY, JSON.stringify(enabledTools))
  }, [enabledTools])

  // Estimate cost when input or tools change
  useEffect(() => {
    if (!selectedModel || !input.trim()) {
      setEstimatedCost(null)
      return
    }

    const estimateTokens = Math.ceil(input.length / 4) + messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 4), 0)
    const outputEstimate = 500 // Rough estimate for output

    fetch('/api/models/estimate-cost', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: selectedModel,
        input_tokens: estimateTokens,
        output_tokens: outputEstimate,
        tools_used: enabledTools,
        tool_calls: enabledTools.length > 0 ? 1 : 0,
      }),
    })
      .then(res => res.json())
      .then(data => setEstimatedCost({ cost: data.estimated_cost_usd, breakdown: data.breakdown }))
      .catch(() => setEstimatedCost(null))
  }, [selectedModel, input, messages.length, enabledTools])

  // Get current model info
  const currentModel = useMemo(() => models.find(m => m.id === selectedModel), [models, selectedModel])

  // Toggle tool enabled/disabled
  const toggleTool = useCallback((toolName: string) => {
    setEnabledTools(prev => 
      prev.includes(toolName) 
        ? prev.filter(t => t !== toolName)
        : [...prev, toolName]
    )
  }, [])

  // Create initial conversation only if none exist AND we've finished loading
  const [initialized, setInitialized] = useState(false)
  
  useEffect(() => {
    // Wait for localStorage to be loaded before creating new conversation
    if (initialized) return
    
    const stored = localStorage.getItem(STORAGE_KEY)
    const hasStoredConversations = stored && JSON.parse(stored).length > 0
    
    if (!hasStoredConversations && conversations.length === 0) {
      createNewConversation()
    } else if (!activeConversationId && conversations.length > 0) {
      // Restore last active conversation
      const storedActiveId = localStorage.getItem(ACTIVE_CONV_KEY)
      const validId = conversations.find(c => c.id === storedActiveId)?.id || conversations[0].id
      setActiveConversationId(validId)
    }
    
    setInitialized(true)
  }, [conversations.length, activeConversationId, createNewConversation, initialized])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`
    }
  }, [input])


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      model: selectedModel,
    }

    setMessages(prev => [...prev, userMessage, assistantMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Filter out empty messages and error messages before sending
      const validMessages = [...messages, userMessage]
        .filter(m => m.content && m.content.trim() && !m.error)
        .map(m => ({
          role: m.role,
          content: m.content,
        }))

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: validMessages,
          model: selectedModel,
          stream: true,
          tools: enabledTools.length > 0 ? enabledTools.map(name => ({ name })) : undefined,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API Error (${response.status}): ${errorText || response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                setMessages(prev => prev.map(m =>
                  m.id === assistantMessage.id
                    ? { 
                        ...m, 
                        content: m.content + parsed.content,
                        provider: parsed.provider || m.provider,
                        model: parsed.model || m.model
                      }
                    : m
                ))
              }
              if (parsed.error) {
                setMessages(prev => prev.map(m =>
                  m.id === assistantMessage.id
                    ? { 
                        ...m, 
                        content: '', 
                        isStreaming: false,
                        error: {
                          message: parsed.error,
                          details: `Model: ${parsed.model || 'unknown'}\nProvider: ${parsed.provider || 'unknown'}\nTimestamp: ${new Date().toISOString()}`,
                        }
                      }
                    : m
                ))
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }

      // Mark streaming complete and save to conversation
      setMessages(prev => {
        const updated = prev.map(m =>
          m.id === assistantMessage.id
            ? { ...m, isStreaming: false }
            : m
        )
        // Track successful model usage
        const finalMsg = updated.find(m => m.id === assistantMessage.id)
        if (finalMsg?.content) {
          trackModelUsage(selectedModel, finalMsg.content.length, false)
        }
        if (activeConversationId) {
          updateConversation(activeConversationId, updated, selectedModel)
        }
        return updated
      })
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      const errorDetails = error instanceof Error ? error.stack : JSON.stringify(error, null, 2)
      
      // Track error in stats
      trackModelUsage(selectedModel, 0, true)
      
      setMessages(prev => {
        const updated = prev.map(m =>
          m.id === assistantMessage.id
            ? { 
                ...m, 
                content: '', 
                isStreaming: false,
                error: {
                  message: errorMessage,
                  details: errorDetails,
                }
              }
            : m
        )
        if (activeConversationId) {
          updateConversation(activeConversationId, updated, selectedModel)
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  const toggleErrorExpanded = (messageId: string) => {
    setExpandedErrors(prev => {
      const next = new Set(prev)
      if (next.has(messageId)) {
        next.delete(messageId)
      } else {
        next.add(messageId)
      }
      return next
    })
  }

  const retryMessage = async (failedMessageId: string) => {
    // Find the user message before the failed assistant message
    const messageIndex = messages.findIndex(m => m.id === failedMessageId)
    if (messageIndex <= 0) return
    
    const userMessage = messages[messageIndex - 1]
    if (userMessage.role !== 'user') return
    
    // Remove the failed message and retry
    setMessages(prev => prev.filter(m => m.id !== failedMessageId))
    setInput(userMessage.content)
  }

  const copyErrorDetails = async (details: string, messageId: string) => {
    await navigator.clipboard.writeText(details)
    setCopiedId(messageId + '-error')
    setTimeout(() => setCopiedId(null), 2000)
  }

  const clearMessages = () => {
    if (activeConversationId) {
      updateConversation(activeConversationId, [])
    }
    setMessages([])
  }

  const copyMessage = async (content: string, id: string) => {
    await navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex-1 flex h-full">
      {/* Conversation Sidebar */}
      {showSidebar && (
        <aside className="w-64 border-r border-gray-800 flex flex-col bg-gray-900/50">
          <div className="p-3 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-300">Conversations</h2>
            <button
              onClick={createNewConversation}
              className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              title="New chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`group px-3 py-2 cursor-pointer hover:bg-gray-800 flex items-center gap-2 ${
                  activeConversationId === conv.id ? 'bg-gray-800' : ''
                }`}
                onClick={() => setActiveConversationId(conv.id)}
              >
                <MessageSquare className="w-4 h-4 text-gray-500 flex-shrink-0" />
                <span className="text-sm text-gray-300 truncate flex-1">{conv.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-red-400 transition-opacity"
                  title="Delete"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </aside>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
              title={showSidebar ? 'Hide sidebar' : 'Show sidebar'}
            >
              <ChevronLeft className={`w-5 h-5 transition-transform ${!showSidebar ? 'rotate-180' : ''}`} />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-white">AI Chat</h1>
              <p className="text-sm text-gray-400">Powered by xAI Grok + Gemini</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Model Selector with Provider Badge */}
            <div className="relative">
              <select
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                disabled={isLoadingModels}
                className="bg-gray-800 border border-gray-700 rounded-lg pl-3 pr-8 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 appearance-none min-w-[200px]"
              >
                {isLoadingModels ? (
                  <option>Loading models...</option>
                ) : (
                  Object.entries(
                    models.reduce((acc, model) => {
                      const provider = model.provider_id || 'other'
                      if (!acc[provider]) acc[provider] = []
                      acc[provider].push(model)
                      return acc
                    }, {} as Record<string, Model[]>)
                  ).map(([provider, providerModels]) => (
                    <optgroup key={provider} label={provider.charAt(0).toUpperCase() + provider.slice(1)}>
                      {providerModels.map(model => (
                        <option key={model.id} value={model.id}>
                          {model.name} {model.category ? `(${model.category})` : ''}
                        </option>
                      ))}
                    </optgroup>
                  ))
                )}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            </div>

            {/* Provider & Pricing Badge */}
            {currentModel && (
              <div className={`flex items-center gap-2 px-2 py-1 rounded-lg border text-xs ${PROVIDER_COLORS[currentModel.provider_id] || PROVIDER_COLORS.local}`}>
                <span className="font-medium">{currentModel.provider_id}</span>
                <span className="opacity-60">|</span>
                <DollarSign className="w-3 h-3" />
                <span>${currentModel.pricing.input_per_mtok}/{currentModel.pricing.output_per_mtok}</span>
              </div>
            )}

            {/* Capability Badges */}
            {currentModel && (
              <div className="flex items-center gap-1">
                {Object.entries(CAPABILITY_ICONS).map(([key, { icon: Icon, color, label }]) => {
                  const isEnabled = currentModel.capabilities[key as keyof ModelCapabilities]
                  if (!isEnabled) return null
                  return (
                    <div
                      key={key}
                      className={`p-1.5 rounded ${color} bg-gray-800/50`}
                      title={label}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                  )
                })}
              </div>
            )}

            {/* Tool Panel Toggle */}
            {modelAutocomplete?.supports_tools && (
              <button
                onClick={() => setShowToolPanel(!showToolPanel)}
                className={`p-2 rounded-lg transition-colors flex items-center gap-1 ${
                  showToolPanel || enabledTools.length > 0
                    ? 'text-cyan-400 bg-gray-800' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`}
                title="Configure tools"
              >
                <Settings2 className="w-4 h-4" />
                {enabledTools.length > 0 && (
                  <span className="text-xs bg-cyan-600 text-white px-1.5 py-0.5 rounded-full">
                    {enabledTools.length}
                  </span>
                )}
              </button>
            )}

            <button
              onClick={() => setShowStats(!showStats)}
              className={`p-2 rounded-lg transition-colors ${showStats ? 'text-cyan-400 bg-gray-800' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'}`}
              title="Model statistics"
            >
              <BarChart3 className="w-5 h-5" />
            </button>
            <button
              onClick={clearMessages}
              className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
              title="Clear chat"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Stats Panel */}
        {showStats && (
          <div className="border-b border-gray-800 bg-gray-900/50 px-6 py-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-300">Model Usage Statistics</h3>
              <button
                onClick={() => setShowStats(false)}
                className="p-1 text-gray-500 hover:text-gray-300 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-2xl font-bold text-cyan-400">{stats.totalMessages}</div>
                <div className="text-xs text-gray-500">Total Messages</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-2xl font-bold text-green-400">{Object.keys(stats.modelUsage).length}</div>
                <div className="text-xs text-gray-500">Models Used</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-2xl font-bold text-purple-400">
                  {Object.values(stats.modelUsage).reduce((acc, s) => acc + s.tokenEstimate, 0).toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">Est. Tokens</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-2xl font-bold text-red-400">
                  {Object.values(stats.modelUsage).reduce((acc, s) => acc + s.errorCount, 0)}
                </div>
                <div className="text-xs text-gray-500">Errors</div>
              </div>
            </div>
            {Object.keys(stats.modelUsage).length > 0 && (
              <div className="space-y-2">
                <div className="text-xs text-gray-500 mb-2">Usage by Model</div>
                {Object.values(stats.modelUsage)
                  .sort((a, b) => b.messageCount - a.messageCount)
                  .map(modelStat => {
                    const percentage = stats.totalMessages > 0 
                      ? Math.round((modelStat.messageCount / stats.totalMessages) * 100) 
                      : 0
                    return (
                      <div key={modelStat.modelId} className="bg-gray-800 rounded-lg p-2">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-300 truncate">{modelStat.modelId}</span>
                          <span className="text-gray-500">{modelStat.messageCount} msgs ({percentage}%)</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div 
                            className="bg-cyan-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>~{modelStat.tokenEstimate.toLocaleString()} tokens</span>
                          {modelStat.errorCount > 0 && (
                            <span className="text-red-400">{modelStat.errorCount} errors</span>
                          )}
                        </div>
                      </div>
                    )
                  })}
              </div>
            )}
          </div>
        )}

        {/* Tool Panel */}
        {showToolPanel && modelAutocomplete && (
          <div className="border-b border-gray-800 bg-gray-900/50 px-6 py-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-medium text-gray-300">Available Tools for {modelAutocomplete.model_name}</h3>
              </div>
              <button
                onClick={() => setShowToolPanel(false)}
                className="p-1 text-gray-500 hover:text-gray-300 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            {modelAutocomplete.tools.length === 0 ? (
              <p className="text-sm text-gray-500">No tools available for this model.</p>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {modelAutocomplete.tools.map(tool => {
                  const isEnabled = enabledTools.includes(tool.name)
                  return (
                    <button
                      key={tool.id}
                      onClick={() => toggleTool(tool.name)}
                      className={`p-3 rounded-lg border transition-all text-left ${
                        isEnabled
                          ? 'bg-cyan-900/30 border-cyan-700 text-cyan-300'
                          : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm">{tool.display_name}</span>
                        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                          isEnabled ? 'bg-cyan-500 border-cyan-500' : 'border-gray-600'
                        }`}>
                          {isEnabled && <Check className="w-3 h-3 text-white" />}
                        </div>
                      </div>
                      {tool.description && (
                        <p className="text-xs text-gray-500 line-clamp-2">{tool.description}</p>
                      )}
                      <div className="flex items-center gap-2 mt-2 text-xs">
                        {tool.price_per_1k && (
                          <span className="text-yellow-400">${tool.price_per_1k}/1K</span>
                        )}
                        {tool.price_per_use && (
                          <span className="text-yellow-400">${tool.price_per_use}/use</span>
                        )}
                        {tool.token_overhead > 0 && (
                          <span className="text-gray-500">+{tool.token_overhead} tokens</span>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {/* Enabled Tools Summary */}
            {enabledTools.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Enabled:</span>
                  <div className="flex gap-1">
                    {enabledTools.map(name => (
                      <span key={name} className="px-2 py-0.5 bg-cyan-900/50 text-cyan-300 rounded text-xs">
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => setEnabledTools([])}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  Clear all
                </button>
              </div>
            )}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <Bot className="w-16 h-16 mb-4 text-gray-600" />
              <p className="text-lg">Start a conversation</p>
              <p className="text-sm">Ask anything - code, architecture, debugging...</p>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`flex gap-4 message-enter ${
                    message.role === 'user' ? 'justify-end' : ''
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-cyan-600 text-white'
                        : 'bg-gray-800 text-gray-100'
                    }`}
                  >
                    {message.error ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-red-400">
                          <AlertCircle className="w-4 h-4" />
                          <span className="font-medium">Failed to send</span>
                        </div>
                        <p className="text-sm text-red-300">{message.error.message}</p>
                        
                        <div className="flex items-center gap-2 mt-2">
                          <button
                            onClick={() => retryMessage(message.id)}
                            className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                          >
                            <RefreshCw className="w-3 h-3" /> Retry
                          </button>
                          <button
                            onClick={() => toggleErrorExpanded(message.id)}
                            className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                          >
                            <ChevronDown className={`w-3 h-3 transition-transform ${expandedErrors.has(message.id) ? 'rotate-180' : ''}`} />
                            {expandedErrors.has(message.id) ? 'Hide' : 'Show'} Details
                          </button>
                        </div>
                        
                        {expandedErrors.has(message.id) && message.error.details && (
                          <div className="mt-2 p-2 bg-gray-900 rounded text-xs font-mono text-gray-400 overflow-x-auto">
                            <div className="flex justify-between items-start mb-2">
                              <span className="text-gray-500">Debug Info:</span>
                              <button
                                onClick={() => copyErrorDetails(message.error!.details!, message.id)}
                                className="flex items-center gap-1 text-gray-500 hover:text-gray-300"
                              >
                                {copiedId === message.id + '-error' ? (
                                  <><Check className="w-3 h-3" /> Copied</>
                                ) : (
                                  <><Copy className="w-3 h-3" /> Copy</>
                                )}
                              </button>
                            </div>
                            <pre className="whitespace-pre-wrap break-all">{message.error.details}</pre>
                          </div>
                        )}
                      </div>
                    ) : message.role === 'assistant' ? (
                      <div className={`prose prose-invert max-w-none ${message.isStreaming ? 'streaming-cursor' : ''}`}>
                        <ReactMarkdown
                          components={{
                            code({ className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '')
                              const isInline = !match
                              return isInline ? (
                                <code className="bg-gray-900 px-1 py-0.5 rounded text-cyan-300" {...props}>
                                  {children}
                                </code>
                              ) : (
                                <SyntaxHighlighter
                                  style={oneDark}
                                  language={match[1]}
                                  PreTag="div"
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              )
                            },
                          }}
                        >
                          {message.content || ' '}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                    {message.role === 'assistant' && !message.isStreaming && message.content && (
                      <button
                        onClick={() => copyMessage(message.content, message.id)}
                        className="mt-2 text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1"
                      >
                        {copiedId === message.id ? (
                          <>
                            <Check className="w-3 h-3" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" /> Copy
                          </>
                        )}
                      </button>
                    )}
                    
                    {/* Message metadata */}
                    <div className="mt-2 text-xs text-gray-500 flex items-center gap-2">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      {message.model && (
                        <>
                          <span>•</span>
                          <span className={`px-1.5 py-0.5 rounded text-xs ${
                            message.provider === 'google' 
                              ? 'bg-blue-900/30 text-blue-300' 
                              : 'bg-purple-900/30 text-purple-300'
                          }`}>
                            {message.model}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-gray-300" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 px-6 py-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            {/* Input Status Bar */}
            <div className="flex items-center justify-between mb-2 px-1">
              <div className="flex items-center gap-3 text-xs">
                {/* Enabled Tools Indicator */}
                {enabledTools.length > 0 && (
                  <div className="flex items-center gap-1 text-cyan-400">
                    <Wrench className="w-3 h-3" />
                    <span>{enabledTools.length} tool{enabledTools.length > 1 ? 's' : ''} active</span>
                  </div>
                )}
                
                {/* Model Context Info */}
                {currentModel && (
                  <div className="text-gray-500">
                    <span className="text-gray-400">{currentModel.name}</span>
                    <span className="mx-1">•</span>
                    <span>{(currentModel.context_window / 1000).toFixed(0)}K context</span>
                  </div>
                )}
              </div>

              {/* Cost Estimation */}
              {estimatedCost && estimatedCost.cost > 0 && (
                <div className="flex items-center gap-1 text-xs text-yellow-400" title="Estimated cost for this request">
                  <DollarSign className="w-3 h-3" />
                  <span>~${estimatedCost.cost.toFixed(4)}</span>
                </div>
              )}
            </div>

            <div className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={enabledTools.length > 0 
                  ? `Type your message... (${enabledTools.join(', ')} enabled)`
                  : "Type your message... (Shift+Enter for newline)"
                }
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 pr-12 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 resize-none"
                rows={1}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-2 bottom-2 p-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Send className="w-5 h-5 text-white" />
                )}
              </button>
            </div>

            {/* Keyboard Shortcuts Hint */}
            <div className="flex items-center justify-center gap-4 mt-2 text-xs text-gray-600">
              <span><kbd className="px-1 py-0.5 bg-gray-800 rounded text-gray-500">Enter</kbd> to send</span>
              <span><kbd className="px-1 py-0.5 bg-gray-800 rounded text-gray-500">Shift+Enter</kbd> for newline</span>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
