import Cookies from 'js-cookie'
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'
import type { Tag } from '@/app/components/base/tag-management/constant'
import { del, get, patch, post } from './base'
import { refreshAccessTokenOrRelogin } from './refresh-token'

const getTagMutationHeaders = () => ({
  [CSRF_HEADER_NAME]: Cookies.get(CSRF_COOKIE_NAME()) || '',
})
const TAG_MUTATION_TIMEOUT = 5000

export const fetchTagList = (type: string) => {
  return get<Tag[]>('/tags', { params: { type } })
}

export const createTag = async (name: string, type: string) => {
  await refreshAccessTokenOrRelogin(TAG_MUTATION_TIMEOUT)
  return post<Tag>('/tags', {
    headers: getTagMutationHeaders(),
    body: {
      name,
      type,
    },
  })
}

export const updateTag = async (tagID: string, name: string, type: string) => {
  await refreshAccessTokenOrRelogin(TAG_MUTATION_TIMEOUT)
  return patch(`/tags/${tagID}`, {
    headers: getTagMutationHeaders(),
    body: {
      name,
      type,
    },
  })
}

export const deleteTag = async (tagID: string) => {
  await refreshAccessTokenOrRelogin(TAG_MUTATION_TIMEOUT)
  return del(`/tags/${tagID}`, {
    headers: getTagMutationHeaders(),
  })
}

export const bindTag = async (tagIDList: string[], targetID: string, type: string) => {
  await refreshAccessTokenOrRelogin(TAG_MUTATION_TIMEOUT)
  return post('/tag-bindings/create', {
    headers: getTagMutationHeaders(),
    body: {
      tag_ids: tagIDList,
      target_id: targetID,
      type,
    },
  })
}

export const unBindTag = async (tagID: string, targetID: string, type: string) => {
  await refreshAccessTokenOrRelogin(TAG_MUTATION_TIMEOUT)
  return post('/tag-bindings/remove', {
    headers: getTagMutationHeaders(),
    body: {
      tag_id: tagID,
      target_id: targetID,
      type,
    },
  })
}
