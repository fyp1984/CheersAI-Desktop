import type { NextRequest } from 'next/server'
import { Buffer } from 'node:buffer'
import { NextResponse } from 'next/server'
import { ensureWorkspaceTagManagementAccess, getResponsePayload, getSSOConfig } from '../../../../shared'

type JsonObject = Record<string, unknown>

const MAX_TAG_STRING_LENGTH = 500
const SSO_TAG_SPLIT_PATTERN = /[，、；;|,]+/
const DEFAULT_SSO_OWNER = process.env.SSO_PROVISION_OWNER?.trim() || 'CheersAI'
const SSO_REQUEST_TIMEOUT = 5000
const SSO_REQUEST_RETRIES = 2
const SSO_REQUEST_RETRY_DELAY = 300

const buildBasicAuthHeader = (clientId: string, clientSecret: string) => {
  return `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`
}

const isSuccessPayload = (payload: JsonObject) => {
  const status = String(payload?.status || '').toLowerCase()
  return !status || status === 'ok'
}

const parseUserTagNames = (rawValue: unknown) => {
  if (typeof rawValue !== 'string')
    return []

  const normalizedNames: string[] = []
  const seenNames = new Set<string>()

  rawValue.split(SSO_TAG_SPLIT_PATTERN).forEach((value) => {
    const normalizedValue = value.trim()
    if (!normalizedValue || seenNames.has(normalizedValue))
      return

    normalizedNames.push(normalizedValue)
    seenNames.add(normalizedValue)
  })

  return normalizedNames
}

const normalizeString = (value: unknown) => (typeof value === 'string' ? value.trim() : '')

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const shouldRetrySSORequest = (response: Response) => response.status >= 500

const fetchSSOWithRetry = async (url: string, init: RequestInit) => {
  let lastError: unknown

  for (let attempt = 0; attempt <= SSO_REQUEST_RETRIES; attempt += 1) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), SSO_REQUEST_TIMEOUT)

    try {
      const response = await fetch(url, {
        ...init,
        signal: controller.signal,
        cache: 'no-store',
      })

      if (!shouldRetrySSORequest(response) || attempt >= SSO_REQUEST_RETRIES)
        return response
    }
    catch (error) {
      lastError = error
      if (attempt >= SSO_REQUEST_RETRIES)
        throw error
    }
    finally {
      clearTimeout(timeoutId)
    }

    await sleep(SSO_REQUEST_RETRY_DELAY)
  }

  throw lastError instanceof Error ? lastError : new Error('Failed to fetch SSO user.')
}

const buildUnavailableProfileTagResponse = (userId: string) => {
  return NextResponse.json({
    userId,
    tags: '',
    tagNames: [],
    unavailable: true,
  })
}

const buildUserLookupUrl = (ssoBaseUrl: string, nextUserId: string, ssoOwner?: string, ssoUsername?: string) => {
  const getUserUrl = new URL('/api/get-user', ssoBaseUrl)
  const normalizedOwner = normalizeString(ssoOwner) || DEFAULT_SSO_OWNER
  const normalizedUsername = normalizeString(ssoUsername)

  if (normalizedUsername) {
    getUserUrl.searchParams.set('id', `${normalizedOwner}/${normalizedUsername}`)
    return getUserUrl
  }

  getUserUrl.searchParams.set('userId', nextUserId)
  return getUserUrl
}

