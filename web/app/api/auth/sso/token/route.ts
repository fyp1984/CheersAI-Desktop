import type { NextRequest } from 'next/server'
import { Buffer } from 'node:buffer'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { generateSessionId, storeSession } from '@/lib/sso-session'

const SSO_SESSION_COOKIE = 'sso_session_id'

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

    const tokenResponse = await fetch(tokenUrl.toString(), {
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

    const tokenData = await tokenResponse.json()
    const { access_token, refresh_token, expires_in, scope } = tokenData

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
