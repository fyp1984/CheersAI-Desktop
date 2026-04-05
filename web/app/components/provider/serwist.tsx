'use client'

import { SerwistProvider } from '@serwist/turbopack/react'
import { useEffect } from 'react'
import { IS_DEV } from '@/config'
import { isClient } from '@/utils/client'

export function PWAProvider({ children }: { children: React.ReactNode }) {
  const isPWAEnabled = !IS_DEV && process.env.NEXT_PUBLIC_DEPLOY_ENV === 'PRODUCTION'

  if (IS_DEV || isLocalRuntime()) {
    return <DisabledPWAProvider>{children}</DisabledPWAProvider>
  }

  if (!isPWAEnabled) {
    return <>{children}</>
  }

  const basePath = process.env.NEXT_PUBLIC_BASE_PATH || ''
  const swUrl = `${basePath}/serwist/sw.js`

  return (
    <SerwistProvider swUrl={swUrl}>
      {children}
    </SerwistProvider>
  )
}

function isLocalRuntime() {
  if (!isClient)
    return false

  return ['localhost', '127.0.0.1'].includes(window.location.hostname)
}

function DisabledPWAProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (isClient && 'serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations()
        .then((registrations) => {
          registrations.forEach((registration) => {
            registration.unregister()
              .catch((error) => {
                console.error('Error unregistering service worker:', error)
              })
          })
        })
        .catch((error) => {
          console.error('Error unregistering service workers:', error)
        })
    }
  }, [])

  return <>{children}</>
}
