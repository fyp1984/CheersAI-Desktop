import type { NextRequest } from 'next/server'
import type { ICurrentWorkspace } from '@/models/common'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { deleteSession, getSession, shouldRefreshSession, storeSession, updateSession } from '@/lib/sso-session'
import { getWorkspaceCapabilities, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'

const SESSION_TIMEOUT = 5000
const SSO_SESSION_COOKIE = 'sso_session_id'
const externalConsoleApiUrl = process.env.CONSOLE_API_URL?.trim() || ''
const normalizedExternalConsoleApiUrl = externalConsoleApiUrl.replace(/\/$/, '')
const safeExternalConsoleApiUrl = /^https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?$/i.test(normalizedExternalConsoleApiUrl)
  ? ''
  : normalizedExternalConsoleApiUrl
const INTERNAL_CONSOLE_API_BASE = (
  process.env.INTERNAL_API_BASE_URL?.trim()
  || safeExternalConsoleApiUrl
  || 'http://api:5001'
).replace(/\/$/, '')
const INTERNAL_CONSOLE_API_PREFIX = `${INTERNAL_CONSOLE_API_BASE}/console/api`

type AccessTokenResult = {
  accessToken: string
  refreshToken?: string
  sessionId: string
}

type ErrorResult = {
  response: NextResponse
}

type WorkspaceErrorResult = {
  response: NextResponse
  status: number
}

type ProxyRequestInit = {
  method?: string
  body?: string | null
  orgId?: string
}

const PUBLIC_COOKIE_DOMAIN = process.env.NEXT_PUBLIC_COOKIE_DOMAIN?.trim() || ''
const WORKSPACE_COOKIE_KEYS = [
  'access_token',
  'refresh_token',
  'csrf_token',
] as const
const WORKSPACE_AUTH_COOKIE_NAMES = new Set(
  WORKSPACE_COOKIE_KEYS.flatMap(cookieKey => [cookieKey, `__Host-${cookieKey}`]),
)

const parseCookieHeader = (rawCookieHeader: string) => {
  if (!rawCookieHeader.trim())
    return []

  return rawCookieHeader
    .split(';')
    .map(part => part.trim())
    .filter(Boolean)
    .map((part) => {
      const separatorIndex = part.indexOf('=')
      if (separatorIndex < 0)
        return null

      return {
        name: part.slice(0, separatorIndex).trim(),
        value: part.slice(separatorIndex + 1).trim(),
      }
    })
    .filter((cookie): cookie is { name: string, value: string } => Boolean(cookie?.name))
}

const getWorkspaceCookiePreference = () => {
  const preferHostCookies = !PUBLIC_COOKIE_DOMAIN
  return WORKSPACE_COOKIE_KEYS.map((cookieKey) => {
    return preferHostCookies
      ? [`__Host-${cookieKey}`, cookieKey]
      : [cookieKey, `__Host-${cookieKey}`]
  })
}

const buildWorkspaceAuthCookieHeader = (request: NextRequest) => {
  const requestCookies = typeof request.cookies?.getAll === 'function'
    ? request.cookies.getAll()
    : parseCookieHeader(request.headers.get('cookie') || '')

  const cookieValueByName = new Map(
    requestCookies
      .filter(cookie => WORKSPACE_AUTH_COOKIE_NAMES.has(cookie.name))
      .map(cookie => [cookie.name, cookie.value] as const),
  )

  return getWorkspaceCookiePreference()
    .map((cookieNames) => {
      const matchedName = cookieNames.find(cookieName => cookieValueByName.has(cookieName))
      if (!matchedName)
        return null

      return `${matchedName}=${cookieValueByName.get(matchedName)}`
    })
    .filter((cookie): cookie is string => Boolean(cookie))
    .join('; ')
}

const resolveWorkspaceCsrfToken = (request: NextRequest) => {
  const headerToken = request.headers.get('x-csrf-token')?.trim()
  if (headerToken)
    return headerToken

  return request.cookies?.get('__Host-csrf_token')?.value
    || request.cookies?.get('csrf_token')?.value
    || ''
}

export const getSSOConfig = () => {
  const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL?.trim() || ''
  const clientId = process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID?.trim() || ''

  return {
    ssoBaseUrl,
    clientId,
  }
}

export const getResponsePayload = async (response: Response) => {
  try {
    return await response.json() as Record<string, unknown>
  }
  catch {
    return {}
  }
}

const fetchInternalConsoleJson = async (request: NextRequest, pathname: string, init?: { method?: string, body?: string }) => {
  const csrfToken = resolveWorkspaceCsrfToken(request)
  const workspaceCookieHeader = buildWorkspaceAuthCookieHeader(request)

  return fetch(`${INTERNAL_CONSOLE_API_PREFIX}${pathname}`, {
    method: init?.method || 'GET',
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...(workspaceCookieHeader ? { cookie: workspaceCookieHeader } : {}),
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
    },
    ...(init?.body ? { body: init.body } : {}),
    cache: 'no-store',
  })
}

