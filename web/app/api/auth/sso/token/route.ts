import type { NextRequest } from 'next/server'
import { Buffer } from 'node:buffer'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { generateSessionId, storeSession } from '@/lib/sso-session'

const SSO_SESSION_COOKIE = 'sso_session_id'
const TOKEN_EXCHANGE_RETRY_DELAY = 300
const DEFAULT_INTERNAL_API_BASE_URL = process.env.INTERNAL_API_BASE_URL?.trim() || 'http://localhost:5001'
const DEFAULT_INTERNAL_CONSOLE_API_PREFIX = `${DEFAULT_INTERNAL_API_BASE_URL.replace(/\/$/, '')}/console/api`

type SsoTokenResponse = {
  access_token?: string
  refresh_token?: string
  expires_in?: number | string
  scope?: string
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const fetchTokenWithRetry = async (url: string, init: RequestInit) => {
  try {
    return await fetch(url, init)
  }
  catch (error) {
    console.warn('SSO token exchange fetch failed, retrying once:', error)
    await sleep(TOKEN_EXCHANGE_RETRY_DELAY)
    return fetch(url, init)
  }
}

const normalizeInternalApiPrefix = (rawPrefix: string) => {
  const trimmedPrefix = rawPrefix.trim()
  if (!trimmedPrefix)
    return DEFAULT_INTERNAL_CONSOLE_API_PREFIX

  if (/^https?:\/\//i.test(trimmedPrefix))
    return trimmedPrefix.replace(/\/$/, '')

  if (trimmedPrefix.startsWith('/'))
    return `${DEFAULT_INTERNAL_API_BASE_URL.replace(/\/$/, '')}${trimmedPrefix}`.replace(/\/$/, '')

  return `http://${trimmedPrefix}`.replace(/\/$/, '')
}

const uniqueValues = (values: string[]) => [...new Set(values.filter(Boolean))]

const getConsoleApiUrls = (path: string) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const configuredPrefixes = [
    process.env.INTERNAL_CONSOLE_API_PREFIX?.trim(),
    process.env.CONSOLE_API_PREFIX?.trim(),
    process.env.NEXT_PUBLIC_API_PREFIX?.trim(),
  ].filter((prefix): prefix is string => Boolean(prefix))

  const fallbackPrefixes = [
    DEFAULT_INTERNAL_CONSOLE_API_PREFIX,
    'http://127.0.0.1:5001/console/api',
    'http://localhost:5001/console/api',
    'http://api:5001/console/api',
  ]

  return uniqueValues([...configuredPrefixes, ...fallbackPrefixes].map(normalizeInternalApiPrefix))
    .map(prefix => `${prefix}${normalizedPath}`)
}

const exchangeTokenViaProxy = async (body: Record<string, unknown>) => {
  let lastError: unknown = null
  for (const url of getConsoleApiUrls('/auth/sso-proxy/token')) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (response.ok)
        return response.json() as Promise<SsoTokenResponse>

      const errorText = await response.text()
      lastError = new Error(`SSO token proxy exchange failed: ${response.status}`)
      console.error('SSO token proxy exchange failed:', {
        status: response.status,
        body: errorText,
      })
      if (![502, 503, 504].includes(response.status))
        break
    }
    catch (error) {
      lastError = error
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Token exchange failed')
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { code, state, redirectUri, codeVerifier } = body

    if (!code || !state || !redirectUri) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 },
      )
    }

    const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL?.trim()
    const clientId = process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID?.trim()
    if (!ssoBaseUrl || !clientId) {
      return NextResponse.json(
        { error: 'SSO configuration is incomplete: NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL / NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID' },
        { status: 500 },
      )
    }
    const clientSecret = process.env.DESKTOP_SSO_CLIENT_SECRET || ''
    const usePkcePublicClient = Boolean(codeVerifier)

    const tokenUrl = new URL('/api/login/oauth/access_token', ssoBaseUrl)

    const params = new URLSearchParams()
    params.append('grant_type', 'authorization_code')
    params.append('code', code)
    params.append('redirect_uri', redirectUri)
    params.append('client_id', clientId)
    if (!usePkcePublicClient && clientSecret)
      params.append('client_secret', clientSecret)
    if (codeVerifier)
      params.append('code_verifier', codeVerifier)

    const headers: Record<string, string> = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
    }

    if (!usePkcePublicClient && clientSecret) {
      const authString = Buffer.from(`${clientId}:${clientSecret}`).toString('base64')
      headers.Authorization = `Basic ${authString}`
    }

    let tokenData: SsoTokenResponse | null = null
    try {
      const tokenResponse = await fetchTokenWithRetry(tokenUrl.toString(), {
        method: 'POST',
        headers,
        body: params.toString(),
      })

      if (!tokenResponse.ok) {
        const errorText = await tokenResponse.text()
        console.error('SSO token exchange failed:', {
          status: tokenResponse.status,
          tokenUrl: tokenUrl.toString(),
          body: errorText,
        })
        return NextResponse.json(
          { error: 'Token exchange failed' },
          { status: tokenResponse.status },
        )
      }

      tokenData = await tokenResponse.json()
    }
    catch (error) {
      console.warn('[SSO] Token exchange fetch failed, falling back to proxy:', error)
      tokenData = await exchangeTokenViaProxy({
        grantType: 'authorization_code',
        code,
        state,
        redirectUri,
        codeVerifier,
      })
    }
    const { access_token, refresh_token, expires_in, scope } = tokenData || {}

    if (!access_token) {
      return NextResponse.json(
        { error: 'No access token received' },
        { status: 500 },
      )
    }

    const sessionId = generateSessionId()
    const sessionExpiresIn = Number.isFinite(Number(expires_in)) && Number(expires_in) > 0
      ? Number(expires_in)
      : 60 * 60
    storeSession(sessionId, access_token, refresh_token, sessionExpiresIn, scope)

    const cookieStore = await cookies()
    cookieStore.set(SSO_SESSION_COOKIE, sessionId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: sessionExpiresIn,
    })

    console.warn('[SSO] Token stored in session:', `${sessionId.substring(0, 20)}...`)

    return NextResponse.json({
      success: true,
      expires_in: sessionExpiresIn,
    })
  }
  catch (error) {
    const routeError = error as Error & { cause?: unknown }
    console.error('SSO token exchange error:', {
      message: routeError.message,
      cause: routeError.cause,
      error,
    })
    return NextResponse.json(
      {
        error: 'Internal server error',
        details: process.env.NODE_ENV === 'production' ? undefined : String(error),
      },
      { status: 500 },
    )
  }
}
