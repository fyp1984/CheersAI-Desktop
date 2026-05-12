'use client'
import type { FC } from 'react'
import { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { RiFolderLine, RiFileLine, RiArrowLeftLine } from '@remixicon/react'
import Cookies from 'js-cookie'
import Modal from '@/app/components/base/modal'
import Button from '@/app/components/base/button'
import Loading from '@/app/components/base/loading'
import { useToastContext } from '@/app/components/base/toast'
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'

type FileBayFile = {
  name: string
  path: string
  type: 'file' | 'dir'
  size: number
  sha: string
}

type FileBayFilePickerProps = {
  isShow: boolean
  onClose: () => void
  onSelect: (file: FileBayFile) => void
}

const FileBayFilePicker: FC<FileBayFilePickerProps> = ({
  isShow,
  onClose,
  onSelect,
}) => {
  const { t } = useTranslation()
  const { notify } = useToastContext()
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<FileBayFile[]>([])
  const [directories, setDirectories] = useState<FileBayFile[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<FileBayFile | null>(null)

  // 加载文件列表
  const loadFiles = useCallback(async (path: string) => {
    setLoading(true)
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      
      // Add CSRF token for authentication
      const csrfToken = Cookies.get(CSRF_COOKIE_NAME())
      if (csrfToken)
        headers[CSRF_HEADER_NAME] = csrfToken
      
      const response = await fetch(`/console/api/filebay/list-files?path=${encodeURIComponent(path)}`, {
        method: 'GET',
        headers,
        credentials: 'include',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || `HTTP ${response.status}`)
      }

      const data = await response.json()
      setFiles(data.files || [])
      setDirectories(data.directories || [])
    }
    catch (error) {
      notify({
        type: 'error',
        message: `加载文件失败: ${error instanceof Error ? error.message : '未知错误'}`,
      })
      console.error('Failed to load FileBay files:', error)
      setFiles([])
      setDirectories([])
    }
    finally {
      setLoading(false)
    }
  }, [notify])

  // 初始加载
  useEffect(() => {
    if (isShow)
      loadFiles(currentPath)
  }, [isShow])

  // 进入目录
  const handleEnterDirectory = useCallback((dir: FileBayFile) => {
    setCurrentPath(dir.path)
    loadFiles(dir.path)
  }, [loadFiles])

  // 返回上级目录
  const handleGoBack = useCallback(() => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/')
    setCurrentPath(parentPath)
    loadFiles(parentPath)
  }, [currentPath, loadFiles])

  // 选择文件
  const handleSelectFile = useCallback((file: FileBayFile) => {
    setSelectedFile(file)
  }, [])

  // 确认选择
  const handleConfirm = useCallback(() => {
    if (selectedFile) {
      onSelect(selectedFile)
      onClose()
    }
  }, [selectedFile, onSelect, onClose])

  return (
    <Modal
      isShow={isShow}
      onClose={onClose}
      title="从 FileBay 选择"
      className="!max-w-[640px]"
    >
      <div className="flex flex-col h-[480px]">
        {/* 路径导航 */}
        <div className="flex items-center gap-2 p-3 border-b border-divider-subtle">
          {currentPath && (
            <Button
              size="small"
              variant="ghost"
              onClick={handleGoBack}
            >
              <RiArrowLeftLine className="w-4 h-4" />
            </Button>
          )}
          <div className="system-sm-regular text-text-secondary">
            {currentPath || '/'}
          </div>
        </div>

        {/* 文件列表 */}
        <div className="flex-1 overflow-y-auto p-3">
          {loading
            ? (
                <div className="flex items-center justify-center h-full">
                  <Loading />
                </div>
              )
            : (
                <div className="space-y-1">
                  {/* 目录列表 */}
                  {directories.map(dir => (
                    <div
                      key={dir.path}
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-state-base-hover cursor-pointer transition-colors"
                      onClick={() => handleEnterDirectory(dir)}
                    >
                      <RiFolderLine className="w-5 h-5 text-text-accent shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="system-sm-semibold text-text-secondary truncate">
                          {dir.name}
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* 文件列表 */}
                  {files.map(file => (
                    <div
                      key={file.path}
                      className={`flex items-center gap-3 p-3 rounded-lg hover:bg-state-base-hover cursor-pointer transition-colors ${
                        selectedFile?.path === file.path ? 'bg-state-base-active' : ''
                      }`}
                      onClick={() => handleSelectFile(file)}
                    >
                      <RiFileLine className="w-5 h-5 text-text-tertiary shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="system-sm-semibold text-text-secondary truncate">
                          {file.name}
                        </div>
                        <div className="system-xs-regular text-text-tertiary">
                          {(file.size / 1024).toFixed(2)} KB
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* 空状态 */}
                  {!loading && directories.length === 0 && files.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-text-tertiary">
                      <RiFolderLine className="w-12 h-12 mb-2" />
                      <div className="system-sm-regular">
                        未找到文件
                      </div>
                    </div>
                  )}
                </div>
              )}
        </div>

        {/* 底部操作栏 */}
        <div className="flex items-center justify-between p-3 border-t border-divider-subtle">
          <div className="system-sm-regular text-text-tertiary">
            {selectedFile
              ? (
                  <span>
                    已选择: {selectedFile.name}
                  </span>
                )
              : (
                  <span>请选择一个文件</span>
                )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={onClose}
            >
              取消
            </Button>
            <Button
              variant="primary"
              disabled={!selectedFile}
              onClick={handleConfirm}
            >
              确认
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export default FileBayFilePicker
