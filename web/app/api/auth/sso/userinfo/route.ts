import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const accessToken = cookieStore.get('sso_access_token')?.value

    if (!accessToken) {
      return NextResponse.json(
        { error: 'No access token found' },
        { status: 401 }
      )
    }

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
