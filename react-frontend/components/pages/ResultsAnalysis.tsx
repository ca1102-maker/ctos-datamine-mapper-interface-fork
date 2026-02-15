'use client'

import { useState, useMemo, useCallback, useEffect } from 'react'
import { RefreshCw, Activity, TrendingUp, AlertCircle, Database, Info, Download } from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
import { useToast } from '@/components/ui/toast'
import dynamic from 'next/dynamic'
import type PlotType from 'react-plotly.js'

// Dynamic import for Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false }) as typeof PlotType

// Type definitions
type TabId = 'performance' | 'usage' | 'errors' | 'resources'

interface DateRange {
  start: string
  end: string
}

interface EndpointStat {
  endpoint: string
  calls: number
  avgTime: number
  successRate: string
}

interface ErrorStat {
  errorType: string
  count: number
  percentage: string
}

// Generate lognormal distribution for response times (like Streamlit)
function generateResponseTimes(count: number): number[] {
  const data: number[] = []
  for (let i = 0; i < count; i++) {
    const u1 = Math.random()
    const u2 = Math.random()
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
    data.push(Math.exp(z * 0.5))
  }
  return data
}

function generateThroughputData() {
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const throughput = hours.map(i => Math.floor(800 + Math.random() * 400) + i * 10)
  return { hours, throughput }
}

function getDefaultDateRange(): DateRange {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  }
}

