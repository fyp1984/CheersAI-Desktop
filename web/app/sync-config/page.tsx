'use client'

import { useState } from 'react'
import { RiCheckboxCircleLine, RiErrorWarningLine, RiLoader4Line } from '@remixicon/react'

export default function SyncConfigPage() {
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<{
    success: boolean
    message: string
    logs: string[]
    config?: any
  } | null>(null)

  const syncConfig = async () => {
    setSyncing(true)
    setResult(null)
    
    const logs: string[] = []
    
    try {
      // 步骤 1: 获取用户信息
      logs.push('📝 步骤 1: 获取用户信息...')
      setResult({ success: false, message: '正在获取用户信息...', logs: [...logs] })
      
      const userResponse = await fetch('/console/api/account/profile', {
        credentials: 'include'
      })
      
      if (!userResponse.ok) {
        throw new Error('未登录或会话过期')
      }
      
      const user = await userResponse.json()
      logs.push(`✓ 用户信息获取成功`)
      logs.push(`  - ID: ${user.id}`)
      logs.push(`  - 邮箱: ${user.email}`)
      logs.push(`  - 姓名: ${user.name}`)
      setResult({ success: false, message: '正在获取配置...', logs: [...logs] })
      
      // 步骤 2: 获取 FileBay 配置
      logs.push('')
      logs.push('📝 步骤 2: 获取 FileBay 配置...')
      setResult({ success: false, message: '正在获取 FileBay 配置...', logs: [...logs] })
      
      const configResponse = await fetch('/console/api/gitea/config/download', {
        credentials: 'include'
      })
      
      if (!configResponse.ok) {
        throw new Error('获取 FileBay 配置失败')
      }
      
      const config = await configResponse.json()
      logs.push(`✓ FileBay 配置获取成功`)
      logs.push(`  - URL: ${config.gitea_url}`)
      logs.push(`  - 用户名: ${config.gitea_owner}`)
      logs.push(`  - 仓库: ${config.gitea_repo}`)
      logs.push(`  - Token: ${config.gitea_token.substring(0, 20)}...`)
      setResult({ success: false, message: '正在检查 Vault Bridge...', logs: [...logs] })
      
      // 步骤 3: 检查 Vault Bridge
      logs.push('')
      logs.push('📝 步骤 3: 检查 Vault Bridge...')
      setResult({ success: false, message: '正在检查 Vault Bridge...', logs: [...logs] })
      
      const healthResponse = await fetch('http://localhost:8765/health')
      
      if (!healthResponse.ok) {
        throw new Error('Vault Bridge 未运行')
      }
      
      const health = await healthResponse.json()
      logs.push(`✓ Vault Bridge 运行正常`)
      logs.push(`  - 版本: ${health.version}`)
      logs.push(`  - 数据库: ${health.database}`)
      setResult({ success: false, message: '正在同步配置...', logs: [...logs] })
      
      // 步骤 4: 同步配置
      logs.push('')
      logs.push('📝 步骤 4: 同步配置到 Vault 数据库...')
      setResult({ success: false, message: '正在同步配置...', logs: [...logs] })
      
      const syncResponse = await fetch('http://localhost:8765/vault/config/filebay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          config: {
            url: config.gitea_url,
            username: config.gitea_owner,
            repoName: config.gitea_repo,
            email: user.email,
            token: config.gitea_token
          }
        })
      })
      
      if (!syncResponse.ok) {
        throw new Error('同步到 Vault 失败')
      }
      
      const syncResult = await syncResponse.json()
      logs.push(`✓ 配置同步成功`)
      logs.push(`  - 用户 ID: ${syncResult.user_id}`)
      logs.push(`  - 用户名: ${syncResult.username}`)
      logs.push(`  - 仓库: ${syncResult.repo_name}`)
      setResult({ success: false, message: '正在验证...', logs: [...logs] })
      
      // 步骤 5: 验证
      logs.push('')
      logs.push('📝 步骤 5: 验证配置已保存...')
      setResult({ success: false, message: '正在验证...', logs: [...logs] })
      
      const verifyResponse = await fetch(`http://localhost:8765/vault/config/filebay/${user.id}`)
      
      if (!verifyResponse.ok) {
        throw new Error('验证失败：配置未找到')
      }
      
      const savedConfig = await verifyResponse.json()
      logs.push(`✓ 验证成功！配置已保存到 Vault 数据库`)
      logs.push(`  - 更新时间: ${savedConfig.updatedAt}`)
      logs.push('')
      logs.push('🎉 同步完成！')
      
      setResult({
        success: true,
        message: '配置同步成功！',
        logs: [...logs],
        config: savedConfig
      })
      
    } catch (error: any) {
      logs.push('')
      logs.push(`❌ 错误: ${error.message}`)
      
      if (error.message.includes('未登录')) {
        logs.push('')
        logs.push('💡 解决方案:')
        logs.push('1. 请先登录到 Vault 系统')
        logs.push('2. 登录成功后，返回此页面重新同步')
      } else if (error.message.includes('Vault Bridge')) {
        logs.push('')
        logs.push('💡 解决方案:')
        logs.push('1. 打开命令行')
        logs.push('2. 运行: .\\start_vault_bridge.ps1')
        logs.push('3. 等待服务启动后，返回此页面重新同步')
      }
      
      setResult({
        success: false,
        message: `同步失败: ${error.message}`,
        logs: [...logs]
      })
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-2xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6 border-b-4 border-indigo-500 pb-4">
            🔄 同步 FileBay 配置到 Vault
          </h1>
          
          <div className="bg-blue-50 border-l-4 border-blue-500 p-6 mb-6 rounded">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 使用说明</h3>
            <ul className="space-y-2 text-blue-800">
              <li>1. 确保你已经登录到 Vault 系统</li>
              <li>2. 确保 Vault Bridge 服务正在运行（localhost:8765）</li>
              <li>3. 点击下面的"开始同步"按钮</li>
              <li>4. 系统会自动获取配置并同步到 Vault 数据库</li>
            </ul>
          </div>
          
          <button
            onClick={syncConfig}
            disabled={syncing}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-lg"
          >
            {syncing ? (
              <span className="flex items-center justify-center">
                <RiLoader4Line className="animate-spin mr-2" size={20} />
                正在同步...
              </span>
            ) : (
              <span className="flex items-center justify-center">
                🚀 开始同步
              </span>
            )}
          </button>
          
          {result && (
            <div className="mt-6">
              <div className={`p-6 rounded-lg border-2 ${
                result.success 
                  ? 'bg-green-50 border-green-500' 
                  : 'bg-red-50 border-red-500'
              }`}>
                <div className="flex items-center mb-4">
                  {result.success ? (
                    <RiCheckboxCircleLine className="text-green-600 mr-2" size={24} />
                  ) : (
                    <RiErrorWarningLine className="text-red-600 mr-2" size={24} />
                  )}
                  <h3 className={`text-lg font-semibold ${
                    result.success ? 'text-green-900' : 'text-red-900'
                  }`}>
                    {result.message}
                  </h3>
                </div>
                
                <div className="bg-white rounded p-4 font-mono text-sm whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto">
                  {result.logs.join('\n')}
                </div>
                
                {result.success && result.config && (
                  <div className="mt-4 bg-white rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">📦 已保存的配置</h4>
                    <div className="space-y-2">
                      <div className="flex">
                        <span className="font-semibold text-indigo-600 w-32">URL:</span>
                        <span className="text-gray-700">{result.config.url}</span>
                      </div>
                      <div className="flex">
                        <span className="font-semibold text-indigo-600 w-32">用户名:</span>
                        <span className="text-gray-700">{result.config.username}</span>
                      </div>
                      <div className="flex">
                        <span className="font-semibold text-indigo-600 w-32">仓库:</span>
                        <span className="text-gray-700">{result.config.repoName}</span>
                      </div>
                      <div className="flex">
                        <span className="font-semibold text-indigo-600 w-32">邮箱:</span>
                        <span className="text-gray-700">{result.config.email}</span>
                      </div>
                      <div className="flex">
                        <span className="font-semibold text-indigo-600 w-32">Token:</span>
                        <span className="text-gray-700 font-mono">{result.config.token.substring(0, 20)}...</span>
                      </div>
                      <div className="flex">
                        <span className="font-semibold text-indigo-600 w-32">更新时间:</span>
                        <span className="text-gray-700">{new Date(result.config.updatedAt).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {result.success && (
                <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                  <h4 className="font-semibold text-yellow-900 mb-2">🎯 下一步</h4>
                  <ul className="space-y-1 text-yellow-800 text-sm">
                    <li>1. 配置已成功同步到 Vault 数据库</li>
                    <li>2. 现在可以在脱敏应用中读取这个配置</li>
                    <li>3. 或者打开测试页面验证: <a href="/test-config" className="underline">测试配置加载</a></li>
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
