import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Loader2, Trash2, Copy, Check, Plus, MessageSquare, ChevronLeft, AlertCircle, ChevronDown, RefreshCw, BarChart3, X } from 'lucide-react'
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

interface Model {
  id: string
  name: string
  category: string
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
const DEFAULT_MODEL = 'grok-4-fast-reasoning'

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

  // Load models on mount
  useEffect(() => {
    fetch('/api/chat/models')
      .then(res => res.json())
      .then(data => setModels(data.models))
      .catch(console.error)
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
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content,
          })),
          model: selectedModel,
          stream: true,
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
          <div className="flex items-center gap-4">
            <select
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              {models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
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
            <div className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message... (Shift+Enter for newline)"
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
          </form>
        </div>
      </div>
    </div>
  )
}
