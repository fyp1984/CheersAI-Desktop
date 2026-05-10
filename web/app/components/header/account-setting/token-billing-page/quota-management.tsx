'use client'
import type { FC } from 'react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { RiAlertLine, RiCheckLine, RiEditLine, RiRefreshLine, RiSettings3Line } from '@remixicon/react'
import Badge from '@/app/components/base/badge'
import Button from '@/app/components/base/button'
import { useAppContext } from '@/context/app-context'

interface QuotaConfig {
  id: string
  tenant_id: string
  user_id: string | null
  name: string
  description: string | null
  interval_type: 'hourly' | 'daily' | 'weekly' | 'monthly'
  token_limit: number
  cloud_models: Array<{ provider: string; model: string }>
  local_models: Array<{ provider: string; model: string }>
  status: 'active' | 'paused' | 'exceeded'
  priority: number
  created_at: string
  updated_at: string
}

interface QuotaUsage {
  id: string
  period_start: string
  period_end: string
  total_tokens: number
  input_tokens: number
  output_tokens: number
  request_count: number
  is_exceeded: boolean
  exceeded_at: string | null
  model_usage_details: Record<string, { tokens: number; requests: number }>
}

interface QuotaCheckResult {
  within_quota: boolean
  remaining_tokens: number
  should_use_local: boolean
  quota_config: QuotaConfig | null
  current_usage: QuotaUsage | null
}

const cardClassName = 'rounded-2xl border border-divider-regular bg-components-panel-bg p-4 shadow-xs'

const formatInteger = (value: number) => Intl.NumberFormat().format(value || 0)

const getIntervalText = (intervalType: string) => {
  const map: Record<string, string> = {
    hourly: '每小时',
    daily: '每天',
    weekly: '每周',
    monthly: '每月',
  }
  return map[intervalType] || intervalType
}

