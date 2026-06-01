import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

const DEFAULT_INTERNAL_CONSOLE_API_PREFIX = 'http://localhost:5001/console/api'

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

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(getConsoleApiUrl('/account/profile'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.cookies.getAll().map(cookie => `${cookie.name}=${cookie.value}`).join('; '),
      },
      cache: 'no-store',
    })

    if (response.ok)
      return NextResponse.json({ logged_in: true })

    if (response.status === 401)
      return NextResponse.json({ logged_in: false })

    return NextResponse.json({ logged_in: false, upstream_status: response.status })
  }
  catch {
    return NextResponse.json({ logged_in: false })
  }
}
