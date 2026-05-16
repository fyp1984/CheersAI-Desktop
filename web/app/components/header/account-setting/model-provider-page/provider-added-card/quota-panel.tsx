import type { ComponentType, FC } from 'react'
import type { ModelProvider } from '../declarations'
import * as React from 'react'
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { AnthropicShortLight, Deepseek, Gemini, Grok, OpenaiSmall, Tongyi } from '@/app/components/base/icons/src/public/llm'
import Loading from '@/app/components/base/loading'
import Tooltip from '@/app/components/base/tooltip'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import useTimestamp from '@/hooks/use-timestamp'
import { ModelProviderQuotaGetPaid } from '@/types/model-provider'
import { cn } from '@/utils/classnames'
import { formatNumber } from '@/utils/format'
import { PreferredProviderTypeEnum } from '../declarations'
import { MODEL_PROVIDER_QUOTA_GET_PAID, modelNameMap } from '../utils'

// Icon map for each provider - single source of truth for provider icons
const providerIconMap: Record<ModelProviderQuotaGetPaid, ComponentType<{ className?: string }>> = {
  [ModelProviderQuotaGetPaid.OPENAI]: OpenaiSmall,
  [ModelProviderQuotaGetPaid.ANTHROPIC]: AnthropicShortLight,
  [ModelProviderQuotaGetPaid.GEMINI]: Gemini,
  [ModelProviderQuotaGetPaid.X]: Grok,
  [ModelProviderQuotaGetPaid.DEEPSEEK]: Deepseek,
  [ModelProviderQuotaGetPaid.TONGYI]: Tongyi,
}

// Derive allProviders from the shared constant
const allProviders = MODEL_PROVIDER_QUOTA_GET_PAID.map(key => ({
  key,
  Icon: providerIconMap[key],
}))

type QuotaPanelProps = {
  providers: ModelProvider[]
  isLoading?: boolean
}
const QuotaPanel: FC<QuotaPanelProps> = ({
  providers,
  isLoading = false,
}) => {
  const { t } = useTranslation()
  const { currentWorkspace, isCurrentWorkspaceManager } = useAppContext()
  const { trial_models } = useGlobalPublicStore(s => s.systemFeatures)
  const credits = Math.max((currentWorkspace.trial_credits - currentWorkspace.trial_credits_used) || 0, 0)
  const providerMap = useMemo(() => new Map(
    providers.map(p => [p.provider, p.preferred_provider_type]),
  ), [providers])
  const installedProvidersMap = useMemo(() => new Map(
    providers.map(p => [p.provider, p.custom_configuration.available_credentials]),
  ), [providers])
  const { formatTime } = useTimestamp()

  if (isLoading) {
    return (
      <div className="my-2 flex min-h-[72px] items-center justify-center rounded-xl border-[0.5px] border-components-panel-border bg-third-party-model-bg-default shadow-xs">
        <Loading />
      </div>
    )
  }

  return (
    <div className={cn('my-2 min-w-[72px] shrink-0 rounded-xl border-[0.5px] pb-2.5 pl-4 pr-2.5 pt-3 shadow-xs', credits <= 0 ? 'border-state-destructive-border hover:bg-state-destructive-hover' : 'border-components-panel-border bg-third-party-model-bg-default')}>
      <div className="system-xs-medium-uppercase mb-2 flex h-4 items-center text-text-tertiary">
        {t('modelProvider.quota', { ns: 'common' })}
        <Tooltip popupContent={t('modelProvider.card.tip', { ns: 'common', modelNames: trial_models.map(key => modelNameMap[key as keyof typeof modelNameMap]).filter(Boolean).join(', ') })} />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-text-tertiary">
          <span className="system-md-semibold-uppercase mr-0.5 text-text-secondary">{formatNumber(credits)}</span>
          <span>{t('modelProvider.credits', { ns: 'common' })}</span>
          {currentWorkspace.next_credit_reset_date
            ? (
                <>
                  <span>·</span>
                  <span>
                    {t('modelProvider.resetDate', {
                      ns: 'common',
                      date: formatTime(currentWorkspace.next_credit_reset_date, t('dateFormat', { ns: 'appLog' })),
                      interpolation: { escapeValue: false },
                    })}
                  </span>
                </>
              )
            : null}
        </div>
        <div className="flex items-center gap-1">
          {allProviders.filter(({ key }) => trial_models.includes(key)).map(({ key, Icon }) => {
            const providerType = providerMap.get(key)
            const isConfigured = (installedProvidersMap.get(key)?.length ?? 0) > 0 // means the provider is configured API key
            const getTooltipKey = () => {
              // if provider type is not set, it means the provider is not installed
              if (!providerType)
                return isCurrentWorkspaceManager ? 'modelProvider.configureTip' : 'model.sharedConfigHint'
              if (isConfigured && providerType === PreferredProviderTypeEnum.custom)
                return 'modelProvider.card.modelAPI'
              return 'modelProvider.card.modelSupported'
            }
            return (
              <Tooltip
                key={key}
                popupContent={!providerType
                  ? t(getTooltipKey(), { ns: 'common' })
                  : t(getTooltipKey(), { modelName: modelNameMap[key], ns: 'common' })}
              >
                <div
                  className="relative h-6 w-6"
                >
                  <Icon className="h-6 w-6 rounded-lg" />
                  {!providerType && (
                    <div className="absolute inset-0 rounded-lg border-[0.5px] border-components-panel-border-subtle bg-background-default-dodge opacity-30" />
                  )}
                </div>
              </Tooltip>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default React.memo(QuotaPanel)
