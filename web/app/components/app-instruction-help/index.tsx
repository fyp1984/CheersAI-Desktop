'use client'

import type { AppInstruction, AppInstructionSource } from '@/service/app-instruction'
import { RiDeleteBinLine, RiFileTextLine, RiQuestionLine, RiUploadCloudLine } from '@remixicon/react'
import { useEffect, useRef, useState } from 'react'
import ActionButton, { ActionButtonState } from '@/app/components/base/action-button'
import Button from '@/app/components/base/button'
import { Markdown } from '@/app/components/base/markdown'
import Modal from '@/app/components/base/modal'
import { useToastContext } from '@/app/components/base/toast'
import Tooltip from '@/app/components/base/tooltip'
import { useAppContext } from '@/context/app-context'
import { deleteAppInstruction, fetchAppInstruction, updateAppInstruction } from '@/service/app-instruction'
import { cn } from '@/utils/classnames'

type Props = {
  appId?: string
  manageAppId?: string
  source: AppInstructionSource
  className?: string
}

const MAX_INSTRUCTION_FILE_SIZE = 1024 * 1024

const formatFileSize = (size = 0) => {
  if (size >= 1024 * 1024)
    return `${(size / 1024 / 1024).toFixed(1)} MB`
  if (size >= 1024)
    return `${(size / 1024).toFixed(1)} KB`
  return `${size} B`
}

