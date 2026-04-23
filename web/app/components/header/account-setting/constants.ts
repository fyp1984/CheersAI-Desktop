export const ACCOUNT_SETTING_MODAL_ACTION = 'showSettings'

export const ACCOUNT_SETTING_TAB = {
  PROVIDER: 'provider',
  MEMBERS: 'members',
  BILLING: 'billing',
  TOKEN_BILLING: 'token-billing',
  DATA_SOURCE: 'data-source',
  API_BASED_EXTENSION: 'api-based-extension',
  CUSTOM: 'custom',
  DATA_SECURITY: 'data-security',
  GITEA_SETTINGS: 'gitea-settings',
  LANGUAGE: 'language',
  GITEA_SETTINGS: 'gitea-settings',
} as const

export type AccountSettingTab = typeof ACCOUNT_SETTING_TAB[keyof typeof ACCOUNT_SETTING_TAB]

export const DEFAULT_ACCOUNT_SETTING_TAB = ACCOUNT_SETTING_TAB.MEMBERS

export const isValidAccountSettingTab = (tab: string | null): tab is AccountSettingTab => {
  if (!tab)
    return false
  return Object.values(ACCOUNT_SETTING_TAB).includes(tab as AccountSettingTab)
}
