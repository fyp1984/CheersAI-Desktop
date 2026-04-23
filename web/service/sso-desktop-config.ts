import { DatasetAttr } from '@/types/feature'

const readRuntimeAttr = (attr: DatasetAttr) => {
  if (typeof document === 'undefined')
    return ''
  return document.body?.getAttribute(attr) || ''
}

const readRuntimeValue = (envValue: string | undefined, attr: DatasetAttr, defaultValue = '') => {
  const normalizedEnvValue = envValue?.trim()
  if (normalizedEnvValue)
    return normalizedEnvValue

  const attrValue = readRuntimeAttr(attr).trim()
  if (attrValue)
    return attrValue

  return defaultValue
}

export const getDesktopSSOLoginBaseUrl = () => {
  return readRuntimeValue(
    process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL,
    DatasetAttr.DATA_PUBLIC_DESKTOP_SSO_LOGIN_URL,
  )
}

export const getDesktopSSOClientId = () => {
  return readRuntimeValue(
    process.env.NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID,
    DatasetAttr.DATA_PUBLIC_DESKTOP_SSO_CLIENT_ID,
  )
}

export const getDesktopSSOProtocol = () => {
  return readRuntimeValue(
    process.env.NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL,
    DatasetAttr.DATA_PUBLIC_DESKTOP_SSO_PROTOCOL,
    'oauth',
  ).replace('oauth2', 'oauth')
}

export const isDesktopSSOEnabledRuntime = () => {
  const enabled = readRuntimeValue(
    process.env.NEXT_PUBLIC_DESKTOP_SSO_ENABLED,
    DatasetAttr.DATA_PUBLIC_DESKTOP_SSO_ENABLED,
  ).toLowerCase()

  return enabled === 'true' || enabled === '1'
}
