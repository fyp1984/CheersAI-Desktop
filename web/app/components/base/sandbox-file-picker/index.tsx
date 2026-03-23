'use client'

import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  RiCloseLine,
  RiFile3Line,
  RiFolder3Line,
  RiRefreshLine,
  RiShieldCheckLine,
} from '@remixicon/react'
import { useSandboxSecurity } from '@/context/sandbox-security-context'
import { get } from '@/service/base'

interface SandboxFile {
  name: string
  size: number
  created_at: string
  type?: string
  path?: string
}

interface SandboxFilePickerProps {
  open: boolean
  onClose: () => void
  onSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
}

export function SandboxFilePicker({ open, onClose, onSelect, accept, multiple }: SandboxFilePickerProps) {
  const { sandboxPath: contextPath } = useSandboxSecurity()
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<SandboxFile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [giteaOwner, setGiteaOwner] = useState('root')
  const [giteaRepo, setGiteaRepo] = useState('cheersAI')
  const [giteaDefaultPath, setGiteaDefaultPath] = useState('')

  const loadFiles = useCallback(async (path: string = '') => {
    setLoading(true)
    setError('')
    try {
      const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      const url = `http://localhost:5001/console/api/gitea/files?path=${encodeURIComponent(path)}`
      const res = await fetch(url, {
        credentials: 'include',
        headers: {
          'X-CSRF-Token': csrfToken,
        },
      })
      
      if (!res.ok) {
        if (res.status === 401) {
          setError('未登录或会话已过期，请重新登录')
          setLoading(false)
          return
        }
        if (res.status === 500) {
          const errorData = await res.json().catch(() => ({}))
          const errorMsg = errorData.error || '服务器错误'
          if (errorMsg.includes('GITEA_URL') || errorMsg.includes('GITEA_TOKEN')) {
            setError('FileBay 未配置，请先在「数据安全」页面配置 FileBay 连接信息')
          } else {
            setError(`加载失败: ${errorMsg}`)
          }
          setLoading(false)
          return
        }
        throw new Error(`HTTP ${res.status}`)
      }
      
      const data = await res.json()
      let fileList: SandboxFile[] = (data.files || []).map((f: any) => ({
        name: f.name,
        size: f.size || 0,
        created_at: new Date().toISOString(),
        type: f.type,
        path: f.path,
      }))

      if (accept) {
        const exts = accept.split(',').map(e => e.trim().toLowerCase()).filter(e => e.startsWith('.'))
        if (exts.length > 0) {
          const filtered = fileList.filter(f =>
            exts.some(ext => f.name.toLowerCase().endsWith(ext)),
          )
          if (filtered.length > 0)
            fileList = filtered
        }
      }
      
      fileList = fileList.filter(f => !f.name.endsWith('.mapping.json'))
      
      setFiles(fileList)
    }
    catch (err) {
      console.error('Failed to load files from Gitea:', err)
      setError('无法从 FileBay 加载文件列表，请确认 FileBay 配置正确')
    }
    finally {
      setLoading(false)
    }
  }, [accept])

  useEffect(() => {
    if (open) {
      const loadGiteaConfig = async () => {
        try {
          const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
          const res = await fetch('http://localhost:5001/console/api/gitea/config', {
            credentials: 'include',
            headers: { 'X-CSRF-Token': csrfToken },
          })
          if (res.ok) {
            const config = await res.json()
            if (config.gitea_owner) setGiteaOwner(config.gitea_owner)
            if (config.gitea_repo) setGiteaRepo(config.gitea_repo)
            const defaultPath = config.gitea_path || ''
            setGiteaDefaultPath(defaultPath)
            setCurrentPath(defaultPath)
            loadFiles(defaultPath)
          }
        } catch (err) {
          console.error('Failed to load Gitea config:', err)
          setCurrentPath('')
          loadFiles('')
        }
      }
      
      loadGiteaConfig()
      setSelected(new Set())
    }
  }, [open, loadFiles])

  const handleFolderClick = (folderPath: string) => {
    setCurrentPath(folderPath)
    loadFiles(folderPath)
    setSelected(new Set())
  }

  const handleBackClick = () => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/')
    setCurrentPath(parentPath)
    loadFiles(parentPath)
    setSelected(new Set())
  }

  const toggleSelect = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(name))
        next.delete(name)
      else if (!multiple)
        return new Set([name])
      else
        next.add(name)
      return next
    })
  }

  const handleConfirm = async () => {
    if (selected.size === 0) return
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
    const filePromises = Array.from(selected).map(async (name) => {
      const filePath = currentPath ? `${currentPath}/${name}` : name
      
      const res = await fetch(
        `http://localhost:5001/console/api/gitea/files/${encodeURIComponent(filePath)}`,
        {
          credentials: 'include',
          headers: {
            'X-CSRF-Token': csrfToken,
          },
        },
      )
      if (!res.ok) throw new Error(`Failed to read ${name}`)
      
      const blob = await res.blob()
      const file = new File([blob], name)
      
      ;(file as unknown as Record<string, unknown>)._fromSandbox = true
      return file
    })
    try {
      const fileObjects = await Promise.all(filePromises)
      onSelect(fileObjects)
      onClose()
    }
    catch (err) {
      setError('从 FileBay 读取文件失败')
      console.error('Failed to read files from Gitea:', err)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50">
      <div className="w-[560px] max-h-[70vh] bg-white rounded-2xl shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <RiShieldCheckLine className="w-5 h-5 text-blue-600" />
            <h3 className="text-base font-semibold text-gray-900">FileBay 文件选择</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100">
            <RiCloseLine className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="px-5 py-2 bg-blue-50 border-b border-blue-100 flex items-center gap-2">
          <RiFolder3Line className="w-4 h-4 text-blue-500 shrink-0" />
          <span className="text-xs text-blue-700 truncate font-mono">
            {currentPath ? `${giteaOwner}/${giteaRepo}/${currentPath}` : `${giteaOwner}/${giteaRepo}`}
          </span>
          {currentPath && (
            <button onClick={handleBackClick} className="p-1 rounded hover:bg-blue-100 shrink-0" title="返回上级">
              <span className="text-xs text-blue-600">↑ 返回</span>
            </button>
          )}
          <button onClick={() => loadFiles(currentPath)} className="ml-auto p-1 rounded hover:bg-blue-100 shrink-0">
            <RiRefreshLine className="w-3.5 h-3.5 text-blue-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2 min-h-[200px]">
          {loading && (
            <div className="flex items-center justify-center py-12 text-sm text-gray-400">加载中...</div>
          )}
          {error && (
            <div className="flex items-center justify-center py-12 text-sm text-red-500">{error}</div>
          )}
          {!loading && !error && files.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <RiFile3Line className="w-10 h-10 mb-2" />
              <span className="text-sm">FileBay 仓库中没有文件</span>
              <span className="text-xs mt-1">请先在 FileBay 仓库中上传文件</span>
            </div>
          )}
          {!loading && files.map(f => (
            <button
              key={f.name}
              onClick={() => f.type === 'dir' ? handleFolderClick(f.path || f.name) : toggleSelect(f.name)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-left transition-colors ${
                f.type === 'dir' ? 'hover:bg-blue-50 border border-transparent' :
                selected.has(f.name)
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50 border border-transparent'
              }`}
            >
              {f.type === 'dir' ? (
                <RiFolder3Line className="w-4 h-4 shrink-0 text-yellow-500" />
              ) : (
                <RiFile3Line className={`w-4 h-4 shrink-0 ${selected.has(f.name) ? 'text-blue-600' : 'text-gray-400'}`} />
              )}
              <div className="flex-1 min-w-0">
                <div className={`text-sm truncate ${
                  f.type === 'dir' ? 'text-gray-700 font-medium' :
                  selected.has(f.name) ? 'text-blue-700 font-medium' : 'text-gray-700'
                }`}>
                  {f.name}{f.type === 'dir' ? '/' : ''}
                </div>
                <div className="text-xs text-gray-400">{formatSize(f.size)}</div>
              </div>
              {selected.has(f.name) && (
                <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
          <p className="text-xs text-gray-500">从 FileBay 仓库选择文件</p>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-1.5 text-sm text-gray-600 rounded-lg hover:bg-gray-200">
              取消
            </button>
            <button
              onClick={handleConfirm}
              disabled={selected.size === 0}
              className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              确认选择
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
