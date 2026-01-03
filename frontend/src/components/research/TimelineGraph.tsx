import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { Paper } from '../../hooks/useResearch'

interface TimelineGraphProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Extract year from paper metadata
function extractYear(paper: Paper): number {
  if (paper.year) return paper.year
  if (paper.published_date) {
    const match = paper.published_date.match(/\d{4}/)
    if (match) return parseInt(match[0])
  }
  const text = paper.title || ''
  const yearMatch = text.match(/20[0-2]\d/)
  if (yearMatch) return parseInt(yearMatch[0])
  return 2024
}

// Get importance score (similarity as proxy for citations)
function getImportance(paper: Paper): number {
  return paper.citation_count || (paper.similarity ? paper.similarity * 100 : 50)
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

export default function TimelineGraph({ 
  papers, 
  onNodeClick,
  className = ''
}: TimelineGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoveredPaper, setHoveredPaper] = useState<Paper | null>(null)
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 })
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  // Calculate ranges
  const { yearRange, importanceRange } = useMemo(() => {
    if (papers.length === 0) return { 
      yearRange: { min: 2020, max: 2025 }, 
      importanceRange: { min: 0, max: 100 } 
    }
    const years = papers.map(extractYear)
    const importances = papers.map(getImportance)
    return {
      yearRange: { min: Math.min(...years) - 1, max: Math.max(...years) + 1 },
      importanceRange: { min: 0, max: Math.max(...importances) * 1.2 }
    }
  }, [papers])

  // Paper positions for hit detection
  const paperPositions = useMemo(() => {
    const padding = { top: 60, right: 40, bottom: 60, left: 80 }
    const plotWidth = dimensions.width - padding.left - padding.right
    const plotHeight = dimensions.height - padding.top - padding.bottom

    return papers.map(paper => {
      const year = extractYear(paper)
      const importance = getImportance(paper)
      const x = padding.left + ((year - yearRange.min) / (yearRange.max - yearRange.min)) * plotWidth
      const y = padding.top + plotHeight - ((importance - importanceRange.min) / (importanceRange.max - importanceRange.min)) * plotHeight
      return { paper, x, y, radius: 8 + (importance / importanceRange.max) * 12 }
    })
  }, [papers, dimensions, yearRange, importanceRange])

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

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    canvas.width = dimensions.width * dpr
    canvas.height = dimensions.height * dpr
    ctx.scale(dpr, dpr)

    const padding = { top: 60, right: 40, bottom: 60, left: 80 }
    const plotWidth = dimensions.width - padding.left - padding.right
    const plotHeight = dimensions.height - padding.top - padding.bottom

    // Clear and set background
    ctx.fillStyle = '#fafbfc'
    ctx.fillRect(0, 0, dimensions.width, dimensions.height)

    // Draw grid lines
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1

    // Vertical grid (years)
    const yearStep = Math.ceil((yearRange.max - yearRange.min) / 8)
    for (let year = yearRange.min; year <= yearRange.max; year += yearStep) {
      const x = padding.left + ((year - yearRange.min) / (yearRange.max - yearRange.min)) * plotWidth
      ctx.beginPath()
      ctx.moveTo(x, padding.top)
      ctx.lineTo(x, padding.top + plotHeight)
      ctx.stroke()

      // Year label
      ctx.fillStyle = '#6b7280'
      ctx.font = '12px Inter, system-ui, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(year.toString(), x, dimensions.height - padding.bottom + 20)
    }

    // Horizontal grid (importance)
    const impStep = Math.ceil(importanceRange.max / 5)
    for (let imp = 0; imp <= importanceRange.max; imp += impStep) {
      const y = padding.top + plotHeight - ((imp - importanceRange.min) / (importanceRange.max - importanceRange.min)) * plotHeight
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(padding.left + plotWidth, y)
      ctx.stroke()

      // Importance label
      ctx.fillStyle = '#6b7280'
      ctx.font = '11px Inter, system-ui, sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(imp.toFixed(0), padding.left - 10, y + 4)
    }

    // Draw axes
    ctx.strokeStyle = '#374151'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(padding.left, padding.top)
    ctx.lineTo(padding.left, padding.top + plotHeight)
    ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight)
    ctx.stroke()

    // Axis labels
    ctx.fillStyle = '#374151'
    ctx.font = 'bold 13px Inter, system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Publication Year', padding.left + plotWidth / 2, dimensions.height - 15)
    
    ctx.save()
    ctx.translate(20, padding.top + plotHeight / 2)
    ctx.rotate(-Math.PI / 2)
    ctx.fillText('Relevance Score', 0, 0)
    ctx.restore()

    // Draw quadrant highlight (top-right = most relevant)
    const quadrantX = padding.left + plotWidth * 0.6
    const quadrantY = padding.top
    const quadrantWidth = plotWidth * 0.4
    const quadrantHeight = plotHeight * 0.4
    ctx.fillStyle = 'rgba(34, 197, 94, 0.08)'
    ctx.fillRect(quadrantX, quadrantY, quadrantWidth, quadrantHeight)
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.3)'
    ctx.lineWidth = 1
    ctx.strokeRect(quadrantX, quadrantY, quadrantWidth, quadrantHeight)
    ctx.fillStyle = 'rgba(34, 197, 94, 0.7)'
    ctx.font = '11px Inter, system-ui, sans-serif'
    ctx.fillText('Most Relevant', quadrantX + quadrantWidth - 60, quadrantY + 20)

    // Draw connection lines (light)
    ctx.strokeStyle = 'rgba(100, 120, 180, 0.15)'
    ctx.lineWidth = 1
    paperPositions.forEach((pos1, i) => {
      paperPositions.forEach((pos2, j) => {
        if (i >= j) return
        const yearDiff = Math.abs(extractYear(pos1.paper) - extractYear(pos2.paper))
        if (yearDiff <= 2) {
          ctx.beginPath()
          ctx.moveTo(pos1.x, pos1.y)
          ctx.lineTo(pos2.x, pos2.y)
          ctx.stroke()
        }
      })
    })

    // Draw papers as circles
    paperPositions.forEach(({ paper, x, y, radius }) => {
      const category = detectCategory(paper)
      const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.default
      const isHovered = hoveredPaper?.paper_id === paper.paper_id

      // Shadow
      ctx.shadowColor = 'rgba(0, 0, 0, 0.15)'
      ctx.shadowBlur = isHovered ? 12 : 6
      ctx.shadowOffsetX = 0
      ctx.shadowOffsetY = 2

      // Circle
      ctx.beginPath()
      ctx.arc(x, y, isHovered ? radius * 1.3 : radius, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()

      // Border
      ctx.shadowBlur = 0
      ctx.strokeStyle = isHovered ? '#1e40af' : '#ffffff'
      ctx.lineWidth = isHovered ? 3 : 2
      ctx.stroke()
    })

  }, [papers, dimensions, yearRange, importanceRange, paperPositions, hoveredPaper])

  // Mouse interaction
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return

    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    // Find hovered paper
    const hovered = paperPositions.find(pos => {
      const dx = x - pos.x
      const dy = y - pos.y
      return Math.sqrt(dx * dx + dy * dy) < pos.radius + 5
    })

    setHoveredPaper(hovered?.paper || null)
    setHoverPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }, [paperPositions])

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return

    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const clicked = paperPositions.find(pos => {
      const dx = x - pos.x
      const dy = y - pos.y
      return Math.sqrt(dx * dx + dy * dy) < pos.radius + 5
    })

    if (clicked) {
      onNodeClick?.(clicked.paper.paper_id)
    }
  }, [paperPositions, onNodeClick])

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-50 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={`h-full w-full relative ${className}`}>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%' }}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
        className="cursor-pointer"
      />

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white border border-gray-200 rounded-xl p-4 shadow-lg max-w-xs">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Categories</h3>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(CATEGORY_COLORS).filter(([k]) => k !== 'default').slice(0, 6).map(([name, color]) => (
            <div key={name} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
              <span className="text-xs text-gray-600 capitalize">{name.replace(/-/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm">
        <p className="text-sm text-gray-600">
          <span className="font-semibold text-blue-600">{papers.length}</span> papers • 
          <span className="text-amber-600 ml-1">Canvas</span>
        </p>
      </div>

      {/* Tooltip */}
      {hoveredPaper && (
        <div 
          className="absolute z-50 bg-white border border-gray-200 rounded-xl shadow-xl p-4 max-w-sm pointer-events-none"
          style={{ 
            left: Math.min(hoverPosition.x + 15, dimensions.width - 300), 
            top: Math.min(hoverPosition.y + 15, dimensions.height - 150)
          }}
        >
          <h4 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
            {hoveredPaper.title || 'Untitled'}
          </h4>
          {hoveredPaper.authors && (
            <p className="text-xs text-gray-600 mb-2">{hoveredPaper.authors}</p>
          )}
          <div className="flex items-center gap-2 text-xs mb-2">
            <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              {extractYear(hoveredPaper)}
            </span>
            <span 
              className="px-2 py-0.5 rounded text-white"
              style={{ backgroundColor: CATEGORY_COLORS[detectCategory(hoveredPaper)] }}
            >
              {detectCategory(hoveredPaper).replace(/-/g, ' ')}
            </span>
          </div>
          <p className="text-xs text-blue-600 font-medium">Click to view details</p>
        </div>
      )}

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 text-gray-500 text-xs bg-white/90 border border-gray-200 px-3 py-1.5 rounded-lg">
        Hover for details • Click to view paper
      </div>
    </div>
  )
}
