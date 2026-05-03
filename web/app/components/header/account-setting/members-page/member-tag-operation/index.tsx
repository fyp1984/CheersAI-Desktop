'use client'

import type { CategorizedTag, SystemTagCategory } from './set-tag-stringify'
import type { Tag } from '@/app/components/base/tag-management/constant'
import type { Member } from '@/models/common'
import { RiArrowDownSLine, RiArrowRightSLine } from '@remixicon/react'
import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Confirm from '@/app/components/base/confirm'
import { Tag01 } from '@/app/components/base/icons/src/vender/line/financeAndECommerce'
import {
  PortalToFollowElem,
  PortalToFollowElemContent,
  PortalToFollowElemTrigger,
} from '@/app/components/base/portal-to-follow-elem'
import { useToastContext } from '@/app/components/base/toast'
import { useAppContext } from '@/context/app-context'
import {
  clearCachedSystemTags,
  fetchCachedSystemTags,
  fetchSSOUserProfileTag,
  updateSSOUserProfileTag,
} from '@/service/sso-member-tags'
import { cn } from '@/utils/classnames'
import {
  buildGroupedTagSections,
  categorizeSystemTags,
  createVirtualTag,
  ensureNonEmptySystemTags,
  exceedsTagStringLimit,
  parseUserTagNames,
  resolveCategorizedTagsByNames,
  stringifySelectedTagNames,
} from './set-tag-stringify'
import { createMemberTagSelectionStore, useMemberTagSelectionStore } from './store'

type Props = {
  member: Member
  orgId: string
  onOperate?: () => void
}

const SYNC_ERROR_MESSAGE = '标签同步失败，请稍后重试'
const CATEGORY_LABELS: Array<{ key: SystemTagCategory, label: string }> = [
  { key: 'app', label: 'Agent/Workflow' },
  { key: 'kb', label: '知识库' },
]

type SelectionChangeRecord = {
  id: string
  action: 'select' | 'unselect'
  tagName: string
  changedAt: string
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message)
    return error.message

  return fallback
}

const isFulfilled = <T,>(result: PromiseSettledResult<T>): result is PromiseFulfilledResult<T> => {
  return result.status === 'fulfilled'
}

const getTriggerLabel = (tags: CategorizedTag[]) => {
  if (!tags.length)
    return '设置标签'

  if (tags.length === 1)
    return tags[0].displayName

  return tags[0].displayName
}

