/**
 * Vault Bridge Service - 用于 Desktop 登录后同步 FileBay 配置到本地 Vault 数据库
 * 
 * 架构：
 * Desktop 登录成功 → notifyVaultBridge() → HTTP POST localhost:8765 → Vault DB → 脱敏系统读取
 */

export interface VaultFileBayConfig {
  url: string
  username: string
  repoName: string
  email: string
  token: string
}

export interface VaultBridgeResponse {
  success: boolean
  message?: string
  error?: string
  user_id?: string
  username?: string
  repo_name?: string
}

export interface VaultBridgeHealthResponse {
  status: string
  service: string
  version: string
  database: string
  database_exists: boolean
}

const VAULT_BRIDGE_URL = 'http://localhost:8765'
const VAULT_BRIDGE_TIMEOUT = 3000 // 3秒超时

/**
 * 检查 Vault Bridge 服务是否运行
 */
export const checkVaultBridgeHealth = async (): Promise<boolean> => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), VAULT_BRIDGE_TIMEOUT)
    
    const response = await fetch(`${VAULT_BRIDGE_URL}/health`, {
      method: 'GET',
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok)
      return false
    
    const data: VaultBridgeHealthResponse = await response.json()
    return data.status === 'ok'
  }
  catch (error) {
    // 服务未运行或超时
    console.debug('Vault Bridge health check failed:', error)
    return false
  }
}

/**
 * 通知 Vault Bridge 保存 FileBay 配置
 * 
 * @param userId - 用户ID
 * @param config - FileBay 配置信息
 * @returns 是否成功保存
 */
export const notifyVaultBridge = async (
  userId: string,
  config: VaultFileBayConfig,
): Promise<boolean> => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), VAULT_BRIDGE_TIMEOUT)
    
    const response = await fetch(`${VAULT_BRIDGE_URL}/vault/config/filebay`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        config: {
          url: config.url,
          username: config.username,
          repoName: config.repoName,
          email: config.email,
          token: config.token,
        },
      }),
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      console.error('Vault Bridge notification failed:', errorData)
      return false
    }
    
    const data: VaultBridgeResponse = await response.json()
    console.log('FileBay config saved to Vault successfully:', data)
    return true
  }
  catch (error) {
    // 网络错误或超时
    console.error('Failed to notify Vault Bridge:', error)
    return false
  }
}

/**
 * 从 Vault Bridge 获取 FileBay 配置
 * 
 * @param userId - 用户ID
 * @returns FileBay 配置或 null
 */
export const getVaultFileBayConfig = async (
  userId: string,
): Promise<VaultFileBayConfig | null> => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), VAULT_BRIDGE_TIMEOUT)
    
    const response = await fetch(`${VAULT_BRIDGE_URL}/vault/config/filebay/${userId}`, {
      method: 'GET',
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      if (response.status === 404) {
        console.debug('No Vault config found for user:', userId)
        return null
      }
      throw new Error(`Failed to get Vault config: ${response.status}`)
    }
    
    const data = await response.json()
    return {
      url: data.url,
      username: data.username,
      repoName: data.repoName,
      email: data.email,
      token: data.token,
    }
  }
  catch (error) {
    console.error('Failed to get Vault config:', error)
    return null
  }
}

/**
 * 通过邮箱从 Vault Bridge 获取 FileBay 配置
 * 
 * @param email - 用户邮箱
 * @returns FileBay 配置或 null
 */
export const getVaultFileBayConfigByEmail = async (
  email: string,
): Promise<VaultFileBayConfig | null> => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), VAULT_BRIDGE_TIMEOUT)
    
    const response = await fetch(`${VAULT_BRIDGE_URL}/vault/config/filebay/by-email/${encodeURIComponent(email)}`, {
      method: 'GET',
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      if (response.status === 404) {
        console.debug('No Vault config found for email:', email)
        return null
      }
      throw new Error(`Failed to get Vault config: ${response.status}`)
    }
    
    const data = await response.json()
    return {
      url: data.url,
      username: data.username,
      repoName: data.repoName,
      email: data.email,
      token: data.token,
    }
  }
  catch (error) {
    console.error('Failed to get Vault config by email:', error)
    return null
  }
}

/**
 * 删除 Vault Bridge 中的 FileBay 配置
 * 
 * @param userId - 用户ID
 * @returns 是否成功删除
 */
export const deleteVaultFileBayConfig = async (
  userId: string,
): Promise<boolean> => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), VAULT_BRIDGE_TIMEOUT)
    
    const response = await fetch(`${VAULT_BRIDGE_URL}/vault/config/filebay/${userId}`, {
      method: 'DELETE',
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      console.error('Failed to delete Vault config:', response.status)
      return false
    }
    
    console.log('Vault config deleted successfully')
    return true
  }
  catch (error) {
    console.error('Failed to delete Vault config:', error)
    return false
  }
}
