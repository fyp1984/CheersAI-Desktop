import { Buffer } from 'node:buffer'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { deleteSession, getSession, shouldRefreshSession, updateSession } from '@/lib/sso-session'

type RawSSOUserInfo = {
  sub?: string
  owner?: string
  preferred_username?: string
  preferredUsername?: string
  name?: string
  displayName?: string
  email?: string
  groups?: unknown
  roles?: unknown
  permissions?: unknown
  iss?: string
  aud?: string | string[]
}

type RawSSOAccountResponse = {
  data?: {
    owner?: string
    name?: string
  }
}

type SsoTokenResponse = {
  access_token?: string
  refresh_token?: string
  expires_in?: number | string
  scope?: string
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

const normalizeStringArray = (values: unknown) => {
  if (!Array.isArray(values))
    return []

  return [...new Set(values.flatMap((value) => {
    if (typeof value === 'string' && value.trim())
      return [value.trim()]

    if (value && typeof value === 'object') {
      const record = value as Record<string, unknown>
      const normalizedValue = [record.name, record.displayName, record.id]
        .find(item => typeof item === 'string' && item.trim())

      if (typeof normalizedValue === 'string' && normalizedValue.trim())
        return [normalizedValue.trim()]
    }

    return []
  }))]
}

const normalizeUserInfo = (rawUserInfo: RawSSOUserInfo) => {
  const { ssoBaseUrl, clientId } = getSSOConfig()

  return {
    sub: rawUserInfo?.sub || '',
    preferred_username: rawUserInfo?.preferred_username || rawUserInfo?.preferredUsername || '',
    owner: rawUserInfo?.owner || '',
    name: rawUserInfo?.name || rawUserInfo?.displayName || '',
    email: rawUserInfo?.email || '',
    groups: normalizeStringArray(rawUserInfo?.groups),
    roles: normalizeStringArray(rawUserInfo?.roles),
    permissions: normalizeStringArray(rawUserInfo?.permissions),
    iss: rawUserInfo?.iss || ssoBaseUrl,
    aud: Array.isArray(rawUserInfo?.aud) ? rawUserInfo.aud[0] : (rawUserInfo?.aud || clientId),
  }
}

const validateUserInfo = (userInfo: ReturnType<typeof normalizeUserInfo>) => {
  const { ssoBaseUrl, clientId } = getSSOConfig()

  if (!userInfo.sub)
    return 'Missing SSO subject'

  if (userInfo.iss && userInfo.iss !== ssoBaseUrl)
    return 'Invalid SSO issuer'

  if (userInfo.aud && userInfo.aud !== clientId)
    return 'Invalid SSO audience'

  return null
}

const canFallbackToTokenClaims = (status: number) => [400, 414, 431].includes(status)
const DEFAULT_INTERNAL_API_BASE_URL = process.env.INTERNAL_API_BASE_URL?.trim() || 'http://localhost:5001'
const DEFAULT_INTERNAL_CONSOLE_API_PREFIX = `${DEFAULT_INTERNAL_API_BASE_URL.replace(/\/$/, '')}/console/api`

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

const fetchConsoleApiWithFallback = async (path: string, init: RequestInit) => {
  let lastError: unknown = null
  for (const url of getConsoleApiUrls(path)) {
    try {
      const response = await fetch(url, init)
      if (response.ok || ![502, 503, 504].includes(response.status))
        return response
      lastError = new Error(`Internal API returned ${response.status}`)
    }
    catch (error) {
      lastError = error
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Internal API is unavailable')
}

const refreshTokenViaProxy = async (refreshToken: string) => {
  const response = await fetchConsoleApiWithFallback('/auth/sso-proxy/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      grantType: 'refresh_token',
      refreshToken,
    }),
  })

  if (!response.ok)
    throw new Error(`SSO refresh proxy failed: ${response.status}`)

  return response.json() as Promise<SsoTokenResponse>
}

const fetchUserInfoViaProxy = async (accessToken: string) => {
  const response = await fetchConsoleApiWithFallback('/auth/sso-proxy/userinfo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accessToken }),
  })

  if (!response.ok)
    throw new Error(`SSO userinfo proxy failed: ${response.status}`)

  return response.json() as Promise<RawSSOUserInfo>
}

const tryTokenClaimsFallback = (accessToken: string, sessionId: string) => {
  const fallbackUserInfo = decodeJwtPayload(accessToken)
  if (!fallbackUserInfo)
    return null

  const normalizedFallbackUserInfo = normalizeUserInfo(fallbackUserInfo)
  const validationError = validateUserInfo(normalizedFallbackUserInfo)
  if (validationError)
    return null

  updateSession(sessionId, {
    lastSyncedAt: Date.now(),
  })

  return normalizedFallbackUserInfo
}

const fetchAccountIdentityViaProxy = async (accessToken: string) => {
  const response = await fetchConsoleApiWithFallback('/auth/sso-proxy/get-account', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accessToken }),
  })

  if (!response.ok)
    return null

  const payload = await response.json() as RawSSOAccountResponse
  const owner = payload?.data?.owner?.trim()
  const preferredUsername = payload?.data?.name?.trim()
  if (!owner && !preferredUsername)
    return null

  return {
    owner: owner || '',
    preferred_username: preferredUsername || '',
  } satisfies Pick<RawSSOUserInfo, 'owner' | 'preferred_username'>
}