const QuotaManagement: FC = () => {
  const { t } = useTranslation()
  const { currentWorkspace } = useAppContext()
  const [quotaInfo, setQuotaInfo] = useState<QuotaCheckResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchQuotaInfo = async () => {
    try {
      setRefreshing(true)
      const response = await fetch('/console/api/token-quota/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tokens_to_use: 0 }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setQuotaInfo(data)
      }
    }
    catch (error) {
      console.error('Failed to fetch quota info:', error)
    }
    finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchQuotaInfo()
    // 每分钟刷新一次
    const interval = setInterval(fetchQuotaInfo, 60000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className={cardClassName}>
        <div className="system-sm-regular text-text-tertiary">加载配额信息...</div>
      </div>
    )
  }

  if (!quotaInfo?.quota_config) {
    return (
      <div className="rounded-3xl border border-dashed border-divider-regular bg-background-section-burn p-6">
        <div className="flex items-center gap-2">
          <Badge>未配置</Badge>
          <div className="system-sm-medium text-text-tertiary">Token 配额未配置</div>
        </div>
        <div className="title-2xl-semi-bold mt-4 text-text-primary">配置 Token 配额</div>
        <div className="system-md-regular mt-2 max-w-[720px] text-text-secondary">
          Token 配额系统可以帮助你控制云端模型的使用成本。当达到配额上限时，系统会自动切换到本地模型。
        </div>
        <Button className="mt-4" variant="primary">
          <RiSettings3Line className="mr-2 h-4 w-4" />
          配置配额
        </Button>
      </div>
    )
  }

  const { quota_config, remaining_tokens, should_use_local, current_usage } = quotaInfo
  const usedTokens = quota_config.token_limit - remaining_tokens
  const usagePercent = Math.min((usedTokens / quota_config.token_limit) * 100, 100)

  return (
    <div className="space-y-4">
      {/* 配额状态卡片 */}
      <div className="rounded-3xl border border-divider-regular bg-gradient-to-r from-components-panel-bg to-background-section-burn p-5">
        <div className="flex items-center justify-between">
          <div className="flex flex-wrap items-center gap-2">
            {should_use_local ? (
              <>
                <Badge className="bg-warning-50 text-warning-600">
                  <RiAlertLine className="mr-1 h-3 w-3" />
                  配额已用完
                </Badge>
                <div className="system-sm-regular text-text-tertiary">
                  已切换到本地模型
                </div>
              </>
            ) : (
              <>
                <Badge className="bg-success-50 text-success-600">
                  <RiCheckLine className="mr-1 h-3 w-3" />
                  配额充足
                </Badge>
                <div className="system-sm-regular text-text-tertiary">
                  {refreshing ? '刷新中...' : '使用云端模型'}
                </div>
              </>
            )}
          </div>
          <Button
            variant="secondary"
            size="small"
            onClick={fetchQuotaInfo}
            disabled={refreshing}
          >
            <RiRefreshLine className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        <div className="title-2xl-semi-bold mt-3 text-text-primary">
          Token 配额管理
        </div>
        <div className="system-md-regular mt-2 text-text-secondary">
          {quota_config.name} - {getIntervalText(quota_config.interval_type)} {formatInteger(quota_config.token_limit)} tokens
        </div>

        {/* 配额使用进度条 */}
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="text-text-tertiary">已使用</span>
            <span className="font-medium text-text-primary">
              {formatInteger(usedTokens)} / {formatInteger(quota_config.token_limit)} tokens
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className={`h-full transition-all duration-300 ${
                usagePercent > 90
                  ? 'bg-error-600'
                  : usagePercent > 70
                    ? 'bg-warning-600'
                    : 'bg-primary-600'
              }`}
              style={{ width: `${usagePercent}%` }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-text-tertiary">
            <span>{usagePercent.toFixed(1)}% 已使用</span>
            <span>剩余: {formatInteger(remaining_tokens)} tokens</span>
          </div>
        </div>
      </div>

      {/* 配额详情卡片 */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {/* 总使用量 */}
        <div className={cardClassName}>
          <div className="system-xs-medium-uppercase text-text-tertiary">总使用量</div>
          <div className="title-2xl-semi-bold mt-3 text-text-primary">
            {formatInteger(current_usage?.total_tokens || 0)}
          </div>
          <div className="system-sm-regular mt-1 text-text-tertiary">
            本周期已使用的 Token 数
          </div>
        </div>

        {/* 请求次数 */}
        <div className={cardClassName}>
          <div className="system-xs-medium-uppercase text-text-tertiary">请求次数</div>
          <div className="title-2xl-semi-bold mt-3 text-text-primary">
            {formatInteger(current_usage?.request_count || 0)}
          </div>
          <div className="system-sm-regular mt-1 text-text-tertiary">
            本周期的 API 调用次数
          </div>
        </div>

        {/* 输入 Token */}
        <div className={cardClassName}>
          <div className="system-xs-medium-uppercase text-text-tertiary">输入 Token</div>
          <div className="title-2xl-semi-bold mt-3 text-text-primary">
            {formatInteger(current_usage?.input_tokens || 0)}
          </div>
          <div className="system-sm-regular mt-1 text-text-tertiary">
            Prompt 使用的 Token 数
          </div>
        </div>

        {/* 输出 Token */}
        <div className={cardClassName}>
          <div className="system-xs-medium-uppercase text-text-tertiary">输出 Token</div>
          <div className="title-2xl-semi-bold mt-3 text-text-primary">
            {formatInteger(current_usage?.output_tokens || 0)}
          </div>
          <div className="system-sm-regular mt-1 text-text-tertiary">
            生成内容使用的 Token 数
          </div>
        </div>
      </div>

      {/* 模型使用详情 */}
      {current_usage?.model_usage_details && Object.keys(current_usage.model_usage_details).length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-divider-regular bg-components-panel-bg">
          <div className="border-b border-divider-regular px-4 py-4">
            <div className="system-md-semibold text-text-primary">模型使用详情</div>
            <div className="system-sm-regular mt-1 text-text-tertiary">
              本周期各模型的使用情况
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-divider-regular">
              <thead className="bg-background-section-burn">
                <tr className="text-left system-xs-medium-uppercase text-text-tertiary">
                  <th className="px-4 py-3">模型</th>
                  <th className="px-4 py-3">Token 使用量</th>
                  <th className="px-4 py-3">请求次数</th>
                  <th className="px-4 py-3">占比</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-divider-regular">
                {Object.entries(current_usage.model_usage_details).map(([modelKey, details]) => {
                  const percentage = ((details.tokens / (current_usage.total_tokens || 1)) * 100).toFixed(1)
                  return (
                    <tr key={modelKey} className="system-sm-regular text-text-secondary">
                      <td className="px-4 py-3">
                        <div className="font-medium text-text-primary">{modelKey}</div>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        {formatInteger(details.tokens)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        {formatInteger(details.requests)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-20 overflow-hidden rounded-full bg-gray-200">
                            <div
                              className="h-full bg-primary-600"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span>{percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 配额配置信息 */}
      <div className="overflow-hidden rounded-3xl border border-divider-regular bg-components-panel-bg">
        <div className="flex items-center justify-between border-b border-divider-regular px-4 py-4">
          <div>
            <div className="system-md-semibold text-text-primary">配额配置</div>
            <div className="system-sm-regular mt-1 text-text-tertiary">
              当前生效的配额规则
            </div>
          </div>
          <Button variant="secondary" size="small">
            <RiEditLine className="mr-2 h-4 w-4" />
            编辑配置
          </Button>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <div className="system-xs-medium-uppercase text-text-tertiary">配额名称</div>
              <div className="system-sm-regular mt-1 text-text-primary">{quota_config.name}</div>
            </div>
            <div>
              <div className="system-xs-medium-uppercase text-text-tertiary">时间间隔</div>
              <div className="system-sm-regular mt-1 text-text-primary">
                {getIntervalText(quota_config.interval_type)}
              </div>
            </div>
            <div>
              <div className="system-xs-medium-uppercase text-text-tertiary">配额上限</div>
              <div className="system-sm-regular mt-1 text-text-primary">
                {formatInteger(quota_config.token_limit)} tokens
              </div>
            </div>
            <div>
              <div className="system-xs-medium-uppercase text-text-tertiary">状态</div>
              <div className="mt-1">
                <Badge className={
                  quota_config.status === 'active'
                    ? 'bg-success-50 text-success-600'
                    : quota_config.status === 'exceeded'
                      ? 'bg-error-50 text-error-600'
                      : 'bg-gray-100 text-gray-600'
                }>
                  {quota_config.status === 'active' ? '激活' : quota_config.status === 'exceeded' ? '已超额' : '暂停'}
                </Badge>
              </div>
            </div>
            {quota_config.description && (
              <div className="md:col-span-2">
                <div className="system-xs-medium-uppercase text-text-tertiary">描述</div>
                <div className="system-sm-regular mt-1 text-text-primary">
                  {quota_config.description}
                </div>
              </div>
            )}
            {quota_config.cloud_models.length > 0 && (
              <div className="md:col-span-2">
                <div className="system-xs-medium-uppercase text-text-tertiary">云端模型</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {quota_config.cloud_models.map((model, index) => (
                    <Badge key={index} className="bg-primary-50 text-primary-600">
                      {model.provider}/{model.model}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {quota_config.local_models.length > 0 && (
              <div className="md:col-span-2">
                <div className="system-xs-medium-uppercase text-text-tertiary">本地模型（超额后使用）</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {quota_config.local_models.map((model, index) => (
                    <Badge key={index} className="bg-gray-100 text-gray-600">
                      {model.provider}/{model.model}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 周期信息 */}
      {current_usage && (
        <div className="rounded-2xl border border-divider-regular bg-background-section-burn p-4">
          <div className="system-xs-medium-uppercase text-text-tertiary">当前周期</div>
          <div className="system-sm-regular mt-2 text-text-secondary">
            开始时间: {new Date(current_usage.period_start).toLocaleString('zh-CN')}
          </div>
          <div className="system-sm-regular mt-1 text-text-secondary">
            结束时间: {new Date(current_usage.period_end).toLocaleString('zh-CN')}
          </div>
          {current_usage.is_exceeded && current_usage.exceeded_at && (
            <div className="system-sm-regular mt-1 text-warning-600">
              超额时间: {new Date(current_usage.exceeded_at).toLocaleString('zh-CN')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default QuotaManagement
