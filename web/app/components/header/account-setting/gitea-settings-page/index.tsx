'use client'

import {
  RiCheckLine,
  RiCloseLine,
  RiDownloadLine,
  RiEyeLine,
  RiEyeOffLine,
  RiLoader4Line,
  RiRefreshLine,
  RiSave3Line,
} from '@remixicon/react'
import { useEffect, useRef, useState } from 'react'
import Button from '@/app/components/base/button'
import Toast from '@/app/components/base/toast'
import { API_PREFIX } from '@/config'

type GiteaConfig = {
  gitea_url: string
  gitea_owner: string
  gitea_repo: string
  gitea_token: string
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
  const [config, setConfig] = useState<GiteaConfig>({
    gitea_url: '',
    gitea_owner: '',
    gitea_repo: '',
    gitea_token: '',
  })
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean, message: string } | null>(null)
  const [autoDownloading, setAutoDownloading] = useState(false)
  const hasAutoDownloaded = useRef(false)

  useEffect(() => {
    loadConfig()
  }, [])

  // 自动下载配置文件(仅执行一次)
  useEffect(() => {
    if (!loading && !hasAutoDownloaded.current && config.gitea_url) {
      hasAutoDownloaded.current = true
      autoDownloadConfig()
    }
  }, [loading, config.gitea_url])

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

  const autoDownloadConfig = async () => {
    setAutoDownloading(true)
    try {
      await downloadConfig(true)
    }
    finally {
      setAutoDownloading(false)
    }
  }

  const downloadConfig = async (isAuto = false) => {
    try {
      // 获取完整配置(包含未 masked 的 token)
      const configResponse = await fetch(`${API_PREFIX}/gitea/config/download`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      let downloadConfig: any = {}
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

      if (!isAuto) {
        Toast.notify({
          type: 'success',
          message: 'FileBay 配置文件已下载成功',
        })
      }
    }
    catch (error) {
      console.error('Download failed:', error)
      if (!isAuto) {
        Toast.notify({
          type: 'error',
          message: `下载失败: ${error}`,
        })
      }
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await fetch(`${API_PREFIX}/gitea/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(config),
      })
      if (!res.ok)
        throw new Error('Failed to save config')
      const data = await res.json()
      Toast.notify({
        type: 'success',
        message: data.message || '配置保存成功',
      })
      loadConfig()
    }
    catch {
      Toast.notify({
        type: 'error',
        message: '保存配置失败',
      })
    }
    finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await fetch(`${API_PREFIX}/gitea/config/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(config),
      })
      if (!res.ok)
        throw new Error('Failed to test connection')
      const data = await res.json()
      setTestResult(data)
      Toast.notify({
        type: data.success ? 'success' : 'error',
        message: data.message,
      })
    }
    catch {
      setTestResult({
        success: false,
        message: '测试连接失败',
      })
      Toast.notify({
        type: 'error',
        message: '测试连接失败',
      })
    }
    finally {
      setTesting(false)
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
    <div className="w-full">
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="space-y-6">
          {/* Gitea URL */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Gitea 服务器地址
            </label>
            <input
              type="text"
              value={config.gitea_url}
              onChange={e => setConfig({ ...config, gitea_url: e.target.value })}
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
              onChange={e => setConfig({ ...config, gitea_owner: e.target.value })}
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
              onChange={e => setConfig({ ...config, gitea_repo: e.target.value })}
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
                onChange={e => setConfig({ ...config, gitea_token: e.target.value })}
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

          {/* Test Result */}
          {testResult && (
            <div
              className={`rounded-lg border p-4 ${
                testResult.success
                  ? 'border-green-200 bg-green-50'
                  : 'border-red-200 bg-red-50'
              }`}
            >
              <div className="flex items-start gap-3">
                {testResult.success
                  ? (
                      <RiCheckLine className="mt-0.5 h-5 w-5 shrink-0 text-green-600" />
                    )
                  : (
                      <RiCloseLine className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
                    )}
                <div className="flex-1">
                  <p
                    className={`text-sm font-medium ${
                      testResult.success ? 'text-green-900' : 'text-red-900'
                    }`}
                  >
                    {testResult.success ? '连接成功' : '连接失败'}
                  </p>
                  <p
                    className={`mt-1 text-sm ${
                      testResult.success ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    {testResult.message}
                  </p>
                </div>
              </div>
            </div>
          )}

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
              onClick={handleTest}
              disabled={testing}
              className="flex items-center gap-2"
            >
              {testing
                ? (
                    <RiLoader4Line className="h-4 w-4 animate-spin" />
                  )
                : (
                    <RiRefreshLine className="h-4 w-4" />
                  )}
              测试连接
            </Button>

            <Button
              onClick={() => downloadConfig(false)}
              disabled={autoDownloading}
              className="flex items-center gap-2"
            >
              {autoDownloading
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
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h3 className="mb-2 text-sm font-medium text-blue-900">
            📝 配置说明
          </h3>
          <ul className="space-y-1 text-sm text-blue-700">
            <li>• 在 FileBay 中创建一个用于文件存储的仓库</li>
            <li>• 在 FileBay 设置 → 应用 → 生成新令牌，选择 repo 权限</li>
            <li>• 填写上述配置信息并点击"测试连接"验证</li>
            <li>• 配置成功后，文件选择器将从 FileBay 仓库获取文件</li>
            <li>• 注意：当前配置为临时配置，重启后失效。永久配置请修改 api/.env 文件</li>
          </ul>
        </div>

        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <h3 className="mb-2 text-sm font-medium text-green-900">
            💻 Desktop App 集成
          </h3>
          <ul className="space-y-1 text-sm text-green-700">
            <li>• 登录后系统会自动下载 FileBay 配置文件到本地</li>
            <li>• 也可以点击"下载配置文件"按钮手动下载</li>
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
