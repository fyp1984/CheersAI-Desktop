import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { code, state, redirectUri } = body

    if (!code || !state || !redirectUri) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 }
      )
    }

    const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL || 'http://localhost:8000'
    const clientId = process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID || '35f82ac3f099085a6fd0'
    const clientSecret = process.env.DESKTOP_SSO_CLIENT_SECRET || ''

    const tokenUrl = new URL('/api/login/oauth/access_token', ssoBaseUrl)
    
    const tokenResponse = await fetch(tokenUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        client_id: clientId,
        client_secret: clientSecret,
        code,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code',
      }),
    })

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text()
      console.error('SSO token exchange failed:', errorText)
      return NextResponse.json(
        { error: 'Token exchange failed' },
        { status: tokenResponse.status }
      )
    }

    const tokenData = await tokenResponse.json()
    const { access_token, refresh_token } = tokenData

    if (!access_token) {
      return NextResponse.json(
        { error: 'No access token received' },
        { status: 500 }
      )
    }

    const cookieStore = await cookies()
    cookieStore.set('sso_access_token', access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 * 7,
    })

    if (refresh_token) {
      cookieStore.set('sso_refresh_token', refresh_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24 * 30,
      })
    }

    return NextResponse.json({
      success: true,
      access_token,
      refresh_token,
    })
  }
  catch (error) {
    console.error('SSO token exchange error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
