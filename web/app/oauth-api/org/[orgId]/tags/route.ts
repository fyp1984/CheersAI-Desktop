import type { NextRequest } from 'next/server'
import { proxySSORequest } from '../../shared'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params
  return proxySSORequest(request, `/api/v1/org/${orgId}/tags`, { orgId })
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params
  const body = await request.text()
  return proxySSORequest(request, `/api/v1/org/${orgId}/tags`, {
    method: 'POST',
    body,
    orgId,
  })
}
