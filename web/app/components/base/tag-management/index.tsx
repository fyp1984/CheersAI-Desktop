'use client'

import { RiAddLine, RiCloseLine } from '@remixicon/react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import Modal from '@/app/components/base/modal'
import { ToastContext } from '@/app/components/base/toast'
import {
  createTag,
  fetchTagList,
} from '@/service/tag'
import { useStore as useTagStore } from './store'
import TagItemEditor from './tag-item-editor'
import useCanManageTags from './use-can-manage-tags'

type TagManagementModalProps = {
  type: 'knowledge' | 'app'
  show: boolean
}

const TagManagementModal = ({ show, type }: TagManagementModalProps) => {
  const { t } = useTranslation()
  const { notify } = useContext(ToastContext)
  const canManageTags = useCanManageTags(type)
  const tagList = useTagStore(s => s.tagList)
  const setTagList = useTagStore(s => s.setTagList)
  const setShowTagManagementModal = useTagStore(s => s.setShowTagManagementModal)

  const getTagList = useCallback(async (type: 'knowledge' | 'app') => {
    const res = await fetchTagList(type)
    setTagList(res)
  }, [setTagList])

  const [name, setName] = useState<string>('')
  const trimmedName = name.trim()
  const canCreate = useMemo(() => {
    return !!trimmedName && !tagList.some(tag => tag.type === type && tag.name === trimmedName)
  }, [trimmedName, tagList, type])
  const pendingRef = useRef(false)
  const createNewTag = async () => {
    if (!canManageTags) {
      notify({ type: 'error', message: t('actionMsg.modifiedUnsuccessfully', { ns: 'common' }) })
      return
    }
    if (!trimmedName)
      return
    if (pendingRef.current)
      return
    pendingRef.current = true
    try {
      const newTag = await createTag(trimmedName, type)
      notify({ type: 'success', message: t('tag.created', { ns: 'common' }) })
      setTagList([
        newTag,
        ...tagList,
      ])
      setName('')
    }
    catch (error: any) {
      notify({ type: 'error', message: error?.message || t('tag.failed', { ns: 'common' }) })
    }
    finally {
      pendingRef.current = false
    }
  }

  useEffect(() => {
    getTagList(type)
  }, [getTagList, type])

  return (
    <Modal
      className="!w-[600px] !max-w-[600px] rounded-xl px-8 py-6"
      isShow={show}
      onClose={() => setShowTagManagementModal(false)}
    >
      <div className="relative pb-2 text-xl font-semibold leading-[30px] text-text-primary">{t('tag.manageTags', { ns: 'common' })}</div>
      <div className="absolute right-4 top-4 cursor-pointer p-2" onClick={() => setShowTagManagementModal(false)}>
        <RiCloseLine className="h-4 w-4 text-text-tertiary" />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {canManageTags && (
          <form
            className="flex shrink-0 items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              void createNewTag()
            }}
          >
            <input
              className="w-[100px] shrink-0 appearance-none rounded-lg border border-dashed border-divider-regular bg-transparent px-2 py-1 text-sm leading-5 text-text-secondary caret-primary-600  outline-none placeholder:text-text-quaternary focus:border-solid"
              placeholder={t('tag.addNew', { ns: 'common' }) || ''}
              autoFocus
              value={name}
              onChange={e => setName(e.target.value)}
            />
            {canCreate && (
              <button
                type="submit"
                className="flex items-center gap-x-1 rounded-lg px-2 py-1.5 hover:bg-state-base-hover"
              >
                <RiAddLine className="h-4 w-4 text-text-tertiary" />
                <div className="system-md-regular grow truncate px-1 text-text-secondary">
                  {`${t('tag.create', { ns: 'common' })} `}
                  <span className="system-md-medium">{`'${trimmedName}'`}</span>
                </div>
              </button>
            )}
          </form>
        )}
        {tagList.filter(tag => tag.type === type).map(tag => (
          <TagItemEditor
            key={tag.id}
            tag={tag}
          />
        ))}
      </div>
    </Modal>
  )
}

export default TagManagementModal
