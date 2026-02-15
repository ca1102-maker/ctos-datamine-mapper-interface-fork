import type { Metadata } from 'next'
import './globals.css'
import { ToastProvider } from '@/components/ui/toast'

export const metadata: Metadata = {
  title: 'Frederick Semantic Mapping Platform',
  description: 'AI-Enhanced Terminology Mapping Platform',
  icons: {
    icon: '🔬',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-white">
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  )
}

