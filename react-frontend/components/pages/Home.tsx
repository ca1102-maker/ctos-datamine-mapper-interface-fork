'use client'

import Image from 'next/image'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowUp, Mic, Plus, Search, Settings2, User } from 'lucide-react'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Category {
  id: string
  name: string
  description: string
}

function StreamingText({
  text,
  active,
  onDone,
  onProgress,
}: {
  text: string
  active: boolean
  onDone?: () => void
  onProgress?: () => void
}) {
  const [shownChars, setShownChars] = useState(active ? 0 : text.length)
  const rafRef = useRef<number | null>(null)
  const startRef = useRef<number | null>(null)
  const onDoneRef = useRef(onDone)
  const onProgressRef = useRef(onProgress)
  const hasCalledDoneRef = useRef(false)
  const lastProgressRef = useRef(0)

  // Keep refs updated without causing effect re-runs
  useEffect(() => {
    onDoneRef.current = onDone
    onProgressRef.current = onProgress
  }, [onDone, onProgress])

  const finish = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    rafRef.current = null
    startRef.current = null
    setShownChars(text.length)
    if (!hasCalledDoneRef.current) {
      hasCalledDoneRef.current = true
      onDoneRef.current?.()
    }
  }

  useEffect(() => {
    // Respect reduced motion.
    const reduce =
      typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches

    if (!active || reduce) {
      setShownChars(text.length)
      startRef.current = null
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
      if (active && !hasCalledDoneRef.current) {
        hasCalledDoneRef.current = true
        onDoneRef.current?.()
      }
      return
    }

    // Reset for new streaming
    hasCalledDoneRef.current = false
    lastProgressRef.current = 0
    setShownChars(0)
    startRef.current = null

    const msPerChar = 1000 / 60 // ~60 chars/sec
    const tick = (t: number) => {
      if (startRef.current == null) startRef.current = t
      const elapsed = t - startRef.current
      const next = Math.min(text.length, Math.floor(elapsed / msPerChar))
      setShownChars(next)
      
      // Call onProgress every ~20 characters to trigger scroll
      if (next - lastProgressRef.current >= 20) {
        lastProgressRef.current = next
        onProgressRef.current?.()
      }
      
      if (next >= text.length) {
        rafRef.current = null
        onProgressRef.current?.() // Final scroll
        if (!hasCalledDoneRef.current) {
          hasCalledDoneRef.current = true
          onDoneRef.current?.()
        }
        return
      }
      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
      startRef.current = null
    }
  }, [active, text])

  const isDone = shownChars >= text.length
  const isStreaming = active && !isDone

  return (
    <p
      className={`whitespace-pre-wrap leading-relaxed ${isStreaming ? 'cursor-pointer select-none' : ''}`}
      title={isStreaming ? 'Click to reveal full message' : undefined}
      onClick={() => {
        if (isStreaming) finish()
      }}
    >
      {text.slice(0, shownChars)}
    </p>
  )
}

