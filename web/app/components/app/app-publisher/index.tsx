import type { ModelAndParameter } from '../configuration/debug/types'
import type { InputVar, Variable } from '@/app/components/workflow/types'
import type { AppLifecycleResponse } from '@/service/apps'
import type { I18nKeysByPrefix } from '@/types/i18n'
import type { PublishWorkflowParams } from '@/types/workflow'
import {
  RiArrowDownSLine,
  RiArrowRightSLine,
  RiBuildingLine,
  RiGlobalLine,
  RiLockLine,
  RiPlanetLine,
  RiPlayCircleLine,
  RiPlayList2Line,
  RiTerminalBoxLine,
  RiVerifiedBadgeLine,
} from '@remixicon/react'
import { useKeyPress, useRequest } from 'ahooks'
import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { useTranslation } from 'react-i18next'
import EmbeddedModal from '@/app/components/app/overview/embedded'
import { useStore as useAppStore } from '@/app/components/app/store'
import { trackEvent } from '@/app/components/base/amplitude'
import Button from '@/app/components/base/button'
import { CodeBrowser } from '@/app/components/base/icons/src/vender/line/development'
import {
  PortalToFollowElem,
  PortalToFollowElemContent,
  PortalToFollowElemTrigger,
} from '@/app/components/base/portal-to-follow-elem'
import UpgradeBtn from '@/app/components/billing/upgrade-btn'
import WorkflowToolConfigureButton from '@/app/components/tools/workflow-tool/configure-button'
import { appDefaultIconBackground, NEED_REFRESH_APP_LIST_KEY } from '@/config'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useAsyncWindowOpen } from '@/hooks/use-async-window-open'
import { useFormatTimeFromNow } from '@/hooks/use-format-time-from-now'
import { AccessMode } from '@/models/access-control'
import { useAppWhiteListSubjects, useGetUserCanAccessApp } from '@/service/access-control'
import { fetchAppDetailDirect, fetchAppLifecycle, publishAppLifecycle, recallAppLifecycle, stashAppLifecycle } from '@/service/apps'
import { fetchInstalledAppList } from '@/service/explore'
import { useInvalidateAppList } from '@/service/use-apps'
import { AppModeEnum } from '@/types/app'
import { basePath } from '@/utils/var'
import Divider from '../../base/divider'
import Loading from '../../base/loading'
import Modal from '../../base/modal'
import Textarea from '../../base/textarea'
import Toast from '../../base/toast'
import Tooltip from '../../base/tooltip'
import ShortcutsName from '../../workflow/shortcuts-name'
import { getKeyboardKeyCodeBySystem } from '../../workflow/utils'
import AccessControl from '../app-access-control'
import PublishWithMultipleModel from './publish-with-multiple-model'
import SuggestedAction from './suggested-action'

type AccessModeLabel = I18nKeysByPrefix<'app', 'accessControlDialog.accessItems.'>
type InstalledAppListResponse = {
  installed_apps?: Array<{ id: string }>
}

type OnPublishHandler
  = ((params?: ModelAndParameter) => Promise<unknown> | unknown)
    | ((params?: PublishWorkflowParams) => Promise<unknown> | unknown)

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error)
    return error.message

  if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string')
    return error.message

  return undefined
}

const ACCESS_MODE_MAP: Record<AccessMode, { label: AccessModeLabel, icon: React.ElementType }> = {
  [AccessMode.ORGANIZATION]: {
    label: 'organization',
    icon: RiBuildingLine,
  },
  [AccessMode.SPECIFIC_GROUPS_MEMBERS]: {
    label: 'specific',
    icon: RiLockLine,
  },
  [AccessMode.PUBLIC]: {
    label: 'anyone',
    icon: RiGlobalLine,
  },
  [AccessMode.EXTERNAL_MEMBERS]: {
    label: 'external',
    icon: RiVerifiedBadgeLine,
  },
}

const AccessModeDisplay: React.FC<{ mode?: AccessMode }> = ({ mode }) => {
  const { t } = useTranslation()

  if (!mode || !ACCESS_MODE_MAP[mode])
    return null

  const { icon: Icon, label } = ACCESS_MODE_MAP[mode]

  return (
    <>
      <Icon className="h-4 w-4 shrink-0 text-text-secondary" />
      <div className="grow truncate">
        <span className="system-sm-medium text-text-secondary">{t(`accessControlDialog.accessItems.${label}`, { ns: 'app' })}</span>
      </div>
    </>
  )
}

