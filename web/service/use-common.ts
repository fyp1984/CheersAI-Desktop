import type { FileTypesRes } from './datasets'
import type {
  Model,
  ModelParameterRule,
  ModelProvider,
  ModelTypeEnum,
} from '@/app/components/header/account-setting/model-provider-page/declarations'
import type {
  AccountIntegrate,
  ApiBasedExtension,
  CodeBasedExtension,
  CommonResponse,
  DataSourceNotion,
  FileUploadConfigResponse,
  ICurrentWorkspace,
  IWorkspace,
  LangGeniusVersionResponse,
  Member,
  PluginProvider,
  StructuredOutputRulesRequestBody,
  StructuredOutputRulesResponse,
  UserProfileResponse,
} from '@/models/common'
import type { RETRIEVE_METHOD } from '@/types/app'
import { useMutation, useQuery } from '@tanstack/react-query'
import { hasModelProviderReadWorkspaceCapability } from '@/utils/workspace-capabilities'
import { get, post } from './base'
import { useInvalid } from './use-base'

const NAME_SPACE = 'common'
export type TokenBillingScope = 'workspace' | 'self' | 'system'

export const commonQueryKeys = {
  fileUploadConfig: [NAME_SPACE, 'file-upload-config'] as const,
  userProfile: [NAME_SPACE, 'user-profile'] as const,
  currentWorkspace: [NAME_SPACE, 'current-workspace'] as const,
  workspaces: [NAME_SPACE, 'workspaces'] as const,
  members: [NAME_SPACE, 'members'] as const,
  filePreview: (fileID: string) => [NAME_SPACE, 'file-preview', fileID] as const,
  schemaDefinitions: [NAME_SPACE, 'schema-type-definitions'] as const,
  isLogin: [NAME_SPACE, 'is-login'] as const,
  modelProviders: (workspaceId?: string, userId?: string) =>
    [NAME_SPACE, 'model-providers', workspaceId ?? '', userId ?? ''] as const,
  teamModelConfigs: (workspaceId?: string, userId?: string) =>
    [NAME_SPACE, 'team-model-configs', workspaceId ?? '', userId ?? ''] as const,
  modelList: (type: ModelTypeEnum, workspaceId?: string, userId?: string) =>
    [NAME_SPACE, 'model-list', type, workspaceId ?? '', userId ?? ''] as const,
  defaultModel: (type: ModelTypeEnum, workspaceId?: string, userId?: string) =>
    [NAME_SPACE, 'default-model', type, workspaceId ?? '', userId ?? ''] as const,
  retrievalMethods: [NAME_SPACE, 'support-retrieval-methods'] as const,
  accountIntegrates: [NAME_SPACE, 'account-integrates'] as const,
  pluginProviders: [NAME_SPACE, 'plugin-providers'] as const,
  notionConnection: [NAME_SPACE, 'notion-connection'] as const,
  apiBasedExtensions: [NAME_SPACE, 'api-based-extensions'] as const,
  codeBasedExtensions: (module?: string) => [NAME_SPACE, 'code-based-extensions', module] as const,
  invitationCheck: (params?: { workspace_id?: string, email?: string, token?: string }) => [
    NAME_SPACE,
    'invitation-check',
    params?.workspace_id ?? '',
    params?.email ?? '',
    params?.token ?? '',
  ] as const,
  notionBinding: (code?: string | null) => [NAME_SPACE, 'notion-binding', code] as const,
  modelParameterRules: (provider?: string, model?: string) => [NAME_SPACE, 'model-parameter-rules', provider, model] as const,
  langGeniusVersion: (currentVersion?: string | null) => [NAME_SPACE, 'langgenius-version', currentVersion] as const,
  forgotPasswordValidity: (token?: string | null) => [NAME_SPACE, 'forgot-password-validity', token] as const,
  dataSourceIntegrates: [NAME_SPACE, 'data-source-integrates'] as const,
  tokenBillingUsage: (scope: TokenBillingScope) => [NAME_SPACE, 'token-billing-usage', scope] as const,
}

export const useFileUploadConfig = () => {
  return useQuery<FileUploadConfigResponse>({
    queryKey: commonQueryKeys.fileUploadConfig,
    queryFn: () => get<FileUploadConfigResponse>('/files/upload'),
  })
}

