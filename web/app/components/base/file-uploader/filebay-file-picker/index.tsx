'use client'
import type { FC } from 'react'
import { RiArrowLeftLine, RiFileLine, RiFolderLine } from '@remixicon/react'
import Cookies from 'js-cookie'
import { useCallback, useEffect, useRef, useState } from 'react'
import Button from '@/app/components/base/button'
import Loading from '@/app/components/base/loading'
import Modal from '@/app/components/base/modal'
import { useToastContext } from '@/app/components/base/toast'
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'

type FileBayFile = {
  name: string
  path: string
  type: 'file' | 'dir'
  size: number
  sha: string
}

type FileBayFileList = {
  files: FileBayFile[]
  directories: FileBayFile[]
}

type FileBayFileListCacheEntry = {
  data: FileBayFileList
  savedAt: number
}

const FILEBAY_LIST_CACHE_TTL = 5 * 60 * 1000
const fileBayFileListCache = new Map<string, FileBayFileListCacheEntry>()

const normalizeFileBayPath = (path: string) => path.trim().replace(/^\/+|\/+$/g, '')

const getFileBayListCache = (path: string) => {
  const cacheEntry = fileBayFileListCache.get(normalizeFileBayPath(path))
  if (!cacheEntry)
    return null

  if (Date.now() - cacheEntry.savedAt > FILEBAY_LIST_CACHE_TTL)
    return null

  return cacheEntry.data
}

const setFileBayListCache = (path: string, data: FileBayFileList) => {
  fileBayFileListCache.set(normalizeFileBayPath(path), {
    data,
    savedAt: Date.now(),
  })
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
  const { notify } = useToastContext()
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<FileBayFile[]>([])
  const [directories, setDirectories] = useState<FileBayFile[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<FileBayFile | null>(null)
  const loadingRequestRef = useRef(0)
  const wasShownRef = useRef(false)

  // 加载文件列表
  const loadFiles = useCallback(async (path: string, options?: { force?: boolean }) => {
    const normalizedPath = normalizeFileBayPath(path)
    const cachedFileList = options?.force ? null : getFileBayListCache(normalizedPath)
    const requestId = loadingRequestRef.current + 1
    loadingRequestRef.current = requestId

    if (cachedFileList) {
      setFiles(cachedFileList.files)
      setDirectories(cachedFileList.directories)
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }

      // Add CSRF token for authentication
      const csrfToken = Cookies.get(CSRF_COOKIE_NAME())
      if (csrfToken)
        headers[CSRF_HEADER_NAME] = csrfToken

      const response = await fetch(`/console/api/filebay/list-files?path=${encodeURIComponent(normalizedPath)}`, {
        method: 'GET',
        headers,
        credentials: 'include',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        throw new Error(errorData.error || `HTTP ${response.status}`)
      }

      const data = await response.json()
      const nextFileList = {
        files: data.files || [],
        directories: data.directories || [],
      }

      setFileBayListCache(normalizedPath, nextFileList)

      if (requestId !== loadingRequestRef.current)
        return

      setFiles(nextFileList.files)
      setDirectories(nextFileList.directories)
    }
    catch (error) {
      if (requestId !== loadingRequestRef.current)
        return

      notify({
        type: 'error',
        message: `加载文件失败: ${error instanceof Error ? error.message : '未知错误'}`,
      })
      console.error('Failed to load FileBay files:', error)
      setFiles([])
      setDirectories([])
    }
    finally {
      if (requestId === loadingRequestRef.current)
        setLoading(false)
    }
  }, [notify])

  // 初始加载
  useEffect(() => {
    if (isShow && !wasShownRef.current)
      loadFiles(currentPath)

    wasShownRef.current = isShow
  }, [currentPath, isShow, loadFiles])

  // 进入目录
  const handleEnterDirectory = useCallback((dir: FileBayFile) => {
    setCurrentPath(dir.path)
    setSelectedFile(null)
    loadFiles(dir.path)
  }, [loadFiles])

  // 返回上级目录
  const handleGoBack = useCallback(() => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/')
    setCurrentPath(parentPath)
    setSelectedFile(null)
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
      <div className="flex h-[480px] flex-col">
        {/* 路径导航 */}
        <div className="flex items-center gap-2 border-b border-divider-subtle p-3">
          {currentPath && (
            <Button
              size="small"
              variant="ghost"
              onClick={handleGoBack}
            >
              <RiArrowLeftLine className="h-4 w-4" />
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
                <div className="flex h-full items-center justify-center">
                  <Loading />
                </div>
              )
            : (
                <div className="space-y-1">
                  {/* 目录列表 */}
                  {directories.map(dir => (
                    <div
                      key={dir.path}
                      className="flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors hover:bg-state-base-hover"
                      onClick={() => handleEnterDirectory(dir)}
                    >
                      <RiFolderLine className="h-5 w-5 shrink-0 text-text-accent" />
                      <div className="min-w-0 flex-1">
                        <div className="system-sm-semibold truncate text-text-secondary">
                          {dir.name}
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* 文件列表 */}
                  {files.map(file => (
                    <div
                      key={file.path}
                      className={`flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors hover:bg-state-base-hover ${
                        selectedFile?.path === file.path ? 'bg-state-base-active' : ''
                      }`}
                      onClick={() => handleSelectFile(file)}
                    >
                      <RiFileLine className="h-5 w-5 shrink-0 text-text-tertiary" />
                      <div className="min-w-0 flex-1">
                        <div className="system-sm-semibold truncate text-text-secondary">
                          {file.name}
                        </div>
                        <div className="system-xs-regular text-text-tertiary">
                          {(file.size / 1024).toFixed(2)}
                          {' '}
                          KB
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* 空状态 */}
                  {!loading && directories.length === 0 && files.length === 0 && (
                    <div className="flex h-full flex-col items-center justify-center text-text-tertiary">
                      <RiFolderLine className="mb-2 h-12 w-12" />
                      <div className="system-sm-regular">
                        未找到文件
                      </div>
                    </div>
                  )}
                </div>
              )}
        </div>

        {/* 底部操作栏 */}
        <div className="flex items-center justify-between border-t border-divider-subtle p-3">
          <div className="system-sm-regular text-text-tertiary">
            {selectedFile
              ? (
                  <span>
                    已选择:
                    {' '}
                    {selectedFile.name}
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