const AppInstructionHelpButton = ({
  appId,
  manageAppId,
  source,
  className,
}: Props) => {
  const { notify } = useToastContext()
  const { canEditApps, isCurrentWorkspaceEditor, isCurrentWorkspaceManager } = useAppContext()
  const [instruction, setInstruction] = useState<AppInstruction | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isShow, setIsShow] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const targetAppId = manageAppId || appId
  const canManageInstruction = canEditApps || isCurrentWorkspaceEditor || isCurrentWorkspaceManager

  useEffect(() => {
    let ignore = false
    const loadInstruction = async () => {
      if (!appId) {
        setInstruction(null)
        return
      }
      setIsLoading(true)
      try {
        const res = await fetchAppInstruction(appId, source)
        if (!ignore)
          setInstruction(res.instruction)
      }
      catch {
        if (!ignore)
          setInstruction(null)
      }
      finally {
        if (!ignore)
          setIsLoading(false)
      }
    }
    loadInstruction()
    return () => {
      ignore = true
    }
  }, [appId, source])

  const hasInstruction = !!instruction?.content
  const canOpen = hasInstruction || canManageInstruction
  const isDisabled = !canOpen || isLoading
  const tooltipContent = hasInstruction
    ? '查看使用说明'
    : canManageInstruction
      ? '上传使用说明'
      : '暂无使用说明'

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || !targetAppId)
      return

    const fileName = file.name
    const lowerName = fileName.toLowerCase()
    if (!lowerName.endsWith('.md') && !lowerName.endsWith('.markdown') && !lowerName.endsWith('.txt')) {
      notify({ type: 'error', message: '仅支持 Markdown 或 TXT 使用说明文件' })
      return
    }
    if (file.size > MAX_INSTRUCTION_FILE_SIZE) {
      notify({ type: 'error', message: '使用说明文件不能超过 1 MB' })
      return
    }

    setIsSaving(true)
    try {
      const content = await file.text()
      const res = await updateAppInstruction(targetAppId, {
        title: fileName.replace(/\.(md|markdown|txt)$/i, ''),
        content,
        source_file_name: fileName,
        source_file_size: file.size,
      })
      setInstruction(res.instruction)
      setIsShow(true)
      notify({ type: 'success', message: '使用说明已保存' })
    }
    catch {
      notify({ type: 'error', message: '使用说明保存失败，请确认当前账号有智能体编辑权限' })
    }
    finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!targetAppId)
      return

    setIsSaving(true)
    try {
      await deleteAppInstruction(targetAppId)
      setInstruction(null)
      notify({ type: 'success', message: '使用说明已删除' })
    }
    catch {
      notify({ type: 'error', message: '使用说明删除失败，请确认当前账号有智能体编辑权限' })
    }
    finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <Tooltip popupContent={tooltipContent}>
        <div
          className={cn(
            'inline-flex items-center gap-2 rounded-lg px-2 py-1',
            canOpen && 'cursor-pointer text-text-secondary hover:bg-state-base-hover hover:text-text-primary',
            isDisabled && 'cursor-not-allowed text-text-disabled',
            className,
          )}
          onClick={() => {
            if (!isDisabled)
              setIsShow(true)
          }}
        >
          <span className="system-xs-medium select-none whitespace-nowrap">使用说明</span>
          <ActionButton
            size="l"
            state={canOpen ? ActionButtonState.Default : ActionButtonState.Disabled}
            disabled={isDisabled}
          >
            <RiQuestionLine className="h-[18px] w-[18px]" />
          </ActionButton>
        </div>
      </Tooltip>
      {isShow && canOpen && (
        <Modal
          isShow
          onClose={() => setIsShow(false)}
          closable
          className="max-w-[920px] p-0"
          containerClassName="p-6"
        >
          <div className="flex max-h-[78vh] min-h-[360px] flex-col bg-components-panel-bg text-text-primary">
            <div className="shrink-0 border-b border-divider-subtle px-7 py-5 pr-16">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-state-accent-hover text-text-accent">
                  <RiFileTextLine className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <div className="title-xl-semi-bold truncate text-text-primary">
                    {instruction?.title || '使用说明'}
                  </div>
                  <div className="system-xs-regular mt-1 text-text-tertiary">
                    {hasInstruction ? instruction?.source_file_name || '已上传使用说明' : '当前智能体暂无使用说明文件'}
                  </div>
                </div>
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-7 py-6">
              {hasInstruction && (
                <Markdown
                  content={instruction.content}
                  className={cn(
                    'text-sm leading-7',
                    '[&_a]:text-text-accent',
                    '[&_blockquote]:border-l-4 [&_blockquote]:border-text-accent [&_blockquote]:pl-4',
                    '[&_h1]:mb-4 [&_h1]:text-xl [&_h1]:font-semibold',
                    '[&_h2]:mb-3 [&_h2]:mt-6 [&_h2]:text-lg [&_h2]:font-semibold',
                    '[&_h3]:mb-2 [&_h3]:mt-5 [&_h3]:text-base [&_h3]:font-semibold',
                    '[&_hr]:my-6 [&_hr]:border-divider-subtle',
                    '[&_pre]:bg-background-section-burn',
                    '[&_table]:overflow-hidden [&_table]:rounded-lg [&_table]:border [&_table]:border-divider-subtle',
                    '[&_td]:border-divider-subtle [&_td]:px-3 [&_td]:py-2',
                    '[&_th]:border-divider-subtle [&_th]:bg-background-section-burn [&_th]:px-3 [&_th]:py-2',
                    '[&_code]:text-text-primary',
                  )}
                />
              )}
              {!hasInstruction && (
                <div className="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-divider-regular bg-background-section-burn px-6 py-10 text-center">
                  <RiFileTextLine className="mb-3 h-9 w-9 text-text-tertiary" />
                  <div className="system-md-semibold text-text-primary">暂无使用说明文件</div>
                  <div className="body-xs-regular mt-1 text-text-tertiary">
                    上传 Markdown 或 TXT 文件后，用户可在这里查看。
                  </div>
                </div>
              )}
            </div>
            {canManageInstruction && (
              <div className="flex shrink-0 items-center justify-between gap-3 border-t border-divider-subtle bg-background-section-burn px-7 py-4">
                <div className="min-w-0">
                  <div className="system-xs-medium truncate text-text-secondary">
                    {instruction?.source_file_name || 'Markdown / TXT 使用说明'}
                  </div>
                  <div className="system-xs-regular mt-0.5 text-text-tertiary">
                    {hasInstruction ? formatFileSize(instruction.source_file_size) : '最大 1 MB'}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {hasInstruction && (
                    <ActionButton
                      size="l"
                      disabled={isSaving}
                      onClick={handleDelete}
                    >
                      <RiDeleteBinLine className="h-[18px] w-[18px]" />
                    </ActionButton>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".md,.markdown,.txt,text/markdown,text/plain"
                    className="hidden"
                    onChange={handleUpload}
                  />
                  <Button
                    size="small"
                    loading={isSaving}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <RiUploadCloudLine className="mr-1 h-4 w-4" />
                    {hasInstruction ? '替换文件' : '上传文件'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </>
  )
}

export default AppInstructionHelpButton
