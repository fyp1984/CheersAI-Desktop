'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useRef } from 'react'
import Toast from '@/app/components/base/toast'
import { exchangeSSOToken } from '@/service/sso'

export default function OAuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const hasExchangedRef = useRef(false)

  useEffect(() => {
    if (hasExchangedRef.current) {
      console.warn('[SSO] Token exchange already in progress, skipping')
      return
    }

    hasExchangedRef.current = true

    const code = searchParams.get('code')
    const state = searchParams.get('state')

    if (!code || !state) {
      console.error('[SSO] Missing code or state parameters')
      Toast.notify({ type: 'error', message: 'Invalid SSO callback parameters' })
      router.replace('/signin')
      return
    }

    const storedState = sessionStorage.getItem('desktop-sso-state')
    const codeVerifier = sessionStorage.getItem('desktop-sso-code-verifier')
    if (state !== storedState) {
      console.error('[SSO] State mismatch - stored:', storedState, 'received:', state)
      Toast.notify({ type: 'error', message: 'SSO login failed: state mismatch' })
      router.replace('/signin')
      return
    }

    if (!codeVerifier) {
      console.error('[SSO] Missing PKCE code verifier')
      Toast.notify({ type: 'error', message: 'SSO login failed: missing verifier' })
      router.replace('/signin')
      return
    }

    const redirectUri = `${window.location.protocol}//${window.location.host}/oauth-callback`

    exchangeSSOToken({ code, state, redirectUri, codeVerifier })
      .then(async () => {
        sessionStorage.removeItem('desktop-sso-state')
        sessionStorage.removeItem('desktop-sso-code-verifier')
        await new Promise<void>((resolve) => {
          const redirectTimer = window.setTimeout(() => {
            window.clearTimeout(redirectTimer)
            resolve()
          }, 1000)
        })
        window.location.href = '/apps'
      })
      .catch((error) => {
        console.error('[SSO] Token exchange failed:', error)
        sessionStorage.removeItem('desktop-sso-state')
        sessionStorage.removeItem('desktop-sso-code-verifier')
        Toast.notify({ type: 'error', message: 'SSO login failed' })
        router.replace('/signin')
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div className="text-center">
        <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-4 text-sm text-gray-500">Completing SSO login...</p>
      </div>
    </div>
  )
}
