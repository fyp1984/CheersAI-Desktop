import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { deleteSession } from '@/lib/sso-session'

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const sessionId = cookieStore.get('sso_session_id')?.value

    if (sessionId) {
      deleteSession(sessionId)
    }

    // Clear the session cookie
    cookieStore.delete('sso_session_id')

    return NextResponse.json({ success: true })
  }
  catch (error) {
    console.error('SSO logout error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