type UserProfileWithMeta = {
  profile: UserProfileResponse
  meta: {
    currentVersion: string | null
    currentEnv: string | null
  }
}

export const useUserProfile = () => {
  return useQuery<UserProfileWithMeta>({
    queryKey: commonQueryKeys.userProfile,
    queryFn: async () => {
      const response = await get<Response>('/account/profile', {}, { needAllResponseContent: true }) as Response
      const profile = await response.clone().json() as UserProfileResponse
      return {
        profile,
        meta: {
          currentVersion: response.headers.get('x-version'),
          currentEnv: response.headers.get('x-env'),
        },
      }
    },
    staleTime: 0,
    gcTime: 0,
    retry: false,
  })
}

export const useLangGeniusVersion = (currentVersion?: string | null, enabled?: boolean) => {
  return useQuery<LangGeniusVersionResponse>({
    queryKey: commonQueryKeys.langGeniusVersion(currentVersion || undefined),
    queryFn: () => get<LangGeniusVersionResponse>('/version', { params: { current_version: currentVersion } }),
    enabled: !!currentVersion && (enabled ?? true),
  })
}

export const useCurrentWorkspace = () => {
  return useQuery<ICurrentWorkspace>({
    queryKey: commonQueryKeys.currentWorkspace,
    queryFn: () => post<ICurrentWorkspace>('/workspaces/current', { body: {} }),
    retry: false,
  })
}

export const useWorkspaces = () => {
  return useQuery<{ workspaces: IWorkspace[] }>({
    queryKey: commonQueryKeys.workspaces,
    queryFn: () => get<{ workspaces: IWorkspace[] }>('/workspaces'),
  })
}

export const useGenerateStructuredOutputRules = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'generate-structured-output-rules'],
    mutationFn: (body: StructuredOutputRulesRequestBody) => {
      return post<StructuredOutputRulesResponse>(
        '/rule-structured-output-generate',
        { body },
      )
    },
  })
}

export type MailSendResponse = { data: string, result: string }
export const useSendMail = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'mail-send'],
    mutationFn: (body: { email: string, language: string }) => {
      return post<MailSendResponse>('/email-register/send-email', { body })
    },
  })
}

export type MailValidityResponse = { is_valid: boolean, token: string }

export const useMailValidity = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'mail-validity'],
    mutationFn: (body: { email: string, code: string, token: string }) => {
      return post<MailValidityResponse>('/email-register/validity', { body })
    },
  })
}

export type MailRegisterResponse = { result: string, data: {} }

export const useMailRegister = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'mail-register'],
    mutationFn: (body: { token: string, new_password: string, password_confirm: string, invite_code?: string }) => {
      return post<MailRegisterResponse>('/email-register', { body })
    },
  })
}

export type AccountInviteCode = {
  id: string
  code: string
  status: 'unused' | 'used'
  used_at: number | null
  used_by_account_id: string | null
}

export type AccountInviteCodesResponse = {
  limit: number
  data: AccountInviteCode[]
}

export const useAccountInviteCodes = () => {
  return useQuery<AccountInviteCodesResponse>({
    queryKey: [NAME_SPACE, 'account-invite-codes'],
    queryFn: () => get<AccountInviteCodesResponse>('/account/invite-codes'),
  })
}

export type AccountPointReward = {
  id: string
  name: string
  description: string
  points: number
  benefit_type: 'token' | 'service'
  benefit_amount: number
}

export type AccountPointTransaction = {
  id: string
  points: number
  remaining_points: number
  expires_at: number | null
  type: 'earn' | 'redeem' | 'expire'
  source: string
  description: string
  created_at: number | null
}

export type AccountPointRedemption = {
  id: string
  reward_id: string
  reward_name: string
  points: number
  status: string
  created_at: number | null
}

export type AccountPointCalendarTransaction = {
  id: string
  points: number
  type: 'earn' | 'redeem' | 'expire'
  source: string
  description: string
  created_at: number | null
}

export type AccountPointCalendarDay = {
  date: string
  day: number
  is_today: boolean
  is_checked_in: boolean
  earned_points: number
  spent_points: number
  expired_points: number
  net_points: number
  transactions: AccountPointCalendarTransaction[]
}

