'use client'

import type { DuplicateAppModalProps } from '@/app/components/app/duplicate-modal'
import type { HtmlContentProps } from '@/app/components/base/popover'
import type { Tag } from '@/app/components/base/tag-management/constant'
import type { CreateAppModalProps } from '@/app/components/explore/create-app-modal'
import type { EnvironmentVariable } from '@/app/components/workflow/types'
import type { App } from '@/types/app'
import { RiBuildingLine, RiGlobalLine, RiLockLine, RiMoreFill, RiShareForwardLine, RiVerifiedBadgeLine } from '@remixicon/react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import * as React from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import { AppTypeIcon } from '@/app/components/app/type-selector'
import AppIcon from '@/app/components/base/app-icon'
import Divider from '@/app/components/base/divider'
import CustomPopover from '@/app/components/base/popover'
import TagSelector from '@/app/components/base/tag-management/selector'
import Toast, { ToastContext } from '@/app/components/base/toast'
import Tooltip from '@/app/components/base/tooltip'
import { NEED_REFRESH_APP_LIST_KEY } from '@/config'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useProviderContext } from '@/context/provider-context'
import { useAsyncWindowOpen } from '@/hooks/use-async-window-open'
import { AccessMode } from '@/models/access-control'
import { useGetUserCanAccessApp } from '@/service/access-control'
import { copyApp, deleteApp, exportAppConfig, updateAppInfo } from '@/service/apps'
import { fetchInstalledAppList } from '@/service/explore'
import { useInvalidateAppList } from '@/service/use-apps'
import { fetchWorkflowDraft } from '@/service/workflow'
import { AppModeEnum } from '@/types/app'
import { getRedirection } from '@/utils/app-redirection'
import { cn } from '@/utils/classnames'
import { downloadBlob } from '@/utils/download'
import { formatTime } from '@/utils/time'
import { basePath } from '@/utils/var'
import SharePosterModal from '../app/overview/share-poster-modal'

const EditAppModal = dynamic(() => import('@/app/components/explore/create-app-modal'), {
  ssr: false,
})
const DuplicateAppModal = dynamic(() => import('@/app/components/app/duplicate-modal'), {
  ssr: false,
})
const SwitchAppModal = dynamic(() => import('@/app/components/app/switch-app-modal'), {
  ssr: false,
})
const Confirm = dynamic(() => import('@/app/components/base/confirm'), {
  ssr: false,
})
const DSLExportConfirmModal = dynamic(() => import('@/app/components/workflow/dsl-export-confirm-modal'), {
  ssr: false,
})
const AccessControl = dynamic(() => import('@/app/components/app/app-access-control'), {
  ssr: false,
})

const getAppPublishStatus = (app: App) => {
  const isWorkflowBackedApp = app.mode === AppModeEnum.WORKFLOW || app.mode === AppModeEnum.ADVANCED_CHAT
  const isConfigurationReady = app.is_configuration_ready ?? (isWorkflowBackedApp ? Boolean(app.workflow?.id) : Boolean(app.model_config || app.app_model_config))

  if (app.publish_status) {
    if (app.publish_status === 'published' && !isConfigurationReady) {
      return {
        label: '未发布',
        description: '当前配置不完整，应用暂不可用',
        className: 'border border-slate-200 bg-slate-50 text-slate-600',
        dotClassName: 'bg-slate-400',
      }
    }

    if (app.publish_status === 'pending') {
      return {
        label: '待发布',
        description: app.publish_status_description || '当前存在未发布改动',
        className: 'border border-[#fcd34d] bg-[#fef3c7] text-[#92400e]',
        dotClassName: 'bg-amber-400',
      }
    }

    if (app.publish_status === 'published') {
      return {
        label: '已发布',
        description: app.publish_status_description || '当前版本已可对外使用',
        className: 'border border-[#a7f3d0] bg-[#d1fae5] text-[#065f46]',
        dotClassName: 'bg-[#10b981]',
      }
    }

    if (app.publish_status === 'recalled') {
      return {
        label: '已回收',
        description: app.publish_status_description || '当前已被回收，暂不可用',
        className: 'border border-red-200 bg-red-50 text-red-600',
        dotClassName: 'bg-red-500',
      }
    }

    return {
      label: '未发布',
      description: app.publish_status_description || '当前已配置，但尚未对外发布',
      className: 'border border-slate-200 bg-slate-50 text-slate-600',
      dotClassName: 'bg-slate-400',
    }
  }

  if (!isConfigurationReady) {
    return {
      label: '未发布',
      description: '当前配置不完整，应用暂不可用',
      className: 'border border-slate-200 bg-slate-50 text-slate-600',
      dotClassName: 'bg-slate-400',
    }
  }

  if (app.has_draft_trigger) {
    return {
      label: '待发布',
      description: '当前存在未发布改动',
      className: 'border border-[#fcd34d] bg-[#fef3c7] text-[#92400e]',
      dotClassName: 'bg-amber-400',
    }
  }

  if (app.enable_site || app.enable_api) {
    return {
      label: '已发布',
      description: '当前版本已可对外使用',
      className: 'border border-[#a7f3d0] bg-[#d1fae5] text-[#065f46]',
      dotClassName: 'bg-[#10b981]',
    }
  }

  return {
    label: '未发布',
    description: '当前已配置，但尚未对外发布',
    className: 'border border-slate-200 bg-slate-50 text-slate-600',
    dotClassName: 'bg-slate-400',
  }
}

