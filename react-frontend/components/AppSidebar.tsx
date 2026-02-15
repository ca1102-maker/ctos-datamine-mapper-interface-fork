'use client'

import Image from 'next/image'
import { Target, Network, BarChart3, MessageCircle, LayoutDashboard, Menu, PanelLeftClose, Download, Upload, Home } from 'lucide-react'
import SettingsPanel from './SettingsPanel'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useToast } from '@/components/ui/toast'

interface Category {
  id: string
  name: string
  icon: any
}

interface AppSidebarProps {
  currentPage: string | null
  onNavigate: (category: string | null) => void
  isOpen: boolean
  onToggle: () => void
}

export default function AppSidebar({ currentPage, onNavigate, isOpen, onToggle }: AppSidebarProps) {
  const { toast } = useToast()

  const handleExportData = () => {
    toast({ title: 'Data Export Initiated', description: 'Exporting data (dev)...', variant: 'default' })
  }
  const categories: Category[] = [
    {
      id: 'home',
      name: 'Home',
      icon: Home,
    },
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'graph',
      name: 'Graph Visualization',
      icon: Network,
    },
    {
      id: 'analysis',
      name: 'Performance Metrics',
      icon: BarChart3,
    },
    {
      id: 'fileupload',
      name: 'File Upload',
      icon: Upload,
    },
    {
      id: 'mapping',
      name: 'Semantic Mapping',
      icon: Target,
    },
    {
      id: 'feedback',
      name: 'Feedback Portal',
      icon: MessageCircle,
    },
  ]

  return (
    <TooltipProvider delayDuration={75} skipDelayDuration={0}>
      <aside
        className={`bg-slate-50 dark:bg-gray-900 border-r border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden transition-[width] duration-300 ease-in-out ${
          isOpen ? 'w-64' : 'w-16'
        }`}
      >
        {/* Header */}
        <div className="border-slate-200 dark:border-slate-900 h-16 px-3 flex items-center bg-slate-50 dark:bg-gray-900 relative">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {/* Logo area stays in the same spot; in collapsed mode it swaps to the hamburger on hover */}
            <div className="relative w-10 h-10 group/logo flex-shrink-0">
              <div
                className={`absolute inset-0 grid place-items-center transition-opacity duration-200 ${
                  isOpen ? 'opacity-100' : 'opacity-100 group-hover/logo:opacity-0 group-focus-within/logo:opacity-0'
                }`}
              >
                <div className="relative w-8 h-8">
                  <Image
                    src="/logo-transparent.png"
                    alt="Frederick Platform Logo"
                    fill
                    className="object-contain"
                    priority
                  />
                </div>
              </div>

              {!isOpen && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={onToggle}
                      className="absolute inset-0 grid place-items-center rounded-lg transition-all duration-200 opacity-0 pointer-events-none group-hover/logo:opacity-100 group-hover/logo:pointer-events-auto group-focus-within/logo:opacity-100 group-focus-within/logo:pointer-events-auto hover:bg-slate-100 dark:hover:bg-slate-800"
                      aria-label="Open sidebar"
                      type="button"
                    >
                      <Menu className="w-5 h-5 text-slate-600 dark:text-slate-400 translate-x-1" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right" align="center">
                    Open sidebar
                  </TooltipContent>
                </Tooltip>
              )}
            </div>

            <h1
              className={`text-md font-medium text-slate-900 dark:text-slate-100 whitespace-nowrap transition-all duration-300 ${
                isOpen ? 'opacity-100 -translate-x-3' : 'opacity-0 -translate-x-2 w-0 overflow-hidden'
              }`}
            >
              Frederick Platform
            </h1>
          </div>

          {/* Collapse button only shows in expanded state (keeps header height constant) */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onToggle}
                className={`p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all flex-shrink-0 ${
                  isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
                }`}
                aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
                tabIndex={isOpen ? 0 : -1}
                type="button"
              >
                <PanelLeftClose className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              </button>
            </TooltipTrigger>
            {isOpen && (
              <TooltipContent side="right" align="center">
                Close sidebar
              </TooltipContent>
            )}
          </Tooltip>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2">
          <div className="space-y-1">
            {categories.map((category) => {
              const Icon = category.icon
              const isActive = currentPage === category.id || (currentPage === null && category.id === 'home')

              const button = (
                <button
                  key={category.id}
                  onClick={() => onNavigate(category.id === 'home' ? null : category.id)}
                  className={`w-full h-9 flex items-center justify-start rounded-lg transition-all ${
                    isOpen ? 'gap-3 px-3' : 'px-3 justify-center'
                  } ${
                    isActive
                      ? 'bg-cyan-600 dark:bg-emerald-600 font-medium text-white'
                      : 'text-slate-900 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                  type="button"
                  aria-label={category.name}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-600 dark:text-slate-400'}`} />
                  <span
                    className={`text-sm font-regular whitespace-nowrap transition-all duration-300 ${
                      isOpen ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-2 w-0 overflow-hidden'
                    }`}
                  >
                    {category.name}
                  </span>
                </button>
              )

              if (isOpen) return button

              return (
                <Tooltip key={category.id}>
                  <TooltipTrigger asChild>{button}</TooltipTrigger>
                  <TooltipContent side="right" align="center">
                    {category.name}
                  </TooltipContent>
                </Tooltip>
              )
            })}
          </div>
          {isOpen && (
            <div className="mt-4 border-t border-slate-200 dark:border-slate-700 pt-4">
              <p className="px-3 pb-2 text-[14px] font-medium text-slate-600 dark:text-slate-400">Quick stats</p>
              <div className="grid grid-cols-2 gap-2 px-2">
                <div className="flex flex-col justify-between bg-white dark:bg-slate-800 rounded-lg p-3">
                  <p className="text-sm text-slate-600 dark:text-slate-400">Active users</p>
                  <p className="text-slate-900 dark:text-slate-100 font-semibold text-xl leading-tight">2,847</p>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">↑ 12%</p>
                </div>
                <div className="flex flex-col justify-between bg-white dark:bg-slate-800 rounded-lg p-3">
                  <p className="text-sm text-slate-600 dark:text-slate-400">Documents</p>
                  <p className="text-slate-900 dark:text-slate-100 font-semibold text-xl leading-tight">15.2K</p>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">↑ 8%</p>
                </div>
              </div>
            </div>
          )}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-700">
          {isOpen ? (
            <button
              className="w-full h-10 flex items-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors gap-3 px-3 justify-start"
              type="button"
              onClick={handleExportData}
            >
              <Download className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              <span className="text-sm text-slate-700 dark:text-slate-300">Export Data</span>
            </button>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  className="w-full flex items-center justify-center px-2 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  type="button"
                  aria-label="Export Data"
                  onClick={handleExportData}
                >
                  <Download className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" align="center">
                Export Data
              </TooltipContent>
            </Tooltip>
          )}

          <div className={isOpen ? 'mt-2' : 'mt-3 flex justify-center'}>
            {isOpen ? <SettingsPanel /> : <SettingsPanel compact />}
          </div>
        </div>
      </aside>
    </TooltipProvider>
  )
}