export type AccountPointsResponse = {
  balance: number
  invite_reward_points: number
  check_in: {
    checked_today: boolean
    today_points: number
    daily_points: number
    weekly_bonus_points: number
    streak_days: number
    monthly_check_in_points: number
    monthly_check_in_cap: number
    next_bonus_in_days: number
    valid_days: number
  }
  expiration: {
    expiring_points_this_month: number
    nearest_expiration_at: number | null
  }
  calendar: {
    year: number
    month: number
    month_start_weekday: number
    today: string
    days: AccountPointCalendarDay[]
  }
  rewards: AccountPointReward[]
  transactions: AccountPointTransaction[]
  redemptions: AccountPointRedemption[]
}

export const useAccountPoints = () => {
  return useQuery<AccountPointsResponse>({
    queryKey: [NAME_SPACE, 'account-points'],
    queryFn: () => get<AccountPointsResponse>('/account/points'),
  })
}

export const useRedeemAccountPoints = () => {
  const invalidate = useInvalid([NAME_SPACE, 'account-points'])
  return useMutation({
    mutationKey: [NAME_SPACE, 'account-points-redeem'],
    mutationFn: (body: { reward_id: string }) => post<{ result: string }>('/account/points/redeem', { body }),
    onSuccess: invalidate,
  })
}

export const useCheckInAccountPoints = () => {
  const invalidate = useInvalid([NAME_SPACE, 'account-points'])
  return useMutation({
    mutationKey: [NAME_SPACE, 'account-points-check-in'],
    mutationFn: () => post<AccountPointsResponse>('/account/points/check-in'),
    onSuccess: invalidate,
  })
}

export const useFileSupportTypes = () => {
  return useQuery<FileTypesRes>({
    queryKey: [NAME_SPACE, 'file-types'],
    queryFn: () => get<FileTypesRes>('/files/support-type'),
  })
}

type MemberResponse = {
  accounts: Member[] | null
}

export const useMembers = () => {
  return useQuery<MemberResponse>({
    queryKey: commonQueryKeys.members,
    queryFn: () => get<MemberResponse>('/workspaces/current/members', { params: {} }),
  })
}

type FilePreviewResponse = {
  content: string
}

export const useFilePreview = (fileID: string) => {
  return useQuery<FilePreviewResponse>({
    queryKey: commonQueryKeys.filePreview(fileID),
    queryFn: () => get<FilePreviewResponse>(`/files/${fileID}/preview`),
    enabled: !!fileID,
  })
}

export type SchemaTypeDefinition = {
  name: string
  schema: {
    properties: Record<string, any>
  }
}

export const useSchemaTypeDefinitions = () => {
  return useQuery<SchemaTypeDefinition[]>({
    queryKey: commonQueryKeys.schemaDefinitions,
    queryFn: () => get<SchemaTypeDefinition[]>('/spec/schema-definitions'),
  })
}

type isLogin = {
  logged_in: boolean
}

export const useIsLogin = () => {
  return useQuery<isLogin>({
    queryKey: commonQueryKeys.isLogin,
    staleTime: 0,
    gcTime: 0,
    retry: false, // Don't retry on error to avoid loops
    queryFn: async (): Promise<isLogin> => {
      try {
        const response = await globalThis.fetch('/internal/auth-status/', {
          method: 'GET',
          credentials: 'include',
          cache: 'no-store',
        })

        if (!response.ok)
          return { logged_in: false }

        return await response.json() as isLogin
      }
      catch {
        // Login page should render normally even when the probe fails.
        return { logged_in: false }
      }
    },
  })
}

export const useLogout = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'logout'],
    mutationFn: () => post('/logout'),
  })
}

type ForgotPasswordValidity = CommonResponse & { is_valid: boolean, email: string }
export const useVerifyForgotPasswordToken = (token?: string | null) => {
  return useQuery<ForgotPasswordValidity>({
    queryKey: commonQueryKeys.forgotPasswordValidity(token),
    queryFn: () => post<ForgotPasswordValidity>('/forgot-password/validity', { body: { token } }),
    enabled: !!token,
    staleTime: 0,
    gcTime: 0,
    retry: false,
  })
}

