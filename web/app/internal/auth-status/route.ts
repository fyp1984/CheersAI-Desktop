import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

const DEFAULT_INTERNAL_API_BASE_URL = process.env.INTERNAL_API_BASE_URL?.trim() || 'http://localhost:5001'
const DEFAULT_INTERNAL_CONSOLE_API_PREFIX = `${DEFAULT_INTERNAL_API_BASE_URL.replace(/\/$/, '')}/console/api`
const AUTH_COOKIE_NAMES = [
  'access_token',
  'refresh_token',
  'csrf_token',
  '__Host-access_token',
  '__Host-refresh_token',
  '__Host-csrf_token',
  'sso_session_id',
]

const normalizeInternalApiPrefix = (rawPrefix: string) => {
  const trimmedPrefix = rawPrefix.trim()
  if (!trimmedPrefix)
    return DEFAULT_INTERNAL_CONSOLE_API_PREFIX

  if (/^https?:\/\//i.test(trimmedPrefix))
    return trimmedPrefix.replace(/\/$/, '')

  if (trimmedPrefix.startsWith('/'))
    return `http://localhost:5001${trimmedPrefix}`.replace(/\/$/, '')

  return `http://${trimmedPrefix}`.replace(/\/$/, '')
}

const getConsoleApiUrl = (path: string) => {
  const apiPrefix = process.env.INTERNAL_CONSOLE_API_PREFIX?.trim()
    || process.env.CONSOLE_API_PREFIX?.trim()
    || process.env.NEXT_PUBLIC_API_PREFIX?.trim()
    || DEFAULT_INTERNAL_CONSOLE_API_PREFIX
  const normalizedPrefix = normalizeInternalApiPrefix(apiPrefix)
  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  return `${normalizedPrefix}${normalizedPath}`
}

const buildCookieHeader = (request: NextRequest) => {
  return request.cookies.getAll()
    .map(cookie => `${cookie.name}=${cookie.value}`)
    .join('; ')
}

const resolveCsrfToken = (request: NextRequest) => {
  return request.cookies.get('__Host-csrf_token')?.value
    || request.cookies.get('csrf_token')?.value
    || ''
}

const clearAuthCookies = (response: NextResponse) => {
  AUTH_COOKIE_NAMES.forEach((cookieName) => {
    response.cookies.delete(cookieName)
  })
  return response
}

const loggedOutResponse = (payload: Record<string, unknown> = {}) => {
  return clearAuthCookies(NextResponse.json({ logged_in: false, ...payload }))
}

const fetchConsoleApi = (request: NextRequest, path: string, init?: RequestInit) => {
  const cookieHeader = buildCookieHeader(request)
  const csrfToken = resolveCsrfToken(request)

  return fetch(getConsoleApiUrl(path), {
    method: init?.method || 'GET',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      ...init?.headers,
    },
    body: init?.body,
    cache: 'no-store',
  })
}

export async function GET(request: NextRequest) {
  try {
    const profileResponse = await fetchConsoleApi(request, '/account/profile')

    if (!profileResponse.ok) {
      if (profileResponse.status === 401 || profileResponse.status === 403)
        return loggedOutResponse()

      return NextResponse.json({ logged_in: false, upstream_status: profileResponse.status })
    }

    const workspaceResponse = await fetchConsoleApi(request, '/workspaces/current', {
      method: 'POST',
      body: JSON.stringify({}),
    })

    if (workspaceResponse.ok)
      return NextResponse.json({ logged_in: true })

    if (workspaceResponse.status === 401 || workspaceResponse.status === 403)
      return loggedOutResponse({ upstream_status: workspaceResponse.status })

    return NextResponse.json({ logged_in: false, upstream_status: workspaceResponse.status })
  }
  catch {
    return loggedOutResponse()
  }
}
