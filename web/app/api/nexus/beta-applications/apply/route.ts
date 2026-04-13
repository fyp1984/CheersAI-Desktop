import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

const NEXUS_BETA_APPLY_PATH = '/nexus/api/beta-applications/apply'

const buildNexusTargetUrl = () => {
  const configuredBase = process.env.NEXUS_API_BASE_URL || process.env.NEXT_PUBLIC_NEXUS_API_PREFIX || 'http://localhost:5173'
  if (!configuredBase)
    return null
  return `${configuredBase.replace(/\/+$/, '')}${NEXUS_BETA_APPLY_PATH}`
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, language } = body || {}

    if (!name || !email) {
      return NextResponse.json(
        { result: 'fail', message: 'Missing required fields: name/email' },
        { status: 400 },
      )
    }

    const targetUrl = buildNexusTargetUrl()
    if (!targetUrl) {
      return NextResponse.json(
        { result: 'fail', message: 'Nexus API base URL is not configured' },
        { status: 500 },
      )
    }
    const upstreamResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ name, email, language }),
      cache: 'no-store',
    })

    const upstreamBody = await upstreamResponse.text()
    const contentType = upstreamResponse.headers.get('content-type')
    const responseHeaders = new Headers()
    if (contentType)
      responseHeaders.set('Content-Type', contentType)

    return new NextResponse(upstreamBody || JSON.stringify({ result: upstreamResponse.ok ? 'success' : 'fail' }), {
      status: upstreamResponse.status,
      headers: responseHeaders,
    })
  }
  catch (error) {
    console.error('Nexus beta application proxy failed:', error)
    return NextResponse.json(
      { result: 'fail', message: 'Nexus apply proxy request failed' },
      { status: 502 },
    )
  }
}
