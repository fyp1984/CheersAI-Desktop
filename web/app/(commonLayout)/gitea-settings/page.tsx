'use client'

import {
  RiDownloadLine,
  RiEyeLine,
  RiEyeOffLine,
  RiLoader4Line,
  RiSave3Line,
} from '@remixicon/react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import Toast from '@/app/components/base/toast'
import { API_PREFIX } from '@/config'
import { post } from '@/service/base'

type GiteaConfig = {
  gitea_url: string
  gitea_owner: string
  gitea_repo: string
  gitea_token: string
}

type SaveFeedback = {
  type: 'success' | 'error'
  message: string
}

const validateConfig = (config: GiteaConfig) => {
  if (!config.gitea_url.trim())
    return 'FileBay 服务器地址不能为空'
  if (!/^https?:\/\/.+/i.test(config.gitea_url.trim()))
    return 'FileBay 服务器地址格式不正确'
  if (!config.gitea_owner.trim())
    return '仓库所有者不能为空'
  if (!config.gitea_repo.trim())
    return '仓库名称不能为空'
  return ''
}

type FileBayConfig = {
  url: string
  username: string
  repoName: string
  email: string
  token: string
  downloadedAt: string
  version: string
}

export default function GiteaSettingsPage() {
  useTranslation()
  const [config, setConfig] = useState<GiteaConfig>({
    gitea_url: '',
    gitea_owner: '',
    gitea_repo: '',
    gitea_token: '',
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState<SaveFeedback | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  async function loadConfig() {
    setLoading(true)
    try {
      const res = await fetch(`${API_PREFIX}/gitea/config`, {
        credentials: 'include',
      })
      if (!res.ok)
        throw new Error('Failed to load config')
      const data = await res.json()
      setConfig(data)
    }
    catch {
      Toast.notify({
        type: 'error',
        message: '加载配置失败',
      })
    }
    finally {
      setLoading(false)
    }
  }

  const downloadConfig = async () => {
    setDownloading(true)
    try {
      // 获取完整配置(包含未 masked 的 token)
      const configResponse = await fetch(`${API_PREFIX}/gitea/config/download`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      let downloadConfig: GiteaConfig = {
        gitea_url: '',
        gitea_owner: '',
        gitea_repo: '',
        gitea_token: '',
      }
      if (configResponse.ok) {
        downloadConfig = await configResponse.json()
      }
      else {
        throw new Error('Failed to fetch config')
      }

      // 获取用户邮箱
      let userEmail = ''
      try {
        const userResponse = await fetch(`${API_PREFIX}/account/profile`, {
          method: 'GET',
          credentials: 'include',
        })
        if (userResponse.ok) {
          const userData = await userResponse.json()
          userEmail = userData.email || ''
        }
      }
      catch (e) {
        console.warn('Failed to get user email:', e)
      }

      // 构建配置对象
      const fileBayConfig: FileBayConfig = {
        url: downloadConfig.gitea_url || '',
        username: downloadConfig.gitea_owner || '',
        repoName: downloadConfig.gitea_repo || '',
        email: userEmail,
        token: downloadConfig.gitea_token || '',
        downloadedAt: new Date().toISOString(),
        version: '1.0.0',
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

      Toast.notify({
        type: 'success',
        message: 'FileBay 配置文件已下载成功',
      })
    }
    catch (error) {
      console.error('Download failed:', error)
      Toast.notify({
        type: 'error',
        message: `下载失败: ${error}`,
      })
    }
    finally {
      setDownloading(false)
    }
  }

  const handleSave = async () => {
    const validationMessage = validateConfig(config)
    if (validationMessage) {
      setSaveFeedback({
        type: 'error',
        message: validationMessage,
      })
      Toast.notify({
        type: 'error',
        message: validationMessage,
      })
      return
    }

    setSaving(true)
    try {
      const data = await post<{ message?: string }>('/gitea/config', { body: config })
      setSaveFeedback({
        type: 'success',
        message: data.message || '配置保存成功',
      })
      Toast.notify({
        type: 'success',
        message: data.message || '配置保存成功',
      })
      loadConfig()
    }
    catch (error) {
      setSaveFeedback({
        type: 'error',
        message: error instanceof Error ? error.message : '保存配置失败',
      })
      Toast.notify({
        type: 'error',
        message: error instanceof Error ? error.message : '保存配置失败',
      })
    }
    finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RiLoader4Line className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Gitea 配置</h1>
        <p className="mt-2 text-sm text-gray-600">
          配置 Gitea 服务器连接信息，用于文件存储和管理
        </p>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="space-y-6">
          {saveFeedback && (
            <div
              role="alert"
              className={
                saveFeedback.type === 'success'
                  ? 'rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700'
                  : 'rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'
              }
            >
              {saveFeedback.message}
            </div>
          )}
          {/* Gitea URL */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Gitea 服务器地址
            </label>
            <input
              type="text"
              value={config.gitea_url}
              onChange={(e) => {
                setSaveFeedback(null)
                setConfig({ ...config, gitea_url: e.target.value })
              }}
              placeholder="http://localhost:3000"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Gitea 服务器的完整 URL（包括端口）
            </p>
          </div>

          {/* Repository Owner */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              仓库所有者
            </label>
            <input
              type="text"
              value={config.gitea_owner}
              onChange={(e) => {
                setSaveFeedback(null)
                setConfig({ ...config, gitea_owner: e.target.value })
              }}
              placeholder="cheersai"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Gitea 用户名或组织名
            </p>
          </div>

          {/* Repository Name */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              仓库名称
            </label>
            <input
              type="text"
              value={config.gitea_repo}
              onChange={(e) => {
                setSaveFeedback(null)
                setConfig({ ...config, gitea_repo: e.target.value })
              }}
              placeholder="file-storage"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              用于存储文件的仓库名称
            </p>
          </div>

          {/* API Token */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              API Token
            </label>
            <div className="relative">
              <input
                type={showToken ? 'text' : 'password'}
                value={config.gitea_token}
                onChange={(e) => {
                  setSaveFeedback(null)
                  setConfig({ ...config, gitea_token: e.target.value })
                }}
                placeholder="输入新的 Token 或留空保持不变"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
              >
                {showToken
                  ? (
                      <RiEyeOffLine className="h-5 w-5" />
                    )
                  : (
                      <RiEyeLine className="h-5 w-5" />
                    )}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              在 Gitea 设置中生成的 API Token（需要 repo 权限）
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 border-t border-gray-200 pt-4">
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2"
            >
              {saving
                ? (
                    <RiLoader4Line className="h-4 w-4 animate-spin" />
                  )
                : (
                    <RiSave3Line className="h-4 w-4" />
                  )}
              保存配置
            </Button>

            <Button
              onClick={downloadConfig}
              disabled={downloading}
              className="flex items-center gap-2"
            >
              {downloading
                ? (
                    <RiLoader4Line className="h-4 w-4 animate-spin" />
                  )
                : (
                    <RiDownloadLine className="h-4 w-4" />
                  )}
              下载配置文件
            </Button>

            <Button
              onClick={loadConfig}
              disabled={loading}
              className="ml-auto"
            >
              重置
            </Button>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 space-y-4">
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <h3 className="mb-2 text-sm font-medium text-green-900">
            💻 Desktop App 集成
          </h3>
          <ul className="space-y-1 text-sm text-green-700">
            <li>• 点击"下载配置文件"按钮下载 FileBay 配置</li>
            <li>• 打开 Desktop App，进入"沙箱管理"页面</li>
            <li>• 在 FileBay 配置管理区域，点击"导入配置"按钮</li>
            <li>• 选择下载的 filebay-config.json 文件导入</li>
            <li>• 导入成功后，Desktop App 即可使用 FileBay 进行文件脱敏</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
