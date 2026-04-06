import { get, post } from './base'

export const getUserSAMLSSOUrl = (invite_token?: string) => {
  const url = invite_token ? `/enterprise/sso/saml/login?invite_token=${invite_token}` : '/enterprise/sso/saml/login'
  return get<{ url: string }>(url)
}

export const getUserOIDCSSOUrl = (invite_token?: string) => {
  const url = invite_token ? `/enterprise/sso/oidc/login?invite_token=${invite_token}` : '/enterprise/sso/oidc/login'
  return get<{ url: string, state: string }>(url)
}

export const getUserOAuth2SSOUrl = (invite_token?: string) => {
  const url = invite_token ? `/enterprise/sso/oauth2/login?invite_token=${invite_token}` : '/enterprise/sso/oauth2/login'
  return get<{ url: string, state: string }>(url)
}

export type DesktopSSOLoginUrlParams = {
  clientId: string
  redirectUri: string
  state: string
  protocol?: string
}

export const getDesktopSSOLoginUrl = (params: DesktopSSOLoginUrlParams) => {
  const { clientId, redirectUri, state, protocol = 'oauth' } = params
  const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL || 'http://localhost:8000'
  const normalizedProtocol = protocol === 'oauth2' ? 'oauth' : protocol
  const authUrl = new URL(`/login/${normalizedProtocol}/authorize`, ssoBaseUrl)
  authUrl.searchParams.set('client_id', clientId)
  authUrl.searchParams.set('redirect_uri', redirectUri)
  authUrl.searchParams.set('state', state)
  authUrl.searchParams.set('response_type', 'code')
  authUrl.searchParams.set('scope', 'openid profile email')
  return authUrl.toString()
}

export type ExchangeTokenParams = {
  code: string
  state: string
  redirectUri: string
}

export type SSOUserInfo = {
  sub: string
  email: string
  name: string
  preferred_username?: string
  role?: string
  type?: string
  groups?: string[]
  roles?: string[]
  permissions?: string[]
  iss?: string
  aud?: string
}

export const exchangeSSOToken = async (params: ExchangeTokenParams) => {
  // 1. Exchange OAuth code for SSO access_token
  const response = await fetch('/api/auth/sso/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    console.error('[SSO] Token exchange failed:', errorData)
    throw new Error(errorData.error || 'Token exchange failed')
  }

  // 2. Fetch User Info from SSO using the token
  const userInfoResponse = await fetch('/api/auth/sso/userinfo/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!userInfoResponse.ok) {
    console.error('[SSO] Failed to fetch user info')
    throw new Error('Failed to fetch user info from SSO')
  }

  const userInfo = await userInfoResponse.json() as SSOUserInfo
  const result = await post('/auth/desktop-sso/login', {
    body: {
      sub: userInfo.sub,
      email: userInfo.email,
      name: userInfo.name,
      preferred_username: userInfo.preferred_username,
      role: userInfo.role || userInfo.type,
      type: userInfo.type,
      groups: userInfo.groups || [],
      roles: userInfo.roles || [],
      permissions: userInfo.permissions || [],
      iss: userInfo.iss,
      aud: userInfo.aud,
    },
  })

  return result
}

export const getSSOUserInfo = async () => {
  const response = await fetch('/api/auth/sso/userinfo/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || 'Failed to fetch user info')
  }
  return response.json() as Promise<SSOUserInfo>
}
