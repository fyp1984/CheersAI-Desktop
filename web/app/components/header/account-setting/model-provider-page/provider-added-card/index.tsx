import type { FC } from 'react'
import type {
  ModelItem,
  ModelProvider,
} from '../declarations'
import {
  RiArrowRightSLine,
  RiLoader2Line,
} from '@remixicon/react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  AddCustomModel,
  ManageCustomModelCredentials,
} from '@/app/components/header/account-setting/model-provider-page/model-auth'
import { useAppContext } from '@/context/app-context'
import { useEventEmitterContextContext } from '@/context/event-emitter'
import { fetchModelProviderModelList } from '@/service/common'
import { cn } from '@/utils/classnames'
import { ConfigurationMethodEnum } from '../declarations'
import ModelBadge from '../model-badge'
import ProviderIcon from '../provider-icon'
import {
  modelTypeFormat,
} from '../utils'
import CredentialPanel from './credential-panel'
import ModelList from './model-list'

export const UPDATE_MODEL_PROVIDER_CUSTOM_MODEL_LIST = 'UPDATE_MODEL_PROVIDER_CUSTOM_MODEL_LIST'
type ProviderAddedCardProps = {
  notConfigured?: boolean
  provider: ModelProvider
}
const ProviderAddedCard: FC<ProviderAddedCardProps> = ({
  notConfigured,
  provider,
}) => {
  const { t } = useTranslation()
  const { eventEmitter } = useEventEmitterContextContext()
  const [fetched, setFetched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [collapsed, setCollapsed] = useState(true)
  const [modelList, setModelList] = useState<ModelItem[]>([])
  const configurationMethods = provider.configurate_methods.filter(method => method !== ConfigurationMethodEnum.fetchFromRemote)
  const hasModelList = fetched && !!modelList.length
  const { isCurrentWorkspaceManager } = useAppContext()
  const showCredential = configurationMethods.includes(ConfigurationMethodEnum.predefinedModel) && isCurrentWorkspaceManager

  const getModelList = async (providerName: string) => {
    if (loading)
      return
    try {
      setLoading(true)
      const modelsData = await fetchModelProviderModelList(`/workspaces/current/model-providers/${providerName}/models`)
      setModelList(modelsData.data)
      setCollapsed(false)
      setFetched(true)
    }
    finally {
      setLoading(false)
    }
  }
  const handleOpenModelList = () => {
    if (fetched) {
      setCollapsed(false)
      return
    }

    getModelList(provider.provider)
  }

  eventEmitter?.useSubscription((v: any) => {
    if (v?.type === UPDATE_MODEL_PROVIDER_CUSTOM_MODEL_LIST && v.payload === provider.provider)
      getModelList(v.payload)
  })

  return (
    <div
      className={cn(
        'mb-2 rounded-xl border-[0.5px] border-divider-regular bg-third-party-model-bg-default shadow-xs dark:border-white/10 dark:bg-[#1f2026] dark:shadow-black/20',
        notConfigured && 'border-[#bfdbfe] ring-1 ring-inset ring-[#dbeafe] dark:border-blue-400/40 dark:ring-blue-400/35',
        provider.provider === 'langgenius/openai/openai' && 'bg-third-party-model-bg-openai dark:bg-[#20252b]',
        provider.provider === 'langgenius/anthropic/anthropic' && 'bg-third-party-model-bg-anthropic dark:bg-[#27231f]',
      )}
    >
      <div className="flex rounded-t-xl py-2 pl-3 pr-2">
        <div className="grow px-1 pb-0.5 pt-1">
          <ProviderIcon
            className="mb-2"
            provider={provider}
          />
          <div className="flex gap-0.5">
            {
              provider.supported_model_types.map(modelType => (
                <ModelBadge key={modelType}>
                  {modelTypeFormat(modelType)}
                </ModelBadge>
              ))
            }
          </div>
        </div>
        {
          showCredential && (
            <CredentialPanel
              provider={provider}
            />
          )
        }
      </div>
      {
        collapsed && (
          <div className="system-xs-medium group flex items-center justify-between border-t border-t-divider-subtle py-1.5 pl-2 pr-[11px] text-text-tertiary dark:border-t-white/10 dark:text-gray-400">
            <>
              <div className="flex h-6 items-center pl-1 pr-1.5 leading-6 group-hover:hidden">
                {
                  hasModelList
                    ? t('modelProvider.modelsNum', { ns: 'common', num: modelList.length })
                    : t('modelProvider.showModels', { ns: 'common' })
                }
                {!loading && <RiArrowRightSLine className="h-4 w-4" />}
              </div>
              <div
                className="hidden h-6 cursor-pointer items-center rounded-lg pl-1 pr-1.5 hover:bg-components-button-ghost-bg-hover group-hover:flex dark:hover:bg-white/10"
                onClick={handleOpenModelList}
              >
                {
                  hasModelList
                    ? t('modelProvider.showModelsNum', { ns: 'common', num: modelList.length })
                    : t('modelProvider.showModels', { ns: 'common' })
                }
                {!loading && <RiArrowRightSLine className="h-4 w-4" />}
                {
                  loading && (
                    <RiLoader2Line className="ml-0.5 h-3 w-3 animate-spin" />
                  )
                }
              </div>
            </>
            {
              configurationMethods.includes(ConfigurationMethodEnum.customizableModel) && isCurrentWorkspaceManager && (
                <div className="flex grow justify-end">
                  <ManageCustomModelCredentials
                    provider={provider}
                    currentCustomConfigurationModelFixedFields={undefined}
                  />
                  <AddCustomModel
                    provider={provider}
                    configurationMethod={ConfigurationMethodEnum.customizableModel}
                    currentCustomConfigurationModelFixedFields={undefined}
                  />
                </div>
              )
            }
          </div>
        )
      }
      {
        !collapsed && (
          <ModelList
            provider={provider}
            models={modelList}
            onCollapse={() => setCollapsed(true)}
            onChange={(provider: string) => getModelList(provider)}
          />
        )
      }
    </div>
  )
}

export default ProviderAddedCard
