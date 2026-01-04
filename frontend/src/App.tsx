import { useState } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { MessageSquare, GitBranch, Settings, Zap, BookOpen, Activity, CloudRain, FolderOpen } from 'lucide-react'
import ChatView from './views/ChatView'
import { ArtifactManagerPage } from './pages/ArtifactManagerPage'
import { WorkflowPage } from './pages/WorkflowPage'
import ResearchPage from './pages/ResearchPage'
import { P2REPage } from './pages/P2REPage'

function App() {
  const location = useLocation()
  const [apiKeyConfigured, setApiKeyConfigured] = useState<boolean | null>(null)

  // Check API health on mount
  useState(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setApiKeyConfigured(data.api_key_configured))
      .catch(() => setApiKeyConfigured(false))
  })

  const navItems = [
    { path: '/', icon: MessageSquare, label: 'Chat' },
    { path: '/workflow', icon: CloudRain, label: 'Workflow' },
    { path: '/artifacts', icon: FolderOpen, label: 'Artifacts' },
    { path: '/research', icon: BookOpen, label: 'Research' },
    { path: '/p2re', icon: Activity, label: 'P2RE Tools' },
  ]

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <aside className="w-16 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-4">
        {/* Logo */}
        <div className="mb-8">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 flex flex-col gap-2">
          {navItems.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path
            return (
              <Link
                key={path}
                to={path}
                className={`w-12 h-12 rounded-lg flex items-center justify-center transition-colors ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`}
                title={label}
              >
                <Icon className="w-5 h-5" />
              </Link>
            )
          })}
        </nav>

        {/* Settings */}
        <div className="mt-auto">
          <button
            className="w-12 h-12 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-800 hover:text-gray-200 transition-colors"
            title="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* API Key Warning */}
        {apiKeyConfigured === false && (
          <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 text-amber-400 text-sm">
            ⚠️ XAI_API_KEY not configured. Set it in your environment to enable chat.
          </div>
        )}

        {/* Routes */}
        <Routes>
          <Route path="/" element={<ChatView />} />
          <Route path="/workflow" element={<WorkflowPage />} />
          <Route path="/artifacts" element={<ArtifactManagerPage />} />
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/p2re" element={<P2REPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
