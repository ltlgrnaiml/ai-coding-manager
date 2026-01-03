import { useState, useCallback } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import { SidebarTabs } from './SidebarTabs'
import { ArtifactList } from './ArtifactList'
import { P2REToolsPanel } from './P2REToolsPanel'
import type { ArtifactType, ArtifactSummary } from './types'

const TAB_ORDER: ArtifactType[] = ['chatlog', 'discussion', 'adr', 'spec', 'plan', 'contract', 'session', 'bug', 'guide', 'trace']

interface WorkflowSidebarProps {
  onArtifactSelect: (artifact: ArtifactSummary) => void
  selectedArtifactId?: string
}

export function WorkflowSidebar({ onArtifactSelect, selectedArtifactId }: WorkflowSidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<ArtifactType>('chatlog')
  const [searchQuery, setSearchQuery] = useState('')

  const handleNavigateList = useCallback((direction: 'left' | 'right') => {
    const currentIndex = TAB_ORDER.indexOf(activeTab)
    if (direction === 'left') {
      const newIndex = currentIndex > 0 ? currentIndex - 1 : TAB_ORDER.length - 1
      setActiveTab(TAB_ORDER[newIndex])
    } else {
      const newIndex = currentIndex < TAB_ORDER.length - 1 ? currentIndex + 1 : 0
      setActiveTab(TAB_ORDER[newIndex])
    }
    setSearchQuery('')
  }, [activeTab])

  return (
    <div
      className={cn(
        'flex flex-col border-r border-zinc-800 bg-zinc-900 transition-all duration-200',
        collapsed ? 'w-12' : 'w-72'
      )}
    >
      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-10 border-b border-zinc-800 hover:bg-zinc-800"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      {!collapsed && (
        <>
          <SidebarTabs activeTab={activeTab} onTabChange={setActiveTab} />
          {activeTab === 'trace' ? (
            <P2REToolsPanel />
          ) : (
            <ArtifactList
              type={activeTab}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onSelect={onArtifactSelect}
              selectedId={selectedArtifactId}
              onNavigateList={handleNavigateList}
            />
          )}
        </>
      )}
    </div>
  )
}
