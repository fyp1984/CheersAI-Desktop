'use client'

import type { FC } from 'react'
import type { App } from '@/types/app'
import {
  RiDragDropLine,
} from '@remixicon/react'
import { useDebounceFn } from 'ahooks'
import dynamic from 'next/dynamic'
import {
  useRouter,
} from 'next/navigation'
import { parseAsString, useQueryState } from 'nuqs'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Input from '@/app/components/base/input'
import TagFilter from '@/app/components/base/tag-management/filter'
import { useStore as useTagStore } from '@/app/components/base/tag-management/store'
import CheckboxWithLabel from '@/app/components/datasets/create/website/base/checkbox-with-label'
import { NEED_REFRESH_APP_LIST_KEY } from '@/config'
import { useAppContext } from '@/context/app-context'

import { CheckModal } from '@/hooks/use-pay'
import { useInfiniteAppList } from '@/service/use-apps'
import { AppModeEnum } from '@/types/app'
import { cn } from '@/utils/classnames'
import AppCard from './app-card'
import { AppCardSkeleton } from './app-card-skeleton'
import Empty from './empty'

import useAppsQueryState from './hooks/use-apps-query-state'
import { useDSLDragDrop } from './hooks/use-dsl-drag-drop'
import NewAppCard from './new-app-card'

// Define valid tabs at module scope to avoid re-creation on each render and stale closures
const validTabs = new Set<string | AppModeEnum>([
  'all',
  AppModeEnum.WORKFLOW,
  AppModeEnum.ADVANCED_CHAT,
  AppModeEnum.CHAT,
  AppModeEnum.AGENT_CHAT,
  AppModeEnum.COMPLETION,
])

const TagManagementModal = dynamic(() => import('@/app/components/base/tag-management'), {
  ssr: false,
})
const CreateFromDSLModal = dynamic(() => import('@/app/components/app/create-from-dsl-modal'), {
  ssr: false,
})

const UNTAGGED_GROUP_KEY = '__untagged__'
const APP_GRID_CLASS_NAME = 'grid grid-cols-1 gap-4 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-5 2k:grid-cols-6'

type GroupedApps = {
  key: string
  label: string
  apps: App[]
  count: number
  isUntagged: boolean
  order: number
}

const getAppDisplayStatus = (app: App) => {
  if (app.publish_status === 'recalled')
    return 'recalled'
  if (app.publish_status === 'pending')
    return 'pending'
  if (app.publish_status === 'published')
    return 'published'
  return 'unpublished'
}

const sortAppsWithinGroup = (apps: App[]) => {
  const statusRank: Record<string, number> = {
    published: 0,
    pending: 1,
    unpublished: 2,
    recalled: 3,
  }

  return [...apps].sort((left, right) => {
    const statusDiff = statusRank[getAppDisplayStatus(left)] - statusRank[getAppDisplayStatus(right)]
    if (statusDiff !== 0)
      return statusDiff
    return (right.updated_at || 0) - (left.updated_at || 0)
  })
}

const groupAppsByPrimaryTag = (apps: App[], orderedTagIds: string[]) => {
  const tagOrderMap = new Map(orderedTagIds.map((id, index) => [id, index]))
  const groups = new Map<string, GroupedApps>()

  apps.forEach((app) => {
    const sortedTags = [...(app.tags || [])].sort((left, right) => {
      const leftOrder = tagOrderMap.get(left.id) ?? Number.MAX_SAFE_INTEGER
      const rightOrder = tagOrderMap.get(right.id) ?? Number.MAX_SAFE_INTEGER
      return leftOrder - rightOrder
    })
    const primaryTag = sortedTags[0]
    const key = primaryTag?.id || UNTAGGED_GROUP_KEY

    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label: primaryTag?.name || '未分组',
        apps: [],
        count: 0,
        isUntagged: !primaryTag,
        order: primaryTag ? (tagOrderMap.get(primaryTag.id) ?? Number.MAX_SAFE_INTEGER) : Number.MAX_SAFE_INTEGER,
      })
    }

    const group = groups.get(key)!
    group.apps.push(app)
    group.count += 1
  })

  return Array.from(groups.values()).map(group => ({
    ...group,
    apps: sortAppsWithinGroup(group.apps),
  })).sort((left, right) => {
    if (left.isUntagged !== right.isUntagged)
      return left.isUntagged ? 1 : -1

    if (left.order !== right.order)
      return left.order - right.order

    return left.label.localeCompare(right.label, 'zh-Hans-CN')
  })
}

