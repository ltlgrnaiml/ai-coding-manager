import { useEffect } from 'react'

interface KeyboardShortcutsOptions {
  onOpenResearch?: () => void
  onEscape?: () => void
}

export function useKeyboardShortcuts(options: KeyboardShortcutsOptions = {}) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Shift+R to open research pane
      if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault()
        options.onOpenResearch?.()
      }
      // Escape to close
      if (e.key === 'Escape') {
        options.onEscape?.()
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [options])
}

export default useKeyboardShortcuts