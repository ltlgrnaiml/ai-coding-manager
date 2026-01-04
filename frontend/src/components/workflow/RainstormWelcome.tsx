import { useState } from 'react'
import { CloudRain, Umbrella, Plus, FolderOpen, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '../../lib/utils'

interface RainstormWelcomeProps {
  onStartNew: () => void
  onOpenExisting: () => void
  onLearnMore?: () => void
  className?: string
}

export function RainstormWelcome({ 
  onStartNew, 
  onOpenExisting, 
  onLearnMore,
  className 
}: RainstormWelcomeProps) {
  const [expanded, setExpanded] = useState(false)
  
  return (
    <div className={cn('flex flex-col items-center justify-center h-full p-8 text-center', className)}>
      {/* Animated Rainstorm Header */}
      <div className="relative mb-8">
        <div className="rainstorm-container">
          {/* Rain animation */}
          <div className="rain-drops">
            {[...Array(12)].map((_, i) => (
              <div 
                key={i} 
                className="rain-drop"
                style={{
                  left: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 2}s`,
                  animationDuration: `${1.5 + Math.random()}s`
                }}
              >
                💧
              </div>
            ))}
          </div>
          
          {/* Main icon */}
          <div className="relative z-10 flex items-center justify-center">
            <CloudRain size={64} className="text-blue-400 animate-pulse" />
          </div>
        </div>
        
        <h1 className="mt-6 text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Welcome to The Rainstorm ⛈️
        </h1>
        
        <p className="mt-2 text-lg text-zinc-400">
          Your ideas are pouring in. Let's organize them.
        </p>
      </div>
      
      {/* Expandable explanation section */}
      <div className="w-full max-w-2xl mb-8">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between px-6 py-4 bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Umbrella size={20} className="text-blue-400" />
            <span className="text-left">
              <span className="block font-medium">What is The Rainstorm?</span>
              <span className="block text-sm text-zinc-500">Learn about the workflow</span>
            </span>
          </div>
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        
        {expanded && (
          <div className="mt-4 p-6 bg-zinc-900/50 rounded-lg text-left space-y-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-1">🌧️</span>
              <div>
                <h3 className="font-semibold mb-1">The Workflow for Complex Topics</h3>
                <p className="text-sm text-zinc-400">
                  When heavy topics fall from the sky, The Rainstorm helps you organize multiple 
                  discussions, decisions, and specifications under a common theme.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-1">☂️</span>
              <div>
                <h3 className="font-semibold mb-1">Umbrella DISCs</h3>
                <p className="text-sm text-zinc-400">
                  Start by creating an Umbrella DISC (Discussion) that groups related artifacts. 
                  Umbrellas can even contain other Umbrellas for deeply nested topics.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-1">📋</span>
              <div>
                <h3 className="font-semibold mb-1">Workflow Builder</h3>
                <p className="text-sm text-zinc-400">
                  The visual Workflow Builder shows your entire artifact family as a tree, 
                  guides you through creating each piece, and auto-discovers files created externally.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-1">✨</span>
              <div>
                <h3 className="font-semibold mb-1">AI Integration</h3>
                <p className="text-sm text-zinc-400">
                  Generate prompts for missing artifacts, copy them to your clipboard, or send 
                  directly to the built-in AI chat for seamless artifact creation.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <button
          onClick={onStartNew}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
        >
          <Plus size={20} />
          Start New Rainstorm
        </button>
        
        <button
          onClick={onOpenExisting}
          className="flex items-center gap-2 px-6 py-3 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors font-medium"
        >
          <FolderOpen size={20} />
          Open Existing
        </button>
        
        {onLearnMore && (
          <button
            onClick={onLearnMore}
            className="flex items-center gap-2 px-6 py-3 bg-transparent hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-white"
          >
            <BookOpen size={20} />
            Learn More
          </button>
        )}
      </div>
      
      {/* CSS for rain animation */}
      <style dangerouslySetInnerHTML={{ __html: `
        .rainstorm-container {
          position: relative;
          width: 200px;
          height: 120px;
        }
        
        .rain-drops {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 100%;
          overflow: hidden;
        }
        
        .rain-drop {
          position: absolute;
          font-size: 16px;
          animation: fall linear infinite;
          opacity: 0.7;
        }
        
        @keyframes fall {
          from {
            transform: translateY(-20px);
            opacity: 0;
          }
          10% {
            opacity: 0.7;
          }
          90% {
            opacity: 0.7;
          }
          to {
            transform: translateY(120px);
            opacity: 0;
          }
        }
      `}} />
    </div>
  )
}
