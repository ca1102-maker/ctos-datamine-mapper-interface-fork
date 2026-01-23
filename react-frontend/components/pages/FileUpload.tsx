'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { UploadCloud, X, Check, FileText, ArrowRight, Loader2 } from 'lucide-react'

type UploadStatus = 'ready' | 'uploading' | 'done' | 'error'
type JobStatus = 'running' | 'completed' | 'failed'

type UploadItem = {
  id: string
  file: File
  status: UploadStatus
  progress: number
}

type UploadType = 'training' | 'validation' | 'test' | 'knowledge'
type TargetModel = 'rag' | 'classification' | 'ner' | 'custom'

const UPLOAD_TYPES = [
    { value: 'training' as const, label: 'Training' },
    { value: 'validation' as const, label: 'Validation' },
    { value: 'test' as const, label: 'Test' },
    { value: 'knowledge' as const, label: 'Knowledge Base' },
]

const MODELS = [
    { value: 'rag' as const, label: 'RAG Model v2.0' },
    { value: 'classification' as const, label: 'Classification v1.5' },
    { value: 'ner' as const, label: 'NER v3.0' },
    { value: 'custom' as const, label: 'Custom' },
]

const RECENT_JOBS = [
    { id: 'TRN-0846', model: 'RAG Model v2.0', files: 12, status: 'completed' as JobStatus, date: 'Jan 20' },
    { id: 'TRN-0845', model: 'Classification v1.5', files: 8, status: 'running' as JobStatus, date: 'Jan 19' },
    { id: 'TRN-0844', model: 'NER v3.0', files: 15, status: 'completed' as JobStatus, date: 'Jan 18' },
    { id: 'TRN-0843', model: 'RAG Model v1.9', files: 10, status: 'failed' as JobStatus, date: 'Jan 17' },
]

const JOB_STATUS: Record<JobStatus, { label: string; color: string }> = {
    running: { label: 'Running', color: 'bg-blue-100 text-blue-700' },
    completed: { label: 'Completed', color: 'bg-emerald-100 text-emerald-700' },
    failed: { label: 'Failed', color: 'bg-red-100 text-red-700' },
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB'] as const
  const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)))
  const val = bytes / Math.pow(1024, i)
  return `${val.toFixed(val >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

function makeId(file: File): string {
  return `${file.name}:${file.size}:${file.lastModified}`
}

export default function FileUpload() {
    const inputRef = useRef<HTMLInputElement>(null)
  const dragDepth = useRef(0)

  const [items, setItems] = useState<UploadItem[]>([])
  const [isDragging, setIsDragging] = useState(false)
    const [uploadType, setUploadType] = useState<UploadType>('training')
    const [targetModel, setTargetModel] = useState<TargetModel>('rag')
    const [uploading, setUploading] = useState(false)

  const stats = useMemo(() => {
    const total = items.length
        const done = items.filter(i => i.status === 'done').length
        const totalBytes = items.reduce((sum, i) => sum + i.file.size, 0)
        return { total, done, totalBytes }
  }, [items])

  const addFiles = (files: File[]) => {
    if (!files.length) return
        setItems(prev => {
            const seen = new Set(prev.map(p => p.id))
            const next = [...prev]
      for (const f of files) {
        const id = makeId(f)
                if (!seen.has(id)) {
        seen.add(id)
        next.push({ id, file: f, status: 'ready', progress: 0 })
                }
      }
      return next
    })
  }

  const startUpload = () => {
        setUploading(true)
        setItems(prev => prev.map(i => i.status === 'done' ? i : { ...i, status: 'uploading', progress: 5 }))
  }

  const clearAll = () => setItems([])
    const removeOne = (id: string) => setItems(prev => prev.filter(i => i.id !== id))

    useEffect(() => {
        const hasUploading = items.some(i => i.status === 'uploading')
        if (!hasUploading) {
            setUploading(false)
            return
        }

        const t = setInterval(() => {
            setItems(prev => prev.map(i => {
          if (i.status !== 'uploading') return i
                const next = Math.min(100, i.progress + 8 + Math.random() * 12)
          if (next >= 100) return { ...i, status: 'done', progress: 100 }
          return { ...i, progress: next }
            }))
        }, 200)

        return () => clearInterval(t)
  }, [items])

  return (
        <div className="min-h-full bg-slate-50 dark:bg-slate-900 overflow-auto">
            <div className="px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-xl font-medium text-slate-900 dark:text-slate-100">Upload Files</h1>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Upload training data, validation sets, or knowledge base files.</p>
            </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Upload Config */}
                        <div className="bg-white rounded-2xl p-6">
                            <div className="mb-6">
                                <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Data type</label>
                                <div className="flex flex-wrap gap-2">
                                    {UPLOAD_TYPES.map(t => (
                                        <button
                                            key={t.value}
                                            type="button"
                                            onClick={() => setUploadType(t.value)}
                                            className={`px-4 py-2 text-sm rounded-xl transition-colors ${
                                                uploadType === t.value
                                                    ? 'bg-cyan-600 dark:bg-emerald-600 text-white'
                                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                            }`}
                                        >
                                            {t.label}
                                        </button>
                                    ))}
            </div>
          </div>

            <div>
                                <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Target model</label>
                                <div className="flex flex-wrap gap-2">
                                    {MODELS.map(m => (
              <button
                                            key={m.value}
                type="button"
                                            onClick={() => setTargetModel(m.value)}
                                            className={`px-4 py-2 text-sm rounded-xl transition-colors ${
                                                targetModel === m.value
                                                    ? 'bg-cyan-600 dark:bg-emerald-600 text-white'
                                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                            }`}
                                        >
                                            {m.label}
              </button>
                                    ))}
                                </div>
            </div>
          </div>

                        {/* Dropzone */}
                        <div className="bg-white rounded-2xl p-6">
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
                                onKeyDown={e => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                inputRef.current?.click()
              }
            }}
                                onDragEnter={e => {
              e.preventDefault()
                                    dragDepth.current++
              setIsDragging(true)
            }}
                                onDragOver={e => e.preventDefault()}
                                onDragLeave={e => {
              e.preventDefault()
                                    dragDepth.current--
              if (dragDepth.current <= 0) {
                dragDepth.current = 0
                setIsDragging(false)
              }
            }}
                                onDrop={e => {
              e.preventDefault()
              dragDepth.current = 0
              setIsDragging(false)
                                    addFiles(Array.from(e.dataTransfer.files))
            }}
                                className={`rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors outline-none ${
              isDragging
                                        ? 'border-gray-400 bg-gray-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}
          >
            <input
              ref={inputRef}
              type="file"
              multiple
                                    accept=".pdf,.txt,.csv,.json,.doc,.docx,.xlsx"
              className="hidden"
                                    onChange={e => {
                                        if (e.target.files) addFiles(Array.from(e.target.files))
                                        e.target.value = ''
                                    }}
                                />
                                <UploadCloud className={`w-8 h-8 mx-auto mb-3 ${isDragging ? 'text-gray-600' : 'text-gray-400'}`} />
                                <p className="text-sm text-gray-900 font-medium">
                                    {isDragging ? 'Drop files here' : 'Drop files or click to browse'}
                                </p>
                                <p className="text-xs text-gray-400 mt-1">CSV, JSON, TXT, PDF, XLSX</p>
              </div>

                            {/* File List */}
        {items.length > 0 && (
                                <div className="mt-6 space-y-2">
                                    {items.map(item => (
                                        <div key={item.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                                            <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between gap-2">
                                                    <p className="text-sm text-gray-900 truncate">{item.file.name}</p>
                      <div className="flex items-center gap-2 flex-shrink-0">
                                                        {item.status === 'uploading' && (
                                                            <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                                                        )}
                                                        {item.status === 'done' && (
                                                            <Check className="w-4 h-4 text-emerald-500" />
                                                        )}
                        <button
                          type="button"
                                                            onClick={() => removeOne(item.id)}
                                                            disabled={item.status === 'uploading'}
                                                            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                                                        >
                                                            <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full rounded-full transition-all ${
                                                                item.status === 'done' ? 'bg-emerald-500' : 'bg-gray-400'
                                                            }`}
                                                            style={{ width: `${item.progress}%` }}
                        />
                      </div>
                                                    <span className="text-xs text-gray-400 tabular-nums w-8">
                                                        {Math.round(item.progress)}%
                                                    </span>
                    </div>
                  </div>
                </div>
                ))}
              </div>
                            )}

                            {/* Actions */}
                            {items.length > 0 && (
                                <div className="mt-6 flex items-center justify-between">
                                    <p className="text-sm text-gray-500">
                                        {stats.done}/{stats.total} uploaded · {formatBytes(stats.totalBytes)}
                                    </p>
                                    <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={clearAll}
                                            disabled={uploading}
                                            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
                                        >
                                            Clear
                                        </button>
                  <button
                    type="button"
                                            onClick={startUpload}
                                            disabled={uploading || stats.done === stats.total}
                                            className="inline-flex items-center gap-2 bg-cyan-600 dark:bg-emerald-600 text-white px-5 py-2 text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                                        >
                                            {uploading ? 'Uploading...' : 'Upload'}
                                            {!uploading && <ArrowRight className="w-4 h-4" />}
                  </button>
                </div>
                                </div>
                            )}
                        </div>
                      </div>

                    {/* Sidebar */}
                    <aside className="space-y-5">
                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-4">Recent Jobs</p>
                            <div className="space-y-3">
                                {RECENT_JOBS.map(job => {
                                    const style = JOB_STATUS[job.status]
                                    return (
                                        <div key={job.id} className="p-3 bg-gray-50 rounded-xl">
                                            <div className="flex items-start justify-between gap-2 mb-1">
                                                <p className="text-sm text-gray-900 line-clamp-1 flex-1">{job.model}</p>
                                                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${style.color}`}>
                                                    {style.label}
                                                </span>
                  </div>
                                            <p className="text-xs text-gray-400">{job.id} · {job.files} files · {job.date}</p>
              </div>
                                    )
                                })}
              </div>
            </div>

                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-3">Accepted formats</p>
                            <div className="flex flex-wrap gap-1.5">
                                {['CSV', 'JSON', 'TXT', 'PDF', 'XLSX'].map(ext => (
                                    <span key={ext} className="px-2 py-1 bg-gray-100 rounded-lg text-xs text-gray-600">
                                        {ext}
                                    </span>
                                ))}
              </div>
            </div>

                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-3">Tips</p>
                            <ul className="space-y-2 text-sm text-gray-500">
                                <li>Use CSV for structured term lists</li>
                                <li>JSON supports nested relationships</li>
                                <li>Max file size: 50MB per file</li>
                            </ul>
                </div>
                    </aside>
        </div>
      </div>
    </div>
  )
}
