'use client'
import type { FC } from 'react'
import type { TokenBillingLeaderboardItem, TokenBillingOrganizationItem, TokenBillingRecord, TokenBillingScope, TokenBillingSummary } from '@/service/use-common'
import dayjs from 'dayjs'
import { RiDownloadLine, RiFlashlightLine, RiHistoryLine, RiPriceTag3Line, RiStackLine } from '@remixicon/react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import Badge from '@/app/components/base/badge'
import { useAppContext } from '@/context/app-context'
import { useTokenBillingUsage } from '@/service/use-common'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import QuotaStatusCard from './quota-status-card'

const cardClassName = 'rounded-2xl border border-divider-regular bg-components-panel-bg p-4 shadow-xs'

const formatInteger = (value: number) => Intl.NumberFormat().format(value || 0)

const formatMoney = (value: string, currency: string) => {
  const amount = Number(value || 0)
  if (!Number.isFinite(amount))
    return `${currency} ${value}`

  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency || 'USD',
    maximumFractionDigits: 4,
  }).format(amount)
}

const formatLatency = (value: number) => {
  if (!value)
    return '-'
  return `${value.toFixed(2)}s`
}

const getDisplayName = (item: TokenBillingLeaderboardItem) => {
  return item.name || item.email || item.user_id || '-'
}

const getOrganizationLabel = (item: TokenBillingOrganizationItem, fallback: string) => {
  return item.organization_name || fallback
}

const getBusinessLabel = (record: TokenBillingRecord, labels: Record<string, string>) => {
  if (!record.business_type)
    return '-'

  const label = labels[record.business_type] || record.business_type

  return record.business_id ? `${label} · ${record.business_id}` : label
}

const StatCard = ({
  title,
  value,
  helper,
  icon,
}: {
  title: string
  value: string
  helper: string
  icon: React.JSX.Element
}) => (
  <div className={cardClassName}>
    <div className="flex items-center justify-between">
      <div className="system-xs-medium-uppercase text-text-tertiary">{title}</div>
      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-background-section-burn text-text-secondary">
        {icon}
      </div>
    </div>
    <div className="title-2xl-semi-bold mt-3 text-text-primary">{value}</div>
    <div className="system-sm-regular mt-1 text-text-tertiary">{helper}</div>
  </div>
)

