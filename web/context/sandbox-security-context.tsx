'use client'

import { createContext, useCallback, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'sandbox_security_enabled'
const SANDBOX_PATH_KEY = 'sandbox_path'

type SandboxSecurityContextValue = {
  /** Whether sandbox-only mode is enabled (default: true) */
  enabled: boolean
  /** Toggle sandbox security on/off */
  setEnabled: (v: boolean) => void
  /** The configured sandbox path */
  sandboxPath: string
  /** Update the sandbox path (also persists to localStorage) */
  setSandboxPath: (path: string) => void
  /** Whether sandbox is properly configured */
  isConfigured: boolean
}

export const SandboxSecurityContext = createContext<SandboxSecurityContextValue>({
  enabled: true,
  setEnabled: () => {},
  sandboxPath: '',
  setSandboxPath: () => {},
  isConfigured: false,
})

export function SandboxSecurityProvider({ children }: { children: React.ReactNode }) {
  const [enabled, setEnabledState] = useState(() => {
    if (typeof window === 'undefined')
      return true

    const saved = localStorage.getItem(STORAGE_KEY)
    return saved === null ? true : saved === 'true'
  })
  const [sandboxPath, setSandboxPathState] = useState(() => {
    if (typeof window === 'undefined')
      return ''

    const path = localStorage.getItem(SANDBOX_PATH_KEY)
    return path && !path.startsWith('[') ? path : ''
  })

  const setEnabled = useCallback((v: boolean) => {
    setEnabledState(v)
    localStorage.setItem(STORAGE_KEY, String(v))
  }, [])

  const updateSandboxPath = useCallback((path: string) => {
    setSandboxPathState(path)
    localStorage.setItem(SANDBOX_PATH_KEY, path)
  }, [])

  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === SANDBOX_PATH_KEY && e.newValue && !e.newValue.startsWith('['))
        setSandboxPathState(e.newValue)

      if (e.key === STORAGE_KEY)
        setEnabledState(e.newValue === null ? true : e.newValue === 'true')
    }

    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const value = useMemo<SandboxSecurityContextValue>(() => ({
    enabled,
    setEnabled,
    sandboxPath,
    setSandboxPath: updateSandboxPath,
    isConfigured: !!sandboxPath,
  }), [enabled, setEnabled, sandboxPath, updateSandboxPath])

  return (
    <SandboxSecurityContext.Provider value={value}>
      {children}
    </SandboxSecurityContext.Provider>
  )
}