type Props = {
  controlRefreshList?: number
}
const List: FC<Props> = ({
  controlRefreshList = 0,
}) => {
  const { t } = useTranslation()

  const router = useRouter()
  const { isLoadingCurrentWorkspace, canViewWorkflow, canEditWorkflow, canViewApps, canEditApps } = useAppContext()
  const showTagManagementModal = useTagStore(s => s.showTagManagementModal)
  const tagList = useTagStore(s => s.tagList)
  const [activeTab] = useQueryState(
    'category',
    parseAsString.withDefault('all').withOptions({ history: 'push' }),
  )

  const { query: { tagIDs = [], keywords = '', isCreatedByMe: queryIsCreatedByMe = false }, setQuery } = useAppsQueryState()
  const [isCreatedByMe, setIsCreatedByMe] = useState(queryIsCreatedByMe)
  const [tagFilterValue, setTagFilterValue] = useState<string[]>(tagIDs)
  const [searchKeywords, setSearchKeywords] = useState(keywords)
  const newAppCardRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [showCreateFromDSLModal, setShowCreateFromDSLModal] = useState(false)
  const [droppedDSLFile, setDroppedDSLFile] = useState<File | undefined>()
  const isWorkflowCategory = activeTab === AppModeEnum.WORKFLOW || activeTab === AppModeEnum.ADVANCED_CHAT
  const currentResourceLabel = isWorkflowCategory ? '工作流' : '应用'
  const groupedResourceLabel = isWorkflowCategory ? '工作流' : 'Agent'
  const canAccessCurrentCategory = isWorkflowCategory ? canViewWorkflow : canViewApps
  const canEditCurrentCategory = isWorkflowCategory ? canEditWorkflow : canEditApps
  const setKeywords = useCallback((keywords: string) => {
    setQuery(prev => ({ ...prev, keywords }))
  }, [setQuery])
  const setTagIDs = useCallback((tagIDs: string[]) => {
    setQuery(prev => ({ ...prev, tagIDs }))
  }, [setQuery])

  const handleDSLFileDropped = useCallback((file: File) => {
    setDroppedDSLFile(file)
    setShowCreateFromDSLModal(true)
  }, [])

  const { dragging } = useDSLDragDrop({
    onDSLFileDropped: handleDSLFileDropped,
    containerRef,
    enabled: canEditCurrentCategory,
  })

  const appListQueryParams = {
    page: 1,
    limit: 30,
    name: searchKeywords,
    tag_ids: tagIDs,
    is_created_by_me: isCreatedByMe,
    ...(activeTab !== 'all' ? { mode: activeTab as AppModeEnum } : {}),
  }

  const {
    data,
    isLoading,
    isFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    error,
    refetch,
  } = useInfiniteAppList(appListQueryParams, { enabled: true })

  useEffect(() => {
    if (controlRefreshList > 0) {
      refetch()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [controlRefreshList])

  const anchorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (localStorage.getItem(NEED_REFRESH_APP_LIST_KEY) === '1') {
      localStorage.removeItem(NEED_REFRESH_APP_LIST_KEY)
      refetch()
    }
  }, [refetch])

  useEffect(() => {
    if (isWorkflowCategory && !canAccessCurrentCategory)
      router.replace('/apps')
    if (!isWorkflowCategory && !canAccessCurrentCategory)
      router.replace('/chat')
  }, [canAccessCurrentCategory, isWorkflowCategory, router])

  useEffect(() => {
    const hasMore = hasNextPage ?? true
    let observer: IntersectionObserver | undefined

    if (error) {
      if (observer)
        observer.disconnect()
      return
    }

    if (anchorRef.current && containerRef.current) {
      // Calculate dynamic rootMargin: clamps to 100-200px range, using 20% of container height as the base value for better responsiveness
      const containerHeight = containerRef.current.clientHeight
      const dynamicMargin = Math.max(100, Math.min(containerHeight * 0.2, 200)) // Clamps to 100-200px range, using 20% of container height as the base value

      observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !isLoading && !isFetchingNextPage && !error && hasMore)
          fetchNextPage()
      }, {
        root: containerRef.current,
        rootMargin: `${dynamicMargin}px`,
        threshold: 0.1, // Trigger when 10% of the anchor element is visible
      })
      observer.observe(anchorRef.current)
    }
    return () => observer?.disconnect()
  }, [isLoading, isFetchingNextPage, fetchNextPage, error, hasNextPage])

  const { run: handleSearch } = useDebounceFn(() => {
    setSearchKeywords(keywords)
  }, { wait: 500 })
  const handleKeywordsChange = (value: string) => {
    setKeywords(value)
    handleSearch()
  }

  const { run: handleTagsUpdate } = useDebounceFn(() => {
    setTagIDs(tagFilterValue)
  }, { wait: 500 })
  const handleTagsChange = (value: string[]) => {
    setTagFilterValue(value)
    handleTagsUpdate()
  }

  const handleCreatedByMeChange = useCallback(() => {
    const newValue = !isCreatedByMe
    setIsCreatedByMe(newValue)
    setQuery(prev => ({ ...prev, isCreatedByMe: newValue }))
  }, [isCreatedByMe, setQuery])

  const pages = data?.pages ?? []
  const flatApps = useMemo(() => pages.flatMap(({ data: apps }) => apps), [pages])
  const publishedAndPendingApps = useMemo(
    () => flatApps.filter(app => !['unpublished', 'recalled'].includes(getAppDisplayStatus(app))),
    [flatApps],
  )
  const archivedApps = useMemo(
    () => flatApps.filter(app => ['unpublished', 'recalled'].includes(getAppDisplayStatus(app))),
    [flatApps],
  )
  const groupedApps = useMemo(() => groupAppsByPrimaryTag(publishedAndPendingApps, tagList.map(tag => tag.id)), [publishedAndPendingApps, tagList])
  const groupedArchivedApps = useMemo(() => groupAppsByPrimaryTag(archivedApps, tagList.map(tag => tag.id)), [archivedApps, tagList])
  const hasAnyApp = flatApps.length > 0
  const emptyStateHint = useMemo(() => {
    if (tagIDs.length || searchKeywords || isCreatedByMe)
      return undefined

    return t('newApp.noVisibleAppsHint', {
      ns: 'app',
      defaultValue: `如果工作区内已有${currentResourceLabel}但这里为空，可能是资源标签与您的 SSO 标签暂未匹配。`,
    })
  }, [currentResourceLabel, isCreatedByMe, searchKeywords, t, tagIDs.length])
  // Show skeleton during initial load or when refetching with no previous data
  const showSkeleton = isLoading || (isFetching && pages.length === 0)
  const showLoadError = !!error && pages.length === 0

  return (
    <>
      <div ref={containerRef} className="relative flex h-0 shrink-0 grow flex-col overflow-y-auto bg-background-body">
        {dragging && (
          <div className="absolute inset-0 z-50 m-0.5 rounded-2xl border-2 border-dashed border-components-dropzone-border-accent bg-[rgba(21,90,239,0.14)] p-2">
          </div>
        )}

        <div className="sticky top-0 z-10 flex flex-wrap items-center justify-end gap-y-2 bg-background-body px-12 pb-5 pt-7">
          <div className="flex items-center gap-2">
            <CheckboxWithLabel
              className="mr-2"
              label={t('showMyCreatedAppsOnly', { ns: 'app' })}
              isChecked={isCreatedByMe}
              onChange={handleCreatedByMeChange}
            />
            <TagFilter type="app" value={tagFilterValue} onChange={handleTagsChange} />
            <Input
              showLeftIcon
              showClearIcon
              wrapperClassName="w-[200px]"
              value={keywords}
              onChange={e => handleKeywordsChange(e.target.value)}
              onClear={() => handleKeywordsChange('')}
            />
          </div>
        </div>
        <div className={cn('relative flex grow flex-col gap-6 px-12 pb-6 pt-2', !hasAnyApp && 'overflow-hidden')}>
          {(canEditCurrentCategory || isLoadingCurrentWorkspace) && (
            <div className={APP_GRID_CLASS_NAME}>
              <NewAppCard
                ref={newAppCardRef}
                isLoading={isLoadingCurrentWorkspace}
                onSuccess={refetch}
                selectedAppType={activeTab}
                className={cn(!hasAnyApp && 'z-10')}
              />
            </div>
          )}
          {(() => {
            if (showSkeleton)
              return (
                <div className={APP_GRID_CLASS_NAME}>
                  <AppCardSkeleton count={6} />
                </div>
              )

            if (showLoadError) {
              return (
                <div className="col-span-full flex min-h-[320px] flex-col items-center justify-center gap-4 text-center">
                  <div className="system-md-medium text-text-secondary">
                    {t('newApp.loadAppsFailed', { ns: 'app' })}
                  </div>
                  <button
                    type="button"
                    className="rounded-lg border border-divider-deep px-4 py-2 system-sm-medium text-text-secondary hover:bg-state-base-hover"
                    onClick={() => refetch()}
                  >
                    {t('operation.reload', { ns: 'common' })}
                  </button>
                </div>
              )
            }

            if (hasAnyApp) {
              return (
                <>
                  <div className="flex flex-col gap-6">
                    {groupedApps.map(group => (
                      <section
                        key={group.key}
                        className="rounded-xl border border-[#e5e7eb] bg-white p-5 shadow-sm transition-all duration-200 ease-in-out hover:shadow-md"
                      >
                        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'inline-flex items-center rounded-full px-4 py-2 text-sm font-semibold shadow-sm',
                              group.isUntagged
                                ? 'border border-[#d1d5db] bg-[#f9fafb] text-[#4b5563]'
                                : 'bg-[#3b82f6] text-white',
                            )}
                            >
                              {group.label}
                            </div>
                            <div className="text-xs text-[#4b5563]">
                              同标签
                              {groupedResourceLabel}
                              已聚合展示
                            </div>
                          </div>
                          <div className="rounded-full bg-[#dbeafe] px-3 py-1 text-xs font-medium text-[#1e40af]">
                            {group.count}
                            {' '}
                            个
                            {groupedResourceLabel}
                          </div>
                        </div>
                        <div className={APP_GRID_CLASS_NAME}>
                          {group.apps.map(app => (
                            <AppCard key={app.id} app={app} onRefresh={refetch} />
                          ))}
                        </div>
                      </section>
                    ))}
                    {groupedArchivedApps.length > 0 && (
                      <section className="rounded-xl border border-[#e5e7eb] bg-[#f8fafc] p-5 shadow-sm">
                        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <div className="inline-flex items-center rounded-full border border-[#d1d5db] bg-white px-4 py-2 text-sm font-semibold text-[#4b5563] shadow-sm">
                              未发布 / 已回收
                            </div>
                            <div className="text-xs text-[#6b7280]">
                              当前不可在探索页直接使用，已统一置于列表底部
                            </div>
                          </div>
                          <div className="rounded-full bg-white px-3 py-1 text-xs font-medium text-[#475569]">
                            {archivedApps.length}
                            {' '}
                            个 Agent
                          </div>
                        </div>
                        <div className="flex flex-col gap-6">
                          {groupedArchivedApps.map(group => (
                            <section
                              key={`archived-${group.key}`}
                              className="rounded-xl border border-[#e5e7eb] bg-white p-5 shadow-sm"
                            >
                              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                                <div className="flex items-center gap-3">
                                  <div className={cn(
                                    'inline-flex items-center rounded-full px-4 py-2 text-sm font-semibold shadow-sm',
                                    group.isUntagged
                                      ? 'border border-[#d1d5db] bg-[#f9fafb] text-[#4b5563]'
                                      : 'bg-[#94a3b8] text-white',
                                  )}
                                  >
                                    {group.label}
                                  </div>
                                  <div className="text-xs text-[#4b5563]">
                                    已按标签分类展示
                                  </div>
                                </div>
                                <div className="rounded-full bg-[#f1f5f9] px-3 py-1 text-xs font-medium text-[#475569]">
                                  {group.count}
                                  {' '}
                                  个
                                  {groupedResourceLabel}
                                </div>
                              </div>
                              <div className={APP_GRID_CLASS_NAME}>
                                {group.apps.map(app => (
                                  <AppCard key={app.id} app={app} onRefresh={refetch} />
                                ))}
                              </div>
                            </section>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                </>
              )
            }

            // No apps - show empty state
            return <Empty hint={emptyStateHint} />
          })()}
          {isFetchingNextPage && (
            <div className={APP_GRID_CLASS_NAME}>
              <AppCardSkeleton count={3} />
            </div>
          )}
        </div>

        {canEditCurrentCategory && (
          <div
            className={`flex items-center justify-center gap-2 py-4 ${dragging ? 'text-text-accent' : 'text-text-quaternary'}`}
            role="region"
            aria-label={t('newApp.dropDSLToCreateApp', { ns: 'app' })}
          >
            <RiDragDropLine className="h-4 w-4" />
            <span className="system-xs-regular">{t('newApp.dropDSLToCreateApp', { ns: 'app' })}</span>
          </div>
        )}

        <CheckModal />
        <div ref={anchorRef} className="h-0"> </div>
        {showTagManagementModal && (
          <TagManagementModal type="app" show={showTagManagementModal} />
        )}
      </div>

      {showCreateFromDSLModal && (
        <CreateFromDSLModal
          show={showCreateFromDSLModal}
          onClose={() => {
            setShowCreateFromDSLModal(false)
            setDroppedDSLFile(undefined)
          }}
          onSuccess={() => {
            setShowCreateFromDSLModal(false)
            setDroppedDSLFile(undefined)
            refetch()
          }}
          droppedFile={droppedDSLFile}
        />
      )}
    </>
  )
}

export default List