export default function HomePage({ onNavigate }: { onNavigate: (category: string | null) => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastUserMessageRef = useRef<HTMLDivElement>(null)
  const streamingMessageRef = useRef<HTMLDivElement>(null)
  const mainScrollRef = useRef<HTMLElement>(null)
  const prevLastUserIndexRef = useRef<number>(-1)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [streamingIndex, setStreamingIndex] = useState<number | null>(null)
  const streamedIndexesRef = useRef<Set<number>>(new Set())

  // Chat controls
  const [model, setModel] = useState('GPT-4 Turbo')
  const [temperature, setTemperature] = useState(0.7)
  const [contextFilter, setContextFilter] = useState('')
  const [showControls, setShowControls] = useState(false)
  const [isClosingControls, setIsClosingControls] = useState(false)
  const controlsTimerRef = useRef<number | null>(null)

  // Scroll to keep streaming content visible
  const scrollToStreamingEnd = useCallback(() => {
    if (streamingMessageRef.current) {
      // Scroll the streaming message's bottom into view with some offset
      streamingMessageRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end'
      })
    }
  }, [])

  const categories: Category[] = [
    { id: 'dashboard', name: 'Dashboard', description: 'View metrics and overview' },
    { id: 'graph', name: 'Graph Visualization', description: 'Explore Neo4j knowledge graph' },
    { id: 'analysis', name: 'Metrics Analysis', description: 'Analyze and compare mapping results' },
    { id: 'fileupload', name: 'File Upload', description: 'Upload files to generate mappings' },
    { id: 'mapping', name: 'Semantic Mapping', description: 'Map your own terms' },
    { id: 'feedback', name: 'Feedback Portal', description: 'Submit expert feedback' },
  ]

  const suggestedPrompts = [
    'Tell me more about semantic mapping in medical terminology',
    'Explain common terminology mapping approaches',
    'Help me understand Neo4j graph relationships',
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Best practice #1: Use useMemo for derived data, not useEffect
  const lastUserIndex = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') return i
    }
    return -1
  }, [messages])

  // Consolidated scroll effect - scrolls to user message when new one appears
  useEffect(() => {
    if (lastUserIndex < 0) {
      scrollToBottom()
      return
    }
    if (lastUserIndex <= prevLastUserIndexRef.current) {
      scrollToBottom()
      return
    }
    // New user message - pin it to top so it's not obscured by footer
    prevLastUserIndexRef.current = lastUserIndex
    lastUserMessageRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [lastUserIndex, messages.length])

  // Scroll to show streaming message when it starts
  useEffect(() => {
    if (streamingIndex !== null) {
      // Small delay to let the DOM update
      const timer = setTimeout(() => {
        scrollToStreamingEnd()
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [streamingIndex, scrollToStreamingEnd])

  useEffect(() => {
    return () => {
      if (controlsTimerRef.current) window.clearTimeout(controlsTimerRef.current)
    }
  }, [])

  const toggleControls = () => {
    if (showControls) {
      setIsClosingControls(true)
      if (controlsTimerRef.current) window.clearTimeout(controlsTimerRef.current)
      controlsTimerRef.current = window.setTimeout(() => {
        setShowControls(false)
        setIsClosingControls(false)
      }, 200)
    } else {
      if (controlsTimerRef.current) window.clearTimeout(controlsTimerRef.current)
      setIsClosingControls(false)
      setShowControls(true)
    }
  }

  const buildDemoAnswer = (prompt: string) => {
    const short = prompt.slice(0, 20)
    return `Based on the knowledge base, here's what I found:\n\n\n\nRelevant Documents: 3 matches found\n\n\n\nDocument A (95% relevance): Contains information about ${short}...\n\nDocument B (87% relevance): Related context on the topic\n\nDocument C (76% relevance): Supporting information\n\nAnswer: This is a simulated response to your query about \"${short}\". In a real implementation, this would retrieve relevant information from your vector database and provide a synthesized answer based on your documents.\n\n\n\nConfidence Score: 92% Sources: [Doc-2847], [Doc-3921], [Doc-1052]`
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setLoading(true)

    try {
      const reply = buildDemoAnswer(currentInput)
      await new Promise((r) => setTimeout(r, 2000))
      // Best practice #5: Set streaming index directly when adding message,
      // not reactively via useEffect
      setMessages((prev) => {
        const newIndex = prev.length
        if (!streamedIndexesRef.current.has(newIndex)) {
          streamedIndexesRef.current.add(newIndex)
          setStreamingIndex(newIndex)
        }
        return [...prev, { role: 'assistant', content: reply }]
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
  }

  const handlePromptClick = (prompt: string) => {
    setInput(prompt)
    if (textareaRef.current) {
      textareaRef.current.focus()
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }

  return (
    <TooltipProvider>
      <div className="h-screen flex flex-col bg-white dark:bg-slate-900 text-[0.90rem] overflow-hidden">
        <main ref={mainScrollRef} className="flex-1 overflow-y-auto bg-white dark:bg-slate-900 scrollbar-hide min-h-0">
          <div className="max-w-4xl mx-auto px-2 pt-2">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4 pt-4">
                <div className="text-center space-y-3">
                  <div className="relative w-28 h-28 mx-auto">
                    <Image
                      src="/logo.webp"
                      alt="Frederick Platform Logo"
                      fill
                      className="object-contain dark:hidden"
                      priority
                    />
                    <Image
                      src="/logo-dark.svg"
                      alt="Frederick Platform Logo Dark"
                      fill
                      className="object-contain hidden dark:block"
                      priority
                    />
                  </div>
                  <h2 className="text-3xl font-semibold text-slate-900 dark:text-slate-100">How can I help you today?</h2>
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Ask about semantic mappings, terminology, or explore our features
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full max-w-4xl">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => onNavigate(category.id)}
                      className="bg-white dark:bg-slate-800 backdrop-blur-lg hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg p-4 text-left transition-all hover:border-cyan-400 dark:hover:border-emerald-400 group"
                    >
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">{category.name}</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-300">{category.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-6 py-4 pb-48">
                {messages.map((message, idx) => {
                  const isStreaming = message.role === 'assistant' && idx === streamingIndex
                  const isUserAtLastIndex = message.role === 'user' && idx === lastUserIndex
                  
                  return (
                    <div
                      key={idx}
                      ref={isStreaming ? streamingMessageRef : (isUserAtLastIndex ? lastUserMessageRef : undefined)}
                      className={`flex gap-4 scroll-mb-4 ${message.role === 'user' ? 'justify-end scroll-mt-3' : 'justify-start scroll-mt-2'}`}
                    >
                      {message.role === 'assistant' && (
                        <div className="w-8 h-8 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                          <div className="relative w-full h-full">
                            <Image
                              src="/logo-og.png"
                              alt="AI Assistant"
                              fill
                              className="object-contain"
                              priority
                            />
                          </div>
                        </div>
                      )}

                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                          message.role === 'user'
                            ? 'bg-cyan-50 dark:bg-cyan-900/30 text-slate-900 dark:text-slate-100'
                            : 'bg-transparent text-slate-900 dark:text-slate-100'
                        }`}
                      >
                        <div className="prose prose-sm max-w-none">
                          {isStreaming ? (
                            <StreamingText
                              text={message.content}
                              active
                              onDone={() => {
                                setStreamingIndex(null)
                              }}
                              onProgress={scrollToStreamingEnd}
                            />
                          ) : (
                            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                          )}
                        </div>
                      </div>

                      {message.role === 'user' && (
                        <div className="w-8 h-8 rounded-full bg-cyan-100 dark:bg-cyan-900/30 flex items-center justify-center flex-shrink-0">
                          <User className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                        </div>
                      )}
                    </div>
                  )
                })}

              {loading && (
                <div className="flex gap-4 justify-start">
                  <div className="w-8 h-8 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-center">
                    <div className="relative w-full h-full">
                      <Image src="/logo-og.png" alt="AI Assistant" fill className="object-contain" priority />
                    </div>
                  </div>
                  <div className="bg-transparent rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex items-center font-medium text-slate-500 dark:text-slate-400 gap-1">
                        Thinking<div className="w-2 h-2 bg-slate-400 dark:bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-slate-400 dark:bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-slate-400 dark:bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      <footer className="bg-white dark:bg-slate-900 flex-shrink-0">
        <div className="max-w-4xl mx-auto px-4 pt-2 pb-6 flex flex-col">
          {(showControls || isClosingControls) && (
            <div
              className={`mb-3 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 shadow-sm px-3 py-2 flex flex-wrap items-center gap-3 ${
                isClosingControls
                  ? 'animate-out fade-out slide-out-to-bottom-2 duration-200'
                  : 'animate-in fade-in slide-in-from-bottom-2 duration-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-600 dark:text-slate-300">Model</span>
                <NativeSelect
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="h-9 w-auto min-w-[160px] rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500"
                >
                  <NativeSelectOption value="GPT-4 Turbo">GPT-4 Turbo</NativeSelectOption>
                  <NativeSelectOption value="Claude 3">Claude 3</NativeSelectOption>
                  <NativeSelectOption value="Llama-2">Llama-2</NativeSelectOption>
                  <NativeSelectOption value="Custom RAG">Custom RAG</NativeSelectOption>
                </NativeSelect>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-600 dark:text-slate-300">Temp</span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="h-2 w-28 accent-cyan-600 dark:accent-emerald-500"
                />
                <span className="text-xs text-slate-700 dark:text-slate-300 w-10 font-semibold">{temperature.toFixed(2)}</span>
              </div>

              <div className="flex items-center gap-2 flex-1 min-w-[180px]">
                <span className="text-xs text-slate-600 dark:text-slate-300 whitespace-nowrap">Context</span>
                <input
                  type="text"
                  value={contextFilter}
                  onChange={(e) => setContextFilter(e.target.value)}
                  placeholder="Filter context e.g. medical, financial, technical..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:focus:ring-emerald-500"
                />
              </div>
            </div>
          )}

          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              placeholder="Ask anything about your knowledge base"
              className="w-full flex items-center justify-center bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-2xl p-10 shadow-sm py-[15.5px] pl-12 pr-28 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-400 resize-none focus:outline-none focus:drop-shadow-lg overflow-hidden"
              rows={1}
              style={{
                minHeight: '52px',
                maxHeight: '200px',
              }}
            />

            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  aria-label="Attach"
                >
                  <Plus className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top">Attach (coming soon)</TooltipContent>
            </Tooltip>

            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={toggleControls}
                    className={`p-2 rounded-lg transition-colors ${
                      showControls || isClosingControls
                        ? 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400 hover:bg-cyan-100 dark:hover:bg-cyan-900/30'
                        : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300'
                    }`}
                    aria-label="Open chat controls"
                  >
                    <Settings2
                      className={`w-5 h-5 ${showControls || isClosingControls ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-600 dark:text-slate-300'}`}
                    />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">Chat settings</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" aria-label="Voice">
                    <Mic className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">Voice (coming soon)</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    className="p-2 bg-cyan-600 dark:bg-emerald-600 rounded-full hover:bg-cyan-700 dark:hover:bg-emerald-700 disabled:bg-slate-300 dark:disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors shadow-sm"
                    aria-label="Send message"
                  >
                    <ArrowUp className={`w-5 h-5 rounded-full ${loading || !input.trim() ? 'text-slate-500 dark:text-slate-400' : 'text-white'}`} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">Send</TooltipContent>
              </Tooltip>
            </div>
          </div>

          {messages.length === 0 && (
            <div className="mt-2 space-y-2">
              {suggestedPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePromptClick(prompt)}
                  className="flex items-center gap-2 w-full text-left px-3 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 rounded-lg transition-colors group border border-transparent hover:border-slate-200 dark:hover:border-slate-700"
                >
                  <Search className="w-4 h-4 text-slate-500 dark:text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-300" />
                  <span>{prompt}</span>
                </button>
              ))}
            </div>
          )}

          <div className="flex-1" />

          <p className="text-xs text-slate-500 dark:text-slate-400 mt-4 text-center">
            Frederick Platform (React) v1.0.0 | Powered by RAG & Neo4j | © 2025 Frederick AI
          </p>
        </div>
      </footer>
      </div>
    </TooltipProvider>
  )
}


