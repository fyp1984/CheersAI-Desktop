'use client'

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  RiCheckLine,
  RiCloseLine,
  RiEyeLine,
  RiEyeOffLine,
  RiLoader4Line,
  RiRefreshLine,
  RiSave3Line,
} from '@remixicon/react'
import Button from '@/app/components/base/button'
import Toast from '@/app/components/base/toast'

interface GiteaConfig {
  gitea_url: string
  gitea_owner: string
  gitea_repo: string
  gitea_token: string
}

export default function GiteaSettingsPage() {
  const { t } = useTranslation()
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
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:5001/console/api/gitea/config', {
        credentials: 'include',
      })
      if (!res.ok) throw new Error('Failed to load config')
      const data = await res.json()
      setConfig(data)
    }
    catch (error) {
      Toast.notify({
        type: 'error',
        message: '加载配置失败',
      })
    }
    finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await fetch('http://localhost:5001/console/api/gitea/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(config),
      })
      if (!res.ok) throw new Error('Failed to save config')
      const data = await res.json()
      Toast.notify({
        type: 'success',
        message: data.message || '配置保存成功',
      })
      loadConfig()
    }
    catch (error) {
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
      const res = await fetch('http://localhost:5001/console/api/gitea/config/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(config),
      })
      if (!res.ok) throw new Error('Failed to test connection')
      const data = await res.json()
      setTestResult(data)
      Toast.notify({
        type: data.success ? 'success' : 'error',
        message: data.message,
      })
    }
    catch (error) {
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
      <div className="flex items-center justify-center h-96">
        <RiLoader4Line className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Gitea 配置</h1>
        <p className="mt-2 text-sm text-gray-600">
          配置 Gitea 服务器连接信息，用于文件存储和管理
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="space-y-6">
          {/* Gitea URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Gitea 服务器地址
            </label>
            <input
              type="text"
              value={config.gitea_url}
              onChange={e => setConfig({ ...config, gitea_url: e.target.value })}
              placeholder="http://localhost:3000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-gray-500">
              Gitea 服务器的完整 URL（包括端口）
            </p>
          </div>

          {/* Repository Owner */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              仓库所有者
            </label>
            <input
              type="text"
              value={config.gitea_owner}
              onChange={e => setConfig({ ...config, gitea_owner: e.target.value })}
              placeholder="cheersai"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-gray-500">
              Gitea 用户名或组织名
            </p>
          </div>

          {/* Repository Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              仓库名称
            </label>
            <input
              type="text"
              value={config.gitea_repo}
              onChange={e => setConfig({ ...config, gitea_repo: e.target.value })}
              placeholder="file-storage"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-gray-500">
              用于存储文件的仓库名称
            </p>
          </div>

          {/* API Token */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Token
            </label>
            <div className="relative">
              <input
                type={showToken ? 'text' : 'password'}
                value={config.gitea_token}
                onChange={e => setConfig({ ...config, gitea_token: e.target.value })}
                placeholder="输入新的 Token 或留空保持不变"
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
              >
                {showToken ? (
                  <RiEyeOffLine className="w-5 h-5" />
                ) : (
                  <RiEyeLine className="w-5 h-5" />
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
              className={`p-4 rounded-lg border ${
                testResult.success
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-start gap-3">
                {testResult.success ? (
                  <RiCheckLine className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                ) : (
                  <RiCloseLine className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
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
                    className={`text-sm mt-1 ${
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
          <div className="flex items-center gap-3 pt-4 border-t border-gray-200">
            <Button
              type="primary"
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2"
            >
              {saving ? (
                <RiLoader4Line className="w-4 h-4 animate-spin" />
              ) : (
                <RiSave3Line className="w-4 h-4" />
              )}
              保存配置
            </Button>

            <Button
              onClick={handleTest}
              disabled={testing}
              className="flex items-center gap-2"
            >
              {testing ? (
                <RiLoader4Line className="w-4 h-4 animate-spin" />
              ) : (
                <RiRefreshLine className="w-4 h-4" />
              )}
              测试连接
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
      <div className="mt-6 bg-blue-50 rounded-lg border border-blue-200 p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">
          📝 配置说明
        </h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• 在 Gitea 中创建一个用于文件存储的仓库</li>
          <li>• 在 Gitea 设置 → 应用 → 生成新令牌，选择 repo 权限</li>
          <li>• 填写上述配置信息并点击"测试连接"验证</li>
          <li>• 配置成功后，文件选择器将从 Gitea 仓库获取文件</li>
          <li>• 注意：当前配置为临时配置，重启后失效。永久配置请修改 api/.env 文件</li>
        </ul>
      </div>
    </div>
  )
}
