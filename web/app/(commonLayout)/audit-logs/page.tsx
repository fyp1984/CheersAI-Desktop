'use client'

import type { Option } from '@/app/components/base/select/custom'
import type { ExportFormat, OperationLog, OperationLogStats } from '@/service/audit'
import { RiDownloadLine } from '@remixicon/react'
import { useCallback, useEffect, useState } from 'react'
import {
  exportAuditLogs,
  fetchOperationLogActions,
  fetchOperationLogs,
  fetchOperationLogStats,
} from '@/service/audit'

const AuditLogsPage = () => {
  const [logs, setLogs] = useState<OperationLog[]>([])
  const [stats, setStats] = useState<OperationLogStats | null>(null)
  const [actions, setActions] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({
    action: '',
    keyword: '',
    start_date: '',
    end_date: '',
    operation_type: '',
    sync_status: '',
  })

  const pageSize = 10

  const operationTypeOptions: Option[] = [
    { label: '全部类型', value: '' },
    { label: 'AI 对话', value: 'chat' },
    { label: '数据脱敏', value: 'desensitize' },
    { label: '数据还原', value: 'restore' },
    { label: '知识库搜索', value: 'search' },
    { label: '工作流执行', value: 'workflow' },
  ]

  const syncStatusOptions: Option[] = [
    { label: '全部状态', value: '' },
    { label: '待同步', value: 'pending' },
    { label: '已同步', value: 'synced' },
    { label: '同步失败', value: 'failed' },
  ]

  const actionNameMap: Record<string, string> = {
    file_mask: '文件脱敏',
    file_delete: '文件删除',
    file_restore: '文件恢复',
    knowledge_sync: '知识库同步',
    rule_create: '规则创建',
    rule_update: '规则更新',
    rule_delete: '规则删除',
    chat: 'AI 对话',
    desensitize: '数据脱敏',
    restore: '数据还原',
    search: '知识库搜索',
    workflow: '工作流执行',
  }

  const operationTypeNameMap: Record<string, string> = {
    chat: 'AI 对话',
    desensitize: '数据脱敏',
    restore: '数据还原',
    search: '知识库搜索',
    workflow: '工作流执行',
  }

  const syncStatusNameMap: Record<string, string> = {
    pending: '待同步',
    synced: '已同步',
    failed: '同步失败',
  }

  const desensitizeStatusNameMap: Record<string, string> = {
    original: '原始',
    desensitized: '已脱敏',
  }

  useEffect(() => {
    loadData()
  }, [page, filters])

  const loadData = async () => {
    try {
      setLoading(true)
      const [logsRes, statsRes, actionsRes] = await Promise.all([
        fetchOperationLogs({
          page,
          limit: pageSize,
          action: filters.action || undefined,
          keyword: filters.keyword || undefined,
          start_date: filters.start_date || undefined,
          end_date: filters.end_date || undefined,
          operation_type: filters.operation_type || undefined,
          sync_status: filters.sync_status || undefined,
        }),
        fetchOperationLogStats(),
        fetchOperationLogActions(),
      ])

      setLogs(logsRes.data)
      setTotal(logsRes.total)
      setStats(statsRes)
      setActions(actionsRes.actions)
    }
    catch (error) {
      console.error('Failed to load audit logs:', error)
    }
    finally {
      setLoading(false)
    }
  }

  const handleExport = useCallback(async (format: ExportFormat) => {
    try {
      const response = await exportAuditLogs(format, {
        action: filters.action || undefined,
        keyword: filters.keyword || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
        operation_type: filters.operation_type || undefined,
        sync_status: filters.sync_status || undefined,
      })

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const contentDisposition = response.headers.get('Content-Disposition')
      const match = contentDisposition?.match(/filename=(.+)/)
      const filename = match ? match[1] : `审计日志_${Date.now()}.xlsx`
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    }
    catch (error) {
      console.error('Failed to export audit logs:', error)
    }
  }, [filters])

  const formatDuration = (ms?: number) => {
    if (!ms)
      return '-'
    if (ms < 1000)
      return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <div className="relative flex h-0 shrink-0 grow flex-col overflow-y-auto bg-background-body">
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background-body px-12 pb-4 pt-7">
        <h2 className="text-lg font-semibold text-text-primary">审计日志</h2>
        <div className="flex items-center gap-2">
          <button
            className="flex items-center gap-1.5 rounded-lg border border-divider-regular bg-components-button-primary-bg px-3 py-1.5 text-sm font-medium text-components-button-primary-text transition-colors hover:bg-components-button-primary-bg-hover"
            onClick={() => handleExport('excel')}
          >
            <RiDownloadLine className="h-4 w-4" />
            导出
          </button>
        </div>
      </div>

      <div className="space-y-4 px-12 pb-8">
        {stats && (
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
              <div className="mb-1 text-xs text-text-tertiary">总操作数</div>
              <div className="text-2xl font-semibold text-text-primary">{stats.total_count || 0}</div>
            </div>
            <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
              <div className="mb-1 text-xs text-text-tertiary">今日操作</div>
              <div className="text-2xl font-semibold text-text-primary">{stats.today_count || 0}</div>
            </div>
          </div>
        )}

        <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-secondary">操作类型</label>
              <select
                className="w-full cursor-pointer appearance-none rounded-lg border border-divider-regular bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                  backgroundPosition: 'right 0.5rem center',
                  backgroundRepeat: 'no-repeat',
                  backgroundSize: '1.5em 1.5em',
                  paddingRight: '2.5rem',
                }}
                value={filters.operation_type}
                onChange={e => setFilters({ ...filters, operation_type: e.target.value })}
              >
                {operationTypeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-secondary">同步状态</label>
              <select
                className="w-full cursor-pointer appearance-none rounded-lg border border-divider-regular bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                  backgroundPosition: 'right 0.5rem center',
                  backgroundRepeat: 'no-repeat',
                  backgroundSize: '1.5em 1.5em',
                  paddingRight: '2.5rem',
                }}
                value={filters.sync_status}
                onChange={e => setFilters({ ...filters, sync_status: e.target.value })}
              >
                {syncStatusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-secondary">搜索</label>
              <input
                type="text"
                className="w-full rounded-lg border border-divider-regular bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-quaternary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                placeholder="搜索日志..."
                value={filters.keyword}
                onChange={e => setFilters({ ...filters, keyword: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-secondary">开始时间</label>
              <input
                type="date"
                className="w-full rounded-lg border border-divider-regular bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                value={filters.start_date}
                onChange={e => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-secondary">结束时间</label>
              <input
                type="date"
                className="w-full rounded-lg border border-divider-regular bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                value={filters.end_date}
                onChange={e => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-secondary">操作行为</label>
              <select
                className="w-full cursor-pointer appearance-none rounded-lg border border-divider-regular bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                  backgroundPosition: 'right 0.5rem center',
                  backgroundRepeat: 'no-repeat',
                  backgroundSize: '1.5em 1.5em',
                  paddingRight: '2.5rem',
                }}
                value={filters.action}
                onChange={e => setFilters({ ...filters, action: e.target.value })}
              >
                <option value="">所有操作</option>
                {actions.map(action => (
                  <option key={action} value={action}>
                    {actionNameMap[action] || action}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {loading && logs.length === 0
          ? (
              <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-12 text-center">
                <div className="text-sm text-text-tertiary">加载中...</div>
              </div>
            )
          : logs.length === 0
            ? (
                <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-12 text-center">
                  <div className="text-sm text-text-tertiary">暂无数据</div>
                </div>
              )
            : (
                <div className="overflow-hidden rounded-lg border border-divider-regular bg-components-panel-bg">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="border-b border-divider-regular bg-background-section-burn">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">时间</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">操作类型</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">操作行为</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">用户</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">脱敏状态</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">执行耗时</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">同步状态</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">IP地址</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-divider-subtle">
                        {logs.map(log => (
                          <tr key={log.id} className="transition-colors hover:bg-state-base-hover">
                            <td className="whitespace-nowrap px-4 py-3 text-sm text-text-secondary">
                              {log.created_at
                                ? new Date(log.created_at * 1000).toLocaleString('zh-CN', {
                                    year: 'numeric',
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    second: '2-digit',
                                  })
                                : 'Invalid Date'}
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-sm text-text-primary">
                              {operationTypeNameMap[log.operation_type || ''] || '-'}
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-sm text-text-primary">
                              {actionNameMap[log.action] || log.action}
                            </td>
                            <td className="px-4 py-3 text-sm text-text-secondary">
                              {log.account_name || '-'}
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-sm text-text-secondary">
                              {desensitizeStatusNameMap[log.desensitize_status || ''] || '-'}
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-sm text-text-secondary">
                              {formatDuration(log.duration)}
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-sm">
                              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                log.sync_status === 'synced'
                                  ? 'bg-green-50 text-green-700'
                                  : log.sync_status === 'failed'
                                    ? 'bg-red-50 text-red-700'
                                    : 'bg-yellow-50 text-yellow-700'
                              }`}
                              >
                                {syncStatusNameMap[log.sync_status || ''] || '-'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-text-secondary">{log.created_ip}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

        {logs.length > 0 && (
          <div className="flex items-center justify-between">
            <div className="text-xs text-text-tertiary">
              显示
              {' '}
              {(page - 1) * pageSize + 1}
              {' '}
              到
              {' '}
              {Math.min(page * pageSize, total)}
              ，共
              {' '}
              {total}
              {' '}
              条
            </div>
            <div className="flex items-center gap-2">
              <button
                className="rounded-lg border border-divider-regular px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-state-base-hover disabled:cursor-not-allowed disabled:opacity-50"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                上一页
              </button>
              <span className="px-3 py-1.5 text-sm text-text-tertiary">
                第
                {' '}
                {page}
                {' '}
                页
              </span>
              <button
                className="rounded-lg border border-divider-regular px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-state-base-hover disabled:cursor-not-allowed disabled:opacity-50"
                disabled={page * pageSize >= total}
                onClick={() => setPage(page + 1)}
              >
                下一页
              </button>
              <span className="mx-2 text-xs text-text-quaternary">跳转到</span>
              <input
                type="number"
                min="1"
                max={Math.ceil(total / pageSize)}
                className="w-16 rounded-lg border border-divider-regular bg-components-input-bg-normal px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                placeholder={String(page)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const value = Number.parseInt((e.target as HTMLInputElement).value)
                    const maxPage = Math.ceil(total / pageSize)
                    if (value >= 1 && value <= maxPage) {
                      setPage(value)
                      ;(e.target as HTMLInputElement).value = ''
                    }
                  }
                }}
              />
              <span className="text-xs text-text-quaternary">页</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AuditLogsPage
