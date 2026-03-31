import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.API_URL || 'http://localhost:5001'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path, 'GET')
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path, 'POST')
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path, 'PUT')
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path, 'DELETE')
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path, 'PATCH')
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  const path = pathSegments.join('/')
  const url = `${API_URL}/${path}`
  
  // Get search params
  const searchParams = request.nextUrl.searchParams.toString()
  const fullUrl = searchParams ? `${url}?${searchParams}` : url
  
  // Copy headers
  const headers = new Headers()
  request.headers.forEach((value, key) => {
    // Skip host header
    if (key.toLowerCase() !== 'host') {
      headers.set(key, value)
    }
  })
  
  // Get body for non-GET requests
  let body: BodyInit | null = null
  if (method !== 'GET' && method !== 'HEAD') {
    try {
      body = await request.text()
    } catch (e) {
      // No body
    }
  }
  
  try {
    const response = await fetch(fullUrl, {
      method,
      headers,
      body,
      // Don't follow redirects - let the browser handle them
      redirect: 'manual',
    })
    
    // Copy response headers, including Set-Cookie
    const responseHeaders = new Headers()
    response.headers.forEach((value, key) => {
      // Forward all headers including Set-Cookie
      responseHeaders.set(key, value)
    })
    
    // Handle redirects (3xx status codes)
    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.get('location')
      if (location) {
        // Return redirect response to browser
        return NextResponse.redirect(location, {
          status: response.status,
          headers: responseHeaders,
        })
      }
    }
    
    // Handle different content types
    const contentType = response.headers.get('content-type')
    
    // If it's JSON, parse and return
    if (contentType && contentType.includes('application/json')) {
      try {
        const text = await response.text()
        if (!text || text.trim() === '') {
          // Empty response
          return NextResponse.json({}, {
            status: response.status,
            statusText: response.statusText,
            headers: responseHeaders,
          })
        }
        const data = JSON.parse(text)
        return NextResponse.json(data, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        })
      } catch (e) {
        console.error('JSON parse error:', e)
        // If JSON parsing fails, return empty object
        return NextResponse.json({}, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        })
      }
    }
    
    // For other content types, return as is
    const responseBody = await response.arrayBuffer()
    
    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    })
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json(
      { error: 'Proxy request failed', details: String(error) },
      { status: 500 }
    )
  }
}
