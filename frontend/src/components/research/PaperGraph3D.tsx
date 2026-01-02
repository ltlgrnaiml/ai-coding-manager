import { useState, useMemo, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { ScatterplotLayer, LineLayer, TextLayer } from '@deck.gl/layers'
import { OrbitView } from '@deck.gl/core'
import { Paper } from '../../hooks/useResearch'

interface PaperGraph3DProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Category colors
const CATEGORY_COLORS: Record<string, [number, number, number, number]> = {
  'agentic-ai': [239, 68, 68, 255],
  'rag': [249, 115, 22, 255],
  'context': [234, 179, 8, 255],
  'code-generation': [34, 197, 94, 255],
  'multi-agent': [20, 184, 166, 255],
  'embedding': [59, 130, 246, 255],
  'transformer': [139, 92, 246, 255],
  'prompt': [236, 72, 153, 255],
  'default': [99, 102, 241, 255]
}

function detectCategory(paper: Paper): string {
  const text = ((paper.title || '') + ' ' + (paper.abstract || '')).toLowerCase()
  if (text.includes('agent') || text.includes('agentic')) return 'agentic-ai'
  if (text.includes('retrieval') || text.includes('rag')) return 'rag'
  if (text.includes('context') || text.includes('window')) return 'context'
  if (text.includes('code') || text.includes('generation')) return 'code-generation'
  if (text.includes('multi-agent') || text.includes('collaboration')) return 'multi-agent'
  if (text.includes('embed') || text.includes('vector')) return 'embedding'
  if (text.includes('transformer') || text.includes('attention')) return 'transformer'
  if (text.includes('prompt') || text.includes('instruction')) return 'prompt'
  return 'default'
}

interface Node3D {
  id: string
  position: [number, number, number]
  color: [number, number, number, number]
  size: number
  label: string
  category: string
  paper: Paper
}

interface Edge3D {
  source: [number, number, number]
  target: [number, number, number]
  color: [number, number, number, number]
}

const INITIAL_VIEW_STATE = {
  target: [0, 0, 0] as [number, number, number],
  zoom: 1.5,
  rotationX: 30,
  rotationOrbit: 45,
  minZoom: 0.3,
  maxZoom: 10
}

// Legend component for 3D
function Legend3D({ categories }: { categories: { name: string; color: [number, number, number, number]; count: number }[] }) {
  return (
    <div className="absolute top-4 left-4 bg-gray-900/95 border border-gray-700 rounded-xl p-4 shadow-xl">
      <h3 className="text-sm font-semibold text-white mb-3">Categories</h3>
      <div className="space-y-2">
        {categories.map(cat => (
          <div key={cat.name} className="flex items-center gap-3">
            <span 
              className="w-4 h-4 rounded-full flex-shrink-0"
              style={{ backgroundColor: `rgba(${cat.color.join(',')})` }}
            />
            <span className="text-sm text-gray-200 capitalize">
              {cat.name.replace(/-/g, ' ')}
            </span>
            <span className="text-xs text-gray-500 ml-auto">{cat.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function PaperGraph3D({ papers, onNodeClick, className = '' }: PaperGraph3DProps) {
  const [viewState, setViewState] = useState<typeof INITIAL_VIEW_STATE>(INITIAL_VIEW_STATE)
  const [hoveredNode, setHoveredNode] = useState<Node3D | null>(null)

  // Generate 3D positions clustered by category
  const { nodes, edges, categoryStats } = useMemo(() => {
    const nodes: Node3D[] = []
    const edges: Edge3D[] = []
    const categoryPositions: Record<string, { x: number; y: number; z: number; count: number }> = {}
    const categoryCounts: Record<string, number> = {}

    // First pass: count categories
    papers.forEach(paper => {
      const cat = detectCategory(paper)
      categoryCounts[cat] = (categoryCounts[cat] || 0) + 1
    })

    // Initialize category cluster positions (spherical distribution)
    const categoryList = Object.keys(categoryCounts)
    categoryList.forEach((cat, i) => {
      const phi = Math.acos(-1 + (2 * i) / categoryList.length)
      const theta = Math.sqrt(categoryList.length * Math.PI) * phi
      categoryPositions[cat] = {
        x: Math.cos(theta) * Math.sin(phi) * 80,
        y: Math.sin(theta) * Math.sin(phi) * 80,
        z: Math.cos(phi) * 80,
        count: 0
      }
    })

    // Create nodes clustered by category
    papers.forEach((paper) => {
      const category = detectCategory(paper)
      const catPos = categoryPositions[category]
      
      // Spiral position within cluster
      const localAngle = catPos.count * 0.5
      const localRadius = 10 + catPos.count * 2
      const localHeight = (catPos.count % 5) * 5
      catPos.count++

      const x = catPos.x + Math.cos(localAngle) * localRadius
      const y = catPos.y + Math.sin(localAngle) * localRadius
      const z = catPos.z + localHeight - 10

      const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.default
      const similarity = paper.similarity || 0.5

      nodes.push({
        id: paper.paper_id,
        position: [x, y, z],
        color,
        size: 200 + similarity * 400,
        label: paper.title?.slice(0, 30) || 'Untitled',
        category,
        paper
      })
    })

    // Create edges within categories
    nodes.forEach((node, i) => {
      nodes.forEach((other, j) => {
        if (i >= j) return
        
        const sameCategory = node.category === other.category
        
        if (sameCategory && Math.random() < 0.3) {
          const color = node.color.slice() as [number, number, number, number]
          color[3] = 60 // Low opacity
          edges.push({
            source: node.position,
            target: other.position,
            color
          })
        }
      })
    })

    const categoryStats = Object.entries(categoryCounts)
      .map(([name, count]) => ({
        name,
        color: CATEGORY_COLORS[name] || CATEGORY_COLORS.default,
        count
      }))
      .sort((a, b) => b.count - a.count)

    return { nodes, edges, categoryStats }
  }, [papers])

  const layers = [
    // Edges
    new LineLayer({
      id: 'edges',
      data: edges,
      getSourcePosition: d => d.source,
      getTargetPosition: d => d.target,
      getColor: d => d.color,
      getWidth: 1,
      pickable: false
    }),
    // Nodes
    new ScatterplotLayer({
      id: 'nodes',
      data: nodes,
      getPosition: d => d.position,
      getFillColor: d => d.id === hoveredNode?.id 
        ? [255, 255, 255, 255] 
        : d.color,
      getRadius: d => d.size,
      pickable: true,
      onHover: info => setHoveredNode(info.object || null),
      onClick: info => {
        if (info.object) onNodeClick?.(info.object.id)
      },
      radiusMinPixels: 4,
      radiusMaxPixels: 20
    }),
    // Labels
    new TextLayer({
      id: 'labels',
      data: nodes,
      getPosition: d => [d.position[0], d.position[1], d.position[2] + 5],
      getText: d => d.label,
      getSize: 12,
      getColor: [226, 232, 240, 200],
      getAngle: 0,
      getTextAnchor: 'middle',
      getAlignmentBaseline: 'bottom',
      billboard: true,
      fontFamily: 'Inter, system-ui, sans-serif',
      fontWeight: 500
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
        style={{ background: 'linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)' }}
      />
      
      {/* Legend */}
      <Legend3D categories={categoryStats} />

      {/* Hover tooltip */}
      {hoveredNode && (
        <div className="absolute top-4 right-4 bg-gray-900/95 border border-gray-600 rounded-lg p-4 max-w-sm shadow-xl">
          <div 
            className="w-3 h-3 rounded-full mb-2"
            style={{ backgroundColor: `rgba(${hoveredNode.color.join(',')})` }}
          />
          <h4 className="text-sm font-medium text-white mb-1">
            {hoveredNode.paper.title}
          </h4>
          {hoveredNode.paper.authors && (
            <p className="text-xs text-gray-400 mb-2">{hoveredNode.paper.authors}</p>
          )}
          <p className="text-xs text-cyan-400">Click for details</p>
        </div>
      )}

      {/* Stats */}
      <div className="absolute bottom-4 left-4 bg-gray-900/95 border border-gray-700 rounded-lg px-4 py-2">
        <p className="text-sm text-cyan-400 font-mono">
          {nodes.length} nodes • {edges.length} edges • WebGL2
        </p>
      </div>

      {/* Controls */}
      <div className="absolute bottom-4 right-4 text-gray-500 text-xs bg-gray-900/80 px-3 py-1.5 rounded-lg">
        Drag to rotate • Scroll to zoom • Shift+drag to pan
      </div>
    </div>
  )
}

export default PaperGraph3D
