export type SignInRuntimeConfig = {
  enableSplash: boolean
  animationDuration: number
  logoUrl: string
}

const DEFAULT_DURATION = 1500

const normalizeLogoUrl = (value?: string | null) => {
  const trimmed = value?.trim()
  if (!trimmed)
    return `${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI-Logo.png`
  return trimmed
}

const normalizeBoolean = (value: unknown, fallback: boolean) => {
  if (typeof value === 'boolean')
    return value
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'on'].includes(normalized))
      return true
    if (['false', '0', 'no', 'off'].includes(normalized))
      return false
  }
  return fallback
}

const normalizeDuration = (value: unknown, fallback: number) => {
  if (typeof value === 'number' && Number.isFinite(value))
    return Math.min(1600, Math.max(600, value))
  if (typeof value === 'string') {
    const parsed = Number.parseInt(value, 10)
    if (Number.isFinite(parsed))
      return Math.min(1600, Math.max(600, parsed))
  }
  return fallback
}

const getBodyAttribute = (name: string) => {
  if (typeof document === 'undefined')
    return undefined
  return document.body?.dataset?.[name]
}

export const getDefaultSignInConfig = (): SignInRuntimeConfig => ({
  enableSplash: true,
  animationDuration: DEFAULT_DURATION,
  logoUrl: normalizeLogoUrl(),
})

export const getEnvSignInConfig = (): SignInRuntimeConfig => ({
  enableSplash: normalizeBoolean(
    getBodyAttribute('signinEnableSplash') ?? process.env.NEXT_PUBLIC_SIGNIN_ENABLE_SPLASH,
    true,
  ),
  animationDuration: normalizeDuration(
    getBodyAttribute('signinAnimationDuration') ?? process.env.NEXT_PUBLIC_SIGNIN_ANIMATION_DURATION,
    DEFAULT_DURATION,
  ),
  logoUrl: normalizeLogoUrl(getBodyAttribute('signinLogoUrl') ?? process.env.NEXT_PUBLIC_SIGNIN_LOGO_URL),
})

type SignInConfigPayload = Partial<{
  enableSplash: boolean | string
  animationDuration: number | string
  logoUrl: string
}>

export const mergeSignInConfig = (
  baseConfig: SignInRuntimeConfig,
  payload?: SignInConfigPayload | null,
) => ({
  enableSplash: normalizeBoolean(payload?.enableSplash, baseConfig.enableSplash),
  animationDuration: normalizeDuration(payload?.animationDuration, baseConfig.animationDuration),
  logoUrl: normalizeLogoUrl(payload?.logoUrl || baseConfig.logoUrl),
})

export const loadSignInConfig = async () => {
  const envConfig = getEnvSignInConfig()

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/config.json`, {
      cache: 'no-store',
    })

    if (!response.ok)
      return envConfig

    const payload = await response.json() as SignInConfigPayload
    const fileConfig = mergeSignInConfig(getDefaultSignInConfig(), payload)
    return mergeSignInConfig(fileConfig, envConfig)
  }
  catch {
    return envConfig
  }
}
