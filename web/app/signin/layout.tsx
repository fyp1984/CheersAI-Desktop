'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useGlobalPublicStore } from '@/context/global-public-context'
import SignInSplash from './components/signin-splash'
import SignInThemeToggle from './components/signin-theme-toggle'
import { getEnvSignInConfig, loadSignInConfig } from './runtime-config'
import './signin.css'

const initialConfig = getEnvSignInConfig()

export default function SignInLayout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()
  const { systemFeatures } = useGlobalPublicStore()
  const [config, setConfig] = useState(initialConfig)
  const [isSplashComplete, setIsSplashComplete] = useState(!initialConfig.enableSplash)

  useEffect(() => {
    document.title = t('pageTitle', { ns: 'login' })
  }, [t])

  useEffect(() => {
    let isActive = true

    loadSignInConfig().then((nextConfig) => {
      if (!isActive)
        return

      setConfig(nextConfig)
      if (!nextConfig.enableSplash)
        setIsSplashComplete(true)
    })

    return () => {
      isActive = false
    }
  }, [])

  return (
    <div className="signin-page">
      <div className="signin-page__shell">
        <div className="signin-page__content">
          <main className="signin-panel">
            <div className="signin-panel__chrome">
              <div className="signin-panel__brand">
                <img
                  src={config.logoUrl}
                  alt="CheersAI Logo"
                  className="signin-shell__logo-image"
                />
                <strong className="signin-shell__logo-title">CheersAI Desktop</strong>
              </div>
              <div className="signin-panel__toolbar">
                <SignInThemeToggle />
              </div>
            </div>
            <div className="signin-shell__card">
              {children}
            </div>
          </main>
        </div>
        {config.enableSplash && !isSplashComplete && (
          <SignInSplash
            duration={config.animationDuration}
            logoUrl={config.logoUrl}
            onComplete={() => setIsSplashComplete(true)}
          />
        )}
        <div className="signin-hero__footer">
          <span className="signin-hero__dot" />
          <span>{t('signinRefresh.heroFootnote', { ns: 'login' })}</span>
        </div>
        {systemFeatures.branding.enabled === false && (
          <div className="signin-copyright">
            <p>
              ©
              {' '}
              {new Date().getFullYear()}
              {' '}
              <Link
                href="https://www.cheersai.cloud"
                target="_blank"
                rel="noopener noreferrer"
                className="signin-copyright__link"
              >
                CheersAI
              </Link>
              . All rights reserved.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
