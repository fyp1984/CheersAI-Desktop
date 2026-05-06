/**
 * Vault Integration Service
 * 
 * Desktop 与 Vault 的集成服务
 * 功能:
 * 1. 检查 Vault 是否运行
 * 2. 同步 FileBay 配置到 Vault
 */

import { del, get, post } from './base'

/**
 * 检查 Vault API 健康状态
 */
export const checkVaultHealth = (vaultApiUrl?: string) => {
  const params = vaultApiUrl ? { vault_api_url: vaultApiUrl } : {}
  return get<{
    available: boolean
    message: string
  }>('/vault/health', { params })
}

/**
 * 同步 FileBay 配置到 Vault
 */
export const syncFileBayConfigToVault = (vaultApiUrl?: string) => {
  const body = vaultApiUrl ? { vault_api_url: vaultApiUrl } : {}
  return post<{
    success: boolean
    message: string
  }>('/vault/sync-config', { body })
}

/**
 * 自动同步配置到 Vault (登录后调用)
 * 
 * 使用场景:
 * 1. 用户登录成功后
 * 2. 用户更新 FileBay 配置后
 */
export const autoSyncToVault = async (vaultApiUrl?: string): Promise<{
  synced: boolean
  message: string
}> => {
  try {
    // 1. 检查 Vault 是否运行
    const healthCheck = await checkVaultHealth(vaultApiUrl)
    
    if (!healthCheck.available) {
      console.log('[Vault Sync] Vault is not running, skipping sync')
      return {
        synced: false,
        message: 'Vault 未运行，跳过同步'
      }
    }
    
    // 2. 同步配置
    const syncResult = await syncFileBayConfigToVault(vaultApiUrl)
    
    if (syncResult.success) {
      console.log('[Vault Sync] Successfully synced config to Vault')
      return {
        synced: true,
        message: '配置已同步到 Vault'
      }
    } else {
      console.error('[Vault Sync] Failed to sync config:', syncResult.message)
      return {
        synced: false,
        message: syncResult.message
      }
    }
  } catch (error) {
    console.error('[Vault Sync] Error during auto sync:', error)
    return {
      synced: false,
      message: '同步失败'
    }
  }
}
