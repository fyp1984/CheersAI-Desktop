'use client'
import { useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Toast from '@/app/components/base/toast'
import { exchangeSSOToken } from '@/service/sso'

export default function OAuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const hasExchangedRef = useRef(false)

  useEffect(() => {
    // Prevent double execution in React Strict Mode
    if (hasExchangedRef.current) {
      console.log('[SSO] Token exchange already in progress, skipping')
      return
    }

    hasExchangedRef.current = true

    console.log('[SSO] OAuth callback page loaded')
    const code = searchParams.get('code')
    const state = searchParams.get('state')

    if (!code || !state) {
      console.error('[SSO] Missing code or state parameters')
      Toast.notify({ type: 'error', message: 'Invalid SSO callback parameters' })
      router.replace('/signin')
      return
    }

    // Validate state
    const storedState = sessionStorage.getItem('desktop-sso-state')
    if (state !== storedState) {
      console.error('[SSO] State mismatch - stored:', storedState, 'received:', state)
      Toast.notify({ type: 'error', message: 'SSO login failed: state mismatch' })
      router.replace('/signin')
      return
    }

    const redirectUri = `${window.location.protocol}//${window.location.host}/oauth-callback`
    console.log('[SSO] Starting token exchange with:', { code, state, redirectUri })

    exchangeSSOToken({ code, state, redirectUri })
      .then(async () => {
        console.log('[SSO] Token exchange successful, waiting 1000ms before redirect')
        sessionStorage.removeItem('desktop-sso-state')

        // Wait longer for cookies to be set by the browser
        await new Promise(resolve => setTimeout(resolve, 1000))

        console.log('[SSO] Redirecting to /apps')
        // Force reload to ensure fresh cookies are used
        window.location.href = '/apps'
      })
      .catch((error) => {
        console.error('[SSO] Token exchange failed:', error)
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
