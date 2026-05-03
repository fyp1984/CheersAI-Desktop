import type { Tag } from '@/app/components/base/tag-management/constant'
import type { Member } from '@/models/common'
import { refreshAccessTokenOrRelogin } from './refresh-token'
import { fetchTagList } from './tag'

export const MEMBER_TAG_PAGE_SIZE = 20
const REQUEST_TIMEOUT = 5000
const REQUEST_RETRIES = 2
const REQUEST_RETRY_DELAY = 500

type RequestRetryOptions = {
  retries?: number
}

type RequestError = Error & {
  status?: number
}

type LooseRecord = Record<string, unknown>

type MemberStatus = Member['status']
type MemberRole = Member['role']

export type SSOOrganizationTag = {
  id: string
  name: string
  color?: string
  description?: string
  binding_count?: number
}

export type SSOOrganizationMember = Pick<Member, 'id' | 'name' | 'email' | 'avatar' | 'avatar_url' | 'created_at' | 'last_active_at' | 'last_login_at' | 'role' | 'status'> & {
  permissions: string[]
  tags: SSOOrganizationTag[]
}

export type SSOOrganizationMemberPage = {
  items: SSOOrganizationMember[]
  total: number
  page: number
  pageSize: number
}

export type UpsertOrganizationTagPayload = {
  name: string
  color?: string
  description?: string
}

type CachedSystemTags = {
  app: Tag[]
  knowledge: Tag[]
}

export type SSOUserProfileTagResponse = {
  userId: string
  tags: string
  tagNames: string[]
}

export type SSOUserIdentity = {
  ssoOwner?: string | null
  ssoUsername?: string | null
}

const ROLE_SET = new Set<MemberRole>(['owner', 'admin', 'editor', 'normal', 'dataset_operator'])
const STATUS_SET = new Set<MemberStatus>(['pending', 'active', 'banned', 'closed'])
let cachedSystemTagsPromise: Promise<CachedSystemTags> | null = null

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const normalizeString = (value: unknown) => (typeof value === 'string' ? value.trim() : '')

const normalizeStringList = (value: unknown) => {
  if (!Array.isArray(value))
    return []

  return [...new Set(value.map(item => normalizeString(item)).filter(Boolean))]
}

const asRecord = (value: unknown): LooseRecord => {
  if (value && typeof value === 'object')
    return value as LooseRecord

  return {}
}

const normalizeTag = (value: unknown): SSOOrganizationTag => {
  const record = asRecord(value)

  return {
    id: String(record.id || record.tagId || record.tag_id || ''),
    name: normalizeString(record.name || record.tagName || record.tag_name),
    color: normalizeString(record.color) || undefined,
    description: normalizeString(record.description) || undefined,
    binding_count: Number.isFinite(Number(record.binding_count)) ? Number(record.binding_count) : undefined,
  }
}

const normalizeTagList = (value: unknown) => {
  if (!Array.isArray(value))
    return []

  return value.map(normalizeTag).filter(tag => tag.id && tag.name)
}

const normalizeMember = (value: unknown): SSOOrganizationMember => {
  const record = asRecord(value)
  const role = normalizeString(record.role)
  const status = normalizeString(record.status)

  return {
    id: String(record.id || record.userId || record.user_id || ''),
    name: normalizeString(record.name || record.display_name || record.username),
    email: normalizeString(record.email),
    avatar: normalizeString(record.avatar),
    avatar_url: normalizeString(record.avatar_url || record.avatarUrl || record.avatar) || null,
    created_at: String(record.created_at || record.createdAt || ''),
    last_active_at: String(record.last_active_at || record.lastActiveAt || ''),
    last_login_at: String(record.last_login_at || record.lastLoginAt || ''),
    role: ROLE_SET.has(role as MemberRole) ? role as MemberRole : 'normal',
    status: STATUS_SET.has(status as MemberStatus) ? status as MemberStatus : 'active',
    permissions: normalizeStringList(record.permissions),
    tags: normalizeTagList(record.tags),
  }
}

