'use client'

import { useMemo } from 'react'
import dynamic from 'next/dynamic'
import { TrendingUp, Network, Target, Clock, Info } from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
import type PlotType from 'react-plotly.js'
import type { Data } from 'plotly.js'

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false }) as typeof PlotType

type Status = 'success' | 'warning' | 'error'

const STATUS_STYLES: Record<Status, { label: string; color: string }> = {
    success: { label: 'Success', color: 'bg-emerald-100 text-emerald-700' },
    warning: { label: 'Warning', color: 'bg-amber-100 text-amber-700' },
    error: { label: 'Error', color: 'bg-red-100 text-red-700' },
}

const ACTIVITIES = [
    { time: '10:00 AM', user: 'Alice Chen', action: 'Uploaded dataset', status: 'success' as Status },
    { time: '10:30 AM', user: 'Bob Smith', action: 'Ran analysis', status: 'success' as Status },
    { time: '11:00 AM', user: 'Carol Davis', action: 'Created visualization', status: 'warning' as Status },
    { time: '11:30 AM', user: 'David Lee', action: 'Exported report', status: 'success' as Status },
    { time: '12:00 PM', user: 'Emma Wilson', action: 'Updated model', status: 'success' as Status },
]

export default function Dashboard() {
    const queryData = useMemo(() => {
        const dates: string[] = []
        const queries: number[] = []
        const successful: number[] = []
        const startDate = new Date('2025-01-01')

        for (let i = 0; i < 30; i++) {
            const date = new Date(startDate)
            date.setDate(date.getDate() + i)
            dates.push(date.toISOString().split('T')[0])
            queries.push(1200 + (i * 37 % 800) + i * 10)
            successful.push(1100 + (i * 29 % 800) + i * 9)
        }

        return { dates, queries, successful }
    }, [])

    const queryVolumeData = useMemo((): Data[] => [
        {
            x: queryData.dates,
            y: queryData.queries,
            type: 'scatter' as const,
            mode: 'lines+markers' as const,
            name: 'Total Queries',
            line: { color: '#374151', width: 2 },
            marker: { size: 4 },
        },
        {
            x: queryData.dates,
            y: queryData.successful,
            type: 'scatter' as const,
            mode: 'lines+markers' as const,
            name: 'Successful',
            line: { color: '#10b981', width: 2 },
            marker: { size: 4 },
        },
    ], [queryData])

    const categoryData = useMemo((): Data[] => [{
        type: 'pie' as const,
        labels: ['Search', 'Analysis', 'Visualization', 'Export', 'Other'],
        values: [35, 28, 20, 12, 5],
        hole: 0.5,
        marker: { colors: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#6b7280'] },
        textinfo: 'percent' as const,
        textfont: { family: 'inherit', size: 12, color: '#374151' },
    }], [])

    const chartLayout = {
        height: 320,
        margin: { l: 40, r: 20, t: 20, b: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        showlegend: true,
        legend: { orientation: 'h' as const, y: -0.15, font: { size: 11, color: '#6b7280' } },
        xaxis: { gridcolor: '#f3f4f6', tickfont: { size: 10, color: '#9ca3af' } },
        yaxis: { gridcolor: '#f3f4f6', tickfont: { size: 10, color: '#9ca3af' } },
    }

    const pieLayout = {
        height: 320,
        margin: { l: 20, r: 20, t: 20, b: 20 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        showlegend: true,
        legend: { orientation: 'h' as const, y: -0.1, font: { size: 11, color: '#6b7280' } },
    }

    return (
        <div className="min-h-full bg-slate-50 dark:bg-slate-900 overflow-auto">
            <div className="px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-xl font-medium text-slate-900 dark:text-slate-100">Frederick Dashboard</h1>
                    <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">Overview of system performance and activity.</p>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <MetricCard
                        icon={Target}
                        label="Total Queries"
                        value="45,392"
                        change="+15.3%"
                        trend="up"
                        help="Total queries processed this month"
                    />
                    <MetricCard
                        icon={Network}
                        label="Graph Nodes"
                        value="8,247"
                        change="+523"
                        trend="up"
                        help="Total nodes in knowledge graph"
                    />
                    <MetricCard
                        icon={TrendingUp}
                        label="Accuracy"
                        value="94.2%"
                        change="+2.1%"
                        trend="up"
                        help="Model accuracy score"
                    />
                    <MetricCard
                        icon={Clock}
                        label="Response Time"
                        value="0.34s"
                        change="-0.08s"
                        trend="down"
                        help="Average response time"
                    />
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                    <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-6">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-4">Query Volume</p>
                        <Plot
                            data={queryVolumeData}
                            layout={chartLayout}
                            config={{ displayModeBar: false, responsive: true }}
                            style={{ width: '100%' }}
                        />
                    </div>

                    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-4">Query Categories</p>
                        <Plot
                            data={categoryData}
                            layout={pieLayout}
                            config={{ displayModeBar: false, responsive: true }}
                            style={{ width: '100%' }}
                        />
                    </div>
                </div>

                {/* Activity */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-6">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-4">Recent Activity</p>
                    <div className="space-y-2">
                        {ACTIVITIES.map((a, i) => {
                            const style = STATUS_STYLES[a.status]
                            return (
                                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
                                    <div className="flex items-center gap-4">
                                        <span className="text-xs text-slate-500 dark:text-slate-400 w-16">{a.time}</span>
                                        <span className="text-sm text-slate-900 dark:text-slate-100 font-medium w-28">{a.user}</span>
                                        <span className="text-sm text-slate-600 dark:text-slate-300">{a.action}</span>
                                    </div>
                                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${style.color}`}>
                                        {style.label}
                                    </span>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>
        </div>
    )
}

function MetricCard({
    icon: Icon,
    label,
    value,
    change,
    trend,
    help,
}: {
    icon: React.ComponentType<{ className?: string }>
    label: string
    value: string
    change: string
    trend: 'up' | 'down'
    help?: string
}) {
    const isPositive = trend === 'up'
    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
                <TooltipProvider delayDuration={0}>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <div className="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-300">
                                <Icon className="w-4 h-4" />
                                {label}
                                <Info className="w-3 h-3 text-slate-400 dark:text-slate-500" />
                            </div>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p className="text-xs">{help}</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </div>
            <div className="flex items-end justify-between">
                <span className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{value}</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    isPositive ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                }`}>
                    {isPositive ? '↑' : '↓'} {change}
                </span>
            </div>
        </div>
    )
}
