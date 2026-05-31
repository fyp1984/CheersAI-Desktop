import { del, get, post } from './base'

export type AppInstruction = {
  id: string
  app_id: string
  title: string
  content: string
  source_file_name?: string | null
  source_file_size?: number
  updated_at?: number | null
}

export type AppInstructionResponse = {
  instruction: AppInstruction | null
}

export type AppInstructionPayload = {
  title?: string
  content: string
  source_file_name?: string | null
  source_file_size?: number
}

export type AppInstructionSource = 'app' | 'installed' | 'trial'

export const fetchAppInstruction = (appId: string, source: AppInstructionSource = 'app') => {
  const prefix = source === 'installed'
    ? 'installed-apps'
    : source === 'trial'
      ? 'trial-apps'
      : 'apps'
  return get<AppInstructionResponse>(`/${prefix}/${appId}/instruction`, {}, { silent: true })
}

export const updateAppInstruction = (appId: string, body: AppInstructionPayload) => {
  return post<AppInstructionResponse>(`/apps/${appId}/instruction`, { body })
}

export const deleteAppInstruction = (appId: string) => {
  return del<{ result: string }>(`/apps/${appId}/instruction`)
}
