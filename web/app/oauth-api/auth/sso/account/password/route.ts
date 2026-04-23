import { Buffer } from 'node:buffer'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { deleteSession, getSession, shouldRefreshSession, updateSession } from '@/lib/sso-session'

type JsonObject = Record<string, unknown>

type RawSSOUserInfo = {
  sub?: string
  preferred_username?: string
  preferredUsername?: string
  name?: string
  displayName?: string
}

const getSSOConfig = () => {
  const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL?.trim() || ''
  const clientId = process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID?.trim() || ''
  const clientSecret = process.env.DESKTOP_SSO_CLIENT_SECRET || ''

  return {
    ssoBaseUrl,
    clientId,
    clientSecret,
  }
}

const buildBasicAuthHeader = (clientId: string, clientSecret: string) => {
  return `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`
}

const getResponsePayload = async (response: Response) => {
  try {
    return await response.json() as JsonObject
  }
  catch {
    return {}
  }
}

const isSuccessPayload = (payload: JsonObject) => {
  const status = String(payload?.status || '').toLowerCase()
  return !status || status === 'ok'
}

const decodeJwtPayload = (token: string) => {
  const [, payload] = token.split('.')
  if (!payload)
    return null

  try {
    const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/')
    const paddedPayload = normalizedPayload.padEnd(Math.ceil(normalizedPayload.length / 4) * 4, '=')
    return JSON.parse(Buffer.from(paddedPayload, 'base64').toString('utf-8')) as RawSSOUserInfo
  }
  catch {
    return null
  }
}

const canFallbackToTokenClaims = (status: number) => [400, 414, 431].includes(status)

const getIdentityFromUserInfo = (userInfo: RawSSOUserInfo) => {
  const subject = (userInfo.sub || '').trim()
  const subjectParts = subject.split('/', 2)
  const owner = (subjectParts.length === 2 ? subjectParts[0] : '') || 'CheersAI'
  const username = (
    userInfo.preferred_username
    || userInfo.preferredUsername
    || (subjectParts.length === 2 ? subjectParts[1] : '')
    || userInfo.name
    || ''
  ).trim()

  return {
    owner,
    username,
  }
}

const refreshAccessToken = async (sessionId: string, refreshToken: string) => {
  const { ssoBaseUrl, clientId } = getSSOConfig()
  const tokenUrl = new URL('/api/login/oauth/access_token', ssoBaseUrl)
  const params = new URLSearchParams()
  params.append('grant_type', 'refresh_token')
  params.append('refresh_token', refreshToken)
  params.append('client_id', clientId)

  const response = await fetch(tokenUrl.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
    },
    body: params.toString(),
  })

  if (!response.ok)
    throw new Error(`SSO refresh failed: ${response.status}`)

  const tokenData = await response.json()
  const expiresIn = Number.isFinite(Number(tokenData?.expires_in)) && Number(tokenData?.expires_in) > 0
    ? Number(tokenData.expires_in)
    : 60 * 60

  updateSession(sessionId, {
    accessToken: tokenData.access_token,
    refreshToken: tokenData.refresh_token || refreshToken,
    scope: tokenData.scope,
    expiresAt: Date.now() + expiresIn * 1000,
    lastSyncedAt: Date.now(),
  })

  return tokenData.access_token as string
}

