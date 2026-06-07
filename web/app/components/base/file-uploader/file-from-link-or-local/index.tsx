import type { FileUpload } from '@/app/components/base/features/types'
import { RiDatabase2Line, RiUploadCloud2Line } from '@remixicon/react'
import Cookies from 'js-cookie'
import {
  memo,
  useState,
} from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import {
  PortalToFollowElem,
  PortalToFollowElemContent,
  PortalToFollowElemTrigger,
} from '@/app/components/base/portal-to-follow-elem'
import { useToastContext } from '@/app/components/base/toast'
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'
import { TransferMethod } from '@/types/app'
import { cn } from '@/utils/classnames'
import { FILE_URL_REGEX } from '../constants'
import FileInput from '../file-input'
import FileBayFilePicker from '../filebay-file-picker'
import { useFile } from '../hooks'
import { useStore } from '../store'
import { getSupportFileType } from '../utils'

type FileBayPickerFile = {
  path: string
  sha?: string
}

type FileBayUploadedFile = {
  id: string
  name: string
  size: number
  mime_type: string
}

type FileBayUploadCacheEntry = {
  file: FileBayUploadedFile
  savedAt: number
}

const FILEBAY_UPLOAD_CACHE_TTL = 30 * 60 * 1000
const fileBayUploadCache = new Map<string, FileBayUploadCacheEntry>()

const getFileBayUploadCacheKey = (file: FileBayPickerFile) => `${file.path}:${file.sha || ''}`

const getCachedFileBayUpload = (file: FileBayPickerFile) => {
  const cacheEntry = fileBayUploadCache.get(getFileBayUploadCacheKey(file))
  if (!cacheEntry)
    return null

  if (Date.now() - cacheEntry.savedAt > FILEBAY_UPLOAD_CACHE_TTL)
    return null

  return cacheEntry.file
}

const setCachedFileBayUpload = (file: FileBayPickerFile, uploadedFile: FileBayUploadedFile) => {
  fileBayUploadCache.set(getFileBayUploadCacheKey(file), {
    file: uploadedFile,
    savedAt: Date.now(),
  })
}

