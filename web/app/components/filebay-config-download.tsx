'use client'

import { useState } from 'react'
import Button from '@/app/components/base/button'
import { RiDownloadLine, RiFileTextLine, RiCheckboxCircleLine, RiErrorWarningLine } from '@remixicon/react'

interface FileBayConfig {
  url: string
  username: string
  repoName: string
  email: string
  token: string
  downloadedAt: string
  version: string
}

export function FileBayConfigDownload() {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const downloadConfig = async () => {
    setLoading(true)
    setStatus('idle')
    setMessage('')

    try {
      // 获取 FileBay 配置 (使用下载专用端点,包含完整 token)
      const configResponse = await fetch('/console/api/gitea/config/download', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      let config: any = {}
      if (configResponse.ok) {
        config = await configResponse.json()
      } else {
        console.warn('API failed, using empty config')
      }

      // 获取用户邮箱
      let userEmail = ''
      try {
        const userResponse = await fetch('/console/api/account/profile', {
          method: 'GET',
          credentials: 'include',
        })
        if (userResponse.ok) {
          const userData = await userResponse.json()
          userEmail = userData.email || ''
        }
      } catch (e) {
        console.warn('Failed to get user email:', e)
      }

      // 构建配置对象
      const fileBayConfig: FileBayConfig = {
        url: config.gitea_url || '',
        username: config.gitea_owner || '',
        repoName: config.gitea_repo || '',
        email: userEmail,
        token: config.gitea_token || '',
        downloadedAt: new Date().toISOString(),
        version: '1.0.0'
      }

      // 创建下载文件
      const configJson = JSON.stringify(fileBayConfig, null, 2)
      const blob = new Blob([configJson], { type: 'application/json' })
      const url = URL.createObjectURL(blob)

      // 触发下载
      const link = document.createElement('a')
      link.href = url
      link.download = 'filebay-config.json'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      setStatus('success')
      setMessage('FileBay 配置文件已下载成功')
    } catch (error) {
      console.error('Download failed:', error)
      setStatus('error')
      setMessage(`下载失败: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="flex items-center gap-3 mb-4">
        <RiFileTextLine className="w-6 h-6 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">FileBay 配置下载</h3>
      </div>
      
      <p className="text-gray-600 mb-6">
        下载 FileBay 配置文件到本地，然后导入到 Desktop App 沙箱中使用。
      </p>

      <div className="space-y-4">
        <Button
          onClick={downloadConfig}
          disabled={loading}
          variant="primary"
          className="w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              正在生成配置文件...
            </>
          ) : (
            <>
              <RiDownloadLine className="w-4 h-4" />
              下载 FileBay 配置文件
            </>
          )}
        </Button>

        {status === 'success' && (
          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
            <RiCheckboxCircleLine className="w-5 h-5 text-green-600" />
            <span className="text-green-800">{message}</span>
          </div>
        )}

        {status === 'error' && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
            <RiErrorWarningLine className="w-5 h-5 text-red-600" />
            <span className="text-red-800">{message}</span>
          </div>
        )}

        <div className="text-sm text-gray-500 space-y-2">
          <p><strong>使用步骤:</strong></p>
          <ol className="list-decimal list-inside space-y-1 ml-4">
            <li>点击上方按钮下载配置文件</li>
            <li>打开 Desktop App</li>
            <li>进入沙箱管理页面</li>
            <li>导入下载的 filebay-config.json 文件</li>
            <li>在脱敏功能中使用配置</li>
          </ol>
        </div>
      </div>
    </div>
  )
}