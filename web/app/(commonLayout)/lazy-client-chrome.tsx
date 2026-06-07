'use client'

import dynamic from 'next/dynamic'
import { useEffect, useState } from 'react'

const PartnerStack = dynamic(() => import('../components/billing/partner-stack'), { ssr: false })
const ReadmePanel = dynamic(() => import('../components/plugins/readme-panel'), { ssr: false })
const GotoAnything = dynamic(() => import('../components/goto-anything'), { ssr: false })
const Splash = dynamic(() => import('../components/splash'), { ssr: false })
const CustomerServiceFloat = dynamic(() => import('../components/base/customer-service-float').then(mod => mod.CustomerServiceFloat), { ssr: false })

const LazyClientChrome = () => {
  const [isIdle, setIsIdle] = useState(false)

  useEffect(() => {
    if (window.requestIdleCallback) {
      const idleId = window.requestIdleCallback(() => setIsIdle(true), { timeout: 1500 })
      return () => window.cancelIdleCallback(idleId)
    }

    const timeoutId = window.setTimeout(() => setIsIdle(true), 800)
    return () => window.clearTimeout(timeoutId)
  }, [])

  if (!isIdle)
    return null

  return (
    <>
      <PartnerStack />
      <ReadmePanel />
      <GotoAnything />
      <Splash />
      <CustomerServiceFloat />
    </>
  )
}

export default LazyClientChrome
