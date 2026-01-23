'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import Image from 'next/image'
import {
  RefreshCw,
  Search,
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  MousePointer2,
  Hand,
  ZoomIn,
  ZoomOut,
  Scissors,
} from 'lucide-react'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { useToast } from '@/components/ui/toast'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import type PlotType from 'react-plotly.js'
import type { PlotMouseEvent, PlotSelectionEvent } from 'plotly.js'

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false }) as typeof PlotType

type LayoutType = 'Force-directed' | 'Circular' | 'Hierarchical' | 'Random'
type NodeType = 'All' | 'Person' | 'Document' | 'Concept' | 'Organization'

interface GraphNode {
  name: string
  type: NodeType
  color: string
}

interface GraphEdge {
  source: string
  target: string
  similarity: number
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  nodePositions: Record<string, [number, number]>
}

type InteractionMode = 'pointer' | 'pan' | 'zoom'

type NodePopoverState = {
  name: string
  screenX: number
  screenY: number
}

export default function GraphVisualization() {
  const { toast } = useToast()
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(false)
  const [nodeTypeFilter, setNodeTypeFilter] = useState<NodeType>('All')
  const [layoutType, setLayoutType] = useState<LayoutType>('Force-directed')
  const [depth, setDepth] = useState(2)
  const [maxNodes, setMaxNodes] = useState(50)
  const [search, setSearch] = useState('')
  const [interactionMode, setInteractionMode] = useState<InteractionMode>('pan')
  const [selectedNodes, setSelectedNodes] = useState<string[]>([])
  const [nodePopover, setNodePopover] = useState<NodePopoverState | null>(null)
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true)
  const [rightSidebarWidth, setRightSidebarWidth] = useState(380)
  const [isResizing, setIsResizing] = useState(false)
  const [cypherQuery, setCypherQuery] = useState(
    'MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25'
  )
  const plotDivRef = useRef<any>(null)
  const canvasRef = useRef<HTMLDivElement>(null)
  const resizeRef = useRef<{ startX: number; startWidth: number } | null>(null)

  useEffect(() => {
    handleGenerate()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layoutType, maxNodes, depth, nodeTypeFilter])

  const handleGenerate = () => {
    setLoading(true)
    const data = generateSampleGraph(maxNodes, layoutType, nodeTypeFilter)
    setGraphData(data)
    setLoading(false)
  }

  const generateSampleGraph = (maxNodesValue: number, layout: LayoutType, nodeType: NodeType): GraphData => {
    const numNodes = Math.min(maxNodesValue, 50)
    const nodeTypes: NodeType[] = ['Person', 'Document', 'Concept', 'Organization']
    const typeColors: Record<NodeType, string> = {
      All: '#4fc3f7',
      Person: '#4fc3f7',
      Document: '#4caf50',
      Concept: '#ff9800',
      Organization: '#9c27b0',
    }

    const allowedTypes = nodeType === 'All' ? nodeTypes : [nodeType]

    const nodes: GraphNode[] = Array.from({ length: numNodes }, (_, i) => {
      const nType = allowedTypes[Math.floor(Math.random() * allowedTypes.length)]
      return { name: `${nType}_${i + 1}`, type: nType, color: typeColors[nType] }
    })

    // Node positions
    const nodePositions: Record<string, [number, number]> = {}
    if (layout === 'Circular') {
      nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length
        nodePositions[node.name] = [Math.cos(angle), Math.sin(angle)]
      })
    } else if (layout === 'Hierarchical') {
      const levels = 4
      const nodesPerLevel = Math.max(1, Math.floor(nodes.length / levels))
      nodes.forEach((node, i) => {
        const level = Math.floor(i / nodesPerLevel)
        const posInLevel = i % nodesPerLevel
        const x = (posInLevel * 2.0) / nodesPerLevel - 1
        const y = 1 - (level * 2.0) / levels
        nodePositions[node.name] = [x, y]
      })
    } else if (layout === 'Force-directed') {
      nodes.forEach((node) => {
        nodePositions[node.name] = [(Math.random() - 0.5) * 4, (Math.random() - 0.5) * 4]
      })
      // quick spreading iterations
      for (let iter = 0; iter < 8; iter++) {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodePositions[nodes[i].name]
            const b = nodePositions[nodes[j].name]
            const dx = a[0] - b[0]
            const dy = a[1] - b[1]
            const dist = Math.sqrt(dx * dx + dy * dy) + 0.01
            if (dist < 1) {
              const force = (1 - dist) * 0.05
              a[0] += (dx / dist) * force
              a[1] += (dy / dist) * force
              b[0] -= (dx / dist) * force
              b[1] -= (dy / dist) * force
            }
          }
        }
      }
    } else {
      nodes.forEach((node) => {
        nodePositions[node.name] = [(Math.random() - 0.5) * 3, (Math.random() - 0.5) * 3]
      })
    }

    // edges
    const edges: GraphEdge[] = []

    for (let i = 0; i < nodes.length; i++) {
      const connections = Math.min(4, Math.max(1, Math.floor(Math.random() * 4) + 1))
      for (let c = 0; c < connections; c++) {
        const j = Math.floor(Math.random() * nodes.length)
        if (i !== j) {
          const source = nodes[i].name
          const target = nodes[j].name
          if (!edges.find((e) => (e.source === source && e.target === target) || (e.source === target && e.target === source))) {
            const similarity = Math.random()
            edges.push({ source, target, similarity })
            // no-op for positions here; positions already stored for plotting
          }
        }
      }
    }

    return { nodes, edges, nodePositions }
  }

  // Memoize graph data separately from interaction mode to prevent unnecessary re-renders
  const plotData = useMemo(() => {
    if (!graphData) return null

    const edgeX: number[] = []
    const edgeY: number[] = []
    const edgeHover: string[] = []

    const selectedSet = new Set(selectedNodes)
    const selEdgeX: number[] = []
    const selEdgeY: number[] = []
    const selEdgeHover: string[] = []

    graphData.edges.forEach((edge) => {
      const positions = graphData.nodePositions
      if (positions[edge.source] && positions[edge.target]) {
        const [x0, y0] = positions[edge.source]
        const [x1, y1] = positions[edge.target]
        edgeX.push(x0, x1, NaN)
        edgeY.push(y0, y1, NaN)
        edgeHover.push(`${edge.source} ↔ ${edge.target}: ${(edge.similarity * 100).toFixed(1)}%`)

        if (selectedSet.size > 0 && (selectedSet.has(edge.source) || selectedSet.has(edge.target))) {
          selEdgeX.push(x0, x1, NaN)
          selEdgeY.push(y0, y1, NaN)
          selEdgeHover.push(`${edge.source} ↔ ${edge.target}: ${(edge.similarity * 100).toFixed(1)}%`)
        }
      }
    })

    const nodeNames = graphData.nodes.map((n) => n.name)
    const nodeX = nodeNames.map((name) => graphData.nodePositions[name]?.[0] || 0)
    const nodeY = nodeNames.map((name) => graphData.nodePositions[name]?.[1] || 0)
    const nodeColors = graphData.nodes.map((n) => n.color || '#4fc3f7')

    const nameToIdx = new Map<string, number>()
    nodeNames.forEach((n, i) => nameToIdx.set(n, i))
    const selectedPoints =
      selectedNodes.length > 0
        ? selectedNodes.map((n) => nameToIdx.get(n)).filter((v): v is number => typeof v === 'number')
        : null

    // Calculate nodes curveNumber: edges are always 0, selected edges (if any) are 1, nodes are last
    const nodesCurveNumber = selectedSet.size > 0 ? 2 : 1

    return {
      data: [
        {
          x: edgeX,
          y: edgeY,
          type: 'scatter' as const,
          mode: 'lines' as const,
          line: { width: 1.25, color: selectedSet.size > 0 ? 'rgba(180,180,180,0.08)' : 'rgba(180,180,180,0.22)' },
          hoverinfo: 'text' as const,
          text: edgeHover,
          showlegend: false,
        },
        ...(selectedSet.size > 0
          ? [
              {
                x: selEdgeX,
                y: selEdgeY,
                type: 'scatter' as const,
                mode: 'lines' as const,
                line: { width: 2, color: 'rgba(34,211,238,0.55)' },
                hoverinfo: 'text' as const,
                text: selEdgeHover,
                showlegend: false,
              },
            ]
          : []),
        {
          x: nodeX,
          y: nodeY,
          type: 'scatter' as const,
          mode: 'text+markers' as const,
          text: nodeNames,
          textposition: 'top center' as const,
          hoverinfo: 'text' as const,
          selectedpoints: selectedPoints ?? undefined,
          marker: {
            size: 16,
            color: nodeColors,
            line: { width: 2, color: '#ffffff' },
          },
          ...(selectedPoints
            ? {
                selected: { marker: { opacity: 1, line: { width: 3, color: '#22d3ee' } } },
                unselected: { marker: { opacity: 0.25 } },
              }
            : {}),
          showlegend: false,
        },
      ],
      nodesCurveNumber, // Store this for use in event handlers
      config: { 
        displayModeBar: false, 
        scrollZoom: true, 
        doubleClick: 'reset' as const, 
        responsive: true,
        // Ensure clicks work even when dragmode is active
        staticPlot: false,
      },
    }
  }, [graphData, selectedNodes])

  // Compute dragmode from interactionMode
  const dragmode = interactionMode === 'pointer' ? 'select' : interactionMode
  
  // Layout includes dragmode so it updates when mode changes
  const plotLayout = useMemo(() => {
    return {
      showlegend: false,
      hovermode: 'closest' as const,
      margin: { b: 0, l: 0, r: 0, t: 0 },
      xaxis: { showgrid: false, zeroline: false, showticklabels: false },
      yaxis: { showgrid: false, zeroline: false, showticklabels: false },
      dragmode: dragmode as 'pan' | 'zoom' | 'select',
      autosize: true,
      template: 'plotly_dark' as unknown as Plotly.Template,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    }
  }, [dragmode])

  const normalizedSearch = search.trim().toLowerCase()
  const searchMatches = useMemo(() => {
    if (!graphData) return []
    if (!normalizedSearch) return []
    return graphData.nodes.filter((n) => n.name.toLowerCase().includes(normalizedSearch))
  }, [graphData, normalizedSearch])

  const pickNode = async (name: string, opts?: { focus?: boolean }) => {
    setSelectedNodes([name])
    setNodePopover(null)
    if (opts?.focus) {
      // Let Plotly update selection styles first.
      requestAnimationFrame(() => {
        focusSelection()
      })
    }
  }

  const relayout = async (update: Record<string, any>) => {
    const gd = plotDivRef.current
    if (!gd) return
    try {
      const mod: any = await import('plotly.js')
      const Plotly = mod?.default ?? mod
      await Plotly.relayout(gd, update)
    } catch {
      // ignore
    }
  }

  const handleResetView = async () => {
    await relayout({ 'xaxis.autorange': true, 'yaxis.autorange': true })
  }

  const handleZoomOut = async () => {
    const gd = plotDivRef.current
    if (!gd) return
    const xRange = gd?.layout?.xaxis?.range
    const yRange = gd?.layout?.yaxis?.range
    if (!Array.isArray(xRange) || !Array.isArray(yRange) || xRange.length < 2 || yRange.length < 2) {
      await handleResetView()
      return
    }
    const [x0, x1] = xRange
    const [y0, y1] = yRange
    const pad = 0.12
    const dx = (x1 - x0) * pad
    const dy = (y1 - y0) * pad
    await relayout({ 'xaxis.range': [x0 - dx, x1 + dx], 'yaxis.range': [y0 - dy, y1 + dy] })
  }

  const handleZoomIn = async () => {
    const gd = plotDivRef.current
    if (!gd) return
    const xRange = gd?.layout?.xaxis?.range
    const yRange = gd?.layout?.yaxis?.range
    if (!Array.isArray(xRange) || !Array.isArray(yRange) || xRange.length < 2 || yRange.length < 2) {
      // If we're fully autoranged, a "zoom in" isn't well-defined; keep it simple.
      return
    }
    const [x0, x1] = xRange
    const [y0, y1] = yRange
    const pad = 0.12
    const dx = (x1 - x0) * pad
    const dy = (y1 - y0) * pad
    const nextX0 = x0 + dx
    const nextX1 = x1 - dx
    const nextY0 = y0 + dy
    const nextY1 = y1 - dy
    if (!(nextX1 > nextX0) || !(nextY1 > nextY0)) return
    await relayout({ 'xaxis.range': [nextX0, nextX1], 'yaxis.range': [nextY0, nextY1] })
  }

  const selectedDetails = useMemo(() => {
    if (!graphData || selectedNodes.length === 0) return []
    const map = new Map(graphData.nodes.map((n) => [n.name, n] as const))
    return selectedNodes.map((n) => map.get(n)).filter((v): v is GraphNode => Boolean(v))
  }, [graphData, selectedNodes])

  const clearSelection = () => setSelectedNodes([])

  const addToSelection = (name: string) => {
    setSelectedNodes((prev) => (prev.includes(name) ? prev : [...prev, name]))
  }

  const copySelection = async () => {
    if (selectedNodes.length === 0) return
    try {
      await navigator?.clipboard?.writeText(selectedNodes.join('\n'))
      toast({ title: 'Copied', description: `${selectedNodes.length} node(s) copied`, variant: 'success' })
    } catch {
      toast({ title: 'Copy failed', description: 'Could not access clipboard', variant: 'error' })
    }
  }

  const focusSelection = async () => {
    if (!graphData || selectedNodes.length === 0) return
    const pts = selectedNodes
      .map((n) => graphData.nodePositions[n])
      .filter((p): p is [number, number] => Array.isArray(p) && p.length === 2)
    if (pts.length === 0) return

    const xs = pts.map((p) => p[0])
    const ys = pts.map((p) => p[1])
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)
    const pad = 0.25
    const dx = Math.max(0.5, (maxX - minX) * pad)
    const dy = Math.max(0.5, (maxY - minY) * pad)
    await relayout({ 'xaxis.range': [minX - dx, maxX + dx], 'yaxis.range': [minY - dy, maxY + dy] })
  }

  const selectedNeighbors = useMemo(() => {
    if (!graphData || selectedNodes.length !== 1) return []
    const selected = selectedNodes[0]
    const neighbors: { name: string; similarity: number }[] = []
    for (const e of graphData.edges) {
      if (e.source === selected) neighbors.push({ name: e.target, similarity: e.similarity })
      else if (e.target === selected) neighbors.push({ name: e.source, similarity: e.similarity })
    }
    neighbors.sort((a, b) => b.similarity - a.similarity)
    return neighbors.slice(0, 10)
  }, [graphData, selectedNodes])

  useEffect(() => {
    if (!nodePopover) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setNodePopover(null)
    }
    const onDown = (e: MouseEvent) => {
      const pop = document.getElementById('node-popover')
      if (!pop) return
      if (pop.contains(e.target as Node)) return
      setNodePopover(null)
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('mousedown', onDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('mousedown', onDown)
    }
  }, [nodePopover])

  // Handle panel resize
  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!resizeRef.current) return
      const delta = resizeRef.current.startX - e.clientX
      const newWidth = Math.min(600, Math.max(280, resizeRef.current.startWidth + delta))
      setRightSidebarWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      resizeRef.current = null
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing])

  const startResize = (e: React.MouseEvent) => {
    e.preventDefault()
    resizeRef.current = { startX: e.clientX, startWidth: rightSidebarWidth }
    setIsResizing(true)
  }

  useEffect(() => {
    const gd = plotDivRef.current
    if (!gd) return

    const target =
      (gd.querySelector?.('.nsewdrag') as HTMLElement | null) ??
      (gd.querySelector?.('.draglayer') as HTMLElement | null) ??
      (gd as HTMLElement)

    const cursorForMode = () => {
      if (interactionMode === 'pointer') return 'pointer'
      if (interactionMode === 'pan') return 'grab'
      return 'crosshair'
    }

    const apply = () => {
      if (!target) return
      target.style.cursor = cursorForMode()
    }

    const onDown = () => {
      if (!target) return
      if (interactionMode === 'pan') target.style.cursor = 'grabbing'
    }
    const onUp = () => apply()
    apply()

    target?.addEventListener?.('mousedown', onDown)
    window.addEventListener('mouseup', onUp)
    return () => {
      target?.removeEventListener?.('mousedown', onDown)
      window.removeEventListener('mouseup', onUp)
    }
  }, [interactionMode])

  return (
    <TooltipProvider delayDuration={75} skipDelayDuration={0}>
      <div className="h-full min-h-0 overflow-hidden flex flex-col text-[0.95rem] p-0 md:p-0 bg-slate-50 dark:bg-slate-900">

        {/* Canvas + Side Panel */}
        <div className="relative bg-white dark:bg-slate-900 overflow-hidden flex flex-col md:flex-row flex-1 min-h-0">
          {/* Small screens: collapsible top panel */}
          <div className="md:hidden border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
            <details className="group">
              <summary className="list-none cursor-pointer select-none flex items-center justify-between px-4 py-3 text-sm font-medium text-slate-900 dark:text-slate-100">
                <span>Graph Controls</span>
                <ChevronDown className="h-4 w-4 text-slate-400 dark:text-slate-500 transition-transform group-open:rotate-180" />
              </summary>
              <div className="px-4 pb-4 space-y-4">
                {selectedNodes.length > 0 && (
                  <div className="bg-white dark:bg-slate-800 rounded-2xl p-3 border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Selection</p>
                        <p className="text-xs text-slate-600 dark:text-slate-400">{selectedNodes.length} selected</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={focusSelection}
                          className="text-xs font-medium text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700"
                        >
                          Focus
                        </button>
                        <button
                          type="button"
                          onClick={clearSelection}
                          className="text-xs font-medium text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                    <div className="mt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={copySelection}
                        className="text-xs font-medium text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700"
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                )}

                <div className="bg-white dark:bg-slate-800 rounded-2xl p-3">
                  <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Search</label>
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                    <input
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && searchMatches.length > 0) {
                          pickNode(searchMatches[0].name, { focus: true })
                        }
                      }}
                      placeholder="Search nodes..."
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 pl-10 pr-8 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    />
                    {search.trim().length > 0 && (
                      <button
                        type="button"
                        onClick={() => setSearch('')}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-600"
                        aria-label="Clear search"
                      >
                        <X className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                      </button>
                    )}
                  </div>
                  {searchMatches.length > 0 && (
                    <div className="mt-2 bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2 max-h-32 overflow-auto">
                      <p className="text-xs text-slate-600 dark:text-slate-400 px-1 mb-1">{searchMatches.length} matches</p>
                      {searchMatches.slice(0, 6).map((n) => (
                        <button
                          key={n.name}
                          type="button"
                          onClick={() => pickNode(n.name, { focus: true })}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-white dark:hover:bg-slate-600 text-sm text-slate-900 dark:text-slate-100 font-mono"
                        >
                          {n.name}
                        </button>
                      ))}
                      {searchMatches.length > 6 && (
                        <p className="text-xs text-slate-500 dark:text-slate-500 px-2 pt-1">+{searchMatches.length - 6} more</p>
                      )}
                    </div>
                  )}
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-2xl p-3 space-y-3">
                  <div>
                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Node Type</label>
                    <NativeSelect
                      value={nodeTypeFilter}
                      onChange={(e) => setNodeTypeFilter(e.target.value as NodeType)}
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    >
                      <NativeSelectOption value="All">All Types</NativeSelectOption>
                      <NativeSelectOption value="Person">Person</NativeSelectOption>
                      <NativeSelectOption value="Document">Document</NativeSelectOption>
                      <NativeSelectOption value="Concept">Concept</NativeSelectOption>
                      <NativeSelectOption value="Organization">Organization</NativeSelectOption>
                    </NativeSelect>
                  </div>

                  <div>
                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Layout</label>
                    <NativeSelect
                      value={layoutType}
                      onChange={(e) => setLayoutType(e.target.value as LayoutType)}
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    >
                      <NativeSelectOption value="Force-directed">Force-directed</NativeSelectOption>
                      <NativeSelectOption value="Hierarchical">Hierarchical</NativeSelectOption>
                      <NativeSelectOption value="Circular">Circular</NativeSelectOption>
                      <NativeSelectOption value="Random">Random</NativeSelectOption>
                    </NativeSelect>
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm text-slate-700 dark:text-slate-300 mb-2">
                      <span>Depth</span>
                      <span className="text-slate-900 dark:text-slate-100 font-medium">{depth}</span>
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={depth}
                      onChange={(e) => setDepth(parseInt(e.target.value))}
                      className="w-full accent-cyan-600 dark:accent-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Max Nodes</label>
                    <input
                      type="number"
                      min="10"
                      max="100"
                      value={maxNodes}
                      onChange={(e) => setMaxNodes(parseInt(e.target.value))}
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-2xl p-3">
                  <details className="group/cypher">
                    <summary className="list-none cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-900 dark:text-slate-100">
                      <span>Cypher Query Builder</span>
                      <ChevronDown className="h-4 w-4 text-slate-400 dark:text-slate-500 transition-transform group-open/cypher:rotate-180" />
                    </summary>
                    <div className="mt-3 space-y-3">
                      <textarea
                        value={cypherQuery}
                        onChange={(e) => setCypherQuery(e.target.value)}
                        className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm font-mono bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent resize-none"
                        rows={3}
                      />
                      <div className="flex flex-wrap gap-2 justify-end">
                        <button
                          onClick={handleGenerate}
                          disabled={loading}
                          className="inline-flex items-center gap-2 bg-cyan-600 dark:bg-emerald-600 text-white px-4 py-2 text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 transition-colors"
                        >
                          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                          Generate
                        </button>
                        <button
                          onClick={async () => {
                            try {
                              await navigator?.clipboard?.writeText(cypherQuery)
                              toast({ title: 'Copied', description: 'Cypher query copied to clipboard', variant: 'success' })
                            } catch {
                              toast({ title: 'Copy failed', description: 'Could not access clipboard', variant: 'error' })
                            }
                          }}
                          className="text-sm font-medium text-slate-700 dark:text-slate-300 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                          Copy Query
                        </button>
                      </div>
                    </div>
                  </details>
                </div>
              </div>
            </details>
          </div>

          {/* Graph canvas */}
          <div ref={canvasRef} className="relative flex-1 min-h-[60vh] md:min-h-0 min-w-0">
            {/* Tool dock (left) */}
            <div className="absolute left-3 top-3 md:top-1/2 md:-translate-y-1/2 z-20">
              <div className="flex md:flex-col gap-1 rounded-xl bg-transparent backdrop-blur-xl border border-white/40 shadow-lg shadow-black/10 p-1.5">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => {
                        setInteractionMode('pointer')
                      }}
                      className={`h-8 w-8 grid place-items-center rounded-lg transition-colors ${
                        interactionMode === 'pointer' ? 'bg-cyan-600 dark:bg-emerald-600 text-white shadow-sm' : 'hover:bg-white/60 dark:hover:bg-slate-700/60 text-slate-600 dark:text-slate-300'
                      }`}
                      aria-label="Cursor"
                    >
                      <MousePointer2 className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Cursor</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => {
                        setInteractionMode('pan')
                      }}
                      className={`h-8 w-8 grid place-items-center rounded-lg transition-colors ${
                        interactionMode === 'pan' ? 'bg-cyan-600 dark:bg-emerald-600 text-white shadow-sm' : 'hover:bg-white/60 dark:hover:bg-slate-700/60 text-slate-600 dark:text-slate-300'
                      }`}
                      aria-label="Pan"
                    >
                      <Hand className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Pan</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => setInteractionMode('zoom')}
                      className={`h-8 w-8 grid place-items-center rounded-lg transition-colors ${
                        interactionMode === 'zoom' ? 'bg-cyan-600 dark:bg-emerald-600 text-white shadow-sm' : 'hover:bg-white/60 dark:hover:bg-slate-700/60 text-slate-600 dark:text-slate-300'
                      }`}
                      aria-label="Box zoom"
                    >
                      <Scissors className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Box zoom</TooltipContent>
                </Tooltip>

                <div className="hidden md:block w-full h-px bg-gray-300/50 my-1" />

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={handleZoomIn}
                      className="h-8 w-8 grid place-items-center rounded-lg transition-colors hover:bg-white/60 text-gray-600"
                      aria-label="Zoom in"
                    >
                      <ZoomIn className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Zoom in</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={handleZoomOut}
                      className="h-8 w-8 grid place-items-center rounded-lg transition-colors hover:bg-white/60 text-gray-600"
                      aria-label="Zoom out"
                    >
                      <ZoomOut className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Zoom out</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={handleResetView}
                      className="h-8 w-8 grid place-items-center rounded-lg transition-colors hover:bg-white/60 text-gray-600"
                      aria-label="Reset view"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Reset view</TooltipContent>
                </Tooltip>
              </div>
            </div>

            {/* Plotly */}
            <div className="relative z-10 h-full min-h-[60vh] md:min-h-0">
              {loading ? (
                <div className="flex items-center justify-center h-[60vh] md:h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-2 border-gray-200 border-t-gray-900 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-500">Loading graph data...</p>
                  </div>
                </div>
              ) : plotData ? (
                <Plot
                  data={plotData.data}
                  layout={plotLayout}
                  config={plotData.config}
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler
                  onInitialized={(_figure, gd) => {
                    plotDivRef.current = gd
                  }}
                  onUpdate={(_figure, gd) => {
                    plotDivRef.current = gd
                  }}
                  onSelected={(e: Readonly<PlotSelectionEvent>) => {
                    if (!e?.points || !graphData || !plotData) return
                    
                    const pts = e.points.filter((p) => p.curveNumber === plotData.nodesCurveNumber)
                    const names = pts
                      .map((p) => graphData.nodes?.[p.pointIndex]?.name ?? p.text)
                      .filter((v): v is string => typeof v === 'string')
                
                    // Only auto-select if it's a drag selection (multiple points)
                    // Single clicks should show the popover via onClick instead
                    if (names.length > 1) {
                      setSelectedNodes(Array.from(new Set(names)))
                      setNodePopover(null)
                    } else if (names.length === 1) {
                      // Single point selection - let onClick handle showing popover
                      // But if it's already selected, we can update the selection
                      if (selectedNodes.includes(names[0])) {
                        // Already selected, just update (might be a re-selection)
                        setSelectedNodes([names[0]])
                        setNodePopover(null)
                      }
                      // Otherwise, onClick will show the popover
                    }
                  }}
                  onDeselect={() => {
                    setSelectedNodes([])
                    setNodePopover(null)
                  }}
                  onClick={(e: Readonly<PlotMouseEvent>) => {
                    if (!e?.points?.length || !graphData || !plotData) return
                    
                    // Find the node point (check all points in case the first isn't a node)
                    let nodePoint = null
                    let nodeName: string | null = null
                    
                    for (const p of e.points) {
                      // Nodes are at the nodesCurveNumber
                      if (p.curveNumber === plotData.nodesCurveNumber) {
                        const name = graphData.nodes?.[p.pointIndex]?.name ?? (p as { text?: string }).text
                        if (typeof name === 'string') {
                          nodePoint = p
                          nodeName = name
                          break
                        }
                      }
                    }
                    
                    console.log('[onClick] node clicked:', nodeName)
                    if (!nodeName) return
                    
                    const shift = Boolean((e.event as MouseEvent)?.shiftKey)
                    if (shift) {
                      // Shift+click: add to selection immediately
                      setSelectedNodes((prev) => {
                        if (prev.includes(nodeName!)) return prev
                        return [...prev, nodeName!]
                      })
                      setNodePopover(null)
                      return
                    }

                    const native = e?.event as MouseEvent | undefined
                    if (!native) {
                      setNodePopover({ name: nodeName, screenX: 24, screenY: 24 })
                      return
                    }
                    const rect = canvasRef.current?.getBoundingClientRect()
                    const x = rect ? native.clientX - rect.left : native.clientX
                    const y = rect ? native.clientY - rect.top : native.clientY
                    setNodePopover({ name: nodeName, screenX: x, screenY: y })
                  }}
                />
              ) : (
                <div className="flex items-center justify-center h-[60vh] md:h-full">
                  <p className="text-sm text-gray-500">No graph data available</p>
                </div>
              )}
            </div>

            {/* Frederick logo watermark */}
            <div className="pointer-events-none absolute bottom-1 left-4 z-20 opacity-75">
              <Image
                src="/logo.webp"
                alt="Frederick AI"
                width={100}
                height={100}
                className="h-28 w-28 object-contain"
                priority={false}
              />
            </div>

            {nodePopover && (
              <div
                id="node-popover"
                className="absolute z-30 w-[min(280px,calc(100%-2rem))] rounded-2xl bg-white/70 backdrop-blur-xl border border-white/40 shadow-lg shadow-black/10 p-4"
                style={{
                  left: Math.max(12, Math.min(nodePopover.screenX, (canvasRef.current?.clientWidth ?? 600) - 292)),
                  top: Math.max(12, Math.min(nodePopover.screenY, (canvasRef.current?.clientHeight ?? 400) - 160)),
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{nodePopover.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Type: {graphData?.nodes?.find((n) => n.name === nodePopover.name)?.type ?? 'Unknown'}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setNodePopover(null)}
                    className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
                    aria-label="Close"
                  >
                    <X className="h-4 w-4 text-gray-400" />
                  </button>
                </div>

                <div className="mt-3 flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => pickNode(nodePopover.name)}
                    className="text-sm font-medium text-gray-700 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    Select
                  </button>
                  <button
                    type="button"
                    onClick={() => pickNode(nodePopover.name, { focus: true })}
                    className="text-sm font-medium text-white bg-cyan-600 dark:bg-emerald-600 px-3 py-1.5 rounded-lg hover:bg-cyan-700 dark:hover:bg-emerald-700 transition-colors"
                  >
                    Focus
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right-side control panel (desktop) */}
          {rightSidebarOpen ? (
            <aside 
              className="hidden md:flex md:flex-col border-l border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 relative"
              style={{ width: rightSidebarWidth }}
            >
              {/* Resize handle */}
              <div
                onMouseDown={startResize}
                className={`absolute left-0 top-0 bottom-0 w-1 cursor-col-resize group z-20 ${isResizing ? 'bg-slate-400' : ''}`}
              >
                <div className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 w-2 h-8 rounded-full transition-all ${
                  isResizing ? 'bg-slate-400' : 'bg-slate-300 dark:bg-slate-600 group-hover:bg-slate-400 dark:group-hover:bg-slate-500'
                }`} />
              </div>

              <div className="p-5 space-y-5 overflow-y-auto flex-1">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100">Graph Controls</h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{graphData?.nodes.length ?? 0} nodes</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleGenerate}
                      disabled={loading}
                      className="inline-flex items-center gap-2 bg-cyan-600 dark:bg-emerald-600 text-white px-4 py-2 text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 transition-colors"
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                      Generate
                    </button>
                    <button
                      type="button"
                      onClick={() => setRightSidebarOpen(false)}
                      className="p-2 rounded-xl border border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      aria-label="Collapse sidebar"
                    >
                      <ChevronRight className="h-4 w-4 text-slate-600 dark:text-slate-400" />
                    </button>
                  </div>
                </div>

                {/* Selection Card */}
                {selectedNodes.length > 0 && (
                  <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Selection</p>
                        <p className="text-xs text-slate-600 dark:text-slate-400">{selectedNodes.length} node(s) selected</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={focusSelection}
                          className="text-xs font-medium text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                          Focus
                        </button>
                        <button
                          type="button"
                          onClick={clearSelection}
                          className="text-xs font-medium text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                          Clear
                        </button>
                      </div>
                    </div>

                    {selectedDetails.length === 1 && (
                      <div className="space-y-2">
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          <p className="font-mono text-slate-900 dark:text-slate-100 break-all">{selectedDetails[0].name}</p>
                          <p className="mt-1">Type: <span className="text-slate-900 dark:text-slate-100">{selectedDetails[0].type}</span></p>
                        </div>
                        {selectedNeighbors.length > 0 && (
                          <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                            <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Connected Nodes</p>
                            <div className="space-y-1.5 max-h-32 overflow-auto">
                              {selectedNeighbors.map((n) => (
                                <div key={n.name} className="flex items-center justify-between gap-2 text-xs">
                                  <button
                                    type="button"
                                    className="font-mono text-slate-900 dark:text-slate-100 hover:text-slate-600 dark:hover:text-slate-400 truncate text-left"
                                    onClick={() => pickNode(n.name, { focus: true })}
                                  >
                                    {n.name}
                                  </button>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    <span className="text-slate-500 dark:text-slate-400">{(n.similarity * 100).toFixed(0)}%</span>
                                    <button
                                      type="button"
                                      className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                                      onClick={() => addToSelection(n.name)}
                                    >
                                      + Add
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {selectedNodes.length > 1 && (
                      <div className="mt-2 max-h-24 overflow-auto bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2 text-xs font-mono text-slate-700 dark:text-slate-300">
                        {selectedNodes.map((n) => (
                          <div key={n} className="truncate py-0.5">{n}</div>
                        ))}
                      </div>
                    )}

                    <div className="mt-3 flex justify-end">
                      <button
                        type="button"
                        onClick={copySelection}
                        className="text-xs font-medium text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                      >
                        Copy to Clipboard
                      </button>
                    </div>
                  </div>
                )}

                {/* Search */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4">
                  <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Search Nodes</label>
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                    <input
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && searchMatches.length > 0) {
                          pickNode(searchMatches[0].name, { focus: true })
                        }
                      }}
                      placeholder="Search nodes..."
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 pl-10 pr-8 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    />
                    {search.trim().length > 0 && (
                      <button
                        type="button"
                        onClick={() => setSearch('')}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors"
                        aria-label="Clear search"
                      >
                        <X className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                      </button>
                    )}
                  </div>
                  {searchMatches.length > 0 && (
                    <div className="mt-2 bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2 max-h-36 overflow-auto">
                      <p className="text-xs text-slate-600 dark:text-slate-400 px-1 mb-1">{searchMatches.length} matches</p>
                      {searchMatches.slice(0, 8).map((n) => (
                        <button
                          key={n.name}
                          type="button"
                          onClick={() => pickNode(n.name, { focus: true })}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-white dark:hover:bg-slate-600 text-sm text-slate-900 dark:text-slate-100 font-mono"
                        >
                          {n.name}
                        </button>
                      ))}
                      {searchMatches.length > 8 && (
                        <p className="text-xs text-slate-500 dark:text-slate-500 px-2 pt-1">+{searchMatches.length - 8} more</p>
                      )}
                    </div>
                  )}
                </div>

                {/* Filters */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 space-y-4">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Filters</p>
                  
                  <div>
                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Node Type</label>
                    <NativeSelect
                      value={nodeTypeFilter}
                      onChange={(e) => setNodeTypeFilter(e.target.value as NodeType)}
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    >
                      <NativeSelectOption value="All">All Types</NativeSelectOption>
                      <NativeSelectOption value="Person">Person</NativeSelectOption>
                      <NativeSelectOption value="Document">Document</NativeSelectOption>
                      <NativeSelectOption value="Concept">Concept</NativeSelectOption>
                      <NativeSelectOption value="Organization">Organization</NativeSelectOption>
                    </NativeSelect>
                  </div>

                  <div>
                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Layout</label>
                    <NativeSelect
                      value={layoutType}
                      onChange={(e) => setLayoutType(e.target.value as LayoutType)}
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    >
                      <NativeSelectOption value="Force-directed">Force-directed</NativeSelectOption>
                      <NativeSelectOption value="Hierarchical">Hierarchical</NativeSelectOption>
                      <NativeSelectOption value="Circular">Circular</NativeSelectOption>
                      <NativeSelectOption value="Random">Random</NativeSelectOption>
                    </NativeSelect>
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm text-slate-700 dark:text-slate-300 mb-2">
                      <span>Depth</span>
                      <span className="text-slate-900 dark:text-slate-100 font-medium">{depth}</span>
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={depth}
                      onChange={(e) => setDepth(parseInt(e.target.value))}
                      className="w-full accent-cyan-600 dark:accent-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Max Nodes</label>
                    <input
                      type="number"
                      min="10"
                      max="100"
                      value={maxNodes}
                      onChange={(e) => setMaxNodes(parseInt(e.target.value))}
                      className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Cypher Query */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4">
                  <details className="group">
                    <summary className="list-none cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-900 dark:text-slate-100">
                      <span>Cypher Query Builder</span>
                      <ChevronDown className="h-4 w-4 text-slate-400 dark:text-slate-500 transition-transform group-open:rotate-180" />
                    </summary>
                    <div className="mt-3 space-y-3">
                      <textarea
                        value={cypherQuery}
                        onChange={(e) => setCypherQuery(e.target.value)}
                        className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm font-mono bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent resize-none"
                        rows={4}
                      />
                      <div className="flex justify-end">
                        <button
                          onClick={async () => {
                            try {
                              await navigator?.clipboard?.writeText(cypherQuery)
                              toast({ title: 'Copied', description: 'Cypher query copied to clipboard', variant: 'success' })
                            } catch {
                              toast({ title: 'Copy failed', description: 'Could not access clipboard', variant: 'error' })
                            }
                          }}
                          className="text-sm font-medium text-slate-700 dark:text-slate-300 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                          Copy Query
                        </button>
                      </div>
                    </div>
                  </details>
                </div>
              </div>
            </aside>
          ) : (
            <div className="hidden md:flex md:flex-col w-12 border-l border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 items-center py-3">
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={() => setRightSidebarOpen(true)}
                    className="h-9 w-9 grid place-items-center rounded-lg hover:bg-gray-100 transition-colors text-gray-600"
                    aria-label="Expand sidebar"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="left">Expand controls</TooltipContent>
              </Tooltip>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}

