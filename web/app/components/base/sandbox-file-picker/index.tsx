'use client'

import { useState, useEffect } from 'react'
import { RiCloseLine, RiFileTextLine, RiDownloadLine, RiFolderLine, RiRefreshLine } from '@remixicon/react'
import { cn } from '@/utils/classnames'

interface SandboxFile {
  name: string
  originalName: string
  size: number
  type: string
  createdAt: string
  modifiedAt: string
}

interface SandboxFilePickerProps {
  open: boolean
  onClose: () => void
  onSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
  className?: string
}

export function SandboxFilePicker({
  open,
  onClose,
  onSelect,
  accept = '',
  multiple = false,
  className = ''
}: SandboxFilePickerProps) {
  const [files, setFiles] = useState<SandboxFile[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)

  // 获取沙箱文件列表
  const fetchFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/sandbox/list')
      if (!response.ok) {
        throw new Error('获取文件列表失败')
      }
      const fileList = await response.json()
      setFiles(fileList)
    } catch (error) {
      console.error('获取沙箱文件列表失败:', error)
      setError('无法加载沙箱文件列表，请检查后端服务是否正常运行')
    } finally {
      setLoading(false)
    }
  }

  // 当弹窗打开时获取文件列表
  useEffect(() => {
    if (open) {
      fetchFiles()
      setSelectedFiles(new Set())
    }
  }, [open])

  // 处理文件选择
  const handleFileSelect = (fileName: string) => {
    if (multiple) {
      const newSelected = new Set(selectedFiles)
      if (newSelected.has(fileName)) {
        newSelected.delete(fileName)
      } else {
        newSelected.add(fileName)
      }
      setSelectedFiles(newSelected)
    } else {
      setSelectedFiles(new Set([fileName]))
    }
  }

  // 确认选择
  const handleConfirm = async () => {
    if (selectedFiles.size === 0) return

    try {
      const selectedFileObjects: File[] = []
      
      for (const fileName of selectedFiles) {
        // 获取文件内容
        const response = await fetch(`/api/sandbox/files/${fileName}`)
        if (response.ok) {
          const blob = await response.blob()
          const file = files.find(f => f.name === fileName)
          if (file) {
            const fileObject = new File([blob], file.originalName, { type: file.type })
            selectedFileObjects.push(fileObject)
          }
        }
      }

      onSelect(selectedFileObjects)
      onClose()
    } catch (error) {
      console.error('读取文件失败:', error)
      setError('读取文件失败')
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 获取文件图标
  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    return <RiFileTextLine className="w-5 h-5 text-blue-500" />
  }

  // 过滤文件（根据accept属性）
  const filteredFiles = files.filter(file => {
    if (!accept) return true
    const acceptedTypes = accept.split(',').map(type => type.trim())
    const fileExt = '.' + file.originalName.split('.').pop()?.toLowerCase()
    return acceptedTypes.some(type => 
      type === fileExt || 
      type === file.type ||
      type === '*'
    )
  })

  if (!open) return null

  return (
    <div className={cn('fixed inset-0 z-[9999] flex items-center justify-center bg-black/50', className)}>
      <div className="w-[800px] max-h-[80vh] bg-white rounded-2xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <RiFolderLine className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900">选择沙箱文件</h3>
            <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
              安全脱敏
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchFiles}
              disabled={loading}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="刷新文件列表"
            >
              <RiRefreshLine className={cn('w-4 h-4', loading && 'animate-spin')} />
            </button>
            <button 
              onClick={onClose} 
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RiCloseLine className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
              <button
                onClick={fetchFiles}
                className="mt-2 text-sm text-red-700 hover:text-red-800 underline"
              >
                重试
              </button>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-3 text-gray-600">加载文件列表...</span>
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <RiFolderLine className="w-12 h-12 mb-4" />
              <p className="text-lg font-medium mb-2">沙箱目录中没有文件</p>
              <p className="text-sm text-center">
                请先在「脱敏沙箱」模块中上传并处理文件，<br />
                然后刷新此列表
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-600">
                  共 {filteredFiles.length} 个文件
                  {selectedFiles.size > 0 && ` • 已选择 ${selectedFiles.size} 个`}
                </p>
                {multiple && (
                  <button
                    onClick={() => setSelectedFiles(new Set())}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    清除选择
                  </button>
                )}
              </div>

              {filteredFiles.map((file) => (
                <div
                  key={file.name}
                  onClick={() => handleFileSelect(file.name)}
                  className={cn(
                    'flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all',
                    selectedFiles.has(file.name)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  )}
                >
                  {/* 选择框 */}
                  <div className={cn(
                    'w-4 h-4 rounded border-2 flex items-center justify-center',
                    selectedFiles.has(file.name)
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300'
                  )}>
                    {selectedFiles.has(file.name) && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>

                  {/* 文件图标 */}
                  <div className="shrink-0">
                    {getFileIcon(file.originalName)}
                  </div>

                  {/* 文件信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-gray-900 truncate">
                        {file.originalName}
                      </p>
                      <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                        已脱敏
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>{formatFileSize(file.size)}</span>
                      <span>•</span>
                      <span>{new Date(file.modifiedAt).toLocaleDateString('zh-CN')}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
          <div className="text-sm text-gray-500">
            {multiple ? '支持多选文件' : '单选文件'}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedFiles.size === 0}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                selectedFiles.size > 0
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              )}
            >
              确认选择
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}