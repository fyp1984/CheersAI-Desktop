/**
 * 加密工具
 * Cryptography Utilities
 */

function getCrypto(): Crypto | undefined {
  if (typeof globalThis.crypto !== 'undefined' && globalThis.crypto.subtle) {
    return globalThis.crypto
  }

  return undefined
}

function encodeBase64(bytes: Uint8Array): string {
  let binary = ''
  for (const byte of bytes) {
    binary += String.fromCodePoint(byte)
  }
  return btoa(binary)
}

function decodeBase64(base64: string): Uint8Array {
  const binary = atob(base64)
  return Uint8Array.from(binary, char => char.charCodeAt(0))
}

/**
 * 加密数据
 * @param data - 要加密的数据
 * @param key - 加密密钥
 * @returns 加密后的数据（Base64 编码）
 */
export async function encrypt(data: string, key: string): Promise<string> {
  const crypto = getCrypto()
  if (crypto) {
    return encryptWithWebCrypto(crypto, data, key)
  }

  throw new Error('No crypto implementation available')
}

/**
 * 解密数据
 * @param encryptedData - 加密的数据（Base64 编码）
 * @param key - 解密密钥
 * @returns 解密后的数据
 */
export async function decrypt(encryptedData: string, key: string): Promise<string> {
  const crypto = getCrypto()
  if (crypto) {
    return decryptWithWebCrypto(crypto, encryptedData, key)
  }

  throw new Error('No crypto implementation available')
}

/**
 * 使用 Web Crypto API 加密
 */
async function encryptWithWebCrypto(crypto: Crypto, data: string, key: string): Promise<string> {
  // 将密钥转换为 CryptoKey
  const encoder = new TextEncoder()
  const keyData = encoder.encode(key.padEnd(32, '0').substring(0, 32))
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'AES-GCM' },
    false,
    ['encrypt'],
  )

  // 生成随机 IV
  const iv = crypto.getRandomValues(new Uint8Array(12))

  // 加密数据
  const dataBuffer = encoder.encode(data)
  const encryptedBuffer = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    cryptoKey,
    dataBuffer,
  )

  // 组合 IV 和加密数据
  const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength)
  combined.set(iv, 0)
  combined.set(new Uint8Array(encryptedBuffer), iv.length)

  // 转换为 Base64
  return encodeBase64(combined)
}

/**
 * 使用 Web Crypto API 解密
 */
async function decryptWithWebCrypto(crypto: Crypto, encryptedData: string, key: string): Promise<string> {
  // 从 Base64 解码
  const combined = decodeBase64(encryptedData)

  // 提取 IV 和加密数据
  const iv = combined.slice(0, 12)
  const encrypted = combined.slice(12)

  // 将密钥转换为 CryptoKey
  const encoder = new TextEncoder()
  const keyData = encoder.encode(key.padEnd(32, '0').substring(0, 32))
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'AES-GCM' },
    false,
    ['decrypt'],
  )

  // 解密数据
  const decryptedBuffer = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    cryptoKey,
    encrypted,
  )

  // 转换为字符串
  const decoder = new TextDecoder()
  return decoder.decode(decryptedBuffer)
}

/**
 * 生成随机密钥
 * @param length - 密钥长度（字节）
 * @returns 随机密钥（十六进制字符串）
 */
export function generateKey(length: number = 32): string {
  const crypto = getCrypto()
  if (crypto) {
    const array = new Uint8Array(length)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  throw new Error('No crypto implementation available')
}

/**
 * 计算数据的哈希值
 * @param data - 要哈希的数据
 * @returns 哈希值（十六进制字符串）
 */
export async function hash(data: string): Promise<string> {
  const crypto = getCrypto()
  if (crypto) {
    const encoder = new TextEncoder()
    const dataBuffer = encoder.encode(data)
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('')
  }

  throw new Error('No crypto implementation available')
}

/**
 * 生成随机加密口令（至少32个字符）
 * @param length - 口令长度（默认32）
 * @returns 随机口令字符串
 */
export function generatePassphrase(length: number = 32): string {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'

  const crypto = getCrypto()
  if (crypto) {
    const array = new Uint8Array(length)
    crypto.getRandomValues(array)
    return Array.from(array, byte => charset[byte % charset.length]).join('')
  }

  // 降级方案：使用 Math.random()
  let result = ''
  for (let i = 0; i < length; i++) {
    result += charset[Math.floor(Math.random() * charset.length)]
  }
  return result
}
