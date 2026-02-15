'use client'

import { useState, useMemo } from 'react'
import { Search, ArrowRight, Download, X } from 'lucide-react'

type MappingDirection = 'forward' | 'bidirectional'
type Confidence = 'high' | 'medium' | 'low'
type MatchType = 'exact' | 'synonym' | 'broader' | 'narrower' | 'related'

const SOURCES = ['SNOMED CT', 'ICD-10', 'LOINC', 'RxNorm', 'MedDRA', 'NCI'] as const
type Source = (typeof SOURCES)[number]

type MappingResult = {
  sourceTerm: string
  mappedTerm: string
    matchType: MatchType
    score: number
    confidence: Confidence
    source: Source
  conceptId: string
}

const CONFIDENCE_STYLES: Record<Confidence, { label: string; color: string }> = {
    high: { label: 'High', color: 'bg-emerald-100 text-emerald-700' },
    medium: { label: 'Medium', color: 'bg-amber-100 text-amber-700' },
    low: { label: 'Low', color: 'bg-gray-100 text-gray-600' },
}

const MATCH_LABELS: Record<MatchType, string> = {
    exact: 'Exact',
    synonym: 'Synonym',
    broader: 'Broader',
    narrower: 'Narrower',
    related: 'Related',
}

// Deterministic random for stable mock data
function hash(s: string): number {
  let h = 2166136261
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return ((h >>> 0) % 100000) / 100000
}