const fetchAccountIdentity = async (ssoBaseUrl: string, accessToken: string) => {
  const accountUrl = new URL('/api/get-account', ssoBaseUrl)
  accountUrl.searchParams.set('access_token', accessToken)

  try {
    const response = await fetch(accountUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
    })

    if (!response.ok)
      return null

    const payload = await response.json() as RawSSOAccountResponse
    const owner = payload?.data?.owner?.trim()
    const preferredUsername = payload?.data?.name?.trim()
    if (!owner && !preferredUsername)
      return null

    return {
      owner: owner || '',
      preferred_username: preferredUsername || '',
    } satisfies Pick<RawSSOUserInfo, 'owner' | 'preferred_username'>
  }
  catch {
    return null
  }
}

const refreshAccessToken = async (sessionId: string, refreshToken: string) => {
  const { ssoBaseUrl, clientId } = getSSOConfig()
  const tokenUrl = new URL('/api/login/oauth/access_token', ssoBaseUrl)
  const params = new URLSearchParams()
  params.append('grant_type', 'refresh_token')
  params.append('refresh_token', refreshToken)
  params.append('client_id', clientId)

  let tokenData: SsoTokenResponse | null = null
  try {
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

    tokenData = await response.json()
  }
  catch (error) {
    console.warn('[SSO] Refresh token fetch failed, falling back to proxy:', error)
    tokenData = await refreshTokenViaProxy(refreshToken)
  }

  if (!tokenData?.access_token)
    throw new Error('SSO refresh response missing access token')

  const refreshedAccessToken = tokenData.access_token
  const expiresIn = Number.isFinite(Number(tokenData.expires_in)) && Number(tokenData.expires_in) > 0
    ? Number(tokenData.expires_in)
    : 60 * 60

  updateSession(sessionId, {
    accessToken: refreshedAccessToken,
    refreshToken: tokenData.refresh_token || refreshToken,
    scope: tokenData.scope,
    expiresAt: Date.now() + expiresIn * 1000,
    lastSyncedAt: Date.now(),
  })

  return refreshedAccessToken
}

export async function POST() {
  try {
    const config = getSSOConfig()
    if (!config.ssoBaseUrl || !config.clientId) {
      return NextResponse.json(
        { error: 'SSO configuration is incomplete: NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL / NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID' },
        { status: 500 },
      )
    }

    const cookieStore = await cookies()
    const sessionId = cookieStore.get('sso_session_id')?.value

    if (!sessionId) {
      return NextResponse.json(
        { error: 'No SSO session found' },
        { status: 401 },
      )
    }

    const session = getSession(sessionId)
    if (!session) {
      return NextResponse.json(
        { error: 'SSO session expired or invalid' },
        { status: 401 },
      )
    }

    const { ssoBaseUrl } = config
    const userinfoUrl = new URL('/api/userinfo', ssoBaseUrl)
    let accessToken = session.accessToken

    if (shouldRefreshSession(session) && session.refreshToken) {
      try {
        accessToken = await refreshAccessToken(sessionId, session.refreshToken)
      }
      catch {
        deleteSession(sessionId)
        cookieStore.delete('sso_session_id')
        return NextResponse.json(
          { error: 'SSO session refresh failed' },
          { status: 401 },
        )
      }
    }

    const tokenClaims = decodeJwtPayload(accessToken)

    let rawUserInfo: RawSSOUserInfo | null = null
    let userinfoStatus = 200
    try {
      const userinfoResponse = await fetch(userinfoUrl.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
      })

      userinfoStatus = userinfoResponse.status
      if (!userinfoResponse.ok)
        throw new Error(`SSO userinfo failed: ${userinfoResponse.status}`)

      rawUserInfo = await userinfoResponse.json()
    }
    catch (error) {
      if (canFallbackToTokenClaims(userinfoStatus)) {
        const fallbackUserInfo = tryTokenClaimsFallback(accessToken, sessionId)
        if (fallbackUserInfo)
          return NextResponse.json(fallbackUserInfo)
      }

      console.warn('[SSO] Userinfo fetch failed, falling back to proxy:', error)
      try {
        rawUserInfo = await fetchUserInfoViaProxy(accessToken)
      }
      catch {
        rawUserInfo = null
      }
    }

    if (!rawUserInfo) {
      const fallbackUserInfo = tryTokenClaimsFallback(accessToken, sessionId)
      if (fallbackUserInfo)
        return NextResponse.json(fallbackUserInfo)

      return NextResponse.json(
        { error: 'Failed to fetch user info' },
        { status: 400 },
      )
    }

    const accountIdentity = (!rawUserInfo?.owner && !tokenClaims?.owner)
      ? await (async () => {
          try {
            return await fetchAccountIdentity(ssoBaseUrl, accessToken)
          }
          catch {
            return await fetchAccountIdentityViaProxy(accessToken)
          }
        })()
      : null
    const userInfo = normalizeUserInfo({
      ...tokenClaims,
      ...rawUserInfo,
      owner: rawUserInfo?.owner || tokenClaims?.owner || accountIdentity?.owner,
      preferred_username:
        rawUserInfo?.preferred_username
        || rawUserInfo?.preferredUsername
        || tokenClaims?.preferred_username
        || tokenClaims?.preferredUsername
        || accountIdentity?.preferred_username,
    })
    const validationError = validateUserInfo(userInfo)

    if (validationError) {
      deleteSession(sessionId)
      cookieStore.delete('sso_session_id')
      return NextResponse.json(
        { error: validationError },
        { status: 401 },
      )
    }

    updateSession(sessionId, {
      lastSyncedAt: Date.now(),
    })

    return NextResponse.json(userInfo)
  }
  catch (error) {
    console.error('SSO userinfo error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 },
    )
  }
}