type OneMoreStepPayload = {
  invitation_code: string
  interface_language: string
  timezone: string
}
export const useOneMoreStep = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'one-more-step'],
    mutationFn: (body: OneMoreStepPayload) => post<CommonResponse>('/account/init', { body }),
  })
}

export const useModelProviders = (enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  const canReadModelProviders = hasModelProviderReadWorkspaceCapability(workspace)
  return useQuery<{ data: ModelProvider[] }>({
    queryKey: commonQueryKeys.modelProviders(workspace?.id, userProfile?.profile?.id),
    queryFn: () => get<{ data: ModelProvider[] }>('/workspaces/current/model-providers'),
    refetchOnWindowFocus: true,
    refetchOnMount: 'always',
    refetchInterval: 5000,
    enabled: enabled && canReadModelProviders && !!workspace?.id && !!userProfile?.profile?.id,
  })
}

export type TeamModelConfigItem = {
  plugin_code: string
  name: string
  version: string
  description?: string
  enabled: boolean
  configured: boolean
  api_key_set: boolean
  base_url: string
  max_concurrent: number | null
  max_qps: number | null
  updated_at: string | null
}

export type TeamModelConfigPayload = {
  plugin_code: string
  api_key?: string
  base_url: string
  max_concurrent?: number | null
  max_qps?: number | null
}

export const useTeamModelConfigs = (enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  return useQuery<{ data: TeamModelConfigItem[] }>({
    queryKey: commonQueryKeys.teamModelConfigs(workspace?.id, userProfile?.profile?.id),
    queryFn: () => get<{ data: TeamModelConfigItem[] }>('/team/model-config'),
    refetchOnWindowFocus: true,
    refetchOnMount: 'always',
    refetchInterval: 5000,
    enabled: enabled && !!workspace?.id && !!userProfile?.profile?.id,
  })
}

export const useSaveTeamModelConfig = () => {
  return useMutation({
    mutationKey: [NAME_SPACE, 'save-team-model-config'],
    mutationFn: (body: TeamModelConfigPayload) => post('/team/model-config', { body }),
  })
}

export const useModelListByType = (type: ModelTypeEnum, enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  return useQuery<{ data: Model[] }>({
    queryKey: commonQueryKeys.modelList(type, workspace?.id, userProfile?.profile?.id),
    queryFn: () => get<{ data: Model[] }>(`/workspaces/current/models/model-types/${type}`),
    enabled: enabled && !!workspace?.id && !!userProfile?.profile?.id,
    refetchOnWindowFocus: true,
    refetchOnMount: 'always',
    refetchInterval: 5000,
  })
}

export const useDefaultModelByType = (type: ModelTypeEnum, enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  return useQuery({
    queryKey: commonQueryKeys.defaultModel(type, workspace?.id, userProfile?.profile?.id),
    queryFn: () => get(`/workspaces/current/default-model?model_type=${type}`),
    enabled,
    refetchOnWindowFocus: true,
    refetchOnMount: 'always',
    refetchInterval: 5000,
  })
}

export const useSupportRetrievalMethods = (enabled = true) => {
  return useQuery<{ retrieval_method: RETRIEVE_METHOD[] }>({
    queryKey: commonQueryKeys.retrievalMethods,
    queryFn: () => get<{ retrieval_method: RETRIEVE_METHOD[] }>('/datasets/retrieval-setting'),
    enabled,
    retry: false,
  })
}

export const useAccountIntegrates = () => {
  return useQuery<{ data: AccountIntegrate[] | null }>({
    queryKey: commonQueryKeys.accountIntegrates,
    queryFn: () => get<{ data: AccountIntegrate[] | null }>('/account/integrates'),
  })
}

type DataSourceIntegratesOptions = {
  enabled?: boolean
  initialData?: { data: DataSourceNotion[] }
}

export const useDataSourceIntegrates = (options: DataSourceIntegratesOptions = {}) => {
  const { enabled = true, initialData } = options
  return useQuery<{ data: DataSourceNotion[] }>({
    queryKey: commonQueryKeys.dataSourceIntegrates,
    queryFn: () => get<{ data: DataSourceNotion[] }>('/data-source/integrates'),
    enabled,
    initialData,
  })
}

