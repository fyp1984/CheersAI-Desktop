import { get, post } from './base'

export type OperationLogContent = {

  file_name?: string

  dataset_name?: string

  app_name?: string

  status?: string

  error?: string

  mode?: string

  size?: number

  [key: string]: unknown

}

export type OperationLog = {

  id: string

  tenant_id?: string

  account_id: string

  account_name: string

  account_email?: string

  action: string

  content: OperationLogContent

  created_at: number

  created_ip: string

  operation_type?: string

  request_content?: string

  response_content?: string

  desensitize_status?: string

  device_info?: string

  duration?: number

  sync_status?: string

  sync_time?: number | null

  is_expired?: boolean

  error_message?: string

}

export type OperationLogListResponse = {

  data: OperationLog[]

  total: number

  page: number

  limit: number

  has_more?: boolean

}

export type OperationLogStats = {

  today_count?: number

  total_count?: number

  verified_count?: number

  failed_count?: number

}

export type OperationLogFilters = {

  page?: number

  limit?: number

  action?: string

  account_id?: string

  account_name?: string

  user_keyword?: string

  keyword?: string

  start_date?: string

  end_date?: string

  operation_type?: string

  sync_status?: string

}

export type ExportFormat = 'excel' | 'pdf'

export const fetchOperationLogs = (filters: OperationLogFilters): Promise<OperationLogListResponse> => {
  const params = new URLSearchParams()

  if (filters.page)

    params.append('page', String(filters.page))

  if (filters.limit)

    params.append('limit', String(filters.limit))

  if (filters.action)

    params.append('action', filters.action)

  if (filters.account_id)

    params.append('account_id', filters.account_id)

  if (filters.account_name)

    params.append('account_name', filters.account_name)

  if (filters.user_keyword)

    params.append('user_keyword', filters.user_keyword)

  if (filters.keyword)

    params.append('keyword', filters.keyword)

  if (filters.start_date)

    params.append('start_date', filters.start_date)

  if (filters.end_date)

    params.append('end_date', filters.end_date)

  if (filters.operation_type)

    params.append('operation_type', filters.operation_type)

  if (filters.sync_status)

    params.append('sync_status', filters.sync_status)

  return get<OperationLogListResponse>(`/operation-logs?${params.toString()}`)
}

export const fetchOperationLogStats = () => {
  return get<OperationLogStats>('/operation-logs/stats')
}

export const fetchOperationLogActions = () => {
  return get<{ actions: string[] }>('/operation-logs/actions')
}

export const exportAuditLogs = (

  format: ExportFormat,

  filters: Omit<OperationLogFilters, 'page' | 'limit'>,

): Promise<Blob> => {
  return post(`/operation-logs/export`, {

    format,

    ...filters,

  }) as Promise<Blob>
}