const clearSSOCookies = async () => {
  const cookieStore = await cookies()
  cookieStore.delete(SSO_SESSION_COOKIE)
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
    cache: 'no-store',
  })

  if (!response.ok)
    throw new Error(`SSO refresh failed: ${response.status}`)

  const payload = await response.json()
  const expiresIn = Number.isFinite(Number(payload?.expires_in)) && Number(payload?.expires_in) > 0
    ? Number(payload.expires_in)
    : 60 * 60

  const nextRefreshToken = (payload.refresh_token || refreshToken) as string
  const updatedSession = updateSession(sessionId, {
    accessToken: payload.access_token,
    refreshToken: nextRefreshToken,
    scope: payload.scope,
    expiresAt: Date.now() + expiresIn * 1000,
    lastSyncedAt: Date.now(),
  })
  if (!updatedSession)
    storeSession(sessionId, payload.access_token, nextRefreshToken, expiresIn, payload.scope)

  return {
    accessToken: payload.access_token as string,
    refreshToken: nextRefreshToken,
  }
}

const resolveAccessToken = async (): Promise<AccessTokenResult | ErrorResult> => {
  const { ssoBaseUrl, clientId } = getSSOConfig()
  if (!ssoBaseUrl || !clientId) {
    return {
      response: NextResponse.json({ message: 'SSO service is not configured.' }, { status: 500 }),
    }
  }

  const cookieStore = await cookies()
  const sessionId = cookieStore.get(SSO_SESSION_COOKIE)?.value
  if (!sessionId) {
    return {
      response: NextResponse.json({ message: 'No SSO session found.' }, { status: 401 }),
    }
  }

  const session = getSession(sessionId)
  if (!session) {
    return {
      response: NextResponse.json({ message: 'SSO session expired or invalid.' }, { status: 401 }),
    }
  }

  let accessToken = session.accessToken
  let refreshToken = session.refreshToken
  if (shouldRefreshSession(session) && refreshToken) {
    try {
      const refreshed = await Promise.race([
        refreshAccessToken(sessionId, refreshToken),
        new Promise<never>((_, reject) => setTimeout(() => reject(new Error('SSO refresh timeout')), SESSION_TIMEOUT)),
      ])
      accessToken = refreshed.accessToken
      refreshToken = refreshed.refreshToken
    }
    catch {
      deleteSession(sessionId)
      await clearSSOCookies()
      return {
        response: NextResponse.json({ message: 'SSO session refresh failed.' }, { status: 401 }),
      }
    }
  }

  return {
    accessToken,
    refreshToken,
    sessionId,
  }
}

const relayResponse = async (response: Response) => {
  const contentType = response.headers.get('content-type') || ''

  if (response.status === 204)
    return new NextResponse(null, { status: 204 })

  if (contentType.includes('application/json')) {
    const payload = await getResponsePayload(response)
    return NextResponse.json(payload, { status: response.status })
  }

  const body = await response.text()
  return new NextResponse(body, {
    status: response.status,
    headers: contentType ? { 'Content-Type': contentType } : undefined,
  })
}

const getWorkspaceAccessErrorResponse = (status: number) => {
  return NextResponse.json(
    { message: status === 401 ? 'Workspace session expired.' : 'Failed to resolve workspace access.' },
    { status: status === 401 ? 401 : status === 403 ? 403 : 500 },
  )
}

const fetchCurrentWorkspace = async (request: NextRequest): Promise<{ workspace: ICurrentWorkspace } | { error: WorkspaceErrorResult }> => {
  const response = await fetchInternalConsoleJson(request, '/workspaces/current', {
    method: 'POST',
    body: JSON.stringify({}),
  })

  if (!response.ok) {
    return {
      error: {
        status: response.status,
        response: getWorkspaceAccessErrorResponse(response.status),
      },
    }
  }

  const workspace = await response.json() as ICurrentWorkspace
  return { workspace }
}

type CurrentAccountProfile = {
  id: string
  email: string
}

type CurrentWorkspaceMember = {
  id: string
  email: string
  role: string
}

const fetchCurrentAccountProfile = async (request: NextRequest): Promise<CurrentAccountProfile | null> => {
  const response = await fetchInternalConsoleJson(request, '/account/profile')
  if (!response.ok)
    return null

  const payload = await response.json() as Partial<CurrentAccountProfile>
  const id = String(payload?.id || '').trim()
  const email = String(payload?.email || '').trim().toLowerCase()
  if (!id && !email)
    return null

  return { id, email }
}

