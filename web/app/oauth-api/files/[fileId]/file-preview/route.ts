import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

const FILES_BASE_URL = process.env.INTERNAL_FILES_URL || process.env.INTERNAL_API_BASE_URL || 'http://api:5001'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ fileId: string }> },
) {
  try {
    const { fileId } = await params
    const targetUrl = `${FILES_BASE_URL}/files/${fileId}/file-preview${request.nextUrl.search}`
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        accept: request.headers.get('accept') || '*/*',
      },
    })

    if (!response.ok)
      return new NextResponse(response.body, { status: response.status, headers: response.headers })

    return new NextResponse(response.body, {
      status: response.status,
      headers: response.headers,
    })
  }
  catch {
    return NextResponse.json({ error: 'Proxy request failed' }, { status: 500 })
  }
}