const isAppUnavailableForExplore = (app: App) => {
  const publishStatus = getAppPublishStatus(app).label
  return publishStatus === '未发布' || publishStatus === '已回收' || publishStatus === '待发布'
}

export type AppCardProps = {
  app: App
  onRefresh?: () => void
}

const AppCard = ({ app, onRefresh }: AppCardProps) => {
  const { t } = useTranslation()
  const { notify } = useContext(ToastContext)
  const systemFeatures = useGlobalPublicStore(s => s.systemFeatures)
  const { canEditApps, canViewWorkflow, canEditWorkflow, isCurrentWorkspaceManager, isCurrentWorkspaceDatasetOperator } = useAppContext()
  const { onPlanInfoChanged } = useProviderContext()
  const invalidateAppList = useInvalidateAppList()
  const { push } = useRouter()
  const openAsyncWindow = useAsyncWindowOpen()

  const [showEditModal, setShowEditModal] = useState(false)
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)
  const [showSwitchModal, setShowSwitchModal] = useState<boolean>(false)
  const [showConfirmDelete, setShowConfirmDelete] = useState(false)
  const [showAccessControl, setShowAccessControl] = useState(false)
  const [showUnavailableConfirm, setShowUnavailableConfirm] = useState(false)
  const [showSharePosterModal, setShowSharePosterModal] = useState(false)
  const [secretEnvList, setSecretEnvList] = useState<EnvironmentVariable[]>([])

  const onConfirmDelete = useCallback(async () => {
    try {
      await deleteApp(app.id)
      notify({ type: 'success', message: t('appDeleted', { ns: 'app' }) })
      if (onRefresh)
        onRefresh()
      onPlanInfoChanged()
    }
    catch (e: any) {
      notify({
        type: 'error',
        message: `${t('appDeleteFailed', { ns: 'app' })}${'message' in e ? `: ${e.message}` : ''}`,
      })
    }
    setShowConfirmDelete(false)
  }, [app.id, notify, onPlanInfoChanged, onRefresh, t])

  const onEdit: CreateAppModalProps['onConfirm'] = useCallback(async ({
    name,
    icon_type,
    icon,
    icon_background,
    description,
    use_icon_as_answer_icon,
    max_active_requests,
  }) => {
    try {
      await updateAppInfo({
        appID: app.id,
        name,
        icon_type,
        icon,
        icon_background,
        description,
        use_icon_as_answer_icon,
        max_active_requests,
      })
      setShowEditModal(false)
      notify({
        type: 'success',
        message: t('editDone', { ns: 'app' }),
      })
      localStorage.setItem(NEED_REFRESH_APP_LIST_KEY, '1')
      invalidateAppList()
      if (onRefresh)
        onRefresh()
    }
    catch (e: any) {
      notify({
        type: 'error',
        message: e.message || t('editFailed', { ns: 'app' }),
      })
    }
  }, [app.id, invalidateAppList, notify, onRefresh, t])

  const onCopy: DuplicateAppModalProps['onConfirm'] = async ({ name, icon_type, icon, icon_background }) => {
    try {
      const newApp = await copyApp({
        appID: app.id,
        name,
        icon_type,
        icon,
        icon_background,
        mode: app.mode,
      })
      setShowDuplicateModal(false)
      notify({
        type: 'success',
        message: t('newApp.appCreated', { ns: 'app' }),
      })
      localStorage.setItem(NEED_REFRESH_APP_LIST_KEY, '1')
      if (onRefresh)
        onRefresh()
      onPlanInfoChanged()
      getRedirection({
        canEditApp: canEditApps,
        canViewWorkflow,
        canEditWorkflow,
      }, newApp, push)
    }
    catch {
      notify({ type: 'error', message: t('newApp.appCreateFailed', { ns: 'app' }) })
    }
  }

  const onExport = async (include = false) => {
    try {
      const { data } = await exportAppConfig({
        appID: app.id,
        include,
      })
      const file = new Blob([data], { type: 'application/yaml' })
      downloadBlob({ data: file, fileName: `${app.name}.yml` })
    }
    catch {
      notify({ type: 'error', message: t('exportFailed', { ns: 'app' }) })
    }
  }

  const exportCheck = async () => {
    if (app.mode !== AppModeEnum.WORKFLOW && app.mode !== AppModeEnum.ADVANCED_CHAT) {
      onExport()
      return
    }
    try {
      const workflowDraft = await fetchWorkflowDraft(`/apps/${app.id}/workflows/draft`)
      const list = (workflowDraft.environment_variables || []).filter(env => env.value_type === 'secret')
      if (list.length === 0) {
        onExport()
        return
      }
      setSecretEnvList(list)
    }
    catch {
      notify({ type: 'error', message: t('exportFailed', { ns: 'app' }) })
    }
  }

  const onSwitch = () => {
    if (onRefresh)
      onRefresh()
    setShowSwitchModal(false)
  }

  const getExploreInstalledPath = useCallback(async () => {
    const { installed_apps }: any = await fetchInstalledAppList(app.id) || {}
    if (installed_apps?.length > 0)
      return `${basePath}/explore/installed/${installed_apps[0].id}`
    return null
  }, [app.id])

  const openApp = useCallback(async () => {
    if (isAppUnavailableForExplore(app)) {
      setShowUnavailableConfirm(true)
      return
    }

    if (!app.has_draft_trigger) {
      try {
        const installedPath = await getExploreInstalledPath()
        if (installedPath) {
          push(installedPath)
          return
        }
      }
      catch {
      }
    }

    getRedirection({
      canEditApp: canEditApps,
      canViewWorkflow,
      canEditWorkflow,
    }, app, push)
  }, [app, canEditApps, canEditWorkflow, canViewWorkflow, getExploreInstalledPath, notify, push])

  const canOpenEditPage = isCurrentWorkspaceManager || isCurrentWorkspaceDatasetOperator

  const onUpdateAccessControl = useCallback(() => {
    if (onRefresh)
      onRefresh()
    setShowAccessControl(false)
  }, [onRefresh, setShowAccessControl])

  const Operations = (props: HtmlContentProps) => {
    const { data: userCanAccessApp, isLoading: isGettingUserCanAccessApp } = useGetUserCanAccessApp({ appId: app?.id, enabled: (!!props?.open && systemFeatures.webapp_auth.enabled) })
    const onMouseLeave = async () => {
      props.onClose?.()
    }
    const onClickSettings = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      setShowEditModal(true)
    }
    const onClickOpenEditPage = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      getRedirection({
        canEditApp: canEditApps,
        canViewWorkflow,
        canEditWorkflow,
      }, app, push)
    }
    const onClickDuplicate = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      setShowDuplicateModal(true)
    }
    const onClickExport = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      exportCheck()
    }
    const onClickSwitch = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      setShowSwitchModal(true)
    }
    const onClickDelete = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      setShowConfirmDelete(true)
    }
    const onClickAccessControl = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      setShowAccessControl(true)
    }
    const onClickInstalledApp = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      props.onClick?.()
      e.preventDefault()
      try {
        await openAsyncWindow(async () => {
          const installedPath = await getExploreInstalledPath()
          if (installedPath)
            return installedPath
          throw new Error('No app found in Explore')
        }, {
          onError: (err) => {
            Toast.notify({ type: 'error', message: `${err.message || err}` })
          },
        })
      }
      catch (e: any) {
        Toast.notify({ type: 'error', message: `${e.message || e}` })
      }
    }
    return (
      <div className="relative flex w-full flex-col py-1" onMouseLeave={onMouseLeave}>
        <button type="button" className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickSettings}>
          <span className="system-sm-regular text-text-secondary">{t('editApp', { ns: 'app' })}</span>
        </button>
        {canOpenEditPage && (
          <button type="button" className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickOpenEditPage}>
            <span className="system-sm-regular text-text-secondary">{t('openEditPage', { ns: 'app' })}</span>
          </button>
        )}
        <Divider className="my-1" />
        <button type="button" className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickDuplicate}>
          <span className="system-sm-regular text-text-secondary">{t('duplicate', { ns: 'app' })}</span>
        </button>
        <button type="button" className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickExport}>
          <span className="system-sm-regular text-text-secondary">{t('export', { ns: 'app' })}</span>
        </button>
        {!isAppUnavailableForExplore(app) && (
          <button
            type="button"
            className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover"
            onClick={(e) => {
              e.stopPropagation()
              props.onClick?.()
              e.preventDefault()
              setShowSharePosterModal(true)
            }}
          >
            <RiShareForwardLine className="h-4 w-4 text-text-tertiary" />
            <span className="system-sm-regular text-text-secondary">分享海报</span>
          </button>
        )}
        {(app.mode === AppModeEnum.COMPLETION || app.mode === AppModeEnum.CHAT) && (
          <>
            <Divider className="my-1" />
            <button
              type="button"
              className="mx-1 flex h-8 cursor-pointer items-center rounded-lg px-3 hover:bg-state-base-hover"
              onClick={onClickSwitch}
            >
              <span className="text-sm leading-5 text-text-secondary">{t('switch', { ns: 'app' })}</span>
            </button>
          </>
        )}
        {
          !app.has_draft_trigger && !isAppUnavailableForExplore(app) && (
            (!systemFeatures.webapp_auth.enabled)
              ? (
                  <>
                    <Divider className="my-1" />
                    <button type="button" className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickInstalledApp}>
                      <span className="system-sm-regular text-text-secondary">{t('openInExplore', { ns: 'app' })}</span>
                    </button>
                  </>
                )
              : !(isGettingUserCanAccessApp || !userCanAccessApp?.result) && (
                  <>
                    <Divider className="my-1" />
                    <button type="button" className="mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickInstalledApp}>
                      <span className="system-sm-regular text-text-secondary">{t('openInExplore', { ns: 'app' })}</span>
                    </button>
                  </>
                )
          )
        }
        <Divider className="my-1" />
        {
          systemFeatures.webapp_auth.enabled && canEditApps && (
            <>
              <button type="button" className="mx-1 flex h-8 cursor-pointer items-center rounded-lg px-3 hover:bg-state-base-hover" onClick={onClickAccessControl}>
                <span className="text-sm leading-5 text-text-secondary">{t('accessControl', { ns: 'app' })}</span>
              </button>
              <Divider className="my-1" />
            </>
          )
        }
        <button
          type="button"
          className="group mx-1 flex h-8 cursor-pointer items-center gap-2 rounded-lg px-3 py-[6px] hover:bg-state-destructive-hover"
          onClick={onClickDelete}
        >
          <span className="system-sm-regular text-text-secondary group-hover:text-text-destructive">
            {t('operation.delete', { ns: 'common' })}
          </span>
        </button>
      </div>
    )
  }

  const [tags, setTags] = useState<Tag[]>(app.tags)
  useEffect(() => {
    setTags(app.tags)
  }, [app.tags])

  const EditTimeText = useMemo(() => {
    const timeText = formatTime({
      date: (app.updated_at || app.created_at) * 1000,
      dateFormat: `${t('segment.dateTimeFormat', { ns: 'datasetDocuments' })}`,
    })
    return `${t('segment.editedAt', { ns: 'datasetDocuments' })} ${timeText}`
  }, [app.updated_at, app.created_at, t])

  const publishStatus = useMemo(() => getAppPublishStatus(app), [app])

  return (
    <>
      <div
        onClick={async (e) => {
          e.preventDefault()
          await openApp()
        }}
        className="group relative col-span-1 inline-flex h-[160px] cursor-pointer flex-col rounded-xl border-[1px] border-solid border-components-card-border bg-components-card-bg shadow-sm transition-all duration-200 ease-in-out hover:shadow-lg"
      >
        <div className="flex min-h-[82px] shrink-0 grow-0 items-start gap-3 px-[14px] pb-3 pt-[14px]">
          <div className="relative shrink-0">
            <AppIcon
              size="large"
              iconType={app.icon_type}
              icon={app.icon}
              background={app.icon_background}
              imageUrl={app.icon_url}
            />
            <AppTypeIcon type={app.mode} wrapperClassName="absolute -bottom-0.5 -right-0.5 w-4 h-4 shadow-sm" className="h-3 w-3" />
          </div>
          <div className="w-0 grow py-[1px]">
            <div className="flex items-center text-sm font-semibold leading-5 text-text-secondary">
              <div className="truncate" title={app.name}>{app.name}</div>
            </div>
            <div className="flex items-center gap-1 text-[10px] font-medium leading-[18px] text-text-tertiary">
              <div className="truncate" title={app.author_name}>{app.author_name}</div>
              <div>·</div>
              <div className="truncate" title={EditTimeText}>{EditTimeText}</div>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <div
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold shadow-sm',
                  publishStatus.className,
                )}
                title={publishStatus.description}
              >
                <span className={cn('h-1.5 w-1.5 rounded-full', publishStatus.dotClassName)} />
                <span>{publishStatus.label}</span>
              </div>
              <span className="truncate text-[10px] leading-[16px] text-text-quaternary">
                {publishStatus.description}
              </span>
            </div>
          </div>
          <div className="flex h-5 w-5 shrink-0 items-center justify-center pt-1">
            {app.access_mode === AccessMode.PUBLIC && (
              <Tooltip asChild={false} popupContent={t('accessItemsDescription.anyone', { ns: 'app' })}>
                <RiGlobalLine className="h-4 w-4 text-text-quaternary" />
              </Tooltip>
            )}
            {app.access_mode === AccessMode.SPECIFIC_GROUPS_MEMBERS && (
              <Tooltip asChild={false} popupContent={t('accessItemsDescription.specific', { ns: 'app' })}>
                <RiLockLine className="h-4 w-4 text-text-quaternary" />
              </Tooltip>
            )}
            {app.access_mode === AccessMode.ORGANIZATION && (
              <Tooltip asChild={false} popupContent={t('accessItemsDescription.organization', { ns: 'app' })}>
                <RiBuildingLine className="h-4 w-4 text-text-quaternary" />
              </Tooltip>
            )}
            {app.access_mode === AccessMode.EXTERNAL_MEMBERS && (
              <Tooltip asChild={false} popupContent={t('accessItemsDescription.external', { ns: 'app' })}>
                <RiVerifiedBadgeLine className="h-4 w-4 text-text-quaternary" />
              </Tooltip>
            )}
          </div>
        </div>
        <div className="title-wrapper h-[90px] px-[14px] text-xs leading-normal text-text-tertiary">
          <div
            className="line-clamp-2"
            title={app.description}
          >
            {app.description}
          </div>
        </div>
        <div className="absolute bottom-1 left-0 right-0 flex h-[42px] shrink-0 items-center pb-[6px] pl-[14px] pr-[6px] pt-1">
          {canEditApps && (
            <>
              <div
                className={cn('flex w-0 grow items-center gap-1')}
                onClick={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                }}
              >
                <div className="mr-[41px] w-full grow group-hover:!mr-0">
                  <TagSelector
                    position="bl"
                    type="app"
                    targetID={app.id}
                    value={tags.map(tag => tag.id)}
                    selectedTags={tags}
                    onCacheUpdate={setTags}
                    onChange={onRefresh}
                  />
                </div>
              </div>
              <div className="mx-1 !hidden h-[14px] w-[1px] shrink-0 bg-divider-regular group-hover:!flex" />
              <div className="!hidden shrink-0 group-hover:!flex">
                <CustomPopover
                  htmlContent={<Operations />}
                  position="br"
                  trigger="click"
                  btnElement={(
                    <div
                      className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-md"
                    >
                      <RiMoreFill className="h-4 w-4 text-text-tertiary" />
                    </div>
                  )}
                  btnClassName={open =>
                    cn(
                      open ? '!bg-state-base-hover !shadow-none' : '!bg-transparent',
                      'h-8 w-8 rounded-md border-none !p-2 hover:!bg-state-base-hover',
                    )}
                  popupClassName={
                    (app.mode === AppModeEnum.COMPLETION || app.mode === AppModeEnum.CHAT)
                      ? '!w-[256px] translate-x-[-224px]'
                      : '!w-[216px] translate-x-[-128px]'
                  }
                  className="!z-20 h-fit"
                />
              </div>
            </>
          )}
          {!isAppUnavailableForExplore(app) && (
            <button
              type="button"
              className="ml-auto flex h-8 shrink-0 items-center gap-1.5 rounded-md px-2 text-xs font-medium text-text-accent hover:bg-state-accent-hover"
              onClick={(e) => {
                e.stopPropagation()
                e.preventDefault()
                setShowSharePosterModal(true)
              }}
            >
              <RiShareForwardLine className="h-4 w-4" />
              分享海报
            </button>
          )}
        </div>
      </div>
      {showEditModal && (
        <EditAppModal
          isEditModal
          appName={app.name}
          appIconType={app.icon_type}
          appIcon={app.icon}
          appIconBackground={app.icon_background}
          appIconUrl={app.icon_url}
          appDescription={app.description}
          appMode={app.mode}
          appUseIconAsAnswerIcon={app.use_icon_as_answer_icon}
          max_active_requests={app.max_active_requests ?? null}
          show={showEditModal}
          onConfirm={onEdit}
          onHide={() => setShowEditModal(false)}
        />
      )}
      {showDuplicateModal && (
        <DuplicateAppModal
          appName={app.name}
          icon_type={app.icon_type}
          icon={app.icon}
          icon_background={app.icon_background}
          icon_url={app.icon_url}
          show={showDuplicateModal}
          onConfirm={onCopy}
          onHide={() => setShowDuplicateModal(false)}
        />
      )}
      {showSwitchModal && (
        <SwitchAppModal
          show={showSwitchModal}
          appDetail={app}
          onClose={() => setShowSwitchModal(false)}
          onSuccess={onSwitch}
        />
      )}
      {showConfirmDelete && (
        <Confirm
          title={t('deleteAppConfirmTitle', { ns: 'app' })}
          content={t('deleteAppConfirmContent', { ns: 'app' })}
          isShow={showConfirmDelete}
          onConfirm={onConfirmDelete}
          onCancel={() => setShowConfirmDelete(false)}
        />
      )}
      {showUnavailableConfirm && (
        <Confirm
          isShow={showUnavailableConfirm}
          type="info"
          title="智能体暂未发布"
          content="该智能体暂未发布，如有需要，请联系管理员。"
          confirmText="我知道了"
          showCancel={false}
          onConfirm={() => setShowUnavailableConfirm(false)}
          onCancel={() => setShowUnavailableConfirm(false)}
        />
      )}
      <SharePosterModal
        isShow={showSharePosterModal}
        onClose={() => setShowSharePosterModal(false)}
        appInfo={app}
      />
      {secretEnvList.length > 0 && (
        <DSLExportConfirmModal
          envList={secretEnvList}
          onConfirm={onExport}
          onClose={() => setSecretEnvList([])}
        />
      )}
      {showAccessControl && (
        <AccessControl app={app} onConfirm={onUpdateAccessControl} onClose={() => setShowAccessControl(false)} />
      )}
    </>
  )
}

export default React.memo(AppCard)
