'use client'

import {
  RiCloseLine,
  RiFile3Line,
  RiFolder3Line,
  RiRefreshLine,
  RiShieldCheckLine,
} from '@remixicon/react'
import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { API_PREFIX } from '@/config'
import { useSandboxSecurity } from '@/context/use-sandbox-security'

type SandboxFile = {
  name: string
  size: number
  created_at: string
  type?: string
  path?: string
}

type SandboxFilePickerProps = {
  open: boolean
  onClose: () => void
  onSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
}

type GiteaListFile = {
  name: string
  size?: number
  type?: string
  path?: string
}

export function SandboxFilePicker({ open, onClose, onSelect, accept, multiple }: SandboxFilePickerProps) {
  useSandboxSecurity()
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<SandboxFile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<Set<string>>(() => new Set())
  const [giteaOwner, setGiteaOwner] = useState('root')
  const [giteaRepo, setGiteaRepo] = useState('cheersAI')

  const loadFiles = useCallback(async (path: string = '') => {
    setLoading(true)
    setError('')
    try {
      const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      const url = `${API_PREFIX}/gitea/files?path=${encodeURIComponent(path)}`
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
          }
          else {
            setError(`加载失败: ${errorMsg}`)
          }
          setLoading(false)
          return
        }
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()
      let fileList: SandboxFile[] = ((data.files || []) as GiteaListFile[]).map(f => ({
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
          const res = await fetch(`${API_PREFIX}/gitea/config`, {
            credentials: 'include',
            headers: { 'X-CSRF-Token': csrfToken },
          })
          if (res.ok) {
            const config = await res.json()
            if (config.gitea_owner)
              setGiteaOwner(config.gitea_owner)
            if (config.gitea_repo)
              setGiteaRepo(config.gitea_repo)
            const defaultPath = config.gitea_path || ''
            setCurrentPath(defaultPath)
            loadFiles(defaultPath)
          }
        }
        catch (err) {
          console.error('Failed to load Gitea config:', err)
          setCurrentPath('')
          loadFiles('')
        }
      }

      loadGiteaConfig()
    }
  }, [loadFiles, open])

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
    if (selected.size === 0)
      return
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
    const filePromises = Array.from(selected).map(async (name) => {
      const filePath = currentPath ? `${currentPath}/${name}` : name

      const res = await fetch(
        `${API_PREFIX}/gitea/files/${encodeURIComponent(filePath)}`,
        {
          credentials: 'include',
          headers: {
            'X-CSRF-Token': csrfToken,
          },
        },
      )
      if (!res.ok)
        throw new Error(`Failed to read ${name}`)

      const blob = await res.blob()
      const file = new File([blob], name)

      ;(file as unknown as Record<string, unknown>)._fromSandbox = true
      return file
    })
    try {
      const fileObjects = await Promise.all(filePromises)
      onSelect(fileObjects)
      setSelected(new Set())
      onClose()
    }
    catch (err) {
      setError('从 FileBay 读取文件失败')
      console.error('Failed to read files from Gitea:', err)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024)
      return `${bytes} B`
    if (bytes < 1024 * 1024)
      return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleClose = () => {
    setSelected(new Set())
    onClose()
  }

  if (!open)
    return null

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50">
      <div className="flex max-h-[70vh] w-[560px] flex-col rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
          <div className="flex items-center gap-2">
            <RiShieldCheckLine className="h-5 w-5 text-blue-600" />
            <h3 className="text-base font-semibold text-gray-900">FileBay 文件选择</h3>
          </div>
          <button onClick={handleClose} className="rounded-lg p-1 hover:bg-gray-100">
            <RiCloseLine className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        <div className="flex items-center gap-2 border-b border-blue-100 bg-blue-50 px-5 py-2">
          <RiFolder3Line className="h-4 w-4 shrink-0 text-blue-500" />
          <span className="truncate font-mono text-xs text-blue-700">
            {currentPath ? `${giteaOwner}/${giteaRepo}/${currentPath}` : `${giteaOwner}/${giteaRepo}`}
          </span>
          {currentPath && (
            <button onClick={handleBackClick} className="shrink-0 rounded p-1 hover:bg-blue-100" title="返回上级">
              <span className="text-xs text-blue-600">↑ 返回</span>
            </button>
          )}
          <button onClick={() => loadFiles(currentPath)} className="ml-auto shrink-0 rounded p-1 hover:bg-blue-100">
            <RiRefreshLine className="h-3.5 w-3.5 text-blue-500" />
          </button>
        </div>

        <div className="min-h-[200px] flex-1 overflow-y-auto px-3 py-2">
          {loading && (
            <div className="flex items-center justify-center py-12 text-sm text-gray-400">加载中...</div>
          )}
          {error && (
            <div className="flex items-center justify-center py-12 text-sm text-red-500">{error}</div>
          )}
          {!loading && !error && files.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <RiFile3Line className="mb-2 h-10 w-10" />
              <span className="text-sm">FileBay 仓库中没有文件</span>
              <span className="mt-1 text-xs">请先在 FileBay 仓库中上传文件</span>
            </div>
          )}
          {!loading && files.map(f => (
            <button
              key={f.name}
              onClick={() => (f.type === 'dir' ? handleFolderClick(f.path || f.name) : toggleSelect(f.name))}
              className={`mb-0.5 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors ${
                f.type === 'dir'
                  ? 'border border-transparent hover:bg-blue-50'
                  : selected.has(f.name)
                    ? 'border border-blue-200 bg-blue-50'
                    : 'border border-transparent hover:bg-gray-50'
              }`}
            >
              {f.type === 'dir'
                ? (
                    <RiFolder3Line className="h-4 w-4 shrink-0 text-yellow-500" />
                  )
                : (
                    <RiFile3Line className={`h-4 w-4 shrink-0 ${selected.has(f.name) ? 'text-blue-600' : 'text-gray-400'}`} />
                  )}
              <div className="min-w-0 flex-1">
                <div className={`truncate text-sm ${
                  f.type === 'dir'
                    ? 'font-medium text-gray-700'
                    : selected.has(f.name) ? 'font-medium text-blue-700' : 'text-gray-700'
                }`}
                >
                  {f.name}
                  {f.type === 'dir' ? '/' : ''}
                </div>
                <div className="text-xs text-gray-400">{formatSize(f.size)}</div>
              </div>
              {selected.has(f.name) && (
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600">
                  <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between rounded-b-2xl border-t border-gray-100 bg-gray-50 px-5 py-3">
          <p className="text-xs text-gray-500">从 FileBay 仓库选择文件</p>
          <div className="flex items-center gap-2">
            <button onClick={handleClose} className="rounded-lg px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-200">
              取消
            </button>
            <button
              onClick={handleConfirm}
              disabled={selected.size === 0}
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
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
