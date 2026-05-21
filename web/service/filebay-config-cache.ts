'use client'

import Cookies from 'js-cookie'
import { API_PREFIX, CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'

export type FileBayCachedConfig = {
  gitea_url: string
  gitea_owner: string
  gitea_repo: string
  gitea_path?: string
  gitea_token: string
  is_enterprise_managed?: boolean
}

type FileBayConfigCachePayload = {
  version: 1
  savedAt: number
  config: FileBayCachedConfig
}

type FetchFileBayConfigOptions = {
  endpoint?: 'config' | 'download' | 'enterprise'
}

const FILEBAY_CONFIG_CACHE_KEY = 'cheersai:filebay-config:v1'
const FILEBAY_CONFIG_CACHE_EVENT = 'cheersai:filebay-config-updated'
const FILEBAY_CONFIG_CACHE_TTL = 7 * 24 * 60 * 60 * 1000

const isBrowser = () => typeof window !== 'undefined'

const normalizeConfig = (value: Partial<FileBayCachedConfig> | null | undefined): FileBayCachedConfig | null => {
  if (!value)
    return null

  const config = {
    gitea_url: String(value.gitea_url || '').trim(),
    gitea_owner: String(value.gitea_owner || '').trim(),
    gitea_repo: String(value.gitea_repo || '').trim(),
    gitea_path: String(value.gitea_path || '').trim(),
    gitea_token: String(value.gitea_token || '').trim(),
    is_enterprise_managed: Boolean(value.is_enterprise_managed),
  }

  if (!config.gitea_url && !config.gitea_owner && !config.gitea_repo && !config.gitea_token)
    return null

  return config
}

export const getCachedFileBayConfig = () => {
  if (!isBrowser())
    return null

  try {
    const rawValue = window.localStorage.getItem(FILEBAY_CONFIG_CACHE_KEY)
    if (!rawValue)
      return null

    const payload = JSON.parse(rawValue) as Partial<FileBayConfigCachePayload>
    if (payload.version !== 1 || !payload.config)
      return null

    if (typeof payload.savedAt === 'number' && Date.now() - payload.savedAt > FILEBAY_CONFIG_CACHE_TTL)
      return null

    return normalizeConfig(payload.config)
  }
  catch {
    return null
  }
}

export const setCachedFileBayConfig = (config: Partial<FileBayCachedConfig>) => {
  if (!isBrowser())
    return

  const normalizedConfig = normalizeConfig(config)
  if (!normalizedConfig)
    return

  try {
    const payload: FileBayConfigCachePayload = {
      version: 1,
      savedAt: Date.now(),
      config: normalizedConfig,
    }
    window.localStorage.setItem(FILEBAY_CONFIG_CACHE_KEY, JSON.stringify(payload))
    window.dispatchEvent(new CustomEvent(FILEBAY_CONFIG_CACHE_EVENT, { detail: normalizedConfig }))
  }
  catch {
    // localStorage may be unavailable in restricted browser modes.
  }
}

export const clearCachedFileBayConfig = () => {
  if (!isBrowser())
    return

  try {
    window.localStorage.removeItem(FILEBAY_CONFIG_CACHE_KEY)
    window.dispatchEvent(new CustomEvent(FILEBAY_CONFIG_CACHE_EVENT))
  }
  catch {
    // best-effort cache cleanup
  }
}

export const fetchFileBayConfig = async (options?: FetchFileBayConfigOptions) => {
  const endpoint = options?.endpoint || 'download'
  const path = endpoint === 'enterprise'
    ? '/gitea/config/enterprise'
    : endpoint === 'config'
      ? '/gitea/config'
      : '/gitea/config/download'

  const response = await fetch(`${API_PREFIX}${path}`, {
    credentials: 'include',
    headers: {
      [CSRF_HEADER_NAME]: Cookies.get(CSRF_COOKIE_NAME()) || '',
    },
  })

  if (!response.ok)
    throw new Error(`Failed to fetch FileBay config: ${response.status}`)

  const data = await response.json() as Partial<FileBayCachedConfig>
  const normalizedConfig = normalizeConfig(data)
  if (!normalizedConfig)
    throw new Error('FileBay config is empty')

  setCachedFileBayConfig(normalizedConfig)
  return normalizedConfig
}

export const getCachedFileBayConfigEventName = () => FILEBAY_CONFIG_CACHE_EVENT
