'use client'

import type { CreateAppModalProps } from '@/app/components/explore/create-app-modal'
import type { App } from '@/models/explore'
import type { Item } from '@/app/components/base/select'
import { useDebounceFn } from 'ahooks'
import { useQueryState } from 'nuqs'
import * as React from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext, useContextSelector } from 'use-context-selector'
import { RiArrowDownSLine, RiArrowRightSLine } from '@remixicon/react'
import DSLConfirmModal from '@/app/components/app/create-from-dsl-modal/dsl-confirm-modal'
import Button from '@/app/components/base/button'
import Input from '@/app/components/base/input'
import Loading from '@/app/components/base/loading'
import { SimpleSelect } from '@/app/components/base/select'
import AppCard from '@/app/components/explore/app-card'
import Banner from '@/app/components/explore/banner/banner'
import Category from '@/app/components/explore/category'
import CreateAppModal from '@/app/components/explore/create-app-modal'
import ExploreContext from '@/context/explore-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useImportDSL } from '@/hooks/use-import-dsl'
import {
  DSLImportMode,
} from '@/models/app'
import { fetchAppDetail } from '@/service/explore'
import { useExploreAppList } from '@/service/use-explore'
import { cn } from '@/utils/classnames'
import TryApp from '../try-app'
import s from './style.module.css'

type AppsProps = {
  onSuccess?: () => void
}

// 分组类型
type GroupType = 'status' | 'category' | 'none'

