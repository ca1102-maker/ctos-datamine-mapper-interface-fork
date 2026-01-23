'use client'

import { useState, useRef, useId, useCallback } from 'react'
import { ArrowRight, Paperclip, X, Check, FileText } from 'lucide-react'

type FeedbackType = 'mapping' | 'missing' | 'suggestion' | 'relationship' | 'platform' | 'other'
type Priority = 'low' | 'medium' | 'high' | 'critical'
type Status = 'pending' | 'reviewing' | 'done'

const TYPES: { value: FeedbackType; label: string }[] = [
    { value: 'mapping', label: 'Incorrect mapping' },
    { value: 'missing', label: 'Missing term' },
    { value: 'suggestion', label: 'Suggestion' },
    { value: 'relationship', label: 'Relationship' },
    { value: 'platform', label: 'Platform' },
    { value: 'other', label: 'Other' },
]

const HISTORY = [
    { id: 'FB-234', subject: 'SNOMED mapping for atrial fibrillation', status: 'reviewing' as Status, date: 'Jan 19' },
    { id: 'FB-198', subject: 'CAR-T cell therapy terminology', status: 'done' as Status, date: 'Jan 17' },
    { id: 'FB-156', subject: 'HTN synonym for Hypertension', status: 'done' as Status, date: 'Jan 15' },
    { id: 'FB-142', subject: 'Drug interaction hierarchy error', status: 'pending' as Status, date: 'Jan 12' },
]

const STATUS_STYLES: Record<Status, { label: string; color: string }> = {
    pending: { label: 'Pending', color: 'bg-gray-100 text-gray-600' },
    reviewing: { label: 'In Review', color: 'bg-amber-100 text-amber-700' },
    done: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700' },
}

