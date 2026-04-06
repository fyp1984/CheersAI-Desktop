'use client'

import type { CSSProperties } from 'react'
import Image from 'next/image'
import { useEffect, useRef } from 'react'
import { trackEvent } from '@/app/components/base/amplitude'

type SignInSplashProps = {
  duration: number
  logoUrl: string
  onComplete: () => void
}

type BrowserSupport = {
  browser: string
  version: number
  isSupported: boolean
  isLowEnd: boolean
  reason?: 'low_end_device' | 'automation'
}

type CharStyle = CSSProperties & Record<'--signin-char-index', number>

const splashSlogan = '让 AI 安全、便捷地进入每一台桌面。'
const splashCharacters = Array.from(splashSlogan).reduce<{ char: string, key: string }[]>((items, char) => {
  const duplicateCount = items.filter(item => item.char === char).length + 1
  items.push({
    char,
    key: `${char.codePointAt(0) ?? 0}-${duplicateCount}`,
  })
  return items
}, [])

const minVersions: Record<string, number> = {
  chrome: 90,
  edge: 90,
  firefox: 88,
  safari: 14,
  ios: 14,
}

const cubicEase = (value: number) => {
  const inverted = 1 - value
  return 1 - inverted * inverted * inverted
}

const clamp = (value: number, min: number, max: number) => {
  return Math.min(max, Math.max(min, value))
}

const normalizeSegment = (current: number, start: number, end: number) => {
  if (current <= start)
    return 0
  if (current >= end)
    return 1
  return (current - start) / (end - start)
}

const parseVersion = (userAgent: string, pattern: RegExp) => {
  const matched = userAgent.match(pattern)
  return matched ? Number.parseInt(matched[1], 10) : 0
}

const getBrowserSupport = (): BrowserSupport => {
  if (typeof window === 'undefined') {
    return {
      browser: 'server',
      version: 999,
      isSupported: true,
      isLowEnd: false,
    }
  }

  const userAgent = navigator.userAgent
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const hardwareConcurrency = navigator.hardwareConcurrency ?? 8
  const deviceMemory = 'deviceMemory' in navigator ? Number((navigator as Navigator & { deviceMemory?: number }).deviceMemory) || 8 : 8
  const isAutomation = navigator.webdriver || /HeadlessChrome/i.test(userAgent)
  const isLowEnd = prefersReducedMotion || hardwareConcurrency <= 4 || deviceMemory <= 4 || isAutomation
  const reason = isAutomation ? 'automation' : 'low_end_device'

  if (/Edg\//.test(userAgent)) {
    const version = parseVersion(userAgent, /Edg\/(\d+)/)
    return {
      browser: 'edge',
      version,
      isSupported: version >= minVersions.edge,
      isLowEnd,
      reason,
    }
  }

  if (/Firefox\//.test(userAgent)) {
    const version = parseVersion(userAgent, /Firefox\/(\d+)/)
    return {
      browser: 'firefox',
      version,
      isSupported: version >= minVersions.firefox,
      isLowEnd,
      reason,
    }
  }

  if (/CriOS\//.test(userAgent)) {
    const version = parseVersion(userAgent, /CriOS\/(\d+)/)
    return {
      browser: 'chrome',
      version,
      isSupported: version >= minVersions.chrome,
      isLowEnd,
      reason,
    }
  }

  if (/Chrome\//.test(userAgent) && !/OPR\//.test(userAgent)) {
    const version = parseVersion(userAgent, /Chrome\/(\d+)/)
    return {
      browser: 'chrome',
      version,
      isSupported: version >= minVersions.chrome,
      isLowEnd,
      reason,
    }
  }

  if (userAgent.includes('Safari') && userAgent.includes('Version/')) {
    const version = parseVersion(userAgent, /Version\/(\d+)/)
    const browser = /iPhone|iPad|iPod/.test(userAgent) ? 'ios' : 'safari'
    return {
      browser,
      version,
      isSupported: version >= minVersions[browser],
      isLowEnd,
      reason,
    }
  }

  return {
    browser: 'unknown',
    version: 0,
    isSupported: false,
    isLowEnd,
    reason,
  }
}

const SignInSplash = ({ duration, logoUrl, onComplete }: SignInSplashProps) => {
  const rootRef = useRef<HTMLDivElement>(null)
  const frameRef = useRef<number | null>(null)
  const timeoutRef = useRef<number | null>(null)

  useEffect(() => {
    const root = rootRef.current

    if (!root) {
      onComplete()
      return
    }

    const support = getBrowserSupport()

    if (!support.isSupported) {
      trackEvent('signin_splash_skipped', {
        reason: 'browser_unsupported',
        browser: support.browser,
        version: support.version,
      })
      onComplete()
      return
    }

    if (support.isLowEnd) {
      root.classList.add('is-static')
      trackEvent('signin_splash_skipped', {
        reason: support.reason || 'low_end_device',
        browser: support.browser,
        version: support.version,
      })
      timeoutRef.current = window.setTimeout(() => {
        onComplete()
      }, Math.min(duration, 420))
      return () => {
        if (timeoutRef.current)
          window.clearTimeout(timeoutRef.current)
      }
    }

    const start = performance.now()

    const step = (now: number) => {
      const elapsed = clamp(now - start, 0, duration)
      const backgroundOpacity = cubicEase(normalizeSegment(elapsed, 0, Math.min(240, duration * 0.18)))
      const revealProgress = cubicEase(normalizeSegment(elapsed, duration * 0.08, duration * 0.42))
      const colorProgress = cubicEase(normalizeSegment(elapsed, duration * 0.24, duration * 0.56))
      const sloganProgress = cubicEase(normalizeSegment(elapsed, duration * 0.46, duration * 0.82))
      const overlayOpacity = 1 - cubicEase(normalizeSegment(elapsed, duration * 0.8, duration))

      root.style.setProperty('--signin-splash-bg-opacity', backgroundOpacity.toFixed(3))
      root.style.setProperty('--signin-splash-reveal-progress', revealProgress.toFixed(3))
      root.style.setProperty('--signin-splash-color-progress', colorProgress.toFixed(3))
      root.style.setProperty('--signin-splash-slogan-progress', sloganProgress.toFixed(3))
      root.style.setProperty('--signin-splash-overlay-opacity', overlayOpacity.toFixed(3))

      if (elapsed >= duration) {
        onComplete()
        return
      }

      frameRef.current = window.requestAnimationFrame(step)
    }

    frameRef.current = window.requestAnimationFrame(step)

    return () => {
      if (frameRef.current !== null)
        window.cancelAnimationFrame(frameRef.current)
      if (timeoutRef.current !== null)
        window.clearTimeout(timeoutRef.current)
    }
  }, [duration, logoUrl, onComplete])

  return (
    <div
      ref={rootRef}
      className="signin-splash"
      data-signin-splash
      aria-hidden="true"
    >
      <div className="signin-splash__content">
        <div className="signin-splash__mark-shell">
          <Image
            src={logoUrl}
            alt="CheersAI Logo"
            width={184}
            height={184}
            unoptimized
            className="signin-splash__logo-asset"
          />
        </div>
        <div className="signin-splash__slogan">
          {splashCharacters.map(({ char, key }, index) => (
            <span
              key={key}
              className="signin-splash__char"
              style={{ '--signin-char-index': index } as CharStyle}
            >
              {char}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SignInSplash
