'use client'
import type { FC } from 'react'
import type { InstalledApp } from '@/models/explore'
import type { Item as SelectItem } from '@/app/components/base/select'
import { RiAppsFill, RiArrowDownSLine, RiArrowRightSLine, RiExpandRightLine, RiLayoutLeft2Line } from '@remixicon/react'
import { useBoolean } from 'ahooks'
import Link from 'next/link'
import { useSelectedLayoutSegments } from 'next/navigation'
import * as React from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import Confirm from '@/app/components/base/confirm'
import Divider from '@/app/components/base/divider'
import { SimpleSelect } from '@/app/components/base/select'
import ExploreContext from '@/context/explore-context'
import useBreakpoints, { MediaType } from '@/hooks/use-breakpoints'
import { useGetInstalledApps, useUninstallApp, useUpdateAppPinStatus } from '@/service/use-explore'
import { cn } from '@/utils/classnames'
import Toast from '../../base/toast'
import Item from './app-nav-item'
import NoApps from './no-apps'

export type IExploreSideBarProps = {
  controlUpdateInstalledApps: number
}

// 分组类型
type GroupType = 'category' | 'mode' | 'none'

const SideBar: FC<IExploreSideBarProps> = ({
  controlUpdateInstalledApps,
}) => {
  const { t } = useTranslation()
  const segments = useSelectedLayoutSegments()
  const lastSegment = segments.slice(-1)[0]
  const isDiscoverySelected = lastSegment === 'apps'
  const { installedApps, setInstalledApps, setIsFetchingInstalledApps } = useContext(ExploreContext)
  const { isFetching: isFetchingInstalledApps, data: ret, refetch: fetchInstalledAppList } = useGetInstalledApps()
  const { mutateAsync: uninstallApp } = useUninstallApp()
  const { mutateAsync: updatePinStatus } = useUpdateAppPinStatus()

  const media = useBreakpoints()
  const isMobile = media === MediaType.mobile
  const [isFold, {
    toggle: toggleIsFold,
  }] = useBoolean(false)

  const [showConfirm, setShowConfirm] = useState(false)
  const [currId, setCurrId] = useState('')
  
  // 分组相关状态
  const [groupBy, setGroupBy] = useState<GroupType>(() => {
    // 从 localStorage 读取上次的选择
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('explore-sidebar-group-by')
      if (saved && ['none', 'category', 'mode'].includes(saved))
        return saved as GroupType
    }
    return 'none'
  })
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

  // 分组选项
  const groupOptions: SelectItem[] = [
    { value: 'none', name: '不分组' },
    { value: 'category', name: '按标签' },
    { value: 'mode', name: '按类型' },
  ]

  // 保存分组选择到 localStorage
  useEffect(() => {
    if (typeof window !== 'undefined')
      localStorage.setItem('explore-sidebar-group-by', groupBy)
  }, [groupBy])

  // 切换分组折叠状态
  const toggleGroup = useCallback((groupKey: string) => {
    setCollapsedGroups((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(groupKey))
        newSet.delete(groupKey)
      else
        newSet.add(groupKey)

      return newSet
    })
  }, [])

  // 分组逻辑
  const groupedApps = useMemo(() => {
    if (groupBy === 'none') {
      return { ungrouped: installedApps }
    }

    const groups: Record<string, InstalledApp[]> = {}

    installedApps.forEach((app) => {
      let groupKey: string

      if (groupBy === 'category') {
        // 按标签分组：根据 mode 映射到标签
        const mode = app.app.mode
        const categoryMap: Record<string, string> = {
          'chat': '对话助手',
          'agent-chat': '智能体',
          'advanced-chat': '高级对话',
          'workflow': '工作流',
          'completion': '文本生成',
        }
        groupKey = categoryMap[mode] || '其他'
      }
      else if (groupBy === 'mode') {
        // 按类型分组：使用原始 mode 值
        const mode = app.app.mode
        const modeNames: Record<string, string> = {
          'chat': '对话型',
          'agent-chat': '智能体型',
          'advanced-chat': '高级对话型',
          'workflow': '工作流型',
          'completion': '文本生成型',
        }
        groupKey = modeNames[mode] || mode || '其他'
      }
      else {
        groupKey = 'ungrouped'
      }

      if (!groups[groupKey])
        groups[groupKey] = []

      groups[groupKey].push(app)
    })

    return groups
  }, [installedApps, groupBy])

  const handleDelete = async () => {
    const id = currId
    await uninstallApp(id)
    setShowConfirm(false)
    Toast.notify({
      type: 'success',
      message: t('api.remove', { ns: 'common' }),
    })
  }

  const handleUpdatePinStatus = async (id: string, isPinned: boolean) => {
    await updatePinStatus({ appId: id, isPinned })
    Toast.notify({
      type: 'success',
      message: t('api.success', { ns: 'common' }),
    })
  }

  useEffect(() => {
    const installed_apps = (ret as any)?.installed_apps
    if (installed_apps && installed_apps.length > 0)
      setInstalledApps(installed_apps)
    else
      setInstalledApps([])
  }, [ret, setInstalledApps])

  useEffect(() => {
    setIsFetchingInstalledApps(isFetchingInstalledApps)
  }, [isFetchingInstalledApps, setIsFetchingInstalledApps])

  useEffect(() => {
    fetchInstalledAppList()
  }, [controlUpdateInstalledApps, fetchInstalledAppList])

  const pinnedAppsCount = installedApps.filter(({ is_pinned }) => is_pinned).length

  // 渲染应用列表项
  const renderAppItem = (app: InstalledApp, index?: number, showDivider?: boolean) => {
    const { id, is_pinned, uninstallable, app: { name, icon_type, icon, icon_url, icon_background } } = app
    return (
      <React.Fragment key={id}>
        <Item
          isMobile={isMobile || isFold}
          name={name}
          icon_type={icon_type}
          icon={icon}
          icon_background={icon_background}
          icon_url={icon_url}
          id={id}
          isSelected={lastSegment?.toLowerCase() === id}
          isPinned={is_pinned}
          togglePin={() => handleUpdatePinStatus(id, !is_pinned)}
          uninstallable={uninstallable}
          onDelete={(id) => {
            setCurrId(id)
            setShowConfirm(true)
          }}
        />
        {showDivider && <Divider />}
      </React.Fragment>
    )
  }

  // 渲染分组内容
  const renderGroupedContent = () => {
    if (groupBy === 'none') {
      return (
        <div
          className="space-y-0.5 overflow-y-auto overflow-x-hidden"
          style={{
            height: 'calc(100vh - 250px)',
          }}
        >
          {installedApps.map((app, index) =>
            renderAppItem(
              app,
              index,
              index === pinnedAppsCount - 1 && index !== installedApps.length - 1,
            ),
          )}
        </div>
      )
    }

    // 分组显示
    return (
      <div
        className="space-y-2 overflow-y-auto overflow-x-hidden"
        style={{
          height: 'calc(100vh - 290px)',
        }}
      >
        {Object.entries(groupedApps).map(([groupKey, apps]) => {
          const isCollapsed = collapsedGroups.has(groupKey)

          return (
            <div key={groupKey} className="rounded-lg border border-divider-subtle bg-background-section-burn">
              {/* 分组标题 */}
              <button
                onClick={() => toggleGroup(groupKey)}
                className="flex w-full items-center justify-between px-2 py-1.5 text-left transition-colors hover:bg-state-base-hover"
              >
                <div className="flex items-center gap-1.5">
                  {isCollapsed
                    ? <RiArrowRightSLine className="h-4 w-4 text-text-tertiary" />
                    : <RiArrowDownSLine className="h-4 w-4 text-text-tertiary" />}
                  <span className="system-xs-semibold text-text-tertiary">
                    {groupKey}
                  </span>
                  <span className="system-2xs-regular rounded bg-background-default-subtle px-1.5 py-0.5 text-text-quaternary">
                    {apps.length}
                  </span>
                </div>
              </button>

              {/* 分组内容 */}
              {!isCollapsed && (
                <div className="space-y-0.5 px-1 pb-1">
                  {apps.map(app => renderAppItem(app))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn('relative w-fit shrink-0 cursor-pointer px-3 pt-6 sm:w-[240px]', isFold && 'sm:w-[56px]')}>
      <div className={cn(isDiscoverySelected ? 'text-text-accent' : 'text-text-tertiary')}>
        <Link
          href="/explore/apps"
          className={cn(isDiscoverySelected ? 'bg-state-base-active' : 'hover:bg-state-base-hover', 'flex h-8 items-center gap-2 rounded-lg px-1 mobile:w-fit mobile:justify-center pc:w-full pc:justify-start')}
        >
          <div className="flex size-6 shrink-0 items-center justify-center rounded-md bg-components-icon-bg-blue-solid">
            <RiAppsFill className="size-3.5 text-components-avatar-shape-fill-stop-100" />
          </div>
          {!isMobile && !isFold && <div className={cn('truncate', isDiscoverySelected ? 'system-sm-semibold text-components-menu-item-text-active' : 'system-sm-regular text-components-menu-item-text')}>{t('sidebar.title', { ns: 'explore' })}</div>}
        </Link>
      </div>

      {installedApps.length === 0 && !isMobile && !isFold
        && (
          <div className="mt-5">
            <NoApps />
          </div>
        )}

      {installedApps.length > 0 && (
        <div className="mt-5">
          {!isMobile && !isFold && (
            <div className="mb-2 flex items-center justify-between px-2">
              <p className="system-xs-medium-uppercase uppercase text-text-tertiary">{t('sidebar.webApps', { ns: 'explore' })}</p>
              {/* 分组选择器 */}
              <SimpleSelect
                key={groupBy} // 添加 key 强制重新渲染
                wrapperClassName="w-[100px]"
                items={groupOptions}
                defaultValue={groupBy}
                onSelect={(item) => {
                  setGroupBy(item.value as GroupType)
                }}
                allowSearch={false}
              />
            </div>
          )}
          {renderGroupedContent()}
        </div>
      )}

      {!isMobile && (
        <div className="absolute bottom-3 left-3 flex size-8 cursor-pointer items-center justify-center text-text-tertiary" onClick={toggleIsFold}>
          {isFold
            ? <RiExpandRightLine className="size-4.5" />
            : (
                <RiLayoutLeft2Line className="size-4.5" />
              )}
        </div>
      )}

      {showConfirm && (
        <Confirm
          title={t('sidebar.delete.title', { ns: 'explore' })}
          content={t('sidebar.delete.content', { ns: 'explore' })}
          isShow={showConfirm}
          onConfirm={handleDelete}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </div>
  )
}

export default React.memo(SideBar)
