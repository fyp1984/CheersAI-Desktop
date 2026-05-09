'use client'
import type { FC } from 'react'
import { useEffect, useState } from 'react'
import { RiAlertLine, RiCheckLine, RiRefreshLine } from '@remixicon/react'
import Badge from '@/app/components/base/badge'

interface QuotaInfo {
  within_quota: boolean
  remaining_tokens: number
  should_use_local: boolean
  quota_config: {
    name: string
    interval_type: 'hourly' | 'daily' | 'weekly' | 'monthly'
    token_limit: number
  } | null
  current_usage: {
    total_tokens: number
    period_end: string
  } | null
}

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

const getTimeRemaining = (endTime: string) => {
  const end = new Date(endTime).getTime()
  const now = new Date().getTime()
  const diff = end - now

  if (diff <= 0)
    return '即将重置'

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

  if (hours > 24) {
    const days = Math.floor(hours / 24)
    return `${days}天后重置`
  }
  if (hours > 0)
    return `${hours}小时${minutes}分钟后重置`

  return `${minutes}分钟后重置`
}

const QuotaStatusCard: FC = () => {
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfo | null>(null)
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

  if (loading || !quotaInfo?.quota_config)
    return null

  const { quota_config, remaining_tokens, should_use_local, current_usage } = quotaInfo
  const usedTokens = quota_config.token_limit - remaining_tokens
  const usagePercent = Math.min((usedTokens / quota_config.token_limit) * 100, 100)

  return (
    <div className="mb-4 overflow-hidden rounded-3xl border border-divider-regular bg-gradient-to-r from-components-panel-bg to-background-section-burn">
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              {should_use_local ? (
                <Badge className="bg-warning-50 text-warning-600">
                  <RiAlertLine className="mr-1 h-3 w-3" />
                  配额已用完
                </Badge>
              ) : (
                <Badge className="bg-success-50 text-success-600">
                  <RiCheckLine className="mr-1 h-3 w-3" />
                  配额充足
                </Badge>
              )}
              <span className="system-xs-medium text-text-tertiary">
                {should_use_local ? '已切换到本地模型' : '使用云端模型'}
              </span>
            </div>

            <div className="mt-3">
              <div className="title-xl-semi-bold text-text-primary">
                剩余 {formatInteger(remaining_tokens)} tokens
              </div>
              <div className="system-sm-regular mt-1 text-text-tertiary">
                {getIntervalText(quota_config.interval_type)}配额 {formatInteger(quota_config.token_limit)} tokens
                {current_usage && (
                  <span className="ml-2">
                    · {getTimeRemaining(current_usage.period_end)}
                  </span>
                )}
              </div>
            </div>

            <div className="mt-4">
              <div className="mb-2 flex items-center justify-between text-xs">
                <span className="text-text-tertiary">已使用 {usagePercent.toFixed(1)}%</span>
                <span className="text-text-tertiary">
                  {formatInteger(usedTokens)} / {formatInteger(quota_config.token_limit)}
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
            </div>
          </div>

          <button
            type="button"
            className="ml-4 flex h-8 w-8 items-center justify-center rounded-lg bg-components-button-secondary-bg text-text-secondary hover:bg-components-button-secondary-bg-hover"
            onClick={fetchQuotaInfo}
            disabled={refreshing}
          >
            <RiRefreshLine className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default QuotaStatusCard
