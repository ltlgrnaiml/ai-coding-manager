import { useState, useMemo, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { ScatterplotLayer, LineLayer } from '@deck.gl/layers'
import { OrbitView } from '@deck.gl/core'
import { Paper } from '../../hooks/useResearch'

interface PaperGraph3DProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

interface Node3D {
  id: string
  position: [number, number, number]
  color: [number, number, number, number]
  size: number
  paper: Paper
}

interface Edge3D {
  source: [number, number, number]
  target: [number, number, number]
}

const INITIAL_VIEW_STATE = {
  target: [0, 0, 0] as [number, number, number],
  zoom: 2,
  rotationX: 45,
  rotationOrbit: 30,
  minZoom: 0.5,
  maxZoom: 10
}

export function PaperGraph3D({ papers, onNodeClick, className = '' }: PaperGraph3DProps) {
  const [viewState, setViewState] = useState<typeof INITIAL_VIEW_STATE>(INITIAL_VIEW_STATE)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  // Generate 3D positions for papers
  const { nodes, edges } = useMemo(() => {
    const nodes: Node3D[] = []
    const edges: Edge3D[] = []

    papers.forEach((paper, index) => {
      // Spherical distribution
      const phi = Math.acos(-1 + (2 * index) / papers.length)
      const theta = Math.sqrt(papers.length * Math.PI) * phi
      const radius = 50 + (paper.similarity || 0) * 20

      const x = radius * Math.cos(theta) * Math.sin(phi)
      const y = radius * Math.sin(theta) * Math.sin(phi)
      const z = radius * Math.cos(phi)

      // Color based on similarity
      const similarity = paper.similarity || 0
      const color: [number, number, number, number] = similarity > 0.5 
        ? [34, 197, 94, 255]   // green
        : similarity > 0.3 
          ? [234, 179, 8, 255]  // yellow
          : [99, 102, 241, 255] // indigo

      nodes.push({
        id: paper.paper_id,
        position: [x, y, z],
        color,
        size: 300 + similarity * 500,
        paper
      })
    })

    // Create edges between nearby nodes
    nodes.forEach((node, i) => {
      const connections = Math.min(2, nodes.length - 1)
      for (let j = 1; j <= connections; j++) {
        const targetIndex = (i + j) % nodes.length
        edges.push({
          source: node.position,
          target: nodes[targetIndex].position
        })
      }
    })

    return { nodes, edges }
  }, [papers])

  const layers = [
    // Edge lines
    new LineLayer({
      id: 'edges',
      data: edges,
      getSourcePosition: d => d.source,
      getTargetPosition: d => d.target,
      getColor: [55, 65, 81, 100],
      getWidth: 1,
      pickable: false
    }),
    // Node spheres
    new ScatterplotLayer({
      id: 'nodes',
      data: nodes,
      getPosition: d => d.position,
      getFillColor: d => d.id === hoveredNode 
        ? [255, 255, 255, 255] 
        : d.color,
      getRadius: d => d.size,
      pickable: true,
      onHover: info => {
        setHoveredNode(info.object?.id || null)
      },
      onClick: info => {
        if (info.object) {
          onNodeClick?.(info.object.id)
        }
      },
      radiusMinPixels: 5,
      radiusMaxPixels: 30
    })
  ]

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  return (
    <div className={`h-full w-full relative ${className}`}>
      <DeckGL
        views={new OrbitView({ orbitAxis: 'Y' })}
        viewState={viewState}
        onViewStateChange={(e: any) => setViewState(e.viewState)}
        controller={true}
        layers={layers}
        style={{ background: '#111827' }}
      />
      
      {/* Hover tooltip */}
      {hoveredNode && (
        <div className="absolute top-4 left-4 bg-gray-800/90 border border-gray-700 rounded-lg p-3 max-w-xs pointer-events-none">
          <p className="text-white text-sm font-medium">
            {nodes.find(n => n.id === hoveredNode)?.paper.title?.slice(0, 80)}...
          </p>
          <p className="text-gray-400 text-xs mt-1">
            Click to view details
          </p>
        </div>
      )}

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 text-gray-500 text-xs">
        Drag to rotate • Scroll to zoom • Shift+drag to pan
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-gray-800/90 border border-gray-700 rounded-lg px-3 py-2">
        <p className="text-cyan-400 text-xs font-mono">
          {papers.length} nodes • {edges.length} edges • WebGL2
        </p>
      </div>
    </div>
  )
}

export default PaperGraph3D
