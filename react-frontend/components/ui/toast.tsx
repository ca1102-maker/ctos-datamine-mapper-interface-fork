"use client"

import * as React from "react"
import { X } from "lucide-react"

type ToastVariant = "default" | "success" | "error"

export type ToastInput = {
  title?: string
  description?: string
  variant?: ToastVariant
  durationMs?: number
}

type ToastItem = ToastInput & {
  id: string
}

type ToastContextValue = {
  toast: (t: ToastInput) => void
}

const ToastContext = React.createContext<ToastContextValue | null>(null)

function variantClasses(variant: ToastVariant) {
  switch (variant) {
    case "success":
      return "border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-100"
    case "error":
      return "border-red-200 bg-red-50 text-red-950 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-100"
    default:
      return "border-gray-200 bg-white text-gray-900 dark:border-[#1f2a3b] dark:bg-[#0f172a] dark:text-white"
  }
}

function ToastItemView({
  t,
  onDismiss,
}: {
  t: ToastItem
  onDismiss: (id: string) => void
}) {
  const [closing, setClosing] = React.useState(false)

  const dismiss = React.useCallback(() => {
    setClosing(true)
    window.setTimeout(() => onDismiss(t.id), 180)
  }, [onDismiss, t.id])

  return (
    <div
      className={`rounded-xl border px-4 py-3 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-white/80 dark:supports-[backdrop-filter]:bg-[#0f172a]/80 ${
        closing
          ? "animate-out fade-out slide-out-to-bottom-4 duration-200"
          : "animate-in fade-in slide-in-from-bottom-4 duration-200"
      } ${variantClasses(t.variant ?? "default")}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          {t.title && (
            <div className="text-sm font-semibold leading-5">{t.title}</div>
          )}
          {t.description && (
            <div className="mt-0.5 text-sm opacity-90 leading-5">
              {t.description}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={dismiss}
          className="rounded-md p-1 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          aria-label="Dismiss toast"
        >
          <X className="h-4 w-4 opacity-70" />
        </button>
      </div>
    </div>
  )
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([])
  const timers = React.useRef<Record<string, number>>({})

  const remove = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
    const timer = timers.current[id]
    if (timer) {
      window.clearTimeout(timer)
      delete timers.current[id]
    }
  }, [])

  const toast = React.useCallback(
    (t: ToastInput) => {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
      const durationMs = t.durationMs ?? 2200
      const item: ToastItem = { id, variant: "default", ...t }
      setToasts((prev) => [item, ...prev].slice(0, 3))
      timers.current[id] = window.setTimeout(() => remove(id), durationMs)
    },
    [remove]
  )

  React.useEffect(() => {
    return () => {
      Object.values(timers.current).forEach((t) => window.clearTimeout(t))
      timers.current = {}
    }
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}

      <div className="fixed right-4 bottom-4 z-[9999] flex w-[360px] max-w-[calc(100vw-2rem)] flex-col gap-2">
        {toasts.map((t) => (
          <ToastItemView key={t.id} t={t} onDismiss={remove} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = React.useContext(ToastContext)
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider")
  }
  return ctx
}