const TokenBillingPage: FC = () => {
  const { t } = useTranslation()
  const text = (key: string, options?: Record<string, unknown>) => String(t(key as never, options as never))
  const { currentWorkspace } = useAppContext()
  const canViewWorkspace = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.settingsTeam)
    || hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.modelManage)
    || hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.modelProviderManage)
  const canViewSystem = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.tokenBillingGlobalView)
  const canExportSystem = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.tokenBillingExport)
  const businessLabels = {
    agent: text('tokenBilling.business.agent', { ns: 'common' }),
    app: text('tokenBilling.business.app', { ns: 'common' }),
    workflow: text('tokenBilling.business.workflow', { ns: 'common' }),
  }
  const [scope, setScope] = useState<TokenBillingScope>(
    canViewSystem ? 'system' : (canViewWorkspace ? 'workspace' : 'self'),
  )
  const { data, isLoading, isFetching } = useTokenBillingUsage(scope)

  const summary: TokenBillingSummary | undefined = data?.summary
  const records = data?.records || []
  const leaderboard = data?.leaderboard || []
  const organizations = data?.organizations || []

  const cards = !summary
    ? []
    : [
        {
          title: t('tokenBilling.summary.totalTokens', { ns: 'common' }),
          value: formatInteger(summary.total_tokens),
          helper: t('tokenBilling.summary.totalTokensHint', { ns: 'common' }),
          icon: <RiStackLine className="h-4 w-4" />,
        },
        {
          title: t('tokenBilling.summary.totalCost', { ns: 'common' }),
          value: formatMoney(summary.total_cost, summary.currency),
          helper: t('tokenBilling.summary.totalCostHint', { ns: 'common' }),
          icon: <RiPriceTag3Line className="h-4 w-4" />,
        },
        {
          title: t('tokenBilling.summary.last7Days', { ns: 'common' }),
          value: formatInteger(summary.tokens_last_7d),
          helper: t('tokenBilling.summary.periodHint', {
            ns: 'common',
            records: formatInteger(summary.records_last_7d),
            cost: formatMoney(summary.cost_last_7d, summary.currency),
          }),
          icon: <RiFlashlightLine className="h-4 w-4" />,
        },
        {
          title: t('tokenBilling.summary.last30Days', { ns: 'common' }),
          value: formatInteger(summary.tokens_last_30d),
          helper: t('tokenBilling.summary.periodHint', {
            ns: 'common',
            records: formatInteger(summary.records_last_30d),
            cost: formatMoney(summary.cost_last_30d, summary.currency),
          }),
          icon: <RiHistoryLine className="h-4 w-4" />,
        },
      ]

  if (isLoading) {
    return <div className="system-sm-regular text-text-tertiary">{t('tokenBilling.loading', { ns: 'common' })}</div>
  }

  if (!data?.table_ready) {
    return (
      <div className="rounded-3xl border border-dashed border-divider-regular bg-background-section-burn p-6">
        <div className="flex items-center gap-2">
          <Badge>{t('tokenBilling.status.pending', { ns: 'common' })}</Badge>
          <div className="system-sm-medium text-text-tertiary">{t('tokenBilling.status.pendingHint', { ns: 'common' })}</div>
        </div>
        <div className="title-2xl-semi-bold mt-4 text-text-primary">{t('tokenBilling.empty.tableTitle', { ns: 'common' })}</div>
        <div className="system-md-regular mt-2 max-w-[720px] text-text-secondary">
          {t('tokenBilling.empty.tableDescription', { ns: 'common' })}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-divider-regular bg-gradient-to-r from-components-panel-bg to-background-section-burn p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{t('tokenBilling.status.active', { ns: 'common' })}</Badge>
          <div className="system-sm-regular text-text-tertiary">
            {isFetching ? t('tokenBilling.refreshing', { ns: 'common' }) : t('tokenBilling.pageDescription', { ns: 'common' })}
          </div>
        </div>
        <div className="title-2xl-semi-bold mt-3 text-text-primary">
          {scope === 'self'
            ? t('tokenBilling.myTitle', { ns: 'common' })
            : scope === 'system'
              ? t('tokenBilling.systemTitle', { ns: 'common' })
              : t('tokenBilling.title', { ns: 'common' })}
        </div>
        <div className="system-md-regular mt-2 text-text-secondary">
          {scope === 'system'
            ? t('tokenBilling.systemSubtitle', { ns: 'common' })
            : t('tokenBilling.subtitle', { ns: 'common' })}
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-2">
          {canViewWorkspace && (
            <button
              type="button"
              className={scope === 'workspace'
                ? 'rounded-lg bg-state-base-active px-3 py-1.5 text-sm text-text-primary'
                : 'rounded-lg bg-components-button-secondary-bg px-3 py-1.5 text-sm text-text-secondary'}
              onClick={() => setScope('workspace')}
            >
              {t('tokenBilling.scope.workspace', { ns: 'common' })}
            </button>
          )}
          {canViewSystem && (
            <button
              type="button"
              className={scope === 'system'
                ? 'rounded-lg bg-state-base-active px-3 py-1.5 text-sm text-text-primary'
                : 'rounded-lg bg-components-button-secondary-bg px-3 py-1.5 text-sm text-text-secondary'}
              onClick={() => setScope('system')}
            >
              {text('tokenBilling.scope.system', { ns: 'common' })}
            </button>
          )}
          <button
            type="button"
            className={scope === 'self'
              ? 'rounded-lg bg-state-base-active px-3 py-1.5 text-sm text-text-primary'
              : 'rounded-lg bg-components-button-secondary-bg px-3 py-1.5 text-sm text-text-secondary'}
            onClick={() => setScope('self')}
          >
            {t('tokenBilling.scope.self', { ns: 'common' })}
          </button>
        </div>
          {canExportSystem && scope === 'system' && (
            <button
              type="button"
              className="flex items-center gap-2 rounded-lg bg-components-button-secondary-bg px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary"
              onClick={() => window.open(`/console/api/token-billing/export?scope=${scope}`, '_blank', 'noopener,noreferrer')}
            >
              <RiDownloadLine className="h-4 w-4" />
              {text('tokenBilling.export', { ns: 'common' })}
            </button>
          )}
        </div>
      </div>

      {/* Token 配额状态卡片 */}
      <QuotaStatusCard />

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(card => (
          <StatCard key={card.title} title={card.title} value={card.value} helper={card.helper} icon={card.icon} />
        ))}
      </div>

      {scope === 'workspace' && leaderboard.length > 0 && (
            <div className="overflow-hidden rounded-3xl border border-divider-regular bg-components-panel-bg">
              <div className="border-b border-divider-regular px-4 py-4">
                <div className="system-md-semibold text-text-primary">{t('tokenBilling.leaderboard.title', { ns: 'common' })}</div>
                <div className="system-sm-regular mt-1 text-text-tertiary">{t('tokenBilling.leaderboard.subtitle', { ns: 'common' })}</div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-divider-regular">
                  <thead className="bg-background-section-burn">
                    <tr className="text-left system-xs-medium-uppercase text-text-tertiary">
                      <th className="px-4 py-3">{t('tokenBilling.leaderboard.user', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.leaderboard.calls', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.tokens', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.cost', { ns: 'common' })}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-divider-regular">
                    {leaderboard.map(item => (
                      <tr key={item.user_id || item.email || 'unknown'} className="system-sm-regular text-text-secondary">
                        <td className="px-4 py-3">
                          <div className="font-medium text-text-primary">{getDisplayName(item)}</div>
                          {item.email && <div className="mt-1 text-text-tertiary">{item.email}</div>}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">{formatInteger(item.record_count)}</td>
                        <td className="whitespace-nowrap px-4 py-3">{formatInteger(item.total_tokens)}</td>
                        <td className="whitespace-nowrap px-4 py-3">{formatMoney(item.total_cost, summary?.currency || 'USD')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
        </div>
      )}

      {scope === 'system' && organizations.length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-divider-regular bg-components-panel-bg">
          <div className="border-b border-divider-regular px-4 py-4">
            <div className="system-md-semibold text-text-primary">{text('tokenBilling.organizations.title', { ns: 'common' })}</div>
            <div className="system-sm-regular mt-1 text-text-tertiary">{text('tokenBilling.organizations.subtitle', { ns: 'common' })}</div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-divider-regular">
              <thead className="bg-background-section-burn">
                <tr className="text-left system-xs-medium-uppercase text-text-tertiary">
                  <th className="px-4 py-3">{text('tokenBilling.columns.organization', { ns: 'common' })}</th>
                  <th className="px-4 py-3">{text('tokenBilling.columns.workspaceCount', { ns: 'common' })}</th>
                  <th className="px-4 py-3">{t('tokenBilling.leaderboard.calls', { ns: 'common' })}</th>
                  <th className="px-4 py-3">{t('tokenBilling.columns.tokens', { ns: 'common' })}</th>
                  <th className="px-4 py-3">{t('tokenBilling.columns.cost', { ns: 'common' })}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-divider-regular">
                {organizations.map(item => (
                  <tr key={item.organization_name || 'unassigned'} className="system-sm-regular text-text-secondary">
                    <td className="px-4 py-3 font-medium text-text-primary">{getOrganizationLabel(item, text('tokenBilling.organizations.unassigned', { ns: 'common' }))}</td>
                    <td className="whitespace-nowrap px-4 py-3">{formatInteger(item.workspace_count)}</td>
                    <td className="whitespace-nowrap px-4 py-3">{formatInteger(item.record_count)}</td>
                    <td className="whitespace-nowrap px-4 py-3">{formatInteger(item.total_tokens)}</td>
                    <td className="whitespace-nowrap px-4 py-3">{formatMoney(item.total_cost, summary?.currency || 'USD')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-3xl border border-divider-regular bg-components-panel-bg">
            <div className="flex items-center justify-between border-b border-divider-regular px-4 py-4">
              <div>
                <div className="system-md-semibold text-text-primary">{t('tokenBilling.recent.title', { ns: 'common' })}</div>
                <div className="system-sm-regular mt-1 text-text-tertiary">
                  {t('tokenBilling.recent.subtitle', { ns: 'common', count: records.length })}
                </div>
              </div>
            </div>

            {records.length === 0 && (
              <div className="px-4 py-10 text-center">
                <div className="system-md-semibold text-text-primary">{t('tokenBilling.empty.recordsTitle', { ns: 'common' })}</div>
                <div className="system-sm-regular mt-2 text-text-tertiary">{t('tokenBilling.empty.recordsDescription', { ns: 'common' })}</div>
              </div>
            )}

            {records.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-divider-regular">
                  <thead className="bg-background-section-burn">
                    <tr className="text-left system-xs-medium-uppercase text-text-tertiary">
                      {scope === 'system' && <th className="px-4 py-3">{text('tokenBilling.columns.workspace', { ns: 'common' })}</th>}
                      <th className="px-4 py-3">{t('tokenBilling.columns.time', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.model', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{text('tokenBilling.columns.business', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.source', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.tokens', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.cost', { ns: 'common' })}</th>
                      <th className="px-4 py-3">{t('tokenBilling.columns.latency', { ns: 'common' })}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-divider-regular">
                    {records.map(record => (
                      <tr key={record.id} className="system-sm-regular text-text-secondary">
                        {scope === 'system' && (
                          <td className="whitespace-nowrap px-4 py-3">
                            <div className="font-medium text-text-primary">{record.tenant_name || '-'}</div>
                            <div className="mt-1 text-text-tertiary">
                              {(record.organization_name || text('tokenBilling.organizations.unassigned', { ns: 'common' }))} · {record.tenant_id}
                            </div>
                          </td>
                        )}
                        <td className="whitespace-nowrap px-4 py-3">
                          {record.created_at ? dayjs(record.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-text-primary">{record.model_name}</div>
                          <div className="mt-1 flex items-center gap-2 text-text-tertiary">
                            <span>{record.provider}</span>
                            <Badge>{record.model_type}</Badge>
                          </div>
                        </td>
                        <td className="px-4 py-3">{getBusinessLabel(record, businessLabels)}</td>
                        <td className="px-4 py-3">
                          {record.invocation_source || (record.is_cloud
                            ? t('tokenBilling.sources.cloud', { ns: 'common' })
                            : t('tokenBilling.sources.local', { ns: 'common' }))}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-text-primary">{formatInteger(record.total_tokens)}</div>
                          <div className="mt-1 text-text-tertiary">
                            {t('tokenBilling.tokenBreakdown', {
                              ns: 'common',
                              input: formatInteger(record.input_tokens),
                              output: formatInteger(record.output_tokens),
                            })}
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">{formatMoney(record.total_price, record.currency)}</td>
                        <td className="whitespace-nowrap px-4 py-3">{formatLatency(record.latency)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default TokenBillingPage
