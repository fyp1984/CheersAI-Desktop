import type { NextRequest } from 'next/server'
import { proxySSORequest } from '../../../shared'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string, tagId: string }> },
) {
  const { orgId, tagId } = await params
  const body = await request.text()
  return proxySSORequest(request, `/api/v1/org/${orgId}/tags/${tagId}`, {
    method: 'PATCH',
    body,
    orgId,
  })
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string, tagId: string }> },
) {
  const { orgId, tagId } = await params
  return proxySSORequest(request, `/api/v1/org/${orgId}/tags/${tagId}`, {
    method: 'DELETE',
    orgId,
  })
}
