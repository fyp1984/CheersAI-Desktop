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

const shouldTryNextInternalApi = (response: Response) => [502, 503, 504].includes(response.status)

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

const fetchConsoleApi = async (request: NextRequest, path: string, init?: RequestInit) => {
  const cookieHeader = buildCookieHeader(request)
  const csrfToken = resolveCsrfToken(request)
  let lastError: unknown = null

  for (const url of getConsoleApiUrls(path)) {
    try {
      const response = await fetch(url, {
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
      if (!shouldTryNextInternalApi(response))
        return response
      lastError = new Error(`Internal API returned ${response.status}`)
    }
    catch (error) {
      lastError = error
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Internal API is unavailable')
}

export async function GET(request: NextRequest) {
  try {
    const profileResponse = await fetchConsoleApi(request, '/account/profile')

    if (!profileResponse.ok) {
      if (profileResponse.status === 401 || profileResponse.status === 403)
        return loggedOutResponse()

      return NextResponse.json({ logged_in: false, upstream_status: profileResponse.status })
    }

    // A successful profile probe already proves the browser session is authenticated.
    // Workspace bootstrap can still fail transiently on CSRF or timing-sensitive paths,
    // so expose it as metadata instead of turning a valid login into a false negative.
    try {
      const workspaceResponse = await fetchConsoleApi(request, '/workspaces/current', {
        method: 'POST',
        body: JSON.stringify({}),
      })

      if (workspaceResponse.ok)
        return NextResponse.json({ logged_in: true })

      return NextResponse.json({ logged_in: true, workspace_status: workspaceResponse.status })
    }
    catch {
      return NextResponse.json({ logged_in: true, workspace_status: 'probe_failed' })
    }
  }
  catch {
    return loggedOutResponse()
  }
}
