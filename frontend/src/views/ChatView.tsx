import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Loader2, Trash2, Copy, Check, Plus, MessageSquare, ChevronLeft } from 'lucide-react'
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
}

const STORAGE_KEY = 'ai-chat-conversations'
const ACTIVE_CONV_KEY = 'ai-chat-active-conversation'

export default function ChatView() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [models, setModels] = useState<Model[]>([])
  const [selectedModel, setSelectedModel] = useState('grok-4-fast-reasoning')
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load conversations from localStorage on mount
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

  // Save active conversation ID
  useEffect(() => {
    if (activeConversationId) {
      localStorage.setItem(ACTIVE_CONV_KEY, activeConversationId)
    }
  }, [activeConversationId])

  // Sync messages with active conversation
  useEffect(() => {
    if (activeConversationId) {
      const conv = conversations.find(c => c.id === activeConversationId)
      if (conv) setMessages(conv.messages)
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
    }
    setConversations(prev => [newConv, ...prev])
    setActiveConversationId(newConv.id)
    setMessages([])
  }, [])

  const updateConversation = useCallback((convId: string, newMessages: Message[]) => {
    setConversations(prev => prev.map(c => {
      if (c.id === convId) {
        // Auto-generate title from first user message
        const title = c.title === 'New Chat' && newMessages.length > 0
          ? newMessages.find(m => m.role === 'user')?.content.slice(0, 40) + '...' || c.title
          : c.title
        return { ...c, messages: newMessages, updatedAt: new Date(), title }
      }
      return c
    }))
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

  // Create initial conversation if none exist
  useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation()
    } else if (!activeConversationId && conversations.length > 0) {
      setActiveConversationId(conversations[0].id)
    }
  }, [conversations.length, activeConversationId, createNewConversation])

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
                    ? { ...m, content: `Error: ${parsed.error}`, isStreaming: false }
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
        if (activeConversationId) {
          updateConversation(activeConversationId, updated)
        }
        return updated
      })
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => {
        const updated = prev.map(m =>
          m.id === assistantMessage.id
            ? { ...m, content: `Error: ${error}`, isStreaming: false }
            : m
        )
        if (activeConversationId) {
          updateConversation(activeConversationId, updated)
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
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
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              {models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
            <button
              onClick={clearMessages}
              className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
              title="Clear chat"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </header>

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
                    {message.role === 'assistant' ? (
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