export async function POST(request: Request) {
  try {
    const { ssoBaseUrl, clientId, clientSecret } = getSSOConfig()
    if (!ssoBaseUrl || !clientId || !clientSecret) {
      return NextResponse.json({ message: 'SSO password service is not configured.' }, { status: 500 })
    }

    const payload = await request.json() as {
      password?: string
      new_password?: string
      repeat_new_password?: string
    }

    const currentPassword = payload.password?.trim() || ''
    const newPassword = payload.new_password?.trim() || ''
    const repeatPassword = payload.repeat_new_password?.trim() || ''

    if (!newPassword)
      return NextResponse.json({ message: 'New password is required.' }, { status: 400 })

    if (newPassword !== repeatPassword)
      return NextResponse.json({ message: 'Repeated password does not match.' }, { status: 400 })

    const cookieStore = await cookies()
    const sessionId = cookieStore.get('sso_session_id')?.value
    if (!sessionId)
      return NextResponse.json({ message: 'No SSO session found.' }, { status: 401 })

    const session = getSession(sessionId)
    if (!session)
      return NextResponse.json({ message: 'SSO session expired or invalid.' }, { status: 401 })

    let accessToken = session.accessToken
    if (shouldRefreshSession(session) && session.refreshToken) {
      try {
        accessToken = await refreshAccessToken(sessionId, session.refreshToken)
      }
      catch {
        deleteSession(sessionId)
        cookieStore.delete('sso_session_id')
        return NextResponse.json({ message: 'SSO session refresh failed.' }, { status: 401 })
      }
    }

    const userinfoUrl = new URL('/api/userinfo', ssoBaseUrl)
    userinfoUrl.searchParams.set('access_token', accessToken)
    const userinfoResponse = await fetch(userinfoUrl.toString(), {
      headers: {
        Accept: 'application/json',
      },
      cache: 'no-store',
    })
    let userInfo: RawSSOUserInfo | null = null
    if (userinfoResponse.ok) {
      userInfo = await userinfoResponse.json() as RawSSOUserInfo
    }
    else if (canFallbackToTokenClaims(userinfoResponse.status)) {
      userInfo = decodeJwtPayload(accessToken)
    }

    if (!userInfo)
      return NextResponse.json({ message: 'Failed to fetch SSO user info.' }, { status: userinfoResponse.status })

    const { owner, username } = getIdentityFromUserInfo(userInfo)
    if (!owner || !username)
      return NextResponse.json({ message: 'Unable to resolve linked SSO user identity.' }, { status: 400 })

    const authHeader = buildBasicAuthHeader(clientId, clientSecret)
    const setPasswordUrl = new URL('/api/set-password', ssoBaseUrl)
    const setPasswordBody = new URLSearchParams({
      userOwner: owner,
      userName: username,
      newPassword,
    })
    if (currentPassword)
      setPasswordBody.set('oldPassword', currentPassword)

    const setPasswordResponse = await fetch(setPasswordUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Authorization': authHeader,
      },
      body: setPasswordBody.toString(),
    })

    const setPasswordPayload = await getResponsePayload(setPasswordResponse)
    if (!setPasswordResponse.ok || !isSuccessPayload(setPasswordPayload)) {
      const message = String(setPasswordPayload?.msg || setPasswordPayload?.message || 'Failed to update SSO password.')
      return NextResponse.json({ message }, { status: setPasswordResponse.ok ? 400 : setPasswordResponse.status })
    }

    const getUserUrl = new URL('/api/get-user', ssoBaseUrl)
    getUserUrl.searchParams.set('id', `${owner}/${username}`)
    const getUserResponse = await fetch(getUserUrl.toString(), {
      headers: {
        Accept: 'application/json',
        Authorization: authHeader,
      },
      cache: 'no-store',
    })

    const getUserPayload = await getResponsePayload(getUserResponse)
    const ssoUser = getUserPayload.data
    if (getUserResponse.ok && isSuccessPayload(getUserPayload) && ssoUser && typeof ssoUser === 'object') {
      const mutableSSOUser = ssoUser as JsonObject
      mutableSSOUser.signinWrongTimes = 0
      mutableSSOUser.lastSigninWrongTime = ''

      const unlockUserUrl = new URL('/api/update-user', ssoBaseUrl)
      unlockUserUrl.searchParams.set('id', `${owner}/${username}`)
      unlockUserUrl.searchParams.set('columns', 'signin_wrong_times,last_signin_wrong_time')
      await fetch(unlockUserUrl.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': authHeader,
        },
        body: JSON.stringify(mutableSSOUser),
      })
    }

    updateSession(sessionId, {
      lastSyncedAt: Date.now(),
    })

    return NextResponse.json({ result: 'success' })
  }
  catch (error) {
    console.error('SSO password update error:', error)
    return NextResponse.json({ message: 'Internal server error' }, { status: 500 })
  }
}
