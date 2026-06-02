import { getDesktopSSOLoginUrl } from './sso'
import { getDesktopSSOClientId, getDesktopSSOProtocol, isDesktopSSOEnabledRuntime } from './sso-desktop-config'

export const DESKTOP_SSO_STATE_KEY = 'desktop-sso-state'
export const DESKTOP_SSO_CODE_VERIFIER_KEY = 'desktop-sso-code-verifier'

const DESKTOP_SSO_CACHE_MAX_AGE_SECONDS = 600

const getCookieValue = (name: string) => {
  if (typeof document === 'undefined')
    return ''

  const prefix = `${name}=`
  return document.cookie
    .split(';')
    .map(item => item.trim())
    .find(item => item.startsWith(prefix))
    ?.slice(prefix.length) || ''
}

const safeSessionStorage = () => {
  if (typeof window === 'undefined')
    return null

  try {
    return window.sessionStorage
  }
  catch {
    return null
  }
}

const safeLocalStorage = () => {
  if (typeof window === 'undefined')
    return null

  try {
    return window.localStorage
  }
  catch {
    return null
  }
}

const setDesktopSSOAuthValue = (key: string, value?: string) => {
  if (!value)
    return

  safeSessionStorage()?.setItem(key, value)
  safeLocalStorage()?.setItem(key, value)

  if (typeof document !== 'undefined') {
    document.cookie = `${key}=${encodeURIComponent(value)}; Path=/; Max-Age=${DESKTOP_SSO_CACHE_MAX_AGE_SECONDS}; SameSite=Lax`
  }
}

export const storeDesktopSSOAuthParams = (params: { state: string, codeVerifier?: string }) => {
  setDesktopSSOAuthValue(DESKTOP_SSO_STATE_KEY, params.state)
  setDesktopSSOAuthValue(DESKTOP_SSO_CODE_VERIFIER_KEY, params.codeVerifier)
}

export const readDesktopSSOAuthValue = (key: string) => {
  return safeSessionStorage()?.getItem(key)
    || safeLocalStorage()?.getItem(key)
    || decodeURIComponent(getCookieValue(key))
}

export const clearDesktopSSOAuthParams = () => {
  safeSessionStorage()?.removeItem(DESKTOP_SSO_STATE_KEY)
  safeSessionStorage()?.removeItem(DESKTOP_SSO_CODE_VERIFIER_KEY)
  safeLocalStorage()?.removeItem(DESKTOP_SSO_STATE_KEY)
  safeLocalStorage()?.removeItem(DESKTOP_SSO_CODE_VERIFIER_KEY)

  if (typeof document !== 'undefined') {
    document.cookie = `${DESKTOP_SSO_STATE_KEY}=; Path=/; Max-Age=0; SameSite=Lax`
    document.cookie = `${DESKTOP_SSO_CODE_VERIFIER_KEY}=; Path=/; Max-Age=0; SameSite=Lax`
  }
}

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
  const clientId = getDesktopSSOClientId()
  if (!clientId)
    throw new Error('NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID is not configured')
  const protocol = getDesktopSSOProtocol()
  const redirectUri = getDesktopCallbackUrl()
  const state = generateRandomState()

  if (typeof window !== 'undefined') {
    storeDesktopSSOAuthParams({ state })

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
  const storedState = readDesktopSSOAuthValue(DESKTOP_SSO_STATE_KEY)

  return hasCode && hasState && !!storedState
}

export const getDesktopSSOCallbackParams = () => {
  if (typeof window === 'undefined')
    return null

  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = params.get('state')
  const storedState = readDesktopSSOAuthValue(DESKTOP_SSO_STATE_KEY)

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
  return isDesktopSSOEnabledRuntime()
}
