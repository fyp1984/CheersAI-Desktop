import type {
  ModelProvider,
} from './declarations'
import {
  RiBrainLine,
} from '@remixicon/react'
import { useDebounce } from 'ahooks'
import { useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import { IS_CLOUD_EDITION } from '@/config'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useProviderContext } from '@/context/provider-context'
import { cn } from '@/utils/classnames'
import { hasBuiltInAdminAccess } from '@/utils/workspace-capabilities'
import {
  CustomConfigurationStatusEnum,
  ModelTypeEnum,
} from './declarations'
import {
  useDefaultModel,
} from './hooks'
import InstallFromMarketplace from './install-from-marketplace'
import ProviderAddedCard from './provider-added-card'
import QuotaPanel from './provider-added-card/quota-panel'
import SystemModelSelector from './system-model-selector'

type Props = {
  searchText: string
}

const FixedModelProvider = ['langgenius/openai/openai', 'langgenius/anthropic/anthropic']

const ModelProviderPage = ({ searchText }: Props) => {
  const debouncedSearchText = useDebounce(searchText, { wait: 500 })
  const { t } = useTranslation()
  const { currentWorkspace, mutateCurrentWorkspace, isValidatingCurrentWorkspace } = useAppContext()
  const { data: textGenerationDefaultModel, isLoading: isTextGenerationDefaultModelLoading } = useDefaultModel(ModelTypeEnum.textGeneration)
  const { data: embeddingsDefaultModel, isLoading: isEmbeddingsDefaultModelLoading } = useDefaultModel(ModelTypeEnum.textEmbedding)
  const { data: rerankDefaultModel, isLoading: isRerankDefaultModelLoading } = useDefaultModel(ModelTypeEnum.rerank)
  const { data: speech2textDefaultModel, isLoading: isSpeech2textDefaultModelLoading } = useDefaultModel(ModelTypeEnum.speech2text)
  const { data: ttsDefaultModel, isLoading: isTTSDefaultModelLoading } = useDefaultModel(ModelTypeEnum.tts)
  const { modelProviders: providers } = useProviderContext()
  const systemFeatures = useGlobalPublicStore(s => s.systemFeatures)
  const { enable_marketplace } = systemFeatures
  const hasBuiltInAdmin = hasBuiltInAdminAccess(currentWorkspace, systemFeatures)
  const isDefaultModelLoading = isTextGenerationDefaultModelLoading
    || isEmbeddingsDefaultModelLoading
    || isRerankDefaultModelLoading
    || isSpeech2textDefaultModelLoading
    || isTTSDefaultModelLoading
  const defaultModelNotConfigured = !isDefaultModelLoading && !textGenerationDefaultModel && !embeddingsDefaultModel && !speech2textDefaultModel && !rerankDefaultModel && !ttsDefaultModel
  const [configuredProviders, notConfiguredProviders] = useMemo(() => {
    const configuredProviders: ModelProvider[] = []
    const notConfiguredProviders: ModelProvider[] = []

    providers.forEach((provider) => {
      if (
        provider.custom_configuration.status === CustomConfigurationStatusEnum.active
        || (
          provider.system_configuration.enabled === true
          && provider.system_configuration.quota_configurations.find(item => item.quota_type === provider.system_configuration.current_quota_type)
        )
      ) {
        configuredProviders.push(provider)
      }
      else {
        notConfiguredProviders.push(provider)
      }
    })

    configuredProviders.sort((a, b) => {
      if (FixedModelProvider.includes(a.provider) && FixedModelProvider.includes(b.provider))
        return FixedModelProvider.indexOf(a.provider) - FixedModelProvider.indexOf(b.provider) > 0 ? 1 : -1
      else if (FixedModelProvider.includes(a.provider))
        return -1
      else if (FixedModelProvider.includes(b.provider))
        return 1
      return 0
    })

    return [configuredProviders, notConfiguredProviders]
  }, [providers])
  const [filteredConfiguredProviders, filteredNotConfiguredProviders] = useMemo(() => {
    const filteredConfiguredProviders = configuredProviders.filter(
      provider => provider.provider.toLowerCase().includes(debouncedSearchText.toLowerCase())
        || Object.values(provider.label).some(text => text.toLowerCase().includes(debouncedSearchText.toLowerCase())),
    )
    const filteredNotConfiguredProviders = notConfiguredProviders.filter(
      provider => provider.provider.toLowerCase().includes(debouncedSearchText.toLowerCase())
        || Object.values(provider.label).some(text => text.toLowerCase().includes(debouncedSearchText.toLowerCase())),
    )

    return [filteredConfiguredProviders, filteredNotConfiguredProviders]
  }, [configuredProviders, debouncedSearchText, notConfiguredProviders])

  useEffect(() => {
    mutateCurrentWorkspace()
  }, [mutateCurrentWorkspace])

  return (
    <div className="relative -mt-2 pt-1">
      <div className={cn('mb-2 flex items-center')}>
        <div className="system-md-semibold grow text-text-primary">{t('modelProvider.models', { ns: 'common' })}</div>
        <div className="flex shrink-0 items-center justify-end gap-2">
          <SystemModelSelector
            notConfigured={defaultModelNotConfigured}
            textGenerationDefaultModel={textGenerationDefaultModel}
            embeddingsDefaultModel={embeddingsDefaultModel}
            rerankDefaultModel={rerankDefaultModel}
            speech2textDefaultModel={speech2textDefaultModel}
            ttsDefaultModel={ttsDefaultModel}
            isLoading={isDefaultModelLoading}
          />
        </div>
      </div>
      {IS_CLOUD_EDITION && <QuotaPanel providers={providers} isLoading={isValidatingCurrentWorkspace} />}
      {!filteredConfiguredProviders?.length && (
        <div className="mb-2 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-[10px] border border-[#bfdbfe] bg-white shadow-sm">
            <RiBrainLine className="h-5 w-5 text-[#2563eb]" />
          </div>
          <div className="system-sm-medium mt-2 text-text-primary">{t('modelProvider.emptyProviderTitle', { ns: 'common' })}</div>
          <div className="system-xs-regular mt-1 text-text-secondary">{t('modelProvider.emptyProviderTip', { ns: 'common' })}</div>
        </div>
      )}
      {!!filteredConfiguredProviders?.length && (
        <div className="relative">
          {filteredConfiguredProviders?.map(provider => (
            <ProviderAddedCard
              key={provider.provider}
              provider={provider}
            />
          ))}
        </div>
      )}
      {!!filteredNotConfiguredProviders?.length && (
        <>
          <div className="relative">
            {filteredNotConfiguredProviders?.map(provider => (
              <ProviderAddedCard
                notConfigured
                key={provider.provider}
                provider={provider}
              />
            ))}
          </div>
        </>
      )}
      {
        enable_marketplace && hasBuiltInAdmin && (
          <InstallFromMarketplace
            providers={providers}
            searchText={searchText}
          />
        )
      }
    </div>
  )
}

export default ModelProviderPage
