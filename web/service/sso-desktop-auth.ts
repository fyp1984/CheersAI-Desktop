import { getDesktopSSOLoginUrl } from './sso'

export const isTauriRuntime = () => {
  if (typeof window === 'undefined')
    return false

  return '__TAURI__' in window
}

export const isDesktopRuntime = () => {
  return isTauriRuntime()
}

export const generateRandomState = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

const toBase64Url = (buffer: ArrayBuffer) => {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (const byte of bytes)
    binary += String.fromCharCode(byte)

  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '')
}

export const generateCodeVerifier = () => {
  const randomBytes = new Uint8Array(32)
  crypto.getRandomValues(randomBytes)
  return toBase64Url(randomBytes.buffer)
}

export const generateCodeChallenge = async (codeVerifier: string) => {
  const encoder = new TextEncoder()
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(codeVerifier))
  return toBase64Url(digest)
}

export const getDesktopCallbackUrl = () => {
  if (typeof window === 'undefined')
    return 'http://localhost:3000/oauth-callback'

  const { protocol, host } = window.location
  return `${protocol}//${host}/oauth-callback`
}

export const startDesktopSSOLogin = () => {
  const clientId = process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID?.trim()
  if (!clientId)
    throw new Error('NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID is not configured')
  const protocol = (process.env.NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL || 'oauth').replace('oauth2', 'oauth')
  const redirectUri = getDesktopCallbackUrl()
  const state = generateRandomState()

  if (typeof window !== 'undefined') {
    sessionStorage.setItem('desktop-sso-state', state)

    const loginUrl = getDesktopSSOLoginUrl({
      clientId,
      redirectUri,
      state,
      protocol,
    })

    window.location.href = loginUrl
  }
}

export const isDesktopSSOCallback = () => {
  if (typeof window === 'undefined')
    return false

  const params = new URLSearchParams(window.location.search)
  const hasCode = params.has('code')
  const hasState = params.has('state')
  const storedState = sessionStorage.getItem('desktop-sso-state')

  return hasCode && hasState && !!storedState
}

export const getDesktopSSOCallbackParams = () => {
  if (typeof window === 'undefined')
    return null

  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = params.get('state')
  const storedState = sessionStorage.getItem('desktop-sso-state')

  if (!code || !state)
    return null

  if (state !== storedState) {
    console.error('SSO state mismatch')
    return null
  }

  return {
    code,
    state,
    redirectUri: getDesktopCallbackUrl(),
  }
}

export const isDesktopSSOEnabled = () => {
  const enabled = process.env.NEXT_PUBLIC_DESKTOP_SSO_ENABLED
  return enabled === 'true' || enabled === '1'
}
