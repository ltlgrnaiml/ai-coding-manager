import { useEffect, useMemo, useRef } from 'react'
import Graph from 'graphology'
import { SigmaContainer, useLoadGraph, useSigma } from '@react-sigma/core'
import '@react-sigma/core/lib/style.css'
import { Paper } from '../../hooks/useResearch'

interface PaperGraph2DProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

interface GraphNode {
  id: string
  label: string
  x: number
  y: number
  size: number
  color: string
}

interface GraphEdge {
  source: string
  target: string
  weight: number
}

function LoadGraphData({ papers, onNodeClick }: { papers: Paper[], onNodeClick?: (paperId: string) => void }) {
  const loadGraph = useLoadGraph()
  const sigma = useSigma()

  useEffect(() => {
    const graph = new Graph()

    // Add nodes for each paper
    papers.forEach((paper, index) => {
      const angle = (2 * Math.PI * index) / papers.length
      const radius = 100 + Math.random() * 50
      
      graph.addNode(paper.paper_id, {
        label: paper.title?.slice(0, 40) + '...' || 'Untitled',
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        size: 8 + (paper.similarity || 0) * 10,
        color: paper.similarity && paper.similarity > 0.5 
          ? '#22c55e' 
          : paper.similarity && paper.similarity > 0.3 
            ? '#eab308' 
            : '#6366f1'
      })
    })

    // Add edges based on similarity (connect papers with similar titles/concepts)
    // For now, create a simple clustering based on index proximity
    papers.forEach((paper, i) => {
      // Connect to nearby papers in the list (simulating concept similarity)
      const connections = Math.min(3, papers.length - 1)
      for (let j = 1; j <= connections; j++) {
        const targetIndex = (i + j) % papers.length
        const targetPaper = papers[targetIndex]
        
        if (!graph.hasEdge(paper.paper_id, targetPaper.paper_id) && 
            !graph.hasEdge(targetPaper.paper_id, paper.paper_id)) {
          graph.addEdge(paper.paper_id, targetPaper.paper_id, {
            size: 1,
            color: '#374151'
          })
        }
      }
    })

    loadGraph(graph)

    // Set up click handler
    sigma.on('clickNode', ({ node }) => {
      onNodeClick?.(node)
    })

    return () => {
      sigma.removeAllListeners()
    }
  }, [papers, loadGraph, sigma, onNodeClick])

  return null
}

export function PaperGraph2D({ papers, onNodeClick, className = '' }: PaperGraph2DProps) {
  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  return (
    <div className={`h-full w-full ${className}`}>
      <SigmaContainer
        style={{ height: '100%', width: '100%', background: '#111827' }}
        settings={{
          renderLabels: true,
          labelSize: 10,
          labelColor: { color: '#9ca3af' },
          defaultNodeColor: '#6366f1',
          defaultEdgeColor: '#374151',
          minCameraRatio: 0.1,
          maxCameraRatio: 10,
          labelRenderedSizeThreshold: 6,
          labelDensity: 0.5
        }}
      >
        <LoadGraphData papers={papers} onNodeClick={onNodeClick} />
      </SigmaContainer>
    </div>
  )
}

export default PaperGraph2D