export type AppPublisherProps = {
  disabled?: boolean
  publishDisabled?: boolean
  publishedAt?: number
  /** only needed in workflow / chatflow mode */
  draftUpdatedAt?: number
  debugWithMultipleModel?: boolean
  multipleModelConfigs?: ModelAndParameter[]
  /** modelAndParameter is passed when debugWithMultipleModel is true */
  onPublish?: OnPublishHandler
  onStash?: () => Promise<unknown> | unknown
  onRestore?: () => Promise<unknown> | unknown
  onToggle?: (state: boolean) => void
  crossAxisOffset?: number
  toolPublished?: boolean
  inputs?: InputVar[]
  outputs?: Variable[]
  onRefreshData?: () => void
  workflowToolAvailable?: boolean
  missingStartNode?: boolean
  hasTriggerNode?: boolean // Whether workflow currently contains any trigger nodes (used to hide missing-start CTA when triggers exist).
  startNodeLimitExceeded?: boolean
}

const PUBLISH_SHORTCUT = ['ctrl', '⇧', 'P']

const AppPublisher = ({
  disabled = false,
  publishDisabled = false,
  publishedAt,
  draftUpdatedAt,
  debugWithMultipleModel = false,
  multipleModelConfigs = [],
  onPublish,
  onStash,
  onRestore,
  onToggle,
  crossAxisOffset = 0,
  toolPublished,
  inputs,
  outputs,
  onRefreshData,
  workflowToolAvailable = true,
  missingStartNode = false,
  hasTriggerNode = false,
  startNodeLimitExceeded = false,
}: AppPublisherProps) => {
  const { t } = useTranslation()

  const [published, setPublished] = useState(false)
  const [open, setOpen] = useState(false)
  const [showAppAccessControl, setShowAppAccessControl] = useState(false)
  const [isAppAccessSet, setIsAppAccessSet] = useState(true)
  const [embeddingModalOpen, setEmbeddingModalOpen] = useState(false)
  const [recallModalOpen, setRecallModalOpen] = useState(false)
  const [recallReason, setRecallReason] = useState('')
  const [recallSubmitting, setRecallSubmitting] = useState(false)
  const [publishSubmitting, setPublishSubmitting] = useState(false)

  const appDetail = useAppStore(state => state.appDetail)
  const setAppDetail = useAppStore(s => s.setAppDetail)
  const systemFeatures = useGlobalPublicStore(s => s.systemFeatures)
  const { formatTimeFromNow } = useFormatTimeFromNow()
  const { app_base_url: appBaseURL = '', access_token: accessToken = '' } = appDetail?.site ?? {}
  const invalidateAppList = useInvalidateAppList()

  const appMode = (appDetail?.mode !== AppModeEnum.COMPLETION && appDetail?.mode !== AppModeEnum.WORKFLOW) ? AppModeEnum.CHAT : appDetail.mode
  const appURL = `${appBaseURL}${basePath}/${appMode}/${accessToken}`
  const appDevelopURL = appDetail?.id ? `${basePath}/app/${appDetail.id}/develop` : undefined
  const isChatApp = [AppModeEnum.CHAT, AppModeEnum.AGENT_CHAT, AppModeEnum.COMPLETION].includes(appDetail?.mode || AppModeEnum.CHAT)
  const isWorkflowPublishFlow = appDetail?.mode === AppModeEnum.WORKFLOW || appDetail?.mode === AppModeEnum.ADVANCED_CHAT

  const { data: userCanAccessApp, isLoading: isGettingUserCanAccessApp, refetch } = useGetUserCanAccessApp({ appId: appDetail?.id, enabled: false })
  const { data: appAccessSubjects, isLoading: isGettingAppWhiteListSubjects } = useAppWhiteListSubjects(appDetail?.id, open && systemFeatures.webapp_auth.enabled && appDetail?.access_mode === AccessMode.SPECIFIC_GROUPS_MEMBERS)
  const openAsyncWindow = useAsyncWindowOpen()

  const { data: appLifecycle, mutate: mutateAppLifecycle } = useRequest<AppLifecycleResponse | undefined, []>(
    async () => {
      if (appDetail?.id)
        return fetchAppLifecycle(appDetail.id)
      return undefined
    },
    { refreshDeps: [appDetail?.id] },
  )

  const handleLifecycleChanged = useCallback((nextLifecycle?: AppLifecycleResponse) => {
    if (nextLifecycle)
      mutateAppLifecycle(nextLifecycle)
    localStorage.setItem(NEED_REFRESH_APP_LIST_KEY, '1')
    invalidateAppList()
    onRefreshData?.()
  }, [invalidateAppList, mutateAppLifecycle, onRefreshData])

  const handleStash = useCallback(async () => {
    if (!appDetail?.id || !appLifecycle)
      return
    try {
      await onStash?.()
      const nextLifecycle = await stashAppLifecycle(appDetail.id, appLifecycle.row_version)
      handleLifecycleChanged(nextLifecycle)
      Toast.notify({ type: 'success', message: '暂存成功' })
    }
    catch (e: unknown) {
      Toast.notify({ type: 'error', message: getErrorMessage(e) || '暂存失败' })
    }
  }, [appDetail?.id, appLifecycle, handleLifecycleChanged, onStash])

  const handleRecall = useCallback(async (reason: string) => {
    if (!appDetail?.id || !appLifecycle)
      return
    const trimmedReason = reason.trim()
    if (!trimmedReason) {
      Toast.notify({ type: 'error', message: '请输入回收原因' })
      return
    }
    try {
      setRecallSubmitting(true)
      const nextLifecycle = await recallAppLifecycle(appDetail.id, appLifecycle.row_version, trimmedReason)
      handleLifecycleChanged(nextLifecycle)
      setRecallModalOpen(false)
      setRecallReason('')
      setPublished(false)
      Toast.notify({ type: 'success', message: '回收成功' })
    }
    catch (e: unknown) {
      Toast.notify({ type: 'error', message: getErrorMessage(e) || '回收失败' })
    }
    finally {
      setRecallSubmitting(false)
    }
  }, [appDetail?.id, appLifecycle, handleLifecycleChanged])

  const noAccessPermission = useMemo(() => systemFeatures.webapp_auth.enabled && appDetail && appDetail.access_mode !== AccessMode.EXTERNAL_MEMBERS && !userCanAccessApp?.result, [systemFeatures, appDetail, userCanAccessApp])
  const disabledFunctionButton = useMemo(() => (!publishedAt || missingStartNode || noAccessPermission), [publishedAt, missingStartNode, noAccessPermission])

  const disabledFunctionTooltip = useMemo(() => {
    if (!publishedAt)
      return t('notPublishedYet', { ns: 'app' })
    if (missingStartNode)
      return t('noUserInputNode', { ns: 'app' })
    if (noAccessPermission)
      return t('noAccessPermission', { ns: 'app' })
  }, [missingStartNode, noAccessPermission, publishedAt, t])

  useEffect(() => {
    if (systemFeatures.webapp_auth.enabled && open && appDetail)
      refetch()
  }, [open, appDetail, refetch, systemFeatures])

  useEffect(() => {
    if (appDetail && appAccessSubjects) {
      if (appDetail.access_mode === AccessMode.SPECIFIC_GROUPS_MEMBERS && appAccessSubjects.groups?.length === 0 && appAccessSubjects.members?.length === 0)
        setIsAppAccessSet(false)
      else
        setIsAppAccessSet(true)
    }
    else {
      setIsAppAccessSet(true)
    }
  }, [appAccessSubjects, appDetail])

  const handlePublish = useCallback(async (params?: ModelAndParameter | PublishWorkflowParams) => {
    try {
      await (onPublish as ((params?: ModelAndParameter | PublishWorkflowParams) => Promise<unknown> | unknown) | undefined)?.(params)
      if (appDetail?.id && appLifecycle) {
        const nextLifecycle = await publishAppLifecycle(appDetail.id, appLifecycle.row_version)
        handleLifecycleChanged(nextLifecycle)
        Toast.notify({ type: 'success', message: '发布成功' })
      }
      setPublished(true)
      trackEvent('app_published_time', { action_mode: 'app', app_id: appDetail?.id, app_name: appDetail?.name })
    }
    catch (e: unknown) {
      setPublished(false)
      Toast.notify({ type: 'error', message: getErrorMessage(e) || '发布失败' })
    }
  }, [appDetail, onPublish, appLifecycle, handleLifecycleChanged])

  const handlePublishWithSubmitting = useCallback(async (params?: ModelAndParameter | PublishWorkflowParams) => {
    if (publishSubmitting)
      return

    try {
      setPublishSubmitting(true)
      await handlePublish(params)
    }
    finally {
      setPublishSubmitting(false)
    }
  }, [handlePublish, publishSubmitting])

  const handleRestore = useCallback(async () => {
    try {
      await onRestore?.()
      setOpen(false)
    }
    catch { }
  }, [onRestore])

  const handleTrigger = useCallback(() => {
    const state = !open

    if (disabled) {
      setOpen(false)
      return
    }

    onToggle?.(state)
    setOpen(state)

    if (state)
      setPublished(false)
  }, [disabled, onToggle, open])

  const handleOpenInExplore = useCallback(async () => {
    await openAsyncWindow(async () => {
      if (!appDetail?.id)
        throw new Error('App not found')
      const { installed_apps } = ((await fetchInstalledAppList(appDetail?.id)) as InstalledAppListResponse) || {}
      if (installed_apps && installed_apps.length > 0)
        return `${basePath}/explore/installed/${installed_apps[0].id}`
      throw new Error('No app found in Explore')
    }, {
      onError: (err: unknown) => {
        Toast.notify({ type: 'error', message: getErrorMessage(err) || `${err}` })
      },
    })
  }, [appDetail?.id, openAsyncWindow])

  const handleRunApp = useCallback(async () => {
    await openAsyncWindow(async () => {
      if (!appDetail?.id)
        throw new Error('App not found')
      const { installed_apps } = ((await fetchInstalledAppList(appDetail.id)) as InstalledAppListResponse) || {}
      if (installed_apps && installed_apps.length > 0)
        return `${basePath}/explore/installed/${installed_apps[0].id}`
      return appURL
    }, {
      onError: (err: unknown) => {
        Toast.notify({ type: 'error', message: getErrorMessage(err) || `${err}` })
      },
    })
  }, [appDetail?.id, appURL, openAsyncWindow])

  const handleAccessControlUpdate = useCallback(async () => {
    if (!appDetail)
      return
    try {
      const res = await fetchAppDetailDirect({ url: '/apps', id: appDetail.id })
      setAppDetail(res)
    }
    finally {
      setShowAppAccessControl(false)
    }
  }, [appDetail, setAppDetail])

  const hasPublishedVersion = !!publishedAt
  const workflowToolDisabled = !hasPublishedVersion || !workflowToolAvailable
  const workflowToolMessage = workflowToolDisabled ? t('common.workflowAsToolDisabledHint', { ns: 'workflow' }) : undefined
  const publishButtonDisabled = useMemo(() => {
    if (published)
      return true

    if (isWorkflowPublishFlow && !publishDisabled)
      return false

    if (appLifecycle)
      return !appLifecycle.can_publish

    return publishDisabled
  }, [appLifecycle, isWorkflowPublishFlow, publishDisabled, published])
  const publishBlockedMessage = useMemo(() => {
    if (published)
      return t('common.published', { ns: 'workflow' })
    if (missingStartNode)
      return t('noUserInputNode', { ns: 'app' })
    if (startNodeLimitExceeded)
      return t('publishLimit.startNodeDesc', { ns: 'workflow' })
    if (publishDisabled)
      return t('panel.checklistTip', { ns: 'workflow' })
    if (appLifecycle && !appLifecycle.can_publish)
      return appLifecycle.display_status_description || '当前状态无法发布'
    return '当前状态无法发布'
  }, [appLifecycle, missingStartNode, publishDisabled, published, startNodeLimitExceeded, t])

  useKeyPress(`${getKeyboardKeyCodeBySystem('ctrl')}.shift.p`, (e) => {
    e.preventDefault()
    if (publishSubmitting) {
      Toast.notify({ type: 'info', message: '正在发布中，请稍候…' })
      return
    }
    if (publishButtonDisabled) {
      Toast.notify({ type: 'error', message: publishBlockedMessage })
      return
    }
    handlePublishWithSubmitting()
  }, { exactMatch: true, useCapture: true })
  const showStartNodeLimitHint = Boolean(startNodeLimitExceeded)
  const upgradeHighlightStyle = useMemo(() => ({
    background: 'linear-gradient(97deg, var(--components-input-border-active-prompt-1, rgba(11, 165, 236, 0.95)) -3.64%, var(--components-input-border-active-prompt-2, rgba(21, 90, 239, 0.95)) 45.14%)',
    WebkitBackgroundClip: 'text',
    backgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  }), [])

  return (
    <>
      <PortalToFollowElem
        open={open}
        onOpenChange={setOpen}
        placement="bottom-end"
        offset={{
          mainAxis: 4,
          crossAxis: crossAxisOffset,
        }}
      >
        <PortalToFollowElemTrigger onClick={handleTrigger}>
          <Button
            variant="primary"
            className="py-2 pl-3 pr-2"
            disabled={disabled}
          >
            {t('common.publish', { ns: 'workflow' })}
            <RiArrowDownSLine className="h-4 w-4 text-components-button-primary-text" />
          </Button>
        </PortalToFollowElemTrigger>
        <PortalToFollowElemContent className="z-[11]">
          <div className="w-[320px] rounded-2xl border-[0.5px] border-components-panel-border bg-components-panel-bg shadow-xl shadow-shadow-shadow-5">
            <div className="p-4 pt-3">
              <div className="system-xs-medium-uppercase flex h-6 items-center text-text-tertiary">
                {publishedAt ? t('common.latestPublished', { ns: 'workflow' }) : t('common.currentDraftUnpublished', { ns: 'workflow' })}
              </div>
              {publishedAt
                ? (
                    <div className="flex items-center justify-between">
                      <div className="system-sm-medium flex items-center text-text-secondary">
                        {t('common.publishedAt', { ns: 'workflow' })}
                        {' '}
                        {formatTimeFromNow(publishedAt)}
                      </div>
                      {isChatApp && (
                        <Button
                          variant="secondary-accent"
                          size="small"
                          onClick={handleRestore}
                          disabled={published}
                        >
                          {t('common.restore', { ns: 'workflow' })}
                        </Button>
                      )}
                    </div>
                  )
                : (
                    <div className="system-sm-medium flex items-center text-text-secondary">
                      {t('common.autoSaved', { ns: 'workflow' })}
                      {' '}
                      ·
                      {Boolean(draftUpdatedAt) && formatTimeFromNow(draftUpdatedAt!)}
                    </div>
                  )}
              {debugWithMultipleModel
                ? (
                    <PublishWithMultipleModel
                      multipleModelConfigs={multipleModelConfigs}
                      onSelect={item => handlePublishWithSubmitting(item)}
                      // textGenerationModelList={textGenerationModelList}
                    />
                  )
                : (
                    <>
                      <div className="mt-3 flex w-full gap-2">
                        <Button
                          className="flex-1"
                          onClick={() => handleStash()}
                          disabled={publishSubmitting || !appLifecycle?.can_stash}
                        >
                          暂存
                        </Button>
                        <Button
                          variant="primary"
                          className={`flex-1 ${(publishSubmitting || publishButtonDisabled) ? 'btn-disabled' : ''}`}
                          aria-disabled={publishSubmitting || publishButtonDisabled}
                          disabled={publishSubmitting}
                          loading={publishSubmitting}
                          onClick={async () => {
                            if (publishSubmitting) {
                              Toast.notify({ type: 'info', message: '正在发布中，请稍候…' })
                              return
                            }
                            if (publishButtonDisabled) {
                              Toast.notify({ type: 'error', message: publishBlockedMessage })
                              return
                            }
                            await handlePublishWithSubmitting()
                          }}
                        >
                          {published && t('common.published', { ns: 'workflow' })}
                          {!published && publishSubmitting && <span>发布中</span>}
                          {!published && !publishSubmitting && (
                            <div className="flex items-center gap-1">
                              <span>{t('common.publishUpdate', { ns: 'workflow' })}</span>
                              <ShortcutsName keys={PUBLISH_SHORTCUT} bgColor="white" />
                            </div>
                          )}
                        </Button>
                        <Button
                          variant="secondary-accent"
                          className="flex-1 text-red-500"
                          onClick={() => {
                            setRecallReason('')
                            setRecallModalOpen(true)
                          }}
                          disabled={publishSubmitting || !appLifecycle?.can_recall}
                        >
                          回收
                        </Button>
                      </div>
                      {showStartNodeLimitHint && (
                        <div className="mt-3 flex flex-col items-stretch">
                          <p
                            className="text-sm font-semibold leading-5 text-transparent"
                            style={upgradeHighlightStyle}
                          >
                            <span className="block">{t('publishLimit.startNodeTitlePrefix', { ns: 'workflow' })}</span>
                            <span className="block">{t('publishLimit.startNodeTitleSuffix', { ns: 'workflow' })}</span>
                          </p>
                          <p className="mt-1 text-xs leading-4 text-text-secondary">
                            {t('publishLimit.startNodeDesc', { ns: 'workflow' })}
                          </p>
                          <UpgradeBtn
                            isShort
                            className="mb-[12px] mt-[9px] h-[32px] w-[93px] self-start"
                          />
                        </div>
                      )}
                    </>
                  )}
            </div>
            {(systemFeatures.webapp_auth.enabled && (isGettingUserCanAccessApp || isGettingAppWhiteListSubjects))
              ? <div className="py-2"><Loading /></div>
              : (
                  <>
                    <Divider className="my-0" />
                    {systemFeatures.webapp_auth.enabled && (
                      <div className="p-4 pt-3">
                        <div className="flex h-6 items-center">
                          <p className="system-xs-medium text-text-tertiary">{t('publishApp.title', { ns: 'app' })}</p>
                        </div>
                        <div
                          className="flex h-8 cursor-pointer items-center gap-x-0.5  rounded-lg bg-components-input-bg-normal py-1 pl-2.5 pr-2 hover:bg-primary-50 hover:text-text-accent"
                          onClick={() => {
                            setShowAppAccessControl(true)
                          }}
                        >
                          <div className="flex grow items-center gap-x-1.5 overflow-hidden pr-1">
                            <AccessModeDisplay mode={appDetail?.access_mode} />
                          </div>
                          {!isAppAccessSet && <p className="system-xs-regular shrink-0 text-text-tertiary">{t('publishApp.notSet', { ns: 'app' })}</p>}
                          <div className="flex h-4 w-4 shrink-0 items-center justify-center">
                            <RiArrowRightSLine className="h-4 w-4 text-text-quaternary" />
                          </div>
                        </div>
                        {!isAppAccessSet && <p className="system-xs-regular mt-1 text-text-warning">{t('publishApp.notSetDesc', { ns: 'app' })}</p>}
                      </div>
                    )}
                    {
                      // Hide run/batch run app buttons when there is a trigger node.
                      !hasTriggerNode && (
                        <div className="flex flex-col gap-y-1 border-t-[0.5px] border-t-divider-regular p-4 pt-3">
                          <Tooltip triggerClassName="flex" disabled={!disabledFunctionButton} popupContent={disabledFunctionTooltip} asChild={false}>
                            <SuggestedAction
                              className="flex-1"
                              disabled={disabledFunctionButton}
                              onClick={() => {
                                if (publishedAt)
                                  handleRunApp()
                              }}
                              icon={<RiPlayCircleLine className="h-4 w-4" />}
                            >
                              {t('common.runApp', { ns: 'workflow' })}
                            </SuggestedAction>
                          </Tooltip>
                          {appDetail?.mode === AppModeEnum.WORKFLOW || appDetail?.mode === AppModeEnum.COMPLETION
                            ? (
                                <Tooltip triggerClassName="flex" disabled={!disabledFunctionButton} popupContent={disabledFunctionTooltip} asChild={false}>
                                  <SuggestedAction
                                    className="flex-1"
                                    disabled={disabledFunctionButton}
                                    link={`${appURL}${appURL.includes('?') ? '&' : '?'}mode=batch`}
                                    icon={<RiPlayList2Line className="h-4 w-4" />}
                                  >
                                    {t('common.batchRunApp', { ns: 'workflow' })}
                                  </SuggestedAction>
                                </Tooltip>
                              )
                            : (
                                <SuggestedAction
                                  onClick={() => {
                                    setEmbeddingModalOpen(true)
                                    handleTrigger()
                                  }}
                                  disabled={!publishedAt}
                                  icon={<CodeBrowser className="h-4 w-4" />}
                                >
                                  {t('common.embedIntoSite', { ns: 'workflow' })}
                                </SuggestedAction>
                              )}
                          <Tooltip triggerClassName="flex" disabled={!disabledFunctionButton} popupContent={disabledFunctionTooltip} asChild={false}>
                            <SuggestedAction
                              className="flex-1"
                              onClick={() => {
                                if (publishedAt)
                                  handleOpenInExplore()
                              }}
                              disabled={disabledFunctionButton}
                              icon={<RiPlanetLine className="h-4 w-4" />}
                            >
                              {t('common.openInExplore', { ns: 'workflow' })}
                            </SuggestedAction>
                          </Tooltip>
                          <Tooltip triggerClassName="flex" disabled={!!publishedAt && !missingStartNode} popupContent={!publishedAt ? t('notPublishedYet', { ns: 'app' }) : t('noUserInputNode', { ns: 'app' })} asChild={false}>
                            <SuggestedAction
                              className="flex-1"
                              disabled={!publishedAt || missingStartNode}
                              link={appDevelopURL}
                              icon={<RiTerminalBoxLine className="h-4 w-4" />}
                            >
                              {t('common.accessAPIReference', { ns: 'workflow' })}
                            </SuggestedAction>
                          </Tooltip>
                          {appDetail?.mode === AppModeEnum.WORKFLOW && (
                            <WorkflowToolConfigureButton
                              disabled={workflowToolDisabled}
                              published={!!toolPublished}
                              detailNeedUpdate={!!toolPublished && published}
                              workflowAppId={appDetail?.id}
                              icon={{
                                content: (appDetail.icon_type === 'image' ? '🤖' : appDetail?.icon) || '🤖',
                                background: (appDetail.icon_type === 'image' ? appDefaultIconBackground : appDetail?.icon_background) || appDefaultIconBackground,
                              }}
                              name={appDetail?.name}
                              description={appDetail?.description}
                              inputs={inputs}
                              outputs={outputs}
                              handlePublish={handlePublish}
                              onRefreshData={onRefreshData}
                              disabledReason={workflowToolMessage}
                            />
                          )}
                        </div>
                      )
                    }
                  </>
                )}
          </div>
        </PortalToFollowElemContent>
        <EmbeddedModal
          siteInfo={appDetail?.site}
          isShow={embeddingModalOpen}
          onClose={() => setEmbeddingModalOpen(false)}
          appBaseUrl={appBaseURL}
          accessToken={accessToken}
        />
        {showAppAccessControl && <AccessControl app={appDetail!} onConfirm={handleAccessControlUpdate} onClose={() => { setShowAppAccessControl(false) }} />}
        <Modal
          isShow={recallModalOpen}
          onClose={() => {
            if (recallSubmitting)
              return
            setRecallModalOpen(false)
          }}
          title="回收 Agent"
          description="请输入回收原因。回收后，Agent 将从对外可用状态撤回。"
          closable
        >
          <div className="mt-4">
            <Textarea
              value={recallReason}
              onChange={e => setRecallReason(e.target.value)}
              placeholder="请输入回收原因"
              className="min-h-[120px]"
            />
          </div>
          <div className="mt-6 flex justify-end gap-2">
            <Button
              onClick={() => setRecallModalOpen(false)}
              disabled={recallSubmitting}
            >
              取消
            </Button>
            <Button
              variant="primary"
              destructive
              loading={recallSubmitting}
              disabled={!recallReason.trim()}
              onClick={() => handleRecall(recallReason)}
            >
              确认回收
            </Button>
          </div>
        </Modal>
      </PortalToFollowElem>
    </>
  )
}

export default memo(AppPublisher)
