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

export interface DesktopSSOLoginUrlParams {
  clientId: string
  redirectUri: string
  state: string
  protocol?: string
}

export const getDesktopSSOLoginUrl = (params: DesktopSSOLoginUrlParams) => {
  const { clientId, redirectUri, state, protocol = 'oauth2' } = params
  const ssoBaseUrl = process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL || 'http://localhost:8000'
  
  const authUrl = new URL(`/login/${protocol}/authorize`, ssoBaseUrl)
  authUrl.searchParams.set('client_id', clientId)
  authUrl.searchParams.set('redirect_uri', redirectUri)
  authUrl.searchParams.set('state', state)
  authUrl.searchParams.set('response_type', 'code')
  
  return authUrl.toString()
}

export interface ExchangeTokenParams {
  code: string
  state: string
  redirectUri: string
}

export const exchangeSSOToken = (params: ExchangeTokenParams) => {
  return post<{ access_token: string, refresh_token: string }>('/auth/sso/token', {
    body: params,
  })
}

export const getSSOUserInfo = () => {
  return post<{ id: string, email: string, name: string }>('/auth/sso/userinfo')
}