const fetchCurrentWorkspaceMembers = async (request: NextRequest): Promise<CurrentWorkspaceMember[] | null> => {
  const response = await fetchInternalConsoleJson(request, '/workspaces/current/members')
  if (!response.ok)
    return null

  const payload = await response.json() as { accounts?: Array<Partial<CurrentWorkspaceMember>> }
  if (!Array.isArray(payload?.accounts))
    return null

  return payload.accounts.map(member => ({
    id: String(member?.id || '').trim(),
    email: String(member?.email || '').trim().toLowerCase(),
    role: String(member?.role || '').trim().toLowerCase(),
  })).filter(member => Boolean(member.id || member.email))
}

const ensureWorkspaceTagManagementAccessFromMembers = async (request: NextRequest, userId: string) => {
  const [currentAccount, members] = await Promise.all([
    fetchCurrentAccountProfile(request),
    fetchCurrentWorkspaceMembers(request),
  ])

  if (!currentAccount || !members)
    return null

  const currentMember = members.find((member) => {
    if (currentAccount.id && member.id)
      return member.id === currentAccount.id
    if (currentAccount.email && member.email)
      return member.email === currentAccount.email
    return false
  })
  const targetMemberExists = members.some(member => member.id === userId)

  if (!currentMember || !targetMemberExists)
    return NextResponse.json({ message: 'Forbidden' }, { status: 403 })

  if (!['owner', 'admin'].includes(currentMember.role))
    return NextResponse.json({ message: 'Forbidden' }, { status: 403 })

  return null
}

export const ensureWorkspaceTagManagementAccess = async (request: NextRequest, orgId: string) => {
  const workspaceResult = await fetchCurrentWorkspace(request)
  if ('error' in workspaceResult) {
    if (workspaceResult.error.status === 401)
      return workspaceResult.error.response

    const targetUserId = request.nextUrl.pathname.match(/\/users\/([^/]+)\/profile-tag\/?$/)?.[1] || ''
    if (targetUserId) {
      const fallbackResponse = await ensureWorkspaceTagManagementAccessFromMembers(request, targetUserId)
      if (!fallbackResponse)
        return null
      if (fallbackResponse.status === 403)
        return fallbackResponse
    }

    return workspaceResult.error.response
  }

  const { workspace } = workspaceResult
  const capabilities = getWorkspaceCapabilities(workspace)
  const canManageMemberTags = workspace.id === orgId
    && ['owner', 'admin'].includes(workspace.role)
    && [
      WORKSPACE_CAPABILITIES.settingsTeam,
      WORKSPACE_CAPABILITIES.teamManage,
    ].some(capability => capabilities.includes(capability))

  if (!canManageMemberTags) {
    return NextResponse.json(
      { message: 'Forbidden' },
      { status: 403 },
    )
  }

  return null
}

export const proxySSORequest = async (
  request: NextRequest,
  pathname: string,
  init?: ProxyRequestInit,
) => {
  if (init?.orgId) {
    const deniedResponse = await ensureWorkspaceTagManagementAccess(request, init.orgId)
    if (deniedResponse)
      return deniedResponse
  }

  const authResult = await resolveAccessToken()
  if ('response' in authResult)
    return authResult.response

  const { ssoBaseUrl } = getSSOConfig()

  const makeRequest = async (accessToken: string) => {
    const targetUrl = new URL(pathname, ssoBaseUrl)
    request.nextUrl.searchParams.forEach((value, key) => {
      targetUrl.searchParams.append(key, value)
    })

    const headers = new Headers({
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    })
    if (init?.body)
      headers.set('Content-Type', 'application/json')

    return fetch(targetUrl.toString(), {
      method: init?.method || request.method,
      headers,
      body: init?.body || undefined,
      cache: 'no-store',
    })
  }

  let response = await makeRequest(authResult.accessToken)
  if (response.status === 401 && authResult.refreshToken) {
    try {
      const refreshed = await Promise.race([
        refreshAccessToken(authResult.sessionId, authResult.refreshToken),
        new Promise<never>((_, reject) => setTimeout(() => reject(new Error('SSO refresh timeout')), SESSION_TIMEOUT)),
      ])
      response = await makeRequest(refreshed.accessToken)
    }
    catch {
      deleteSession(authResult.sessionId)
      await clearSSOCookies()
      return NextResponse.json({ message: 'SSO session refresh failed.' }, { status: 401 })
    }
  }

  return relayResponse(response)
}
