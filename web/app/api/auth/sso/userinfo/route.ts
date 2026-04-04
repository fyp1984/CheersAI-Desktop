import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { getSession } from '@/lib/sso-session'

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const sessionId = cookieStore.get('sso_session_id')?.value

    console.log('[SSO] UserInfo - Session ID from cookie:', sessionId ? sessionId.substring(0, 20) + '...' : 'NOT FOUND')

    if (!sessionId) {
      console.error('[SSO] UserInfo - No session ID in cookie')
      return NextResponse.json(
        { error: 'No SSO session found' },
        { status: 401 }
      )
    }

    const session = getSession(sessionId)
    if (!session) {
      console.error('[SSO] UserInfo - Session not found or expired for ID:', sessionId.substring(0, 20) + '...')
      return NextResponse.json(
        { error: 'SSO session expired or invalid' },
        { status: 401 }
      )
    }

    console.log('[SSO] UserInfo - Session found, fetching user info from Casdoor')
    const accessToken = session.accessToken

    const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL || 'http://localhost:8000'
    const userinfoUrl = new URL('/api/userinfo', ssoBaseUrl)

    const userinfoResponse = await fetch(userinfoUrl.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    })

    if (!userinfoResponse.ok) {
      const errorText = await userinfoResponse.text()
      console.error('SSO userinfo request failed:', errorText)
      return NextResponse.json(
        { error: 'Failed to fetch user info' },
        { status: userinfoResponse.status }
      )
    }

    const userInfo = await userinfoResponse.json()
    
    // Debug: Log all fields from Casdoor
    console.log('[SSO DEBUG] Full userinfo from Casdoor:', JSON.stringify(userInfo, null, 2))

    return NextResponse.json(userInfo)
  }
  catch (error) {
    console.error('SSO userinfo error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
