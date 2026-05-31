import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

const getConsoleApiUrl = (path: string) => {
  const apiPrefix = process.env.CONSOLE_API_PREFIX?.trim() || 'http://localhost:5001/console/api'
  const normalizedPrefix = apiPrefix.replace(/\/$/, '')
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
