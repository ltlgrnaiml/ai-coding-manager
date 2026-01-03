import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { Paper } from '../../hooks/useResearch'

interface TopicTreemapProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  'agentic-ai': '#ef4444',
  'rag': '#f97316',
  'context': '#eab308',
  'code-generation': '#22c55e',
  'multi-agent': '#14b8a6',
  'embedding': '#3b82f6',
  'transformer': '#8b5cf6',
  'prompt': '#ec4899',
  'default': '#6366f1'
}

// Detect category from paper
function detectCategory(paper: Paper): string {
  if (paper.category) return paper.category
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

interface TreemapNode {
  name: string
  category: string
  papers: Paper[]
  value: number
  color: string
  x: number
  y: number
  width: number
  height: number
}

// Simple treemap layout algorithm
function layoutTreemap(
  categories: Map<string, Paper[]>,
  width: number,
  height: number,
  padding: number = 4
): TreemapNode[] {
  const nodes: TreemapNode[] = []
  const total = Array.from(categories.values()).reduce((sum, papers) => sum + papers.length, 0)
  
  if (total === 0) return nodes

  // Sort categories by size (largest first)
  const sorted = Array.from(categories.entries())
    .sort((a, b) => b[1].length - a[1].length)

  let currentX = padding
  let currentY = padding
  let rowHeight = 0
  const availableWidth = width - padding * 2
  const availableHeight = height - padding * 2

  // Simple row-based layout
  sorted.forEach(([category, papers]) => {
    const ratio = papers.length / total
    const area = ratio * availableWidth * availableHeight
    const nodeWidth = Math.sqrt(area * (availableWidth / availableHeight))
    const nodeHeight = area / nodeWidth

    // Check if we need to start a new row
    if (currentX + nodeWidth > width - padding) {
      currentX = padding
      currentY += rowHeight + padding
      rowHeight = 0
    }

    // Ensure positive dimensions
    const finalWidth = Math.max(20, Math.min(nodeWidth, availableWidth - (currentX - padding)))
    const finalHeight = Math.max(20, Math.min(nodeHeight, availableHeight - (currentY - padding)))

    nodes.push({
      name: category,
      category,
      papers,
      value: papers.length,
      color: CATEGORY_COLORS[category] || CATEGORY_COLORS.default,
      x: currentX,
      y: currentY,
      width: finalWidth,
      height: finalHeight
    })

    currentX += nodeWidth + padding
    rowHeight = Math.max(rowHeight, nodeHeight)
  })

  return nodes
}

export default function TopicTreemap({ 
  papers, 
  onNodeClick,
  className = ''
}: TopicTreemapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [hoveredNode, setHoveredNode] = useState<TreemapNode | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [breadcrumb, setBreadcrumb] = useState<string[]>(['All Topics'])

  // Group papers by category
  const categories = useMemo(() => {
    const map = new Map<string, Paper[]>()
    papers.forEach(paper => {
      const category = detectCategory(paper)
      const existing = map.get(category) || []
      existing.push(paper)
      map.set(category, existing)
    })
    return map
  }, [papers])

  // Calculate treemap layout
  const treemapNodes = useMemo(() => {
    return layoutTreemap(categories, dimensions.width, dimensions.height)
  }, [categories, dimensions])

  // Resize observer
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        })
      }
    })

    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  // Handle category drill-down
  const handleCategoryClick = useCallback((category: string) => {
    setSelectedCategory(category)
    setBreadcrumb(['All Topics', category.replace(/-/g, ' ')])
  }, [])

  // Handle back to all
  const handleBackToAll = useCallback(() => {
    setSelectedCategory(null)
    setBreadcrumb(['All Topics'])
  }, [])

  // Papers to show (filtered if drilled down)
  const displayedPapers = useMemo(() => {
    if (!selectedCategory) return null
    return categories.get(selectedCategory) || []
  }, [selectedCategory, categories])

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-50 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={`h-full w-full relative bg-gray-50 ${className}`}>
      {/* Breadcrumb */}
      <div className="absolute top-4 left-4 z-10 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm">
        <div className="flex items-center gap-2 text-sm">
          {breadcrumb.map((crumb, index) => (
            <span key={index} className="flex items-center gap-2">
              {index > 0 && <span className="text-gray-400">›</span>}
              <button 
                onClick={index === 0 ? handleBackToAll : undefined}
                className={`${index === breadcrumb.length - 1 ? 'text-gray-900 font-medium' : 'text-blue-600 hover:underline'}`}
              >
                {crumb}
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 z-10 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm">
        <p className="text-sm text-gray-600">
          <span className="font-semibold text-blue-600">{papers.length}</span> papers • 
          <span className="font-semibold text-purple-600 ml-1">{categories.size}</span> topics
        </p>
      </div>

      {/* Treemap View (when not drilled down) */}
      {!selectedCategory && (
        <svg 
          width={dimensions.width} 
          height={dimensions.height}
          className="cursor-pointer"
        >
          {treemapNodes.map((node) => (
            <g 
              key={node.category}
              onClick={() => handleCategoryClick(node.category)}
              onMouseEnter={() => setHoveredNode(node)}
              onMouseLeave={() => setHoveredNode(null)}
            >
              {/* Rectangle */}
              <rect
                x={node.x}
                y={node.y}
                width={node.width}
                height={node.height}
                fill={node.color}
                rx={8}
                ry={8}
                opacity={hoveredNode?.category === node.category ? 1 : 0.85}
                stroke={hoveredNode?.category === node.category ? '#1e40af' : '#ffffff'}
                strokeWidth={hoveredNode?.category === node.category ? 3 : 2}
                style={{ transition: 'all 0.2s ease' }}
              />
              
              {/* Label */}
              {node.width > 80 && node.height > 50 && (
                <>
                  <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height / 2 - 8}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="14"
                    fontWeight="600"
                    style={{ textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}
                  >
                    {node.name.replace(/-/g, ' ')}
                  </text>
                  <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height / 2 + 12}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="24"
                    fontWeight="700"
                    opacity={0.9}
                  >
                    {node.value}
                  </text>
                  <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height / 2 + 30}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="11"
                    opacity={0.7}
                  >
                    papers
                  </text>
                </>
              )}
            </g>
          ))}
        </svg>
      )}

      {/* Drilled-down Paper List */}
      {selectedCategory && displayedPapers && (
        <div className="absolute inset-0 pt-16 px-4 pb-4 overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayedPapers.map(paper => (
              <div
                key={paper.paper_id}
                onClick={() => onNodeClick?.(paper.paper_id)}
                className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md hover:border-blue-300 cursor-pointer transition-all"
              >
                <h4 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
                  {paper.title || 'Untitled'}
                </h4>
                {paper.authors && (
                  <p className="text-xs text-gray-500 mb-2 line-clamp-1">{paper.authors}</p>
                )}
                {paper.abstract && (
                  <p className="text-xs text-gray-400 line-clamp-3">{paper.abstract}</p>
                )}
                <div className="mt-3 flex items-center gap-2">
                  <span 
                    className="text-xs px-2 py-0.5 rounded text-white"
                    style={{ backgroundColor: CATEGORY_COLORS[selectedCategory] }}
                  >
                    {selectedCategory.replace(/-/g, ' ')}
                  </span>
                  {paper.similarity && (
                    <span className="text-xs text-gray-500">
                      {(paper.similarity * 100).toFixed(0)}% match
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hover Tooltip (treemap view) */}
      {hoveredNode && !selectedCategory && (
        <div 
          className="absolute z-50 bg-white border border-gray-200 rounded-xl shadow-xl p-4 pointer-events-none"
          style={{ 
            left: Math.min(hoveredNode.x + hoveredNode.width / 2, dimensions.width - 200),
            top: Math.max(hoveredNode.y - 80, 60)
          }}
        >
          <h4 className="font-semibold text-gray-900 capitalize mb-1">
            {hoveredNode.name.replace(/-/g, ' ')}
          </h4>
          <p className="text-sm text-gray-600">
            <span className="font-bold text-blue-600">{hoveredNode.value}</span> papers
          </p>
          <p className="text-xs text-blue-500 mt-2">Click to explore</p>
        </div>
      )}

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 z-10 text-gray-500 text-xs bg-white/90 border border-gray-200 px-3 py-1.5 rounded-lg">
        Click topic to drill down • Use breadcrumb to navigate back
      </div>
    </div>
  )
}
