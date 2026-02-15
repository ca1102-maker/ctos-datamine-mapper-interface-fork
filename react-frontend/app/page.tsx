'use client'

import { useState } from 'react'
import AppSidebar from '@/components/AppSidebar'
import HomePage from '@/components/pages/Home'
import Dashboard from '@/components/pages/Dashboard'
import SemanticMapping from '@/components/pages/SemanticMapping'
import GraphVisualization from '@/components/pages/GraphVisualization'
import FileUpload from '@/components/pages/FileUpload'
import SMEFeedback from '@/components/pages/SMEFeedback'
import ResultsAnalysis from '@/components/pages/ResultsAnalysis'

export default function Home() {
  const [currentPage, setCurrentPage] = useState<string | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const handleNavigate = (category: string | null) => {
    setCurrentPage(category)
  }

  return (
    <div className="flex h-screen bg-white text-gray-900">
      {/* Sidebar - visible on all pages */}
      <AppSidebar 
        currentPage={currentPage} 
        onNavigate={handleNavigate}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Content */}
      <main
        className={`flex-1 flex flex-col overflow-hidden bg-white relative ${
          isSidebarOpen ? 'shadow-md' : ''
        }`}
      >
        {currentPage === null ? (
          <HomePage onNavigate={handleNavigate} />
        ) : (
          <div className="flex-1 overflow-y-auto">
            {currentPage === 'dashboard' && <Dashboard />}
            {currentPage === 'mapping' && <SemanticMapping />}
            {currentPage === 'graph' && <GraphVisualization />}
            {currentPage === 'fileupload' && <FileUpload />}
            {currentPage === 'analysis' && <ResultsAnalysis />}
            {currentPage === 'feedback' && <SMEFeedback />}
          </div>
        )}
      </main>
    </div>
  )
}

