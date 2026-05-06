/**
 * Vault 同步指示器组件
 * 
 * 显示 Vault 同步状态，并提供手动同步按钮
 */

'use client'

import { useEffect, useState } from 'react'
import { autoSyncToVault, checkVaultHealth } from '@/service/vault'
import Toast from '@/app/components/base/toast'

interface VaultSyncIndicatorProps {
  /** 是否自动同步 (登录后) */
  autoSync?: boolean
  /** 用户邮箱 */
  userEmail?: string
}

export default function VaultSyncIndicator({ 
  autoSync = false,
  userEmail 
}: VaultSyncIndicatorProps) {
  const [vaultAvailable, setVaultAvailable] = useState<boolean | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)

  // 检查 Vault 健康状态
  const checkHealth = async () => {
    try {
      const result = await checkVaultHealth()
      setVaultAvailable(result.available)
      return result.available
    } catch (error) {
      console.error('[Vault Sync] Health check failed:', error)
      setVaultAvailable(false)
      return false
    }
  }

  // 手动同步
  const handleManualSync = async () => {
    if (syncing) return

    setSyncing(true)
    try {
      const result = await autoSyncToVault()
      
      if (result.synced) {
        setLastSyncTime(new Date())
        Toast.notify({
          type: 'success',
          message: '配置已同步到 Vault',
        })
      } else {
        Toast.notify({
          type: 'warning',
          message: result.message,
        })
      }
    } catch (error) {
      console.error('[Vault Sync] Manual sync failed:', error)
      Toast.notify({
        type: 'error',
        message: '同步失败，请重试',
      })
    } finally {
      setSyncing(false)
    }
  }

  // 自动同步 (登录后)
  useEffect(() => {
    if (autoSync && userEmail) {
      console.log('[Vault Sync] Auto sync triggered for user:', userEmail)
      
      // 延迟 2 秒后自动同步，给 Vault 启动时间
      const timer = setTimeout(async () => {
        const available = await checkHealth()
        
        if (available) {
          console.log('[Vault Sync] Vault is available, starting auto sync')
          const result = await autoSyncToVault()
          
          if (result.synced) {
            setLastSyncTime(new Date())
            console.log('[Vault Sync] Auto sync completed successfully')
          } else {
            console.log('[Vault Sync] Auto sync skipped:', result.message)
          }
        } else {
          console.log('[Vault Sync] Vault is not available, skipping auto sync')
        }
      }, 2000)

      return () => clearTimeout(timer)
    }
  }, [autoSync, userEmail])

  // 定期检查 Vault 健康状态
  useEffect(() => {
    checkHealth()
    
    const interval = setInterval(() => {
      checkHealth()
    }, 30000) // 每 30 秒检查一次

    return () => clearInterval(interval)
  }, [])

  // 如果不显示指示器，返回 null
  if (vaultAvailable === null) {
    return null
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      {/* Vault 状态指示器 */}
      <div className="flex items-center gap-1">
        <div 
          className={`h-2 w-2 rounded-full ${
            vaultAvailable ? 'bg-green-500' : 'bg-gray-400'
          }`}
          title={vaultAvailable ? 'Vault 已连接' : 'Vault 未连接'}
        />
        <span className="text-gray-600">
          {vaultAvailable ? 'Vault' : 'Vault (离线)'}
        </span>
      </div>

      {/* 手动同步按钮 */}
      {vaultAvailable && (
        <button
          onClick={handleManualSync}
          disabled={syncing}
          className="text-blue-600 hover:text-blue-700 disabled:text-gray-400"
          title="同步配置到 Vault"
        >
          {syncing ? '同步中...' : '同步'}
        </button>
      )}

      {/* 最后同步时间 */}
      {lastSyncTime && (
        <span className="text-xs text-gray-500">
          最后同步: {lastSyncTime.toLocaleTimeString()}
        </span>
      )}
    </div>
  )
}