const getErrorMessage = (payload: unknown, fallback: string) => {
  const record = asRecord(payload)
  const message = normalizeString(record.message || record.msg || record.error)
  return message || fallback
}

const parseJsonSafely = async (response: Response) => {
  try {
    return await response.json()
  }
  catch {
    return null
  }
}

const shouldRetry = (error: RequestError) => {
  if (error.name === 'AbortError')
    return true

  if (typeof error.status !== 'number')
    return true

  return error.status >= 500
}

const requestJSON = async <T>(
  url: string,
  init?: RequestInit,
  options?: RequestRetryOptions,
): Promise<T> => {
  const retries = options?.retries ?? 0

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)

    try {
      const response = await fetch(url, {
        ...init,
        credentials: 'include',
        headers: {
          Accept: 'application/json',
          ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
          ...init?.headers,
        },
        signal: controller.signal,
      })

      const payload = await parseJsonSafely(response)
      if (!response.ok) {
        const error = new Error(getErrorMessage(payload, '请求失败')) as RequestError
        error.status = response.status
        throw error
      }

      return payload as T
    }
    catch (error) {
      const normalizedError = error as RequestError
      if (attempt >= retries || !shouldRetry(normalizedError))
        throw normalizedError

      await sleep(REQUEST_RETRY_DELAY)
    }
    finally {
      clearTimeout(timeoutId)
    }
  }

  throw new Error('请求失败')
}

const unwrapTagList = (payload: unknown) => {
  const record = asRecord(payload)
  if (Array.isArray(payload))
    return payload
  if (Array.isArray(record.data))
    return record.data
  if (Array.isArray(record.items))
    return record.items
  return []
}

const unwrapMemberPage = (payload: unknown): SSOOrganizationMemberPage => {
  const record = asRecord(payload)
  const rawData = asRecord(record.data)
  const rawItems = Array.isArray(rawData?.items)
    ? rawData.items
    : Array.isArray(record.data)
      ? record.data
      : Array.isArray(record.items)
        ? record.items
        : []

  const total = Number(rawData.total ?? record.total ?? rawItems.length ?? 0)
  const page = Number(rawData.page ?? record.page ?? 1)
  const pageSize = Number(rawData.page_size ?? rawData.pageSize ?? record.page_size ?? record.pageSize ?? MEMBER_TAG_PAGE_SIZE)

  return {
    items: rawItems.map(normalizeMember).filter(member => member.id),
    total: Number.isFinite(total) ? total : rawItems.length,
    page: Number.isFinite(page) && page > 0 ? page : 1,
    pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : MEMBER_TAG_PAGE_SIZE,
  }
}

const buildMemberQuery = (params: { page: number, pageSize?: number, keyword?: string }) => {
  const query = new URLSearchParams()
  query.set('page', String(params.page))
  query.set('page_size', String(params.pageSize || MEMBER_TAG_PAGE_SIZE))
  if (params.keyword?.trim())
    query.set('keyword', params.keyword.trim())
  return query.toString()
}

const buildOrganizationTagsPath = (orgId: string) => `/oauth-api/org/${orgId}/tags/`
const buildOrganizationTagDetailPath = (orgId: string, tagId: string) => `/oauth-api/org/${orgId}/tags/${tagId}/`
const buildOrganizationUsersPath = (orgId: string, query?: string) => `/oauth-api/org/${orgId}/users/${query ? `?${query}` : ''}`
const buildOrganizationProfileTagPath = (orgId: string, userId: string) => `/oauth-api/org/${orgId}/users/${userId}/profile-tag/`
const buildOrganizationProfileTagRequestPath = (orgId: string, userId: string, identity?: SSOUserIdentity) => {
  const basePath = buildOrganizationProfileTagPath(orgId, userId)
  const searchParams = new URLSearchParams()
  const ssoOwner = normalizeString(identity?.ssoOwner)
  const ssoUsername = normalizeString(identity?.ssoUsername)

  if (ssoOwner)
    searchParams.set('ssoOwner', ssoOwner)
  if (ssoUsername)
    searchParams.set('ssoUsername', ssoUsername)

  const query = searchParams.toString()
  return query ? `${basePath}?${query}` : basePath
}

