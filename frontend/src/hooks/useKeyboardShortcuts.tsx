import { useEffect, useCallback, useRef } from 'react';

type ShortcutHandler = () => void;

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  handler: ShortcutHandler;
  description: string;
}

const SHORTCUTS: ShortcutConfig[] = [
  {
    key: 'p',
    ctrl: true,
    shift: true,
    handler: () => {}, // Will be set dynamically
    description: 'Open Research Papers pane'
  },
  {
    key: 'k',
    ctrl: true,
    shift: true,
    handler: () => {},
    description: 'Quick knowledge lookup'
  },
  {
    key: 'c',
    ctrl: true,
    shift: true,
    handler: () => {},
    description: 'Search concepts'
  },
  {
    key: 'Escape',
    handler: () => {},
    description: 'Close active panel'
  }
];

export function useKeyboardShortcuts(handlers: {
  onOpenResearch?: () => void;
  onQuickLookup?: () => void;
  onSearchConcepts?: () => void;
  onEscape?: () => void;
}) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const { key, ctrlKey, shiftKey, altKey } = event;

    // Ctrl+Shift+P: Open Research Papers
    if (ctrlKey && shiftKey && key.toLowerCase() === 'p') {
      event.preventDefault();
      handlersRef.current.onOpenResearch?.();
      return;
    }

    // Ctrl+Shift+K: Quick Knowledge Lookup
    if (ctrlKey && shiftKey && key.toLowerCase() === 'k') {
      event.preventDefault();
      handlersRef.current.onQuickLookup?.();
      return;
    }

    // Ctrl+Shift+C: Search Concepts
    if (ctrlKey && shiftKey && key.toLowerCase() === 'c') {
      event.preventDefault();
      handlersRef.current.onSearchConcepts?.();
      return;
    }

    // Escape: Close active panel
    if (key === 'Escape') {
      handlersRef.current.onEscape?.();
      return;
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    shortcuts: SHORTCUTS.map(s => ({
      ...s,
      combo: [
        s.ctrl && 'Ctrl',
        s.shift && 'Shift',
        s.alt && 'Alt',
        s.key
      ].filter(Boolean).join('+')
    }))
  };
}

export function ShortcutsHelp({ shortcuts }: { shortcuts: { combo: string; description: string }[] }) {
  return (
    <div className="space-y-2">
      <h4 className="font-medium text-white text-sm">Keyboard Shortcuts</h4>
      <div className="grid gap-1.5">
        {shortcuts.map((s, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span className="text-slate-400">{s.description}</span>
            <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-300 font-mono">
              {s.combo}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
}