export const useInvalidDataSourceIntegrates = () => {
  return useInvalid(commonQueryKeys.dataSourceIntegrates)
}

export type TokenBillingSummary = {
  total_tokens: number
  total_cost: string
  currency: string
  records_last_7d: number
  tokens_last_7d: number
  cost_last_7d: string
  records_last_30d: number
  tokens_last_30d: number
  cost_last_30d: string
}

export type TokenBillingRecord = {
  id: string
  tenant_id: string
  tenant_name: string | null
  organization_name?: string | null
  provider: string
  provider_type: string
  model_name: string
  model_type: string
  user_id: string | null
  is_cloud: boolean
  invocation_source: string | null
  input_tokens: number
  output_tokens: number
  total_tokens: number
  input_price: string
  output_price: string
  total_price: string
  currency: string
  latency: number
  business_type: string | null
  business_id: string | null
  created_at: string | null
}

export type TokenBillingLeaderboardItem = {
  user_id: string | null
  name: string | null
  email: string | null
  total_tokens: number
  total_cost: string
  record_count: number
}

export type TokenBillingOrganizationItem = {
  organization_name: string | null
  workspace_count: number
  total_tokens: number
  total_cost: string
  record_count: number
}

export type TokenBillingUsage = {
  table_ready: boolean
  summary: TokenBillingSummary
  records: TokenBillingRecord[]
  leaderboard: TokenBillingLeaderboardItem[]
  organizations: TokenBillingOrganizationItem[]
}

export const useTokenBillingUsage = (scope: TokenBillingScope) => {
  return useQuery<TokenBillingUsage>({
    queryKey: commonQueryKeys.tokenBillingUsage(scope),
    queryFn: () => get<TokenBillingUsage>('/token-billing/usage', { params: { scope } }),
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
  })
}

export const usePluginProviders = () => {
  return useQuery<PluginProvider[] | null>({
    queryKey: commonQueryKeys.pluginProviders,
    queryFn: () => get<PluginProvider[] | null>('/workspaces/current/tool-providers'),
  })
}

export const useCodeBasedExtensions = (module: string) => {
  return useQuery<CodeBasedExtension>({
    queryKey: commonQueryKeys.codeBasedExtensions(module),
    queryFn: () => get<CodeBasedExtension>(`/code-based-extension?module=${module}`),
  })
}

export const useNotionConnection = (enabled: boolean) => {
  return useQuery<{ data: string }>({
    queryKey: commonQueryKeys.notionConnection,
    queryFn: () => get<{ data: string }>('/oauth/data-source/notion'),
    enabled,
  })
}

export const useApiBasedExtensions = () => {
  return useQuery<ApiBasedExtension[]>({
    queryKey: commonQueryKeys.apiBasedExtensions,
    queryFn: () => get<ApiBasedExtension[]>('/api-based-extension'),
  })
}

export const useInvitationCheck = (params?: { workspace_id?: string, email?: string, token?: string }, enabled?: boolean) => {
  return useQuery({
    queryKey: commonQueryKeys.invitationCheck(params),
    queryFn: () => get<{
      is_valid: boolean
      data: { workspace_name: string, email: string, workspace_id: string }
      result: string
    }>('/activate/check', { params }),
    enabled: enabled ?? !!params?.token,
    retry: false,
  })
}

export const useNotionBinding = (code?: string | null, enabled?: boolean) => {
  return useQuery({
    queryKey: commonQueryKeys.notionBinding(code),
    queryFn: () => get<{ result: string }>('/oauth/data-source/binding/notion', { params: { code } }),
    enabled: !!code && (enabled ?? true),
  })
}

export const useModelParameterRules = (provider?: string, model?: string, enabled?: boolean) => {
  return useQuery<{ data: ModelParameterRule[] }>({
    queryKey: commonQueryKeys.modelParameterRules(provider, model),
    queryFn: () => get<{ data: ModelParameterRule[] }>(`/workspaces/current/model-providers/${provider}/models/parameter-rules`, { params: { model } }),
    enabled: !!provider && !!model && (enabled ?? true),
  })
}
