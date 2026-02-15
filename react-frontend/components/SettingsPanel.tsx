'use client'

import { useState, useEffect } from 'react'
import { Moon, Sun, Bell, Server, Settings } from 'lucide-react'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'

export default function SettingsPanel({ compact = false }: { compact?: boolean }) {
  const [darkMode, setDarkMode] = useState(false)
  const [notifications, setNotifications] = useState(true)
  const [apiEndpoint, setApiEndpoint] = useState('https://api.frederick.ai')
  const [isOpen, setIsOpen] = useState(false)

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode') === 'true'
    const savedNotifications = localStorage.getItem('notifications') !== 'false'
    const savedApiEndpoint = localStorage.getItem('apiEndpoint') || 'https://api.frederick.ai'
    
    setDarkMode(savedDarkMode)
    setNotifications(savedNotifications)
    setApiEndpoint(savedApiEndpoint)
    
    // Apply dark mode to document
    if (savedDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  // Save dark mode to localStorage and apply to document
  const handleDarkModeToggle = (enabled: boolean) => {
    setDarkMode(enabled)
    localStorage.setItem('darkMode', enabled.toString())
    if (enabled) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Save notifications to localStorage
  const handleNotificationsToggle = (enabled: boolean) => {
    setNotifications(enabled)
    localStorage.setItem('notifications', enabled.toString())
  }

  // Save API endpoint to localStorage
  const handleApiEndpointChange = (value: string) => {
    setApiEndpoint(value)
    localStorage.setItem('apiEndpoint', value)
    // Update the API client base URL
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('apiEndpointChanged', { detail: value }))
    }
  }

  const triggerButton = compact ? (
    <button
      className="w-full flex items-center justify-center px-2 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-colors"
      aria-label="Settings"
      type="button"
      onClick={() => setIsOpen(true)}
    >
      <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
    </button>
  ) : (
    <button
      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-colors"
      aria-label="Settings"
      type="button"
      onClick={() => setIsOpen(true)}
    >
      <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      <span>Settings</span>
    </button>
  )

  return (
    <>
      {compact ? (
        <TooltipProvider delayDuration={75}>
          <Tooltip>
            <TooltipTrigger asChild>
              {triggerButton}
            </TooltipTrigger>
            <TooltipContent side="right" align="center">
              Settings
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ) : (
        triggerButton
      )}
      
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[425px] dark:bg-slate-800 dark:border-slate-700">
          <DialogHeader>
            <DialogTitle className="dark:text-gray-100">Settings</DialogTitle>
            <DialogDescription className="dark:text-gray-400">
              Configure your application preferences and settings
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-6 py-4">
            {/* Theme Toggle */}
            <div className="grid gap-3">
              <div className="flex items-center gap-3">
                {darkMode ? (
                  <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                ) : (
                  <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                )}
                <div className="flex-1">
                  <Label htmlFor="theme" className="text-base font-semibold dark:text-gray-100">Theme</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Switch between light and dark mode</p>
                </div>
              </div>
              <div className="flex items-center justify-between pl-8">
                <Label htmlFor="theme" className="text-sm text-gray-700 dark:text-gray-300">
                  {darkMode ? 'Dark Mode' : 'Light Mode'}
                </Label>
                <Switch
                  id="theme"
                  checked={darkMode}
                  onCheckedChange={handleDarkModeToggle}
                />
              </div>
            </div>

            {/* Notifications Toggle */}
            <div className="grid gap-3">
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                <div className="flex-1">
                  <Label htmlFor="notifications" className="text-base font-semibold dark:text-gray-100">Notifications</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Enable or disable system notifications</p>
                </div>
              </div>
              <div className="flex items-center justify-between pl-8">
                <Label htmlFor="notifications" className="text-sm text-gray-700 dark:text-gray-300">
                  {notifications ? 'Enabled' : 'Disabled'}
                </Label>
                <Switch
                  id="notifications"
                  checked={notifications}
                  onCheckedChange={handleNotificationsToggle}
                />
              </div>
            </div>

            {/* API Endpoint */}
            <div className="grid gap-3">
              <div className="flex items-center gap-3">
                <Server className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                <div className="flex-1">
                  <Label htmlFor="api-endpoint" className="text-base font-semibold dark:text-gray-100">API Endpoint</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Configure the backend API URL</p>
                </div>
              </div>
              <div className="pl-8">
                <Label htmlFor="api-endpoint" className="sr-only">API Endpoint</Label>
                <Input
                  id="api-endpoint"
                  value={apiEndpoint}
                  onChange={(e) => handleApiEndpointChange(e.target.value)}
                  placeholder="https://api.frederick.ai"
                  className="dark:bg-[#0a0f1a] dark:border-[#1e293b] dark:text-gray-100"
                />
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                  Changes will take effect on next API call
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" className="dark:border-[#1e293b] dark:text-gray-300 dark:hover:bg-[#1e293b]">Cancel</Button>
            </DialogClose>
            <DialogClose asChild>
              <Button type="button" className="dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200">Save changes</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

