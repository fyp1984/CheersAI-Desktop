'use client'
import type { FC } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useReducer, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import { Lock01 } from '@/app/components/base/icons/src/vender/solid/security'
import Toast from '@/app/components/base/toast'
import { exchangeSSOToken, getUserOAuth2SSOUrl, getUserOIDCSSOUrl, getUserSAMLSSOUrl } from '@/service/sso'
import { getDesktopSSOCallbackParams, isDesktopSSOCallback, isDesktopSSOEnabled, startDesktopSSOLogin } from '@/service/sso-desktop-auth'
import { useIsLogin } from '@/service/use-common'
import { SSOProtocol } from '@/types/feature'

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
  const [isProcessingCallback, setIsProcessingCallback] = useReducer((_: boolean, value: boolean) => value, false)

  useEffect(() => {
    if (isDesktopSSOCallback()) {
      setIsProcessingCallback(true)
      const params = getDesktopSSOCallbackParams()

      if (!params) {
        Toast.notify({
          type: 'error',
          message: 'SSO callback parameters invalid',
        })
        setIsProcessingCallback(false)
        return
      }

      exchangeSSOToken(params)
        .then(async () => {
          await refetchLoginStatus()

          let checkLoginInterval: ReturnType<typeof setInterval> | null = null
          const processingTimeout = window.setTimeout(() => {
            if (checkLoginInterval)
              clearInterval(checkLoginInterval)

            setIsProcessingCallback(false)
          }, 10000)

          checkLoginInterval = setInterval(async () => {
            const { data } = await refetchLoginStatus()
            if (data?.logged_in) {
              if (checkLoginInterval)
                clearInterval(checkLoginInterval)

              clearTimeout(processingTimeout)
              sessionStorage.removeItem('desktop-sso-state')
              router.replace('/apps')
            }
          }, 500)
        })
        .catch((error) => {
          console.error('SSO token exchange failed:', error)
          Toast.notify({
            type: 'error',
            message: 'SSO login failed',
          })
          setIsProcessingCallback(false)
        })
    }
  }, [router, searchParams, refetchLoginStatus])

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
      <div className="w-full py-4 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
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