export default function SemanticMapping() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<MappingResult[]>([])
  const [loading, setLoading] = useState(false)
    const [direction, setDirection] = useState<MappingDirection>('forward')
    const [selectedSources, setSelectedSources] = useState<Source[]>(['SNOMED CT', 'ICD-10', 'LOINC'])
    const [threshold, setThreshold] = useState(0.7)

    const toggleSource = (source: Source) => {
        setSelectedSources(prev =>
            prev.includes(source)
                ? prev.filter(s => s !== source)
                : [...prev, source]
        )
    }

    const runMapping = async () => {
        if (!query.trim()) return
        setLoading(true)

        await new Promise(r => setTimeout(r, 500))

        const terms = query.split('\n').map(t => t.trim()).filter(Boolean)
        const sources = selectedSources.length > 0 ? selectedSources : [...SOURCES]
        const matchTypes: MatchType[] = ['exact', 'synonym', 'broader', 'narrower', 'related']

        const mockResults: MappingResult[] = []
    for (const term of terms) {
            for (let i = 0; i < 3; i++) {
                const score = 0.6 + hash(`${term}:${i}`) * 0.4
                if (score < threshold) continue

                const confidence: Confidence = score >= 0.9 ? 'high' : score >= 0.75 ? 'medium' : 'low'
        const source = sources[i % sources.length]

                mockResults.push({
                    sourceTerm: term,
                    mappedTerm: `${source} concept for "${term}"`,
          matchType: matchTypes[i % matchTypes.length],
                    score: Number(score.toFixed(3)),
          confidence,
          source,
                    conceptId: `C${Math.floor(100000 + hash(`${term}:cid:${i}`) * 900000)}`,
                })
            }
        }

        mockResults.sort((a, b) => b.score - a.score)
        setResults(mockResults.slice(0, 20))
        setLoading(false)
  }

  const exportCsv = () => {
        if (!results.length) return
        const header = ['Source Term', 'Mapped Term', 'Match Type', 'Score', 'Confidence', 'Source', 'Concept ID']
        const rows = results.map(r => [r.sourceTerm, r.mappedTerm, r.matchType, r.score, r.confidence, r.source, r.conceptId].map(v => `"${v}"`).join(','))
    const csv = [header.join(','), ...rows].join('\n')
        const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
        a.download = `mapping-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

    const stats = useMemo(() => {
        if (!results.length) return null
        const avgScore = results.reduce((sum, r) => sum + r.score, 0) / results.length
        const highConf = results.filter(r => r.confidence === 'high').length
        const sources = new Set(results.map(r => r.source)).size
        return { total: results.length, avgScore, highConf, sources }
    }, [results])

  return (
        <div className="min-h-full bg-slate-50 dark:bg-slate-900 overflow-auto">
            <div className="px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-xl font-medium text-slate-900 dark:text-slate-100">Semantic Mapping</h1>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Map medical terms to standardized terminology systems.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Input */}
                        <div className="bg-white rounded-2xl p-6">
                            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Terms to map</label>
            <textarea
              value={query}
                                onChange={e => setQuery(e.target.value)}
                                placeholder="Enter terms, one per line...&#10;&#10;Example:&#10;Hypertension&#10;Type 2 Diabetes&#10;Aspirin"
                                rows={5}
                                className="w-full border bg-slate-50 dark:bg-slate-800 p-3 text-sm rounded-xl outline-none resize-none transition-colors placeholder:text-slate-400 dark:placeholder:text-slate-500 border-slate-200 dark:border-slate-600 focus:border-slate-400 dark:focus:border-slate-500 focus:bg-white dark:focus:bg-slate-700 text-slate-900 dark:text-slate-100"
                            />

                            <div className="mt-6 flex items-center justify-between">
                                <button
                                    type="button"
                                    onClick={() => setQuery('Hypertension\nType 2 Diabetes\nAspirin\nAtrial Fibrillation')}
                                    className="text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                                >
                                    Load example
          </button>
          <button
                                    type="button"
                                    onClick={runMapping}
            disabled={loading || !query.trim()}
                                    className="inline-flex items-center gap-2 bg-cyan-600 dark:bg-emerald-600 text-white px-5 py-2.5 text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
                                    {loading ? 'Mapping...' : 'Map Terms'}
                                    {!loading && <ArrowRight className="w-4 h-4" />}
          </button>
        </div>
      </div>

                        {/* Config */}
                        <div className="bg-white rounded-2xl p-6">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm text-gray-700 mb-2">Direction</label>
                                    <div className="flex gap-2">
                                        {(['forward', 'bidirectional'] as MappingDirection[]).map(d => (
                                            <button
                                                key={d}
                                                type="button"
                                                onClick={() => setDirection(d)}
                                                className={`px-4 py-2 text-sm rounded-xl capitalize transition-colors ${
                                                    direction === d
                                                        ? 'bg-cyan-600 dark:bg-emerald-600 text-white'
                                                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                                }`}
                                            >
                                                {d === 'forward' ? 'Forward' : 'Bidirectional'}
                                            </button>
                                        ))}
                                    </div>
                                </div>

          <div>
                                    <label className="block text-sm text-gray-700 mb-2">
                                        Threshold: {threshold.toFixed(2)}
            </label>
            <input
              type="range"
                                        min={0.5}
                                        max={1}
                                        step={0.05}
              value={threshold}
                                        onChange={e => setThreshold(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          </div>

                            <div className="mt-6">
                                <label className="block text-sm text-gray-700 mb-2">Sources</label>
                                <div className="flex flex-wrap gap-2">
                                    {SOURCES.map(source => (
                                        <button
                                            key={source}
                                            type="button"
                                            onClick={() => toggleSource(source)}
                                            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                                                selectedSources.includes(source)
                                                    ? 'bg-cyan-600 dark:bg-emerald-600 text-white'
                                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                            }`}
                                        >
                                            {source}
                                        </button>
                                    ))}
          </div>
        </div>
      </div>

                        {/* Results */}
      {results.length > 0 && (
                            <div className="bg-white rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
                                    <p className="text-sm font-medium text-gray-900">Results</p>
            <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={exportCsv}
                                            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900"
                                        >
                <Download className="w-4 h-4" />
                Export
              </button>
                                        <button
                                            type="button"
                                            onClick={() => setResults([])}
                                            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900"
                                        >
                                            <X className="w-4 h-4" />
                                            Clear
              </button>
            </div>
          </div>

                                <div className="space-y-2">
                                    {results.map((r, i) => {
                                        const conf = CONFIDENCE_STYLES[r.confidence]
                                        return (
                                            <div key={i} className="p-3 bg-gray-50 rounded-xl">
                                                <div className="flex items-start justify-between gap-3">
                                                    <div className="min-w-0 flex-1">
                                                        <p className="text-sm text-gray-900 font-medium">{r.sourceTerm}</p>
                                                        <p className="text-sm text-gray-500 mt-0.5">{r.mappedTerm}</p>
            </div>
                                                    <div className="flex items-center gap-2 flex-shrink-0">
                                                        <span className="text-xs text-gray-500 tabular-nums">{r.score.toFixed(2)}</span>
                                                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${conf.color}`}>
                                                            {conf.label}
                      </span>
          </div>
            </div>
                                                <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                                                    <span>{MATCH_LABELS[r.matchType]}</span>
                                                    <span>·</span>
                                                    <span>{r.source}</span>
                                                    <span>·</span>
                                                    <span className="font-mono">{r.conceptId}</span>
              </div>
            </div>
                                        )
                                    })}
              </div>
            </div>
                        )}
                    </div>

                    {/* Sidebar */}
                    <aside className="space-y-5">
                        {stats && (
                            <div className="bg-white rounded-2xl p-5">
                                <p className="text-sm font-medium text-gray-900 mb-4">Summary</p>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-sm text-gray-500">Total mappings</span>
                                        <span className="text-sm text-gray-900 font-medium">{stats.total}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-sm text-gray-500">Avg score</span>
                                        <span className="text-sm text-gray-900 font-medium">{stats.avgScore.toFixed(3)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-sm text-gray-500">High confidence</span>
                                        <span className="text-sm text-gray-900 font-medium">{stats.highConf}</span>
              </div>
                                    <div className="flex justify-between">
                                        <span className="text-sm text-gray-500">Sources used</span>
                                        <span className="text-sm text-gray-900 font-medium">{stats.sources}</span>
            </div>
          </div>
        </div>
      )}

                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-3">Supported sources</p>
                            <div className="flex flex-wrap gap-1.5">
                                {SOURCES.map(s => (
                                    <span key={s} className="px-2 py-1 bg-gray-100 rounded-lg text-xs text-gray-600">
                                        {s}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-3">Tips</p>
                            <ul className="space-y-2 text-sm text-gray-500">
                                <li>Enter one term per line</li>
                                <li>Higher threshold = stricter matches</li>
                                <li>Select multiple sources for broader coverage</li>
                            </ul>
                        </div>
                    </aside>
                </div>
            </div>
    </div>
  )
}