export const fetchOrganizationTags = async (orgId: string) => {
  const payload = await requestJSON<unknown>(buildOrganizationTagsPath(orgId))
  return unwrapTagList(payload).map(normalizeTag).filter(tag => tag.id && tag.name)
}

export const createOrganizationTag = async (orgId: string, payload: UpsertOrganizationTagPayload) => {
  await refreshAccessTokenOrRelogin(REQUEST_TIMEOUT)
  const response = await requestJSON<unknown>(buildOrganizationTagsPath(orgId), {
    method: 'POST',
    body: JSON.stringify(payload),
  }, { retries: REQUEST_RETRIES })

  return normalizeTag(asRecord(response).data || response)
}

export const updateOrganizationTag = async (orgId: string, tagId: string, payload: UpsertOrganizationTagPayload) => {
  await refreshAccessTokenOrRelogin(REQUEST_TIMEOUT)
  const response = await requestJSON<unknown>(buildOrganizationTagDetailPath(orgId, tagId), {
    method: 'PATCH',
    body: JSON.stringify(payload),
  }, { retries: REQUEST_RETRIES })

  return normalizeTag(asRecord(response).data || response)
}

export const deleteOrganizationTag = async (orgId: string, tagId: string) => {
  await refreshAccessTokenOrRelogin(REQUEST_TIMEOUT)
  await requestJSON(buildOrganizationTagDetailPath(orgId, tagId), {
    method: 'DELETE',
  }, { retries: REQUEST_RETRIES })
}

export const fetchOrganizationMembers = async (orgId: string, params: { page: number, pageSize?: number, keyword?: string }) => {
  const query = buildMemberQuery(params)
  const payload = await requestJSON<unknown>(buildOrganizationUsersPath(orgId, query))
  return unwrapMemberPage(payload)
}

export const fetchOrganizationMemberTags = async (orgId: string, userId: string, keyword: string) => {
  const response = await fetchOrganizationMembers(orgId, {
    page: 1,
    pageSize: MEMBER_TAG_PAGE_SIZE,
    keyword,
  })

  const matchedMember = response.items.find(item => item.id === userId)
  return matchedMember?.tags || []
}

export const fetchCachedSystemTags = async () => {
  if (!cachedSystemTagsPromise) {
    cachedSystemTagsPromise = Promise.all([
      fetchTagList('app'),
      fetchTagList('knowledge'),
    ]).then(([appTags, knowledgeTags]) => ({
      app: appTags,
      knowledge: knowledgeTags,
    })).catch((error) => {
      cachedSystemTagsPromise = null
      throw error
    })
  }

  return cachedSystemTagsPromise
}

export const clearCachedSystemTags = () => {
  cachedSystemTagsPromise = null
}

export const fetchSSOUserProfileTag = async (orgId: string, userId: string, identity?: SSOUserIdentity) => {
  const payload = await requestJSON<SSOUserProfileTagResponse>(buildOrganizationProfileTagRequestPath(orgId, userId, identity))
  return {
    userId: normalizeString(payload?.userId || userId) || userId,
    tags: normalizeString(payload?.tags),
    tagNames: normalizeStringList(payload?.tagNames),
  } satisfies SSOUserProfileTagResponse
}

export const updateSSOUserProfileTag = async (orgId: string, userId: string, tags: string, identity?: SSOUserIdentity) => {
  await refreshAccessTokenOrRelogin(REQUEST_TIMEOUT)
  await requestJSON(buildOrganizationProfileTagPath(orgId, userId), {
    method: 'PUT',
    body: JSON.stringify({
      userId,
      tags,
      ssoOwner: normalizeString(identity?.ssoOwner),
      ssoUsername: normalizeString(identity?.ssoUsername),
    }),
  }, { retries: REQUEST_RETRIES })
}
