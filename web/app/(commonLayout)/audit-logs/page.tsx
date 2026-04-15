'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Loading from '@/app/components/base/loading'
import Toast from '@/app/components/base/toast'
import { useAppContext } from '@/context/app-context'
import useDocumentTitle from '@/hooks/use-document-title'
import { fetchOperationLogs, fetchOperationLogStats, fetchOperationLogActions, exportAuditLogs } from '@/service/audit'
import type { OperationLog, OperationLogStats } from '@/service/audit'

const AuditLogsPage = () => {
  const router = useRouter()
  const { canViewAudit, isLoadingCurrentWorkspace } = useAppContext()
  useDocumentTitle('审计日志')
  const [logs, setLogs] = useState<OperationLog[]>([])
  const [stats, setStats] = useState<OperationLogStats | null>(null)
  const [actions, setActions] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [isAutoRefresh, setIsAutoRefresh] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  
  // 获取今天的日期 yyyy-MM-dd
  const getToday = () => {
    const today = new Date()
    const year = today.getFullYear()
    const month = String(today.getMonth() + 1).padStart(2, '0')
    const day = String(today.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }
  
  const [filters, setFilters] = useState({
    action: '',
    keyword: '',
    start_date: getToday(),
    end_date: getToday(),
  })

  const pageSize = 10
  const AUTO_REFRESH_INTERVAL = 30000 // 30秒自动刷新

  // 操作类型中文映射
  const actionNameMap: Record<string, string> = {
    'login': '用户登录',
    'logout': '用户登出',
    'access_apps': '访问应用列表',
    'access_app': '访问应用详情',
    'access_agent': '访问智能体',
    'access_datasets': '访问知识库列表',
    'access_dataset': '访问知识库详情',
    'chat_message': '调用智能体对话',
    'chat_completion': '调用大模型补全',
    'file_mask': '文件脱敏',
    'file_delete': '文件删除',
    'file_restore': '文件恢复',
    'file_upload': '文件上传',
    'knowledge_sync': '知识库同步',
    'member_invite': '成员邀请',
    'member_remove': '成员移除',
    'rule_create': '规则创建',
    'rule_update': '规则更新',
    'rule_delete': '规则删除',
  }

  // 自动刷新定时器
  useEffect(() => {
    if (!canViewAudit) return
    
    const interval = setInterval(() => {
      loadData(true)
    }, AUTO_REFRESH_INTERVAL)
    
    return () => clearInterval(interval)
  }, [canViewAudit, filters])

  useEffect(() => {
    if (!isLoadingCurrentWorkspace && !canViewAudit)
      router.replace('/apps')
  }, [canViewAudit, isLoadingCurrentWorkspace, router])

  useEffect(() => {
    if (!canViewAudit)
      return
    loadData()
  }, [canViewAudit, page, filters])

  if (isLoadingCurrentWorkspace || !canViewAudit)
    return <Loading type="app" />

  const loadData = async (isAutoRefresh = false) => {
    try {
      if (!isAutoRefresh) setLoading(true)
      const [logsRes, statsRes, actionsRes] = await Promise.all([
        fetchOperationLogs({ page, limit: pageSize, ...filters }),
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

  const handleToggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh)
  }

  const handleExport = async () => {
    try {
      console.log('Starting export with filters:', filters)
      const response = await exportAuditLogs('excel', filters)
      console.log('Export response:', response)
      
      if (!response || !response.body) {
        console.error('Invalid response:', response)
        Toast.notify({ type: 'error', message: '导出失败：无效的响应' })
        return
      }
      
      const blob = await response.blob()
      console.log('Blob:', blob, blob.type)
      
      if (blob.size === 0) {
        Toast.notify({ type: 'error', message: '导出失败：文件为空' })
        return
      }
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `审计日志_${new Date().toISOString().slice(0,10)}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export audit logs:', error)
      Toast.notify({ type: 'error', message: `导出失败: ${error instanceof Error ? error.message : '未知错误'}` })
    }
  }

  const handleRefresh = () => {
    loadData()
  }

  return (
    <div className="relative flex h-0 shrink-0 grow flex-col overflow-y-auto bg-background-body">
      {/* Top header bar */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background-body px-12 pb-4 pt-7">
          <h2 className="text-lg font-semibold text-text-primary">日志列表</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleToggleAutoRefresh}
            className={`px-4 py-2 text-sm border rounded-lg transition-colors ${
              isAutoRefresh 
                ? 'text-components-button-primary-solid-bg bg-components-button-primary-solid-bg bg-opacity-10 border-components-button-primary-bg' 
                : 'text-text-secondary border-divider-regular hover:bg-state-base-hover'
            }`}
          >
            {isAutoRefresh ? '自动刷新中' : '开启自动刷新'}
          </button>
          <button
            onClick={() => loadData()}
            className="px-4 py-2 text-sm text-text-secondary border border-divider-regular rounded-lg hover:bg-state-base-hover transition-colors"
          >
            刷新
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 text-sm text-white bg-components-button-primary-bg rounded-lg hover:bg-components-button-primary-hover-bg transition-colors"
          >
            导出
          </button>
        </div>
      </div>

      {/* Content area */}
      <div className="px-12 pb-8 space-y-4">
        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-components-panel-bg border border-divider-regular rounded-lg p-4">
              <div className="text-xs text-text-tertiary mb-1">总操作数</div>
              <div className="text-2xl font-semibold text-text-primary">{stats.total_count || 0}</div>
            </div>
            <div className="bg-components-panel-bg border border-divider-regular rounded-lg p-4">
              <div className="text-xs text-text-tertiary mb-1">今日操作</div>
              <div className="text-2xl font-semibold text-text-primary">{stats.today_count || 0}</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-components-panel-bg border border-divider-regular rounded-lg p-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">操作类型</label>
              <select
                className="w-full border border-divider-regular rounded-lg px-3 py-2 text-sm text-text-primary bg-components-input-bg-normal focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg appearance-none cursor-pointer"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                  backgroundPosition: 'right 0.5rem center',
                  backgroundRepeat: 'no-repeat',
                  backgroundSize: '1.5em 1.5em',
                  paddingRight: '2.5rem',
                }}
                value={filters.action}
                onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              >
                <option value="">所有操作</option>
                {actions.map(action => (
                  <option key={action} value={action}>
                    {actionNameMap[action] || action}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">搜索</label>
              <input
                type="text"
                className="w-full border border-divider-regular rounded-lg px-3 py-2 text-sm text-text-primary bg-components-input-bg-normal placeholder:text-text-quaternary focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                placeholder="搜索日志..."
                value={filters.keyword}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">开始日期</label>
              <input
                type="date"
                className="w-full border border-divider-regular rounded-lg px-3 py-2 text-sm text-text-primary bg-components-input-bg-normal focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">结束日期</label>
              <input
                type="date"
                className="w-full border border-divider-regular rounded-lg px-3 py-2 text-sm text-text-primary bg-components-input-bg-normal focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Table */}
        {loading && logs.length === 0 ? (
          <div className="bg-components-panel-bg border border-divider-regular rounded-lg p-12 text-center">
            <div className="text-sm text-text-tertiary">加载中...</div>
          </div>
        ) : logs.length === 0 ? (
          <div className="bg-components-panel-bg border border-divider-regular rounded-lg p-12 text-center">
            <div className="text-sm text-text-tertiary">暂无数据</div>
          </div>
        ) : (
          <div className="bg-components-panel-bg border border-divider-regular rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-background-section-burn border-b border-divider-regular">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">时间</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">操作</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">文件名</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">大小</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-text-tertiary">IP地址</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-divider-subtle">
                  {logs.map(log => (
                    <tr key={log.id} className="hover:bg-state-base-hover transition-colors">
                      <td className="px-4 py-3 text-sm text-text-secondary whitespace-nowrap">
                        {log.created_at ? new Date(log.created_at).toLocaleString('zh-CN', {
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        }) : 'Invalid Date'}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-primary whitespace-nowrap">
                        {actionNameMap[log.action] || log.action}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary max-w-xs truncate" title={log.content?.file_name}>
                        {log.content?.file_name || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary whitespace-nowrap">
                        {log.content?.size ? `${(log.content.size / 1024).toFixed(2)} KB` : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">{log.created_ip}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Pagination */}
        {logs.length > 0 && (
          <div className="flex justify-between items-center">
            <div className="text-xs text-text-tertiary">
              显示 {(page - 1) * pageSize + 1} 到 {Math.min(page * pageSize, total)}，共 {total} 条
            </div>
            <div className="flex items-center gap-2">
              <button
                className="px-3 py-1.5 text-sm text-text-secondary border border-divider-regular rounded-lg hover:bg-state-base-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                上一页
              </button>
              <span className="px-3 py-1.5 text-sm text-text-tertiary">
                第 {page} 页
              </span>
              <button
                className="px-3 py-1.5 text-sm text-text-secondary border border-divider-regular rounded-lg hover:bg-state-base-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                disabled={page * pageSize >= total}
                onClick={() => setPage(page + 1)}
              >
                下一页
              </button>
              <span className="text-xs text-text-quaternary mx-2">跳转到</span>
              <input
                type="number"
                min="1"
                max={Math.ceil(total / pageSize)}
                className="w-16 px-2 py-1.5 text-sm text-text-primary border border-divider-regular rounded-lg bg-components-input-bg-normal focus:outline-none focus:ring-2 focus:ring-components-button-primary-bg"
                placeholder={String(page)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const value = parseInt((e.target as HTMLInputElement).value)
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