const MemberTagOperation = ({
  member,
  orgId,
  onOperate,
}: Props) => {
  const { notify } = useToastContext()
  const { userProfile, mutateUserProfile } = useAppContext()
  const selectionStoreRef = useRef(createMemberTagSelectionStore())
  const selectedTagIds = useMemberTagSelectionStore(selectionStoreRef.current, state => state.selectedTagIds)
  const resetSelectedTagIds = useMemberTagSelectionStore(selectionStoreRef.current, state => state.resetSelectedTagIds)
  const toggleSelectedTagId = useMemberTagSelectionStore(selectionStoreRef.current, state => state.toggleSelectedTagId)
  const selectGroup = useMemberTagSelectionStore(selectionStoreRef.current, state => state.selectGroup)
  const invertGroup = useMemberTagSelectionStore(selectionStoreRef.current, state => state.invertGroup)
  const [open, setOpen] = useState(false)
  const [isBootstrapping, setIsBootstrapping] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [availableTags, setAvailableTags] = useState<CategorizedTag[]>([])
  const [currentTags, setCurrentTags] = useState<CategorizedTag[]>([])
  const [initialized, setInitialized] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)
  const [selectionHistory, setSelectionHistory] = useState<SelectionChangeRecord[]>([])
  const [expandedCategories, setExpandedCategories] = useState<Record<SystemTagCategory, boolean>>({
    app: true,
    kb: true,
  })
  const panelId = `member-tag-panel-${member.id}`
  const panelTitleId = `${panelId}-title`
  const previousSelectedIdsRef = useRef<string[]>([])
  const ssoIdentity = useMemo(() => ({
    ssoOwner: member.desktop_sso_owner,
    ssoUsername: member.desktop_sso_username,
  }), [member.desktop_sso_owner, member.desktop_sso_username])

  const triggerLabel = useMemo(() => getTriggerLabel(currentTags), [currentTags])
  const selectedCount = selectedTagIds.length
  const hasPendingChanges = useMemo(() => {
    if (selectedTagIds.length !== currentTags.length)
      return true

    return selectedTagIds.some((tagId, index) => currentTags[index]?.id !== tagId)
  }, [currentTags, selectedTagIds])

  const groupedSections = useMemo(() => {
    return CATEGORY_LABELS.map(category => ({
      ...category,
      groups: buildGroupedTagSections(availableTags, category.key),
    }))
  }, [availableTags])

  const selectedTagIdSet = useMemo(() => new Set(selectedTagIds), [selectedTagIds])
  const selectedTagMap = useMemo(() => new Map(availableTags.map(tag => [tag.id, tag])), [availableTags])
  const selectedTagNames = useMemo(() => {
    return selectedTagIds
      .map(tagId => selectedTagMap.get(tagId)?.name || '')
      .filter(Boolean)
  }, [selectedTagIds, selectedTagMap])
  const selectedDisplayNames = useMemo(() => {
    return selectedTagIds
      .map(tagId => selectedTagMap.get(tagId)?.displayName || '')
      .filter(Boolean)
  }, [selectedTagIds, selectedTagMap])
  const nextTagString = useMemo(() => stringifySelectedTagNames(selectedTagNames), [selectedTagNames])
  const changeSummary = useMemo(() => {
    const currentTagIdSet = new Set(currentTags.map(tag => tag.id))
    const nextTagIdSet = new Set(selectedTagIds)
    const addedTags = selectedTagIds
      .filter(tagId => !currentTagIdSet.has(tagId))
      .map(tagId => selectedTagMap.get(tagId)?.displayName || selectedTagMap.get(tagId)?.name || tagId)
    const removedTags = currentTags
      .filter(tag => !nextTagIdSet.has(tag.id))
      .map(tag => tag.displayName || tag.name)

    return {
      addedTags,
      removedTags,
    }
  }, [currentTags, selectedTagIds, selectedTagMap])

  const loadMemberTagContext = async () => {
    setIsBootstrapping(true)
    setLoadError('')
    setSubmitError('')
    try {
      const [systemTagsResult, ssoProfileResult] = await Promise.allSettled([
        fetchCachedSystemTags(),
        fetchSSOUserProfileTag(orgId, member.id, ssoIdentity),
      ])

      const loadWarnings: string[] = []
      const { app, knowledge } = isFulfilled(systemTagsResult)
        ? systemTagsResult.value
        : { app: [], knowledge: [] }
      const ssoProfile = isFulfilled(ssoProfileResult)
        ? ssoProfileResult.value
        : { userId: member.id, tags: '', tagNames: [] }

      if (!isFulfilled(systemTagsResult)) {
        clearCachedSystemTags()
        loadWarnings.push(getErrorMessage(systemTagsResult.reason, '系统标签加载失败'))
      }

      if (!isFulfilled(ssoProfileResult))
        loadWarnings.push(getErrorMessage(ssoProfileResult.reason, 'SSO 用户标签加载失败'))

      const resolvedTagMap = new Map<string, Tag>()
      ;[...app, ...knowledge].forEach(tag => resolvedTagMap.set(tag.id, tag))

      const ssoTagNames = ssoProfile.tagNames.length
        ? ssoProfile.tagNames
        : parseUserTagNames(ssoProfile.tags)

      ssoTagNames.forEach((tagName) => {
        const hasTag = Array.from(resolvedTagMap.values()).some(tag => tag.name === tagName)
        if (!hasTag)
          resolvedTagMap.set(`profile-${tagName}`, createVirtualTag(tagName, `profile-${tagName}`))
      })

      const categorizedTags = categorizeSystemTags(ensureNonEmptySystemTags(Array.from(resolvedTagMap.values())))
      const categorizedCurrentTags = resolveCategorizedTagsByNames(categorizedTags, ssoTagNames)

      setAvailableTags(categorizedTags)
      setCurrentTags(categorizedCurrentTags)
      const nextSelectedTagIds = categorizedCurrentTags.map(tag => tag.id)
      resetSelectedTagIds(nextSelectedTagIds)
      previousSelectedIdsRef.current = nextSelectedTagIds
      setSelectionHistory([])
      setLoadError(loadWarnings[0] || '')
      setInitialized(true)
    }
    catch (error) {
      clearCachedSystemTags()
      const fallbackTags = categorizeSystemTags(ensureNonEmptySystemTags([]))
      setAvailableTags(fallbackTags)
      setCurrentTags([])
      resetSelectedTagIds([])
      previousSelectedIdsRef.current = []
      setSelectionHistory([])
      setLoadError(getErrorMessage(error, '成员标签数据加载失败'))
      setInitialized(true)
    }
    finally {
      setIsBootstrapping(false)
    }
  }

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen)
    if (nextOpen && !initialized && !isBootstrapping)
      void loadMemberTagContext()
    if (!nextOpen)
      setSubmitError('')
  }

  const handleSave = async () => {
    if (exceedsTagStringLimit(nextTagString)) {
      setSubmitError('标签总长度超出限制，请减少选择项')
      setIsConfirmOpen(false)
      return
    }

    setIsSaving(true)
    setSubmitError('')

    try {
      await updateSSOUserProfileTag(orgId, member.id, nextTagString, ssoIdentity)

      const persistedProfile = await fetchSSOUserProfileTag(orgId, member.id, ssoIdentity)
      const persistedTagNames = persistedProfile.tagNames.length
        ? persistedProfile.tagNames
        : parseUserTagNames(persistedProfile.tags)
      const persistedCurrentTags = resolveCategorizedTagsByNames(availableTags, persistedTagNames)
      const nextCurrentTags = persistedCurrentTags.length || !persistedTagNames.length
        ? persistedCurrentTags
        : selectedTagIds
            .map(tagId => selectedTagMap.get(tagId))
            .filter((tag): tag is CategorizedTag => Boolean(tag))
      const nextSelectedIds = nextCurrentTags.map(tag => tag.id)

      setCurrentTags(nextCurrentTags)
      resetSelectedTagIds(nextSelectedIds)
      previousSelectedIdsRef.current = nextSelectedIds
      setSelectionHistory([])

      if (userProfile.id === member.id || userProfile.email === member.email)
        mutateUserProfile()
      onOperate?.()
      notify({
        type: 'success',
        message: '成员标签更新成功',
      })
      setIsConfirmOpen(false)
      setOpen(false)
    }
    catch (error) {
      setIsConfirmOpen(false)
      setSubmitError(getErrorMessage(error, SYNC_ERROR_MESSAGE))
    }
    finally {
      setIsSaving(false)
    }
  }

  const handleCancel = useCallback(() => {
    const restoredTagIds = currentTags.map(tag => tag.id)
    resetSelectedTagIds(restoredTagIds)
    previousSelectedIdsRef.current = restoredTagIds
    setSelectionHistory([])
    setSubmitError('')
    setLoadError('')
    setIsConfirmOpen(false)
    setOpen(false)
  }, [currentTags, resetSelectedTagIds])

  const toggleCategory = (category: SystemTagCategory) => {
    setExpandedCategories(prev => ({ ...prev, [category]: !prev[category] }))
  }

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      handleOpenChange(!open)
    }
  }

  const handlePanelKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      event.stopPropagation()
      handleCancel()
    }
  }

  const appendSelectionHistory = useCallback((entries: SelectionChangeRecord[]) => {
    if (!entries.length)
      return

    setSelectionHistory(prev => [...entries, ...prev].slice(0, 10))
  }, [])

  const trackSelectionChange = useCallback((nextSelectedIds: string[]) => {
    const previousSelectedIds = previousSelectedIdsRef.current
    const previousSelectedIdSet = new Set(previousSelectedIds)
    const nextSelectedIdSet = new Set(nextSelectedIds)
    const timestamp = new Date().toISOString()
    const nextHistoryEntries: SelectionChangeRecord[] = []

    nextSelectedIds.forEach((tagId) => {
      if (!previousSelectedIdSet.has(tagId)) {
        nextHistoryEntries.push({
          id: `${timestamp}-${tagId}-select`,
          action: 'select',
          tagName: selectedTagMap.get(tagId)?.displayName || selectedTagMap.get(tagId)?.name || tagId,
          changedAt: timestamp,
        })
      }
    })

    previousSelectedIds.forEach((tagId) => {
      if (!nextSelectedIdSet.has(tagId)) {
        nextHistoryEntries.push({
          id: `${timestamp}-${tagId}-unselect`,
          action: 'unselect',
          tagName: selectedTagMap.get(tagId)?.displayName || selectedTagMap.get(tagId)?.name || tagId,
          changedAt: timestamp,
        })
      }
    })

    appendSelectionHistory(nextHistoryEntries)
    previousSelectedIdsRef.current = nextSelectedIds
  }, [appendSelectionHistory, selectedTagMap])

  const handleToggleSelectedTagId = (tagId: string) => {
    const nextSelectedIds = selectedTagIds.includes(tagId)
      ? selectedTagIds.filter(id => id !== tagId)
      : [...selectedTagIds, tagId]

    toggleSelectedTagId(tagId)
    trackSelectionChange(nextSelectedIds)
  }

  const handleTagKeyDown = (event: React.KeyboardEvent<HTMLInputElement>, tagId: string) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      handleToggleSelectedTagId(tagId)
    }
  }

  const handleGroupSelectAll = (tagIds: string[]) => {
    const nextSelectedIds = [...new Set([...selectedTagIds, ...tagIds])]
    selectGroup(tagIds)
    trackSelectionChange(nextSelectedIds)
  }

  const handleGroupInvert = (tagIds: string[]) => {
    const selectedTagIdSet = new Set(selectedTagIds)
    const nextSelectedIds = selectedTagIds.filter(id => !tagIds.includes(id))
    tagIds.forEach((tagId) => {
      if (!selectedTagIdSet.has(tagId))
        nextSelectedIds.push(tagId)
    })

    invertGroup(tagIds)
    trackSelectionChange(nextSelectedIds)
  }

  useEffect(() => {
    if (!open)
      return

    const handleDocumentEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape')
        return

      event.preventDefault()
      event.stopPropagation()
      event.stopImmediatePropagation?.()
      handleCancel()
    }

    document.addEventListener('keydown', handleDocumentEscape, true)
    return () => {
      document.removeEventListener('keydown', handleDocumentEscape, true)
    }
  }, [handleCancel, open])

  return (
    <PortalToFollowElem
      open={open}
      onOpenChange={handleOpenChange}
      placement="bottom-start"
      offset={4}
    >
      <div className="relative w-full">
        <PortalToFollowElemTrigger
          onClick={() => handleOpenChange(!open)}
          className="block w-full"
          role="button"
          tabIndex={0}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls={panelId}
          onKeyDown={handleTriggerKeyDown}
        >
          <div
            className={cn(
              'flex h-8 cursor-pointer select-none items-center gap-1 rounded-lg border-[0.5px] border-transparent bg-components-input-bg-normal px-2 hover:bg-components-input-bg-hover',
              !!selectedCount && 'shadow-xs',
              loadError && 'border-status-warning-border bg-status-warning-bg',
            )}
          >
            <div className="p-[1px]">
              <Tag01 className="h-3.5 w-3.5 text-text-tertiary" />
            </div>
            <span className="truncate text-[13px] leading-[18px] text-text-tertiary">{triggerLabel}</span>
            {selectedCount > 1 && (
              <span className="text-xs font-medium leading-[18px] text-text-tertiary">{`+${selectedCount - 1}`}</span>
            )}
            <div className="p-[1px]">
              <RiArrowDownSLine className="h-3.5 w-3.5 text-text-tertiary" />
            </div>
          </div>
        </PortalToFollowElemTrigger>
        <PortalToFollowElemContent className="z-[1002]">
          <div
            id={panelId}
            role="dialog"
            aria-modal="false"
            aria-labelledby={panelTitleId}
            onKeyDown={handlePanelKeyDown}
            className="max-md:max-w-screen relative w-[480px] max-w-[calc(100vw-16px)] rounded-xl border-[0.5px] border-components-panel-border bg-components-panel-bg-blur shadow-lg backdrop-blur-[5px] max-md:w-screen max-md:rounded-none"
          >
            <div className="border-b border-divider-subtle px-4 py-3">
              <div id={panelTitleId} className="system-sm-semibold text-text-secondary">
                {member.name}
                {' '}
                标签
              </div>
              <div className="system-xs-regular mt-1 text-text-tertiary">{member.email}</div>
            </div>
            {submitError && (
              <div className="px-4 pt-3">
                <div role="alert" aria-live="assertive" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {submitError}
                </div>
              </div>
            )}
            {loadError && (
              <div className="px-4 pt-3">
                <div className="flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
                  <span className="min-w-0 flex-1 truncate">{loadError}</span>
                  <button
                    type="button"
                    className="shrink-0 text-xs font-medium text-yellow-900 underline"
                    onClick={() => void loadMemberTagContext()}
                  >
                    重试
                  </button>
                </div>
              </div>
            )}
            <div className="max-h-[420px] overflow-y-auto px-3 py-3">
              {isBootstrapping && (
                <div className="px-3 py-12 text-center text-sm text-text-tertiary">
                  <div className="mb-2 inline-flex h-5 w-5 animate-spin rounded-full border-2 border-divider-subtle border-t-text-accent" />
                  <div>加载标签中...</div>
                </div>
              )}
              {!isBootstrapping && groupedSections.every(section => section.groups.length === 0) && (
                <div className="px-3 py-12 text-center text-sm text-text-tertiary">暂无可选标签，请先创建系统标签或稍后重试</div>
              )}
              {!isBootstrapping && groupedSections.map(section => (
                <div key={section.key} className="mb-3 rounded-xl border border-divider-subtle last:mb-0">
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 px-3 py-3 text-left hover:bg-state-base-hover"
                    aria-expanded={expandedCategories[section.key]}
                    aria-controls={`${panelId}-${section.key}`}
                    onClick={() => toggleCategory(section.key)}
                  >
                    <RiArrowRightSLine className={cn('h-4 w-4 shrink-0 text-text-tertiary transition-transform', expandedCategories[section.key] && 'rotate-90')} />
                    <span className="system-sm-semibold text-text-secondary">{section.label}</span>
                    <span className="system-xs-regular ml-auto text-text-tertiary">
                      {section.groups.reduce((count, group) => count + group.tags.length, 0)}
                    </span>
                  </button>
                  {expandedCategories[section.key] && (
                    <div id={`${panelId}-${section.key}`} className="border-t border-divider-subtle px-3 py-3">
                      {section.groups.map(group => (
                        <div key={`${section.key}-${group.groupLabel}`} className="mb-4 last:mb-0">
                          <div className="mb-2 flex items-center gap-2">
                            <div className="system-xs-medium-uppercase text-text-tertiary">{group.groupLabel}</div>
                            <button
                              type="button"
                              className="text-xs text-text-tertiary hover:text-text-secondary"
                              onClick={() => handleGroupSelectAll(group.tags.map(tag => tag.id))}
                            >
                              全选
                            </button>
                            <button
                              type="button"
                              className="text-xs text-text-tertiary hover:text-text-secondary"
                              onClick={() => handleGroupInvert(group.tags.map(tag => tag.id))}
                            >
                              反选
                            </button>
                          </div>
                          <div className="grid grid-cols-3 gap-2 max-md:grid-cols-1">
                            {group.tags.map((tag) => {
                              const inputId = `member-${member.id}-tag-${tag.id}`
                              return (
                                <label
                                  key={tag.id}
                                  htmlFor={inputId}
                                  className="flex cursor-pointer items-start gap-2 rounded-lg border border-transparent px-2 py-2 hover:bg-state-base-hover"
                                >
                                  <input
                                    id={inputId}
                                    type="checkbox"
                                    className="mt-0.5 h-4 w-4 shrink-0 accent-[#295EFF]"
                                    checked={selectedTagIdSet.has(tag.id)}
                                    aria-label={tag.displayName}
                                    onChange={() => handleToggleSelectedTagId(tag.id)}
                                    onKeyDown={event => handleTagKeyDown(event, tag.id)}
                                  />
                                  <span className="system-sm-medium min-w-0 truncate text-text-secondary">{tag.displayName}</span>
                                </label>
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!isBootstrapping && selectionHistory.length > 0 && (
                <div className="mt-3 rounded-xl border border-divider-subtle px-3 py-3">
                  <div className="system-xs-medium-uppercase mb-2 text-text-tertiary">本次修改记录</div>
                  <div className="space-y-1">
                    {selectionHistory.slice(0, 5).map(history => (
                      <div key={history.id} className="system-xs-regular flex items-center justify-between gap-3 text-text-tertiary">
                        <span className="min-w-0 flex-1 truncate">
                          {history.action === 'select' ? '已选择' : '已取消'}
                          {' '}
                          {history.tagName}
                        </span>
                        <span className="shrink-0">{history.changedAt.slice(11, 19)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="flex items-center justify-between border-t border-divider-subtle px-4 py-3">
              <div className="system-sm-medium text-text-tertiary">{`已选 ${selectedCount} 项`}</div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="system-sm-medium rounded-lg px-3 py-1.5 text-text-tertiary hover:bg-state-base-hover"
                  disabled={isSaving}
                  onClick={handleCancel}
                >
                  取消
                </button>
                <button
                  type="button"
                  className="system-sm-medium rounded-lg bg-components-button-primary-bg px-3 py-1.5 text-components-button-primary-text disabled:opacity-60"
                  disabled={isSaving || isBootstrapping || !hasPendingChanges}
                  onClick={() => setIsConfirmOpen(true)}
                >
                  {isSaving ? '保存中...' : '确定'}
                </button>
              </div>
            </div>
          </div>
        </PortalToFollowElemContent>
      </div>
      <Confirm
        isShow={isConfirmOpen}
        title="确认保存成员标签变更？"
        content={(
          <div className="space-y-2">
            <div>{`目标成员：${member.name || member.email || member.id}`}</div>
            <div>{`已选 ${selectedCount} 项，序列化长度 ${nextTagString.length} / 500`}</div>
            {changeSummary.addedTags.length > 0 && (
              <div>{`新增：${changeSummary.addedTags.join('、')}`}</div>
            )}
            {changeSummary.removedTags.length > 0 && (
              <div>{`移除：${changeSummary.removedTags.join('、')}`}</div>
            )}
            {selectedDisplayNames.length > 0 && (
              <div>{`保存结果：${selectedDisplayNames.join('、')}`}</div>
            )}
            {!selectedDisplayNames.length && (
              <div>保存结果：清空当前用户标签</div>
            )}
          </div>
        )}
        confirmText="确认保存"
        cancelText="返回修改"
        isLoading={isSaving}
        isDisabled={exceedsTagStringLimit(nextTagString)}
        onCancel={() => setIsConfirmOpen(false)}
        onConfirm={() => void handleSave()}
      />
    </PortalToFollowElem>
  )
}

export default memo(MemberTagOperation)
