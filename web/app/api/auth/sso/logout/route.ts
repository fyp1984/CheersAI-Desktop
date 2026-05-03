import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { deleteSession } from '@/lib/sso-session'

const SSO_SESSION_COOKIE = 'sso_session_id'

export async function POST() {
  try {
    const cookieStore = await cookies()
    const sessionId = cookieStore.get(SSO_SESSION_COOKIE)?.value

    if (sessionId) {
      deleteSession(sessionId)
    }

    // Clear the session cookie
    cookieStore.delete(SSO_SESSION_COOKIE)

    return NextResponse.json({ success: true })
  }
  catch (error) {
    console.error('SSO logout error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 },
    )
  }
}