const Apps = ({
  onSuccess,
}: AppsProps) => {
  const { t } = useTranslation()
  const { systemFeatures } = useGlobalPublicStore()
  const { hasEditPermission, installedApps } = useContext(ExploreContext)
  const allCategoriesEn = t('apps.allCategories', { ns: 'explore', lng: 'en' })

  const [keywords, setKeywords] = useState('')
  const [searchKeywords, setSearchKeywords] = useState('')
  const [groupBy, setGroupBy] = useState<GroupType>(() => {
    // 从 localStorage 读取上次的选择
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('explore-apps-group-by')
      if (saved && ['none', 'status', 'category'].includes(saved))
        return saved as GroupType
    }
    return 'none'
  })
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

  // 分组选项
  const groupOptions: Item[] = [
    { value: 'none', name: '不分组' },
    { value: 'status', name: '按状态' },
    { value: 'category', name: '按标签' },
  ]

  // 保存分组选择到 localStorage
  useEffect(() => {
    if (typeof window !== 'undefined')
      localStorage.setItem('explore-apps-group-by', groupBy)
  }, [groupBy])

  const hasFilterCondition = !!keywords
  const handleResetFilter = useCallback(() => {
    setKeywords('')
    setSearchKeywords('')
  }, [])

  const { run: handleSearch } = useDebounceFn(() => {
    setSearchKeywords(keywords)
  }, { wait: 500 })

  const handleKeywordsChange = (value: string) => {
    setKeywords(value)
    handleSearch()
  }

  const [currCategory, setCurrCategory] = useQueryState('category', {
    defaultValue: allCategoriesEn,
  })

  const {
    data,
    isLoading,
    isError,
  } = useExploreAppList()

  const filteredList = useMemo(() => {
    if (!data)
      return []
    return data.allList.filter(item => currCategory === allCategoriesEn || item.category === currCategory)
  }, [data, currCategory, allCategoriesEn])

  const searchFilteredList = useMemo(() => {
    if (!searchKeywords || !filteredList || filteredList.length === 0)
      return filteredList

    const lowerCaseSearchKeywords = searchKeywords.toLowerCase()

    return filteredList.filter(item =>
      item.app && item.app.name && item.app.name.toLowerCase().includes(lowerCaseSearchKeywords),
    )
  }, [searchKeywords, filteredList])

  // 分组逻辑
  const groupedApps = useMemo(() => {
    if (groupBy === 'none') {
      return { ungrouped: searchFilteredList }
    }

    const groups: Record<string, App[]> = {}

    searchFilteredList.forEach((app) => {
      let groupKey: string

      if (groupBy === 'status') {
        groupKey = app.installed ? '已安装' : '未安装'
      }
      else if (groupBy === 'category') {
        groupKey = app.category || '未分类'
      }
      else {
        groupKey = 'ungrouped'
      }

      if (!groups[groupKey])
        groups[groupKey] = []

      groups[groupKey].push(app)
    })

    return groups
  }, [searchFilteredList, groupBy])

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

  const [currApp, setCurrApp] = React.useState<App | null>(null)
  const [isShowCreateModal, setIsShowCreateModal] = React.useState(false)

  const {
    handleImportDSL,
    handleImportDSLConfirm,
    versions,
    isFetching,
  } = useImportDSL()
  const [showDSLConfirmModal, setShowDSLConfirmModal] = useState(false)

  const isShowTryAppPanel = useContextSelector(ExploreContext, ctx => ctx.isShowTryAppPanel)
  const setShowTryAppPanel = useContextSelector(ExploreContext, ctx => ctx.setShowTryAppPanel)
  const hideTryAppPanel = useCallback(() => {
    setShowTryAppPanel(false)
  }, [setShowTryAppPanel])
  const appParams = useContextSelector(ExploreContext, ctx => ctx.currentApp)
  const handleShowFromTryApp = useCallback(() => {
    setCurrApp(appParams?.app || null)
    setIsShowCreateModal(true)
  }, [appParams?.app])

  const onCreate: CreateAppModalProps['onConfirm'] = async ({
    name,
    icon_type,
    icon,
    icon_background,
    description,
  }) => {
    hideTryAppPanel()

    const { export_data } = await fetchAppDetail(
      currApp?.app.id as string,
    )
    const payload = {
      mode: DSLImportMode.YAML_CONTENT,
      yaml_content: export_data,
      name,
      icon_type,
      icon,
      icon_background,
      description,
    }
    await handleImportDSL(payload, {
      onSuccess: () => {
        setIsShowCreateModal(false)
      },
      onPending: () => {
        setShowDSLConfirmModal(true)
      },
    })
  }

  const onConfirmDSL = useCallback(async () => {
    await handleImportDSLConfirm({
      onSuccess,
    })
  }, [handleImportDSLConfirm, onSuccess])

  if (isLoading) {
    return (
      <div className="flex h-full items-center">
        <Loading type="area" />
      </div>
    )
  }

  if (isError || !data)
    return null

  const { categories } = data

  // 渲染分组内容
  const renderGroupedContent = () => {
    if (groupBy === 'none') {
      return (
        <nav
          className={cn(
            s.appList,
            'grid shrink-0 content-start gap-4 px-6 sm:px-12',
          )}
        >
          {searchFilteredList.map(app => (
            <AppCard
              key={app.app_id}
              isExplore
              app={app}
              canCreate={hasEditPermission}
              onCreate={() => {
                setCurrApp(app)
                setIsShowCreateModal(true)
              }}
            />
          ))}
        </nav>
      )
    }

    // 分组显示
    return (
      <div className="space-y-4 px-6 sm:px-12">
        {Object.entries(groupedApps).map(([groupKey, apps]) => {
          const isCollapsed = collapsedGroups.has(groupKey)

          return (
            <div key={groupKey} className="rounded-lg border border-divider-regular bg-background-default">
              {/* 分组标题 */}
              <button
                onClick={() => toggleGroup(groupKey)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-background-default-hover"
              >
                <div className="flex items-center gap-2">
                  {isCollapsed
                    ? <RiArrowRightSLine className="h-5 w-5 text-text-tertiary" />
                    : <RiArrowDownSLine className="h-5 w-5 text-text-tertiary" />}
                  <span className="system-md-semibold text-text-secondary">
                    {groupKey}
                  </span>
                  <span className="system-xs-regular rounded-md bg-background-section px-2 py-0.5 text-text-tertiary">
                    {apps.length}
                  </span>
                </div>
              </button>

              {/* 分组内容 */}
              {!isCollapsed && (
                <div className="border-t border-divider-subtle p-4">
                  <nav
                    className={cn(
                      s.appList,
                      'grid shrink-0 content-start gap-4',
                    )}
                  >
                    {apps.map(app => (
                      <AppCard
                        key={app.app_id}
                        isExplore
                        app={app}
                        canCreate={hasEditPermission}
                        onCreate={() => {
                          setCurrApp(app)
                          setIsShowCreateModal(true)
                        }}
                      />
                    ))}
                  </nav>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn(
      'flex h-full flex-col border-l-[0.5px] border-divider-regular',
    )}
    >
      {systemFeatures.enable_explore_banner && (
        <div className="mt-4 px-12">
          <Banner />
        </div>
      )}
      <div className={cn(
        'mt-6 flex items-center justify-between px-12',
      )}
      >
        <div className="flex items-center gap-3">
          <div className="system-xl-semibold grow truncate text-text-primary">{!hasFilterCondition ? t('apps.title', { ns: 'explore' }) : t('apps.resultNum', { num: searchFilteredList.length, ns: 'explore' })}</div>
          {hasFilterCondition && (
            <>
              <div className="h-4 w-px bg-divider-regular"></div>
              <Button size="medium" onClick={handleResetFilter}>{t('apps.resetFilter', { ns: 'explore' })}</Button>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* 分组选择器 */}
          <SimpleSelect
            key={groupBy} // 添加 key 强制重新渲染
            wrapperClassName="w-[140px]"
            items={groupOptions}
            defaultValue={groupBy}
            onSelect={(item) => {
              setGroupBy(item.value as GroupType)
            }}
            allowSearch={false}
          />
          <Input
            showLeftIcon
            showClearIcon
            wrapperClassName="w-[200px] self-start"
            value={keywords}
            onChange={e => handleKeywordsChange(e.target.value)}
            onClear={() => handleKeywordsChange('')}
          />
        </div>
      </div>

      <div className="mt-2 px-12">
        <Category
          list={categories}
          value={currCategory}
          onChange={setCurrCategory}
          allCategoriesEn={allCategoriesEn}
        />
      </div>

      <div className={cn(
        'relative mt-4 flex flex-1 shrink-0 grow flex-col overflow-auto pb-6',
      )}
      >
        {renderGroupedContent()}
      </div>
      {isShowCreateModal && (
        <CreateAppModal
          appIconType={currApp?.app.icon_type || 'emoji'}
          appIcon={currApp?.app.icon || ''}
          appIconBackground={currApp?.app.icon_background || ''}
          appIconUrl={currApp?.app.icon_url}
          appName={currApp?.app.name || ''}
          appDescription={currApp?.app.description || ''}
          show={isShowCreateModal}
          onConfirm={onCreate}
          confirmDisabled={isFetching}
          onHide={() => setIsShowCreateModal(false)}
        />
      )}
      {
        showDSLConfirmModal && (
          <DSLConfirmModal
            versions={versions}
            onCancel={() => setShowDSLConfirmModal(false)}
            onConfirm={onConfirmDSL}
            confirmDisabled={isFetching}
          />
        )
      }

      {isShowTryAppPanel && (
        <TryApp
          appId={appParams?.appId || ''}
          app={appParams?.app}
          category={appParams?.app?.category}
          onClose={hideTryAppPanel}
          onCreate={handleShowFromTryApp}
        />
      )}
    </div>
  )
}

export default React.memo(Apps)
