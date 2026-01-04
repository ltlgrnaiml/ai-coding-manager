import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { UmbrellaDisc, ArtifactTreeNode, RainstormState, ArtifactSummary } from './types'

const STORAGE_KEY = 'rainstorm-state'
const POLL_INTERVAL = 3000 // 3 seconds
const API_BASE = '/api/devtools'

const DEFAULT_STATE: RainstormState = {
  activeUmbrella: null,
  artifactTree: [],
  selectedNode: null,
  expandedNodes: new Set<string>(),
  discoveryEnabled: true,
  lastDiscoveryCheck: 0,
}

export function useRainstormState() {
  const [state, setState] = useState<RainstormState>(DEFAULT_STATE)
  
  // Load from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setState({
          ...parsed,
          expandedNodes: new Set(parsed.expandedNodes || []),
        })
      } catch {
        sessionStorage.removeItem(STORAGE_KEY)
      }
    }
  }, [])
  
  // Persist to sessionStorage on change
  useEffect(() => {
    if (state.activeUmbrella) {
      const toSave = {
        ...state,
        expandedNodes: Array.from(state.expandedNodes),
      }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
    }
  }, [state])
  
  // Poll for new artifacts when discovery is enabled
  const { data: artifacts } = useQuery({
    queryKey: ['artifacts', 'discovery'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/artifacts`)
      if (!response.ok) throw new Error('Failed to fetch artifacts')
      const data = await response.json()
      return data.items as ArtifactSummary[]
    },
    enabled: state.discoveryEnabled && state.activeUmbrella !== null,
    refetchInterval: POLL_INTERVAL,
  })
  
  // Check for new artifacts
  useEffect(() => {
    if (artifacts && state.lastDiscoveryCheck > 0) {
      const newArtifacts = artifacts.filter(
        a => new Date(a.updated_date || '').getTime() > state.lastDiscoveryCheck
      )
      if (newArtifacts.length > 0) {
        // TODO: Show notification for new artifacts
        console.log('New artifacts discovered:', newArtifacts)
      }
    }
    if (artifacts) {
      setState(prev => ({ ...prev, lastDiscoveryCheck: Date.now() }))
    }
  }, [artifacts])
  
  const startRainstorm = useCallback((umbrella: UmbrellaDisc) => {
    setState({
      ...DEFAULT_STATE,
      activeUmbrella: umbrella,
      lastDiscoveryCheck: Date.now(),
    })
  }, [])
  
  const selectNode = useCallback((node: ArtifactTreeNode | null) => {
    setState(prev => ({ ...prev, selectedNode: node }))
  }, [])
  
  const toggleNodeExpanded = useCallback((nodeId: string) => {
    setState(prev => {
      const newExpanded = new Set(prev.expandedNodes)
      if (newExpanded.has(nodeId)) {
        newExpanded.delete(nodeId)
      } else {
        newExpanded.add(nodeId)
      }
      return { ...prev, expandedNodes: newExpanded }
    })
  }, [])
  
  const updateArtifactTree = useCallback((tree: ArtifactTreeNode[]) => {
    setState(prev => ({ ...prev, artifactTree: tree }))
  }, [])
  
  const toggleDiscovery = useCallback((enabled: boolean) => {
    setState(prev => ({ ...prev, discoveryEnabled: enabled }))
  }, [])
  
  const resetRainstorm = useCallback(() => {
    setState(DEFAULT_STATE)
    sessionStorage.removeItem(STORAGE_KEY)
  }, [])
  
  return {
    ...state,
    startRainstorm,
    selectNode,
    toggleNodeExpanded,
    updateArtifactTree,
    toggleDiscovery,
    resetRainstorm,
  }
}