export default function ResultsAnalysis() {
  const { toast } = useToast()
  
  // Client-side hydration flag
  const [isClient, setIsClient] = useState(false)
  const [dateRange, setDateRange] = useState<DateRange>({ start: '', end: '' })
  const [selectedTab, setSelectedTab] = useState<TabId>('performance')
  const [refreshKey, setRefreshKey] = useState(0)

  // Client-only random data state (initialized empty to avoid hydration mismatch)
  const [responseTimes, setResponseTimes] = useState<number[]>([])
  const [throughputData, setThroughputData] = useState({ hours: [] as number[], throughput: [] as number[] })
  const [cpuUsage, setCpuUsage] = useState<number[]>([])
  const [memoryUsage, setMemoryUsage] = useState<number[]>([])

  // Initialize data on client only (after hydration)
  useEffect(() => {
    setIsClient(true)
    setDateRange(getDefaultDateRange())
    setResponseTimes(generateResponseTimes(1000))
    setThroughputData(generateThroughputData())
    setCpuUsage(Array.from({ length: 60 }, () => Math.floor(40 + Math.random() * 40)))
    setMemoryUsage(Array.from({ length: 60 }, () => Math.floor(50 + Math.random() * 20)))
  }, [])

  // Regenerate data on refresh
  useEffect(() => {
    if (refreshKey > 0) {
      setResponseTimes(generateResponseTimes(1000))
      setThroughputData(generateThroughputData())
      setCpuUsage(Array.from({ length: 60 }, () => Math.floor(40 + Math.random() * 40)))
      setMemoryUsage(Array.from({ length: 60 }, () => Math.floor(50 + Math.random() * 20)))
    }
  }, [refreshKey])

  const endpointStats = useMemo<EndpointStat[]>(() => [
    { endpoint: '/search', calls: 15234, avgTime: 234, successRate: '99.2%' },
    { endpoint: '/analyze', calls: 8921, avgTime: 567, successRate: '97.8%' },
    { endpoint: '/graph', calls: 6547, avgTime: 890, successRate: '95.3%' },
    { endpoint: '/upload', calls: 3210, avgTime: 123, successRate: '99.9%' },
    { endpoint: '/export', calls: 1876, avgTime: 456, successRate: '98.1%' },
  ], [])

  const errorStats = useMemo<ErrorStat[]>(() => [
    { errorType: 'Timeout', count: 45, percentage: '16.7%' },
    { errorType: 'Bad Request', count: 123, percentage: '45.6%' },
    { errorType: 'Server Error', count: 12, percentage: '4.4%' },
    { errorType: 'Not Found', count: 67, percentage: '24.8%' },
    { errorType: 'Auth Failed', count: 23, percentage: '8.5%' },
  ], [])

  const handleRefresh = useCallback(() => {
    setRefreshKey(prev => prev + 1)
  }, [])

  const handleExport = useCallback(() => {
    toast({ title: 'Export Started', description: 'User data export initiated', variant: 'success' })
  }, [toast])

  const handleDateChange = useCallback((field: 'start' | 'end', value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }))
  }, [])

  return (
    <TooltipProvider>
      <div className="min-h-full bg-slate-50 dark:bg-slate-900 overflow-auto">
        <div className="px-8 py-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-xl font-medium text-slate-900 dark:text-slate-100">Performance Metrics</h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Monitor system performance, usage, and resource utilization.
            </p>
          </div>

          {/* Date Range Selector */}
          <div className="bg-white rounded-2xl p-5 mb-6">
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 mb-2">
                  Select Date Range
                </label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => handleDateChange('start', e.target.value)}
                    max={dateRange.end}
                    className="flex-1 border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                  />
                  <input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => handleDateChange('end', e.target.value)}
                    min={dateRange.start}
                    className="flex-1 border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleRefresh}
                  className="inline-flex items-center gap-2 bg-cyan-600 dark:bg-emerald-600 text-white px-5 py-2.5 text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh Metrics
                </button>
                <button
                  type="button"
                  onClick={handleExport}
                  className="inline-flex items-center gap-2 border border-gray-300 text-gray-700 px-5 py-2.5 text-sm font-medium rounded-xl hover:bg-gray-50 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Export Data
                </button>
              </div>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <MetricCard
              label="Avg Response Time"
              value="0.34s"
              change="-12%"
              trend="down"
              helpText="Average query response time"
            />
            <MetricCard
              label="Success Rate"
              value="94.2%"
              change="+2.1%"
              trend="up"
              helpText="Percentage of successful queries"
            />
            <MetricCard
              label="Active Sessions"
              value="127"
              change="+15"
              trend="up"
              helpText="Current active user sessions"
            />
            <MetricCard
              label="Error Rate"
              value="0.8%"
              change="-0.3%"
              trend="down"
              helpText="Percentage of failed requests"
            />
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b border-gray-200">
            {[
              { id: 'performance' as const, label: 'Performance', icon: Activity },
              { id: 'usage' as const, label: 'Usage', icon: TrendingUp },
              { id: 'errors' as const, label: 'Errors', icon: AlertCircle },
              { id: 'resources' as const, label: 'Resources', icon: Database },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setSelectedTab(id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
                  selectedTab === id
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {selectedTab === 'performance' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Response Time Distribution</h3>
                <Plot
                  data={[{
                    x: responseTimes,
                    type: 'histogram' as const,
                    nbinsx: 30,
                    marker: { color: '#4fc3f7' },
                  } as Plotly.Data]}
                  layout={{
                    height: 300,
                    margin: { l: 50, r: 30, t: 20, b: 50 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    xaxis: { 
                      title: 'Response Time (s)', 
                      gridcolor: '#e5e7eb',
                      tickfont: { size: 11, color: '#6b7280' }
                    },
                    yaxis: { 
                      title: 'Frequency',
                      gridcolor: '#e5e7eb',
                      tickfont: { size: 11, color: '#6b7280' }
                    },
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%' }}
                />
              </div>

              <div className="bg-white rounded-2xl p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Throughput Over Time</h3>
                <Plot
                  data={[{
                    x: throughputData.hours,
                    y: throughputData.throughput,
                    type: 'bar' as const,
                    marker: { color: '#4caf50' },
                  }]}
                  layout={{
                    height: 300,
                    margin: { l: 50, r: 30, t: 20, b: 50 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    xaxis: { 
                      title: 'Hour of Day',
                      gridcolor: '#e5e7eb',
                      tickfont: { size: 11, color: '#6b7280' }
                    },
                    yaxis: { 
                      title: 'Requests/Hour',
                      gridcolor: '#e5e7eb',
                      tickfont: { size: 11, color: '#6b7280' }
                    },
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}

          {selectedTab === 'usage' && (
            <div className="bg-white rounded-2xl p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-4">API Usage Statistics</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Endpoint</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-700">Calls</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-700">Avg Time (ms)</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-700">Success Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {endpointStats.map((stat, idx) => (
                      <tr key={stat.endpoint} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                        <td className="py-3 px-4 text-gray-900 font-mono text-xs">{stat.endpoint}</td>
                        <td className="py-3 px-4 text-right text-gray-900">{stat.calls.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-gray-900">{stat.avgTime}</td>
                        <td className="py-3 px-4 text-right text-gray-900">{stat.successRate}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedTab === 'errors' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white rounded-2xl p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Error Analysis</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-700">Error Type</th>
                        <th className="text-right py-3 px-4 font-medium text-gray-700">Count</th>
                        <th className="text-right py-3 px-4 font-medium text-gray-700">Percentage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {errorStats.map((stat, idx) => (
                        <tr key={stat.errorType} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                          <td className="py-3 px-4 text-gray-900">{stat.errorType}</td>
                          <td className="py-3 px-4 text-right text-gray-900">{stat.count}</td>
                          <td className="py-3 px-4 text-right text-gray-900">{stat.percentage}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6">
                <Plot
                  data={[{
                    type: 'pie' as const,
                    labels: errorStats.map(s => s.errorType),
                    values: errorStats.map(s => s.count),
                    hole: 0.4,
                    marker: {
                      colors: ['#ef4444', '#f59e0b', '#eab308', '#84cc16', '#22c55e'],
                    },
                  }]}
                  layout={{
                    height: 250,
                    margin: { l: 20, r: 20, t: 20, b: 20 },
                    paper_bgcolor: 'transparent',
                    showlegend: false,
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}

          {selectedTab === 'resources' && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-4">System Resources</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-2xl p-6">
                  {isClient && cpuUsage.length > 0 && (
                  <Plot
                    data={[{
                      y: cpuUsage,
                      type: 'scatter' as const,
                      mode: 'lines' as const,
                      line: { color: '#ff9800', width: 2 },
                    }]}
                    layout={{
                      title: { text: 'CPU Usage (%)', font: { size: 14, color: '#374151' } },
                      height: 250,
                      margin: { l: 50, r: 30, t: 40, b: 40 },
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      xaxis: { 
                        gridcolor: '#e5e7eb',
                        tickfont: { size: 11, color: '#6b7280' },
                        showticklabels: false
                      },
                      yaxis: { 
                        gridcolor: '#e5e7eb',
                        tickfont: { size: 11, color: '#6b7280' }
                      },
                      showlegend: false,
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    style={{ width: '100%' }}
                  />
                  )}
                </div>

                <div className="bg-white rounded-2xl p-6">
                  {isClient && memoryUsage.length > 0 && (
                  <Plot
                    data={[{
                      y: memoryUsage,
                      type: 'scatter' as const,
                      mode: 'lines' as const,
                      line: { color: '#9c27b0', width: 2 },
                    }]}
                    layout={{
                      title: { text: 'Memory Usage (%)', font: { size: 14, color: '#374151' } },
                      height: 250,
                      margin: { l: 50, r: 30, t: 40, b: 40 },
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      xaxis: { 
                        gridcolor: '#e5e7eb',
                        tickfont: { size: 11, color: '#6b7280' },
                        showticklabels: false
                      },
                      yaxis: { 
                        gridcolor: '#e5e7eb',
                        tickfont: { size: 11, color: '#6b7280' }
                      },
                      showlegend: false,
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    style={{ width: '100%' }}
                  />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}

// Metric Card Component
function MetricCard({
  label,
  value,
  change,
  trend,
  helpText,
}: {
  label: string
  value: string
  change: string
  trend: 'up' | 'down'
  helpText: string
}) {
  return (
    <div className="bg-white rounded-2xl p-5">
      <div className="flex items-center justify-between mb-3">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-1.5 text-sm text-gray-600 cursor-help">
              {label}
              <Info className="w-3.5 h-3.5 text-gray-400" />
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p className="text-xs">{helpText}</p>
          </TooltipContent>
        </Tooltip>
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-semibold text-gray-900">{value}</span>
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            trend === 'down'
              ? 'bg-emerald-100 text-emerald-700'
              : 'bg-blue-100 text-blue-700'
          }`}
        >
          {trend === 'up' ? '↑' : '↓'} {change}
        </span>
      </div>
    </div>
  )
}
