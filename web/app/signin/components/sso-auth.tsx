'use client'
import type { FC } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import { Lock01 } from '@/app/components/base/icons/src/vender/solid/security'
import Toast from '@/app/components/base/toast'
import { exchangeSSOToken, getUserOAuth2SSOUrl, getUserOIDCSSOUrl, getUserSAMLSSOUrl } from '@/service/sso'
import { getDesktopSSOCallbackParams, isDesktopRuntime, isDesktopSSOCallback, isDesktopSSOEnabled, startDesktopSSOLogin } from '@/service/sso-desktop-auth'
import { SSOProtocol } from '@/types/feature'
import { useIsLogin } from '@/service/use-common'

type SSOAuthProps = {
  protocol: SSOProtocol | ''
}

const SSOAuth: FC<SSOAuthProps> = ({
  protocol,
}) => {
  const router = useRouter()
  const { t } = useTranslation()
  const searchParams = useSearchParams()
  const invite_token = decodeURIComponent(searchParams.get('invite_token') || '')
  const { refetch: refetchLoginStatus } = useIsLogin()

  const [isLoading, setIsLoading] = useState(false)
  const [isProcessingCallback, setIsProcessingCallback] = useState(false)

  useEffect(() => {
    if (isDesktopSSOCallback()) {
      console.log('[SSO] Detected SSO callback')
      setIsProcessingCallback(true)
      const params = getDesktopSSOCallbackParams()
      
      if (!params) {
        console.error('[SSO] Invalid callback parameters')
        Toast.notify({
          type: 'error',
          message: 'SSO callback parameters invalid',
        })
        setIsProcessingCallback(false)
        return
      }

      console.log('[SSO] Starting token exchange with params:', params)
      exchangeSSOToken(params)
        .then(async () => {
          console.log('[SSO] Token exchange successful, waiting 1000ms before redirect')
          // Wait longer for cookies to be set by the browser
          await new Promise(resolve => setTimeout(resolve, 1000))
          
          console.log('[SSO] Redirecting to /apps')
          // Force reload to ensure fresh cookies are used
          sessionStorage.removeItem('desktop-sso-state')
          sessionStorage.setItem('sso-just-logged-in', 'true')
          window.location.href = '/apps'
        })
        .catch((error) => {
          console.error('[SSO] Token exchange failed:', error)
          Toast.notify({
            type: 'error',
            message: 'SSO login failed',
          })
          setIsProcessingCallback(false)
        })
    }
  }, [searchParams, router, refetchLoginStatus])

  const handleSSOLogin = () => {
    setIsLoading(true)
    
    if (isDesktopSSOEnabled()) {
      startDesktopSSOLogin()
      return
    }
    
    if (protocol === SSOProtocol.SAML) {
      getUserSAMLSSOUrl(invite_token).then((res) => {
        router.push(res.url)
      }).finally(() => {
        setIsLoading(false)
      })
    }
    else if (protocol === SSOProtocol.OIDC) {
      getUserOIDCSSOUrl(invite_token).then((res) => {
        document.cookie = `user-oidc-state=${res.state};Path=/`
        router.push(res.url)
      }).finally(() => {
        setIsLoading(false)
      })
    }
    else if (protocol === SSOProtocol.OAuth2) {
      getUserOAuth2SSOUrl(invite_token).then((res) => {
        document.cookie = `user-oauth2-state=${res.state};Path=/`
        router.push(res.url)
      }).finally(() => {
        setIsLoading(false)
      })
    }
    else {
      Toast.notify({
        type: 'error',
        message: 'invalid SSO protocol',
      })
      setIsLoading(false)
    }
  }

  if (isProcessingCallback) {
    return (
      <div className="w-full text-center py-4">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-sm text-gray-600">Processing SSO login...</p>
      </div>
    )
  }

  return (
    <Button
      tabIndex={0}
      onClick={() => { handleSSOLogin() }}
      disabled={isLoading}
      className="w-full"
    >
      <Lock01 className="mr-2 h-5 w-5 text-text-accent-light-mode-only" />
      <span className="truncate">{t('withSSO', { ns: 'login' })}</span>
    </Button>
  )
}

export default SSOAuth
