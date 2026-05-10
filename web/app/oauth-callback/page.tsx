'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useRef } from 'react'
import Toast from '@/app/components/base/toast'
import { exchangeSSOToken } from '@/service/sso'
import { checkVaultBridgeHealth, notifyVaultBridge } from '@/service/vault-bridge'

const getCookieValue = (name: string) => {
  const prefix = `${name}=`
  return document.cookie
    .split(';')
    .map(item => item.trim())
    .find(item => item.startsWith(prefix))
    ?.slice(prefix.length) || ''
}

const clearDesktopSSOCache = () => {
  sessionStorage.removeItem('desktop-sso-state')
  sessionStorage.removeItem('desktop-sso-code-verifier')
  document.cookie = 'desktop-sso-state=; Path=/; Max-Age=0; SameSite=Lax'
  document.cookie = 'desktop-sso-code-verifier=; Path=/; Max-Age=0; SameSite=Lax'
}

export default function OAuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const hasExchangedRef = useRef(false)

  useEffect(() => {
    if (hasExchangedRef.current) {
      console.warn('[SSO] Token exchange already in progress, skipping')
      return
    }

    hasExchangedRef.current = true

    const code = searchParams.get('code')
    const state = searchParams.get('state')

    if (!code || !state) {
      console.error('[SSO] Missing code or state parameters')
      Toast.notify({ type: 'error', message: 'Invalid SSO callback parameters' })
      router.replace('/signin')
      return
    }

    const storedState = sessionStorage.getItem('desktop-sso-state') || decodeURIComponent(getCookieValue('desktop-sso-state'))
    const codeVerifier = sessionStorage.getItem('desktop-sso-code-verifier') || decodeURIComponent(getCookieValue('desktop-sso-code-verifier'))
    if (state !== storedState) {
      console.error('[SSO] State mismatch - stored:', storedState, 'received:', state)
      Toast.notify({ type: 'error', message: 'SSO login failed: state mismatch' })
      router.replace('/signin')
      return
    }

    if (!codeVerifier) {
      console.error('[SSO] Missing PKCE code verifier')
      Toast.notify({ type: 'error', message: 'SSO login failed: missing verifier' })
      router.replace('/signin')
      return
    }

    const redirectUri = `${window.location.protocol}//${window.location.host}/oauth-callback`

    exchangeSSOToken({ code, state, redirectUri, codeVerifier })
      .then(async () => {
        clearDesktopSSOCache()
        
        // 尝试同步 FileBay 配置到 Vault Bridge
        try {
          // 检查 Vault Bridge 是否运行
          const isVaultBridgeRunning = await checkVaultBridgeHealth()
          
          if (isVaultBridgeRunning) {
            console.log('[Vault Bridge] Service is running, attempting to sync FileBay config')
            
            // 获取用户信息
            const userResponse = await fetch('/console/api/account/profile', {
              method: 'GET',
              credentials: 'include',
            })
            
            if (userResponse.ok) {
              const userData = await userResponse.json()
              const userId = userData.id
              const userEmail = userData.email
              
              // 获取 FileBay 配置（使用下载专用端点，包含完整 token）
              const configResponse = await fetch('/console/api/gitea/config/download', {
                method: 'GET',
                credentials: 'include',
              })
              
              if (configResponse.ok) {
                const config = await configResponse.json()
                
                // 检查配置是否完整
                if (config.gitea_url && config.gitea_owner && config.gitea_repo && config.gitea_token) {
                  // 通知 Vault Bridge
                  const syncSuccess = await notifyVaultBridge(userId, {
                    url: config.gitea_url,
                    username: config.gitea_owner,
                    repoName: config.gitea_repo,
                    email: userEmail,
                    token: config.gitea_token,
                  })
                  
                  if (syncSuccess) {
                    console.log('[Vault Bridge] FileBay config synced successfully')
                  } else {
                    console.warn('[Vault Bridge] Failed to sync FileBay config')
                  }
                } else {
                  console.warn('[Vault Bridge] FileBay config is incomplete, skipping sync')
                }
              } else {
                console.warn('[Vault Bridge] Failed to fetch FileBay config')
              }
            } else {
              console.warn('[Vault Bridge] Failed to fetch user profile')
            }
          } else {
            console.debug('[Vault Bridge] Service is not running, skipping config sync')
          }
        } catch (vaultError) {
          // 不影响登录流程，只记录错误
          console.error('[Vault Bridge] Error during config sync:', vaultError)
        }
        
        await new Promise<void>((resolve) => {
          const redirectTimer = window.setTimeout(() => {
            window.clearTimeout(redirectTimer)
            resolve()
          }, 1000)
        })
        window.location.href = '/apps'
      })
      .catch((error) => {
        console.error('[SSO] Token exchange failed:', error)
        clearDesktopSSOCache()
        Toast.notify({ type: 'error', message: 'SSO login failed' })
        router.replace('/signin')
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div className="text-center">
        <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-4 text-sm text-gray-500">Completing SSO login...</p>
      </div>
    </div>
  )
}
