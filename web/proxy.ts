import type { NextRequest } from 'next/server'
import { Buffer } from 'node:buffer'
import { NextResponse } from 'next/server'

const NECESSARY_DOMAIN = '*.sentry.io http://localhost:* http://127.0.0.1:* https://analytics.google.com googletagmanager.com *.googletagmanager.com https://www.google-analytics.com https://api.github.com https://api2.amplitude.com *.amplitude.com'
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

const PROTECTED_PATH_PREFIXES = [
  '/account',
  '/app',
  '/apps',
  '/audit-logs',
  '/chat',
  '/data-masking',
  '/datasets',
  '/explore',
  '/gitea-settings',
  '/plugins',
  '/sys-admin',
  '/team-admin',
  '/tools',
  '/workflows',
]

const PUBLIC_PATH_PREFIXES = [
  '/api',
  '/console/api',
  '/files',
  '/filebay-download',
  '/forgot-password',
  '/init',
  '/install',
  '/internal',
  '/oauth-api',
  '/oauth-callback',
  '/proxy-marketplace',
  '/reset-password',
  '/serwist',
  '/signin',
  '/signup',
  '/sync-config',
  '/webapp-signin',
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

const wrapResponseWithXFrameOptions = (response: NextResponse, pathname: string) => {
  // prevent clickjacking: https://owasp.org/www-community/attacks/Clickjacking
  // Chatbot page should be allowed to be embedded in iframe. It's a feature
  if (process.env.NEXT_PUBLIC_ALLOW_EMBED !== 'true' && !pathname.startsWith('/chat') && !pathname.startsWith('/workflow') && !pathname.startsWith('/completion') && !pathname.startsWith('/webapp-signin'))
    response.headers.set('X-Frame-Options', 'DENY')

  return response
}

const normalizePathname = (pathname: string) => {
  if (pathname.length <= 1)
    return '/'

  return pathname.replace(/\/$/, '')
}

const pathMatchesPrefix = (pathname: string, prefix: string) => {
  return pathname === prefix || pathname.startsWith(`${prefix}/`)
}

const isProtectedPath = (pathname: string) => {
  const normalizedPathname = normalizePathname(pathname)

  if (PUBLIC_PATH_PREFIXES.some(prefix => pathMatchesPrefix(normalizedPathname, prefix)))
    return false

  return PROTECTED_PATH_PREFIXES.some(prefix => pathMatchesPrefix(normalizedPathname, prefix))
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

const clearAuthCookies = (response: NextResponse) => {
  AUTH_COOKIE_NAMES.forEach((cookieName) => {
    response.cookies.delete(cookieName)
  })
  return response
}

const redirectToSignin = (request: NextRequest) => {
  const url = request.nextUrl.clone()
  url.pathname = '/signin'
  url.search = ''

  return clearAuthCookies(NextResponse.redirect(url))
}

const hasValidWorkspaceSession = async (request: NextRequest) => {
  const profileResponse = await fetchConsoleApi(request, '/account/profile')
  if (!profileResponse.ok)
    return false

  // Treat a successful profile probe as the source of truth for browser login state.
  // Workspace bootstrap may still reject this server-side probe transiently, but
  // that should not bounce an authenticated user back to /signin.
  return true
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const requestHeaders = new Headers(request.headers)

  if (isProtectedPath(pathname)) {
    const isLoggedIn = await hasValidWorkspaceSession(request).catch(() => false)
    if (!isLoggedIn)
      return wrapResponseWithXFrameOptions(redirectToSignin(request), pathname)
  }

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  })
  if (request.cookies.has('sso_refresh_token'))
    response.cookies.delete('sso_refresh_token')

  const isWhiteListEnabled = !!process.env.NEXT_PUBLIC_CSP_WHITELIST && process.env.NODE_ENV === 'production'
  if (!isWhiteListEnabled)
    return wrapResponseWithXFrameOptions(response, pathname)

  const whiteList = `${process.env.NEXT_PUBLIC_CSP_WHITELIST} ${NECESSARY_DOMAIN}`
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const csp = `'nonce-${nonce}'`

  const scheme_source = 'data: mediastream: blob: filesystem:'

  const cspHeader = `
    default-src 'self' ${scheme_source} ${csp} ${whiteList};
    connect-src 'self' ${scheme_source} ${csp} ${whiteList};
    script-src 'self' ${scheme_source} ${csp} ${whiteList};
    style-src 'self' 'unsafe-inline' ${scheme_source} ${whiteList};
    worker-src 'self' ${scheme_source} ${csp} ${whiteList};
    media-src 'self' ${scheme_source} ${csp} ${whiteList};
    img-src * data: blob:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    upgrade-insecure-requests;
`
  // Replace newline characters and spaces
  const contentSecurityPolicyHeaderValue = cspHeader
    .replace(/\s{2,}/g, ' ')
    .trim()

  requestHeaders.set('x-nonce', nonce)

  requestHeaders.set(
    'Content-Security-Policy',
    contentSecurityPolicyHeaderValue,
  )

  response.headers.set(
    'Content-Security-Policy',
    contentSecurityPolicyHeaderValue,
  )

  return wrapResponseWithXFrameOptions(response, pathname)
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    {
      // source: '/((?!api|_next/static|_next/image|favicon.ico).*)',
      source: '/((?!_next/static|_next/image|favicon.ico).*)',
      // source: '/(.*)',
      // missing: [
      //   { type: 'header', key: 'next-router-prefetch' },
      //   { type: 'header', key: 'purpose', value: 'prefetch' },
      // ],
    },
  ],
}
