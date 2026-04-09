'use client'
import type { FC } from 'react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import { Lock01 } from '@/app/components/base/icons/src/vender/solid/security'
import Toast from '@/app/components/base/toast'
import { getDesktopSSOLoginUrl, getUserOAuth2SSOUrl, getUserOIDCSSOUrl, getUserSAMLSSOUrl } from '@/service/sso'
import { generateCodeChallenge, generateCodeVerifier, generateRandomState, getDesktopCallbackUrl, isDesktopSSOEnabled } from '@/service/sso-desktop-auth'
import { SSOProtocol } from '@/types/feature'

type SSOAuthProps = {
  protocol: SSOProtocol | ''
}

const SSOAuth: FC<SSOAuthProps> = ({
  protocol,
}) => {
  const { t } = useTranslation()
  const inviteToken = ''

  const [isLoading, setIsLoading] = useState(false)

  const handleSSOLogin = () => {
    setIsLoading(true)

    if (isDesktopSSOEnabled()) {
      const state = generateRandomState()
      const protocol = (process.env.NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL || 'oauth').replace('oauth2', 'oauth')
      const codeVerifier = generateCodeVerifier()

      generateCodeChallenge(codeVerifier)
        .then((codeChallenge) => {
          const loginUrl = getDesktopSSOLoginUrl({
            clientId: process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID || '35f82ac3f099085a6fd0',
            redirectUri: getDesktopCallbackUrl(),
            state,
            protocol,
            codeChallenge,
            codeChallengeMethod: 'S256',
          })

          sessionStorage.setItem('desktop-sso-state', state)
          sessionStorage.setItem('desktop-sso-code-verifier', codeVerifier)
          window.location.href = loginUrl
        })
        .catch(() => {
          Toast.notify({
            type: 'error',
            message: 'Failed to initialize SSO login',
          })
          setIsLoading(false)
        })
      return
    }

    if (protocol === SSOProtocol.SAML) {
      getUserSAMLSSOUrl(inviteToken).then((res) => {
        window.location.href = res.url
      }).finally(() => {
        setIsLoading(false)
      })
    }
    else if (protocol === SSOProtocol.OIDC) {
      getUserOIDCSSOUrl(inviteToken).then((res) => {
        document.cookie = `user-oidc-state=${res.state};Path=/`
        window.location.href = res.url
      }).finally(() => {
        setIsLoading(false)
      })
    }
    else if (protocol === SSOProtocol.OAuth2) {
      getUserOAuth2SSOUrl(inviteToken).then((res) => {
        document.cookie = `user-oauth2-state=${res.state};Path=/`
        window.location.href = res.url
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

  return (
    <Button
      tabIndex={0}
      onClick={() => { handleSSOLogin() }}
      disabled={isLoading}
      className="signin-sso-button w-full"
    >
      <Lock01 className="signin-sso-button__icon mr-2 h-5 w-5" />
      <span className="truncate">{t('withSSO', { ns: 'login' })}</span>
    </Button>
  )
}

export default SSOAuth