type FileFromLinkOrLocalProps = {
  showFromLink?: boolean
  showFromLocal?: boolean
  showFromFileBay?: boolean
  trigger: (open: boolean) => React.ReactNode
  fileConfig: FileUpload
}
const FileFromLinkOrLocal = ({
  showFromLink = true,
  showFromLocal = true,
  showFromFileBay = false,
  trigger,
  fileConfig,
}: FileFromLinkOrLocalProps) => {
  const { t } = useTranslation()
  const { notify } = useToastContext()
  const files = useStore(s => s.files)
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [showError, setShowError] = useState(false)
  const [showFileBayPicker, setShowFileBayPicker] = useState(false)
  const { handleLoadFileFromLink, handleAddFile } = useFile(fileConfig)
  const disabled = !!fileConfig.number_limits && files.length >= fileConfig.number_limits

  const handleSaveUrl = () => {
    if (!url)
      return

    if (!FILE_URL_REGEX.test(url)) {
      setShowError(true)
      return
    }
    handleLoadFileFromLink(url)
    setUrl('')
  }

  const handleSelectFileBayFile = async (file: FileBayPickerFile) => {
    try {
      let uploadedFile = getCachedFileBayUpload(file)

      if (!uploadedFile) {
        // 调用 FileBay 上传端点，直接将文件上传到 Dify 存储
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }

        // Add CSRF token for authentication
        const csrfToken = Cookies.get(CSRF_COOKIE_NAME())
        if (csrfToken)
          headers[CSRF_HEADER_NAME] = csrfToken

        const response = await fetch('/console/api/filebay/upload-file', {
          method: 'POST',
          headers,
          credentials: 'include',
          body: JSON.stringify({ file_path: file.path }),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        uploadedFile = await response.json() as FileBayUploadedFile
        setCachedFileBayUpload(file, uploadedFile)
      }

      // 使用上传后的文件信息创建文件对象
      const fileEntity = {
        id: uploadedFile.id,
        name: uploadedFile.name,
        size: uploadedFile.size,
        type: uploadedFile.mime_type,
        progress: 100,
        transferMethod: TransferMethod.local_file,
        supportFileType: getSupportFileType(uploadedFile.name, uploadedFile.mime_type),
        uploadedId: uploadedFile.id,
      }

      // 使用 handleAddFile 添加到文件列表
      handleAddFile(fileEntity)

      notify({
        type: 'success',
        message: `文件 ${uploadedFile.name} 上传成功`,
      })
    }
    catch (error) {
      notify({
        type: 'error',
        message: `上传文件失败: ${error instanceof Error ? error.message : '未知错误'}`,
      })
      console.error('Failed to upload file from FileBay:', error)
    }
  }

  return (
    <>
      <PortalToFollowElem
        placement="top"
        offset={4}
        open={open}
        onOpenChange={setOpen}
      >
        <PortalToFollowElemTrigger onClick={() => setOpen(v => !v)} asChild>
          {trigger(open)}
        </PortalToFollowElemTrigger>
        <PortalToFollowElemContent className="z-[1001]">
          <div className="w-[280px] rounded-xl border-[0.5px] border-components-panel-border bg-components-panel-bg-blur p-3 shadow-lg">
            {
              showFromFileBay && (
                <Button
                  className="w-full"
                  variant="secondary-accent"
                  disabled={disabled}
                  onClick={() => {
                    setOpen(false)
                    setShowFileBayPicker(true)
                  }}
                >
                  <RiDatabase2Line className="mr-1 h-4 w-4" />
                  从 FileBay 选择
                </Button>
              )
            }
            {
              !showFromFileBay && showFromLink && (
                <>
                  <div className={cn(
                    'flex h-8 items-center rounded-lg border border-components-input-border-active bg-components-input-bg-active p-1 shadow-xs',
                    showError && 'border-components-input-border-destructive',
                  )}
                  >
                    <input
                      className="system-sm-regular mr-0.5 block grow appearance-none bg-transparent px-1 outline-none"
                      placeholder={t('fileUploader.pasteFileLinkInputPlaceholder', { ns: 'common' }) || ''}
                      value={url}
                      onChange={(e) => {
                        setShowError(false)
                        setUrl(e.target.value.trim())
                      }}
                      disabled={disabled}
                    />
                    <Button
                      className="shrink-0"
                      size="small"
                      variant="primary"
                      disabled={!url || disabled}
                      onClick={handleSaveUrl}
                    >
                      {t('operation.ok', { ns: 'common' })}
                    </Button>
                  </div>
                  {
                    showError && (
                      <div className="body-xs-regular mt-0.5 text-text-destructive">
                        {t('fileUploader.pasteFileLinkInvalid', { ns: 'common' })}
                      </div>
                    )
                  }
                </>
              )
            }
            {
              !showFromFileBay && (showFromLink && (showFromLocal)) && (
                <div className="system-2xs-medium-uppercase flex h-7 items-center p-2 text-text-quaternary">
                  <div className="mr-2 h-px w-[93px] bg-gradient-to-l from-[rgba(16,24,40,0.08)]" />
                  OR
                  <div className="ml-2 h-px w-[93px] bg-gradient-to-r from-[rgba(16,24,40,0.08)]" />
                </div>
              )
            }
            {
              !showFromFileBay && showFromLocal && (
                <Button
                  className="relative w-full"
                  variant="secondary-accent"
                  disabled={disabled}
                >
                  <RiUploadCloud2Line className="mr-1 h-4 w-4" />
                  {t('fileUploader.uploadFromComputer', { ns: 'common' })}
                  <FileInput fileConfig={fileConfig} />
                </Button>
              )
            }
          </div>
        </PortalToFollowElemContent>
      </PortalToFollowElem>

      {/* FileBay 文件选择器 */}
      <FileBayFilePicker
        isShow={showFileBayPicker}
        onClose={() => setShowFileBayPicker(false)}
        onSelect={handleSelectFileBayFile}
      />
    </>
  )
}

export default memo(FileFromLinkOrLocal)