const buildUserLookupResponse = async (nextUserId: string, ssoOwner?: string, ssoUsername?: string, allowDegraded = false) => {
  const { ssoBaseUrl, clientId } = getSSOConfig()
  const clientSecret = process.env.DESKTOP_SSO_CLIENT_SECRET || ''
  if (!ssoBaseUrl || !clientId || !clientSecret)
    return NextResponse.json({ message: 'SSO tag service is not configured.' }, { status: 500 })

  const authHeader = buildBasicAuthHeader(clientId, clientSecret)
  const getUserUrl = buildUserLookupUrl(ssoBaseUrl, nextUserId, ssoOwner, ssoUsername)
  let getUserResponse: Response
  try {
    getUserResponse = await fetchSSOWithRetry(getUserUrl.toString(), {
      headers: {
        Accept: 'application/json',
        Authorization: authHeader,
      },
    })
  }
  catch (error) {
    if (allowDegraded) {
      console.warn('SSO profile tag fetch degraded:', error)
      return buildUnavailableProfileTagResponse(nextUserId)
    }

    throw error
  }

  const getUserPayload = await getResponsePayload(getUserResponse)
  const ssoUser = getUserPayload.data
  if (allowDegraded && !getUserResponse.ok && getUserResponse.status >= 500) {
    console.warn('SSO profile tag fetch degraded:', getUserResponse.status, getUserPayload)
    return buildUnavailableProfileTagResponse(nextUserId)
  }

  if (!getUserResponse.ok || !isSuccessPayload(getUserPayload) || !ssoUser || typeof ssoUser !== 'object') {
    return NextResponse.json(
      { message: String(getUserPayload?.msg || getUserPayload?.message || 'Failed to fetch SSO user.') },
      { status: getUserResponse.status || 400 },
    )
  }

  return {
    authHeader,
    ssoUser: ssoUser as JsonObject,
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string, userId: string }> },
) {
  try {
    const { orgId, userId } = await params
    const deniedResponse = await ensureWorkspaceTagManagementAccess(request, orgId)
    if (deniedResponse)
      return deniedResponse

    const ssoOwner = request.nextUrl.searchParams.get('ssoOwner')
    const ssoUsername = request.nextUrl.searchParams.get('ssoUsername')
    const lookupResult = await buildUserLookupResponse(userId, ssoOwner || undefined, ssoUsername || undefined, true)
    if (lookupResult instanceof NextResponse)
      return lookupResult

    const rawTag = String(lookupResult.ssoUser.tag || '').trim()
    return NextResponse.json({
      userId,
      tags: rawTag,
      tagNames: parseUserTagNames(rawTag),
    })
  }
  catch (error) {
    console.error('SSO profile tag fetch error:', error)
    return NextResponse.json({ message: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string, userId: string }> },
) {
  try {
    const { orgId, userId } = await params
    const deniedResponse = await ensureWorkspaceTagManagementAccess(request, orgId)
    if (deniedResponse)
      return deniedResponse

    const body = await request.json() as {
      userId?: string
      tags?: string
      ssoOwner?: string
      ssoUsername?: string
    }
    const nextUserId = body.userId?.trim() || userId
    const nextTags = typeof body.tags === 'string' ? body.tags.trim() : ''
    const ssoOwner = normalizeString(body.ssoOwner)
    const ssoUsername = normalizeString(body.ssoUsername)

    if (!nextUserId)
      return NextResponse.json({ message: 'userId is required.' }, { status: 400 })

    if (nextTags.length > MAX_TAG_STRING_LENGTH)
      return NextResponse.json({ message: '标签总长度超出限制，请减少选择项' }, { status: 400 })

    const lookupResult = await buildUserLookupResponse(nextUserId, ssoOwner || undefined, ssoUsername || undefined)
    if (lookupResult instanceof NextResponse)
      return lookupResult

    const previousTags = String(lookupResult.ssoUser.tag || '').trim()
    const mutableSSOUser: JsonObject = { ...lookupResult.ssoUser, tag: nextTags }
    const owner = String(mutableSSOUser.owner || '').trim()
    const name = String(mutableSSOUser.name || '').trim()
    if (!owner || !name)
      return NextResponse.json({ message: 'Unable to resolve target SSO user.' }, { status: 400 })

    const { ssoBaseUrl } = getSSOConfig()
    const updateUserUrl = new URL('/api/update-user', ssoBaseUrl)
    updateUserUrl.searchParams.set('id', `${owner}/${name}`)
    updateUserUrl.searchParams.set('columns', 'tag')
    const updateUserResponse = await fetch(updateUserUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': lookupResult.authHeader,
      },
      body: JSON.stringify(mutableSSOUser),
      cache: 'no-store',
    })

    const updateUserPayload = await getResponsePayload(updateUserResponse)
    if (!updateUserResponse.ok || !isSuccessPayload(updateUserPayload))
      return NextResponse.json({ message: String(updateUserPayload?.msg || updateUserPayload?.message || 'Failed to update SSO user tags.') }, { status: updateUserResponse.status || 400 })

    const previousTagNames = parseUserTagNames(previousTags)
    const nextTagNames = parseUserTagNames(nextTags)
    const previousTagSet = new Set(previousTagNames)
    const nextTagSet = new Set(nextTagNames)
    console.warn('[member-tag-audit]', JSON.stringify({
      orgId,
      userId: nextUserId,
      owner,
      name,
      previousTags,
      nextTags,
      addedTags: nextTagNames.filter(tag => !previousTagSet.has(tag)),
      removedTags: previousTagNames.filter(tag => !nextTagSet.has(tag)),
      changedAt: new Date().toISOString(),
    }))

    return NextResponse.json({ success: true })
  }
  catch (error) {
    console.error('SSO profile tag update error:', error)
    return NextResponse.json({ message: 'Internal server error' }, { status: 500 })
  }
}