export default function SMEFeedback() {
    const id = useId()
    const fileRef = useRef<HTMLInputElement>(null)

    const [form, setForm] = useState({
        name: '',
        email: '',
        type: '' as FeedbackType | '',
        priority: 'medium' as Priority,
        subject: '',
        term: '',
        conceptId: '',
        description: '',
    })
    const [files, setFiles] = useState<File[]>([])
    const [sending, setSending] = useState(false)
    const [sent, setSent] = useState(false)
    const [sentId, setSentId] = useState('')
    const [errors, setErrors] = useState<Record<string, boolean>>({})

    const set = useCallback(<K extends keyof typeof form>(k: K, v: typeof form[K]) => {
        setForm(p => ({ ...p, [k]: v }))
        if (errors[k]) setErrors(p => { const n = { ...p }; delete n[k]; return n })
    }, [errors])

    const validate = () => {
        const e: Record<string, boolean> = {}
        if (!form.name.trim()) e.name = true
        if (!form.email.trim() || !/\S+@\S+\.\S+/.test(form.email)) e.email = true
        if (!form.type) e.type = true
        if (!form.subject.trim()) e.subject = true
        if (form.description.trim().length < 30) e.description = true
        setErrors(e)
        return !Object.keys(e).length
    }

    const submit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!validate()) return
        setSending(true)
        await new Promise(r => setTimeout(r, 800))
        setSentId(`FB-${Math.floor(Math.random() * 900) + 100}`)
        setSent(true)
        setSending(false)
    }

    const reset = () => {
        setForm({ name: '', email: '', type: '', priority: 'medium', subject: '', term: '', conceptId: '', description: '' })
        setFiles([])
        setSent(false)
        setErrors({})
    }

    if (sent) {
        return (
            <div className="min-h-full flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-8">
                <div className="bg-white rounded-2xl p-10 text-center max-w-sm">
                    <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mx-auto mb-5">
                        <Check className="w-7 h-7 text-emerald-600" />
                    </div>
                    <p className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-1">Submitted</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">Reference: {sentId}</p>
                    <button onClick={reset} className="px-5 py-2.5 bg-cyan-600 dark:bg-emerald-600 text-white text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 transition-colors">
                        Submit another
                    </button>
                </div>
            </div>
        )
    }

    const charCount = form.description.trim().length
    const charOk = charCount >= 30

    return (
        <div className="min-h-full bg-slate-50 dark:bg-slate-900 overflow-auto">
            <div className="px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-xl font-medium text-slate-900 dark:text-slate-100">Submit Feedback</h1>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Report issues or suggest improvements to terminology mappings.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Form */}
                    <form onSubmit={submit} className="lg:col-span-2 bg-white rounded-2xl p-6">
                        {/* Contact */}
                        <div className="grid grid-cols-2 gap-4 mb-8">
                            <div>
                                <label htmlFor={`${id}-name`} className="block text-sm text-gray-700 mb-1">Name</label>
                                <input
                                    id={`${id}-name`}
                                    type="text"
                                    value={form.name}
                                    onChange={e => set('name', e.target.value)}
                                    className={`w-full border-b bg-transparent py-1.5 text-sm outline-none transition-colors ${errors.name ? 'border-red-400' : 'border-gray-200 focus:border-gray-900'}`}
                                />
                            </div>
                            <div>
                                <label htmlFor={`${id}-email`} className="block text-sm text-gray-700 mb-1">Email</label>
                                <input
                                    id={`${id}-email`}
                                    type="email"
                                    value={form.email}
                                    onChange={e => set('email', e.target.value)}
                                    className={`w-full border-b bg-transparent py-1.5 text-sm outline-none transition-colors ${errors.email ? 'border-red-400' : 'border-gray-200 focus:border-gray-900'}`}
                                />
                            </div>
                        </div>

                        {/* Type */}
                        <div className="mb-8">
                            <label className="block text-sm text-gray-700 mb-2">
                                Issue type {errors.type && <span className="text-red-500">*</span>}
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {TYPES.map(t => (
                                    <button
                                        key={t.value}
                                        type="button"
                                        onClick={() => set('type', t.value)}
                                        className={`px-4 py-2 text-sm rounded-xl transition-colors ${
                                            form.type === t.value
                                                ? 'bg-cyan-600 dark:bg-emerald-600 text-white'
                                                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                        }`}
                                    >
                                        {t.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Priority */}
                        <div className="mb-8">
                            <label className="block text-sm text-gray-700 mb-2">Priority</label>
                            <div className="flex gap-2">
                                {(['low', 'medium', 'high', 'critical'] as Priority[]).map(p => (
                                    <button
                                        key={p}
                                        type="button"
                                        onClick={() => set('priority', p)}
                                        className={`px-4 py-2 text-sm rounded-xl capitalize transition-colors ${
                                            form.priority === p
                                                ? p === 'critical' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' 
                                                : p === 'high' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                                                : 'bg-cyan-600 dark:bg-emerald-600 text-white'
                                                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                                        }`}
                                    >
                                        {p === 'medium' ? 'normal' : p}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Subject */}
                        <div className="mb-6">
                            <label htmlFor={`${id}-subj`} className="block text-sm text-gray-700 mb-1">Subject</label>
                            <input
                                id={`${id}-subj`}
                                type="text"
                                value={form.subject}
                                onChange={e => set('subject', e.target.value)}
                                placeholder="Brief summary"
                                className={`w-full border-b bg-transparent py-1.5 text-sm outline-none transition-colors placeholder:text-gray-400 ${errors.subject ? 'border-red-400' : 'border-gray-200 focus:border-gray-900'}`}
                            />
                        </div>

                        {/* Term + Concept */}
                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div>
                                <label htmlFor={`${id}-term`} className="block text-sm text-gray-500 mb-1">Term reference</label>
                                <input
                                    id={`${id}-term`}
                                    type="text"
                                    value={form.term}
                                    onChange={e => set('term', e.target.value)}
                                    placeholder="Optional"
                                    className="w-full border-b border-gray-200 bg-transparent py-1.5 text-sm outline-none focus:border-gray-900 transition-colors placeholder:text-gray-400"
                                />
                            </div>
                            <div>
                                <label htmlFor={`${id}-cid`} className="block text-sm text-gray-500 mb-1">Concept ID</label>
                                <input
                                    id={`${id}-cid`}
                                    type="text"
                                    value={form.conceptId}
                                    onChange={e => set('conceptId', e.target.value)}
                                    placeholder="Optional"
                                    className="w-full border-b border-gray-200 bg-transparent py-1.5 text-sm font-mono outline-none focus:border-gray-900 transition-colors placeholder:text-gray-400"
                                />
                            </div>
                        </div>

                        {/* Description */}
                        <div className="mb-6">
                            <label htmlFor={`${id}-desc`} className="block text-sm text-gray-700 mb-1">Description</label>
                            <textarea
                                id={`${id}-desc`}
                                value={form.description}
                                onChange={e => set('description', e.target.value)}
                                placeholder="What happened? What did you expect?"
                                rows={4}
                                className={`w-full border bg-gray-50 p-3 text-sm rounded-xl outline-none resize-none transition-colors placeholder:text-gray-400 ${errors.description ? 'border-red-400' : 'border-gray-200 focus:border-gray-400 focus:bg-white'}`}
                            />
                            <p className={`text-xs mt-1 ${charOk ? 'text-gray-400' : 'text-gray-500'}`}>
                                {charCount}/30 characters {charOk && <Check className="w-3 h-3 inline" />}
                            </p>
                        </div>

                        {/* Files */}
                        <div className="mb-8 flex flex-row items-center justify-between">
                            <button
                                type="button"
                                onClick={() => fileRef.current?.click()}
                                className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1.5"
                            >
                                <Paperclip className="w-4 h-4" />
                                Attach files
                            </button>
                            <input
                                ref={fileRef}
                                type="file"
                                multiple
                                className="hidden"
                                onChange={e => {
                                    if (e.target.files) setFiles(p => [...p, ...Array.from(e.target.files!)])
                                    e.target.value = ''
                                }}
                            />
                            {files.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-3">
                                    {files.map((f, i) => (
                                        <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg text-xs text-gray-600">
                                            <FileText className="w-3 h-3" />
                                            {f.name.length > 20 ? f.name.slice(0, 20) + '...' : f.name}
                                            <button type="button" onClick={() => setFiles(p => p.filter((_, j) => j !== i))} className="text-gray-400 hover:text-gray-600">
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            )}
                            
                            {/* Submit */}
                            <button
                                type="submit"
                                disabled={sending}
                                className="inline-flex items-center gap-2 bg-cyan-600 dark:bg-emerald-600 text-white px-5 py-2.5 text-sm font-medium rounded-xl hover:bg-cyan-700 dark:hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                            >
                                {sending ? 'Sending...' : 'Submit'}
                                {!sending && <ArrowRight className="w-4 h-4" />}
                            </button>
                        </div>

                        
                    </form>

                    {/* Sidebar */}
                    <aside className="space-y-5">
                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-4">Recent Submissions</p>
                            <div className="space-y-3">
                                {HISTORY.map(h => {
                                    const style = STATUS_STYLES[h.status]
                                    return (
                                        <div key={h.id} className="p-3 bg-gray-50 rounded-xl">
                                            <div className="flex items-start justify-between gap-2 mb-1">
                                                <p className="text-sm text-gray-900 line-clamp-1 flex-1">{h.subject}</p>
                                                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${style.color}`}>
                                                    {style.label}
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-400">{h.id} · {h.date}</p>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl p-5">
                            <p className="text-sm font-medium text-gray-900 mb-3">Tips</p>
                            <ul className="space-y-2 text-sm text-gray-500">
                                <li>Include concept IDs when possible</li>
                                <li>Be specific about expected behavior</li>
                                <li>Attach screenshots for complex issues</li>
                            </ul>
                        </div>
                    </aside>
                </div>
            </div>
        </div>
    )
}
