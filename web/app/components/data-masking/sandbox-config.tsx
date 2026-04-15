'use client'

import { ArrowPathIcon, CheckCircleIcon, ClipboardDocumentIcon, EyeIcon, EyeSlashIcon, XCircleIcon } from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState } from 'react'
import { API_PREFIX } from '@/config'
import { useSandboxSecurity } from '@/context/use-sandbox-security'
import { generatePassphrase } from '@/lib/data-masking/crypto-utils'

type SandboxConfigProps = { onConfigured?: (path: string) => void }

async function fetchUserConfig(): Promise<Record<string, string>> {
  try {
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
    const res = await fetch(`${API_PREFIX}/user-config`, { credentials: 'include', headers: { 'X-CSRF-Token': csrfToken } })
    if (!res.ok)
      return {}
    const data = await res.json()
    return (data.config as Record<string, string>) || {}
  }
  catch { return {} }
}

async function saveUserConfig(patch: Record<string, string>): Promise<void> {
  try {
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
    await fetch(`${API_PREFIX}/user-config`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
      body: JSON.stringify({ config: patch }),
    })
  }
  catch { /* best-effort */ }
}

export function SandboxConfig({ onConfigured }: SandboxConfigProps) {
  const { enabled: securityEnabled, setEnabled: setSecurityEnabled, setSandboxPath: setContextSandboxPath } = useSandboxSecurity()
  const [sandboxPath, setSandboxPath] = useState('')
  const [currentPath, setCurrentPath] = useState('')
  const [isValid, setIsValid] = useState<boolean | null>(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [aiReplyDownloadPath, setAiReplyDownloadPath] = useState('')
  const [aiReplyDownloadPathSaved, setAiReplyDownloadPathSaved] = useState(false)
  const [sensitiveWarning, setSensitiveWarning] = useState(true)
  const [encryptionEnabled, setEncryptionEnabled] = useState(true)
  const [configLoaded, setConfigLoaded] = useState(false)
  const [globalPassphrase, setGlobalPassphrase] = useState('')
  const [showPassphrase, setShowPassphrase] = useState(false)
  const [passphraseSaved, setPassphraseSaved] = useState(false)

  // Gitea configuration states
  const [giteaUrl, setGiteaUrl] = useState('')
  const [giteaOwner, setGiteaOwner] = useState('')
  const [giteaRepo, setGiteaRepo] = useState('')
  const [giteaPath, setGiteaPath] = useState('')
  const [giteaToken, setGiteaToken] = useState('')
  const [showGiteaToken, setShowGiteaToken] = useState(false)
  const [giteaTestResult, setGiteaTestResult] = useState<{ success: boolean, message: string } | null>(null)
  const [giteaTesting, setGiteaTesting] = useState(false)
  const [giteaSaving, setGiteaSaving] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const remote = await fetchUserConfig()
      if (cancelled)
        return
      const path = remote.sandbox_path || localStorage.getItem('sandbox_path') || ''
      if (path && !path.startsWith('[')) {
        setCurrentPath(path); setSandboxPath(path); setIsValid(true)
        setContextSandboxPath(path); localStorage.setItem('sandbox_path', path)
        onConfigured?.(path)
      }
      const aiPath = remote.ai_reply_download_path || localStorage.getItem('ai_reply_download_path') || ''
      if (aiPath) { setAiReplyDownloadPath(aiPath); localStorage.setItem('ai_reply_download_path', aiPath) }
      const warn = remote.sensitive_send_warning
      if (warn !== undefined) { setSensitiveWarning(warn !== 'false'); localStorage.setItem('sensitive_send_warning', warn) }
      else {
        const l = localStorage.getItem('sensitive_send_warning'); if (l !== null)
          setSensitiveWarning(l !== 'false')
      }
      const enc = remote.mapping_encryption_enabled
      if (enc !== undefined) { setEncryptionEnabled(enc !== 'false'); localStorage.setItem('mapping_encryption_enabled', enc) }
      else {
        const l = localStorage.getItem('mapping_encryption_enabled'); if (l !== null)
          setEncryptionEnabled(l !== 'false'); else setEncryptionEnabled(true)
      }
      const pass = remote.mapping_encryption_passphrase || localStorage.getItem('mapping_encryption_passphrase') || ''
      if (pass) { setGlobalPassphrase(pass); localStorage.setItem('mapping_encryption_passphrase', pass) }
      const sec = remote.sandbox_security_enabled
      if (sec !== undefined) { setSecurityEnabled(sec === 'true'); localStorage.setItem('sandbox_security_enabled', sec) }
      if (!remote.sandbox_path && path) {
        const m: Record<string, string> = {}
        if (path)
          m.sandbox_path = path
        if (aiPath)
          m.ai_reply_download_path = aiPath
        const lw = localStorage.getItem('sensitive_send_warning'); if (lw !== null)
          m.sensitive_send_warning = lw
        const le = localStorage.getItem('mapping_encryption_enabled'); if (le !== null)
          m.mapping_encryption_enabled = le
        const ls = localStorage.getItem('sandbox_security_enabled'); if (ls !== null)
          m.sandbox_security_enabled = ls
        const lp = localStorage.getItem('sandbox_export_pin'); if (lp)
          m.sandbox_export_pin = lp
        const lpass = localStorage.getItem('mapping_encryption_passphrase'); if (lpass)
          m.mapping_encryption_passphrase = lpass
        if (Object.keys(m).length > 0)
          saveUserConfig(m)
      }

      // Load Gitea configuration
      try {
        const giteaRes = await fetch(`${API_PREFIX}/gitea/config`, { credentials: 'include' })
        if (giteaRes.ok) {
          const data = await giteaRes.json()
          setGiteaUrl(data.gitea_url || '')
          setGiteaOwner(data.gitea_owner || '')
          setGiteaRepo(data.gitea_repo || '')
          setGiteaPath(data.gitea_path || '')
          setGiteaToken(data.gitea_token || '')
        }
      }
      catch { /* ignore */ }

      setConfigLoaded(true)
    })()
    return () => { cancelled = true }
  }, [onConfigured, setContextSandboxPath, setSecurityEnabled])

  const persistSetting = useCallback((key: string, value: string) => {
    localStorage.setItem(key, value); saveUserConfig({ [key]: value })
  }, [])

  const handlePathChange = (e: React.ChangeEvent<HTMLInputElement>) => { setSandboxPath(e.target.value); setIsValid(null); setError('') }

  const handleValidate = async () => {
    const trimmed = sandboxPath.trim()
    if (!trimmed) { setError('请输入沙箱路径'); setIsValid(false); return }
    const isAbsolute = /^[A-Z]:[\\/]/i.test(trimmed) || trimmed.startsWith('/') || trimmed.startsWith('\\\\')
    if (!isAbsolute) { setError('请输入完整的绝对路径'); setIsValid(false); return }
    setIsLoading(true); setError('')
    try {
      const res = await fetch(`${API_PREFIX}/data-masking/sandbox/files/list?sandbox_path=${encodeURIComponent(trimmed)}`)
      if (res.ok) { setIsValid(true); setCurrentPath(trimmed); setContextSandboxPath(trimmed); persistSetting('sandbox_path', trimmed); onConfigured?.(trimmed) }
      else { const d = await res.json().catch(() => ({})); setIsValid(false); setError(d.error || '路径验证失败') }
    }
    catch { setIsValid(false); setError('无法连接后端服务') }
    finally { setIsLoading(false) }
  }

  const handleGiteaSave = async () => {
    setGiteaSaving(true)
    try {
      const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      const res = await fetch(`${API_PREFIX}/gitea/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify({
          gitea_url: giteaUrl,
          gitea_owner: giteaOwner,
          gitea_repo: giteaRepo,
          gitea_path: giteaPath,
          gitea_token: giteaToken,
        }),
      })
      if (res.ok) {
        alert('FileBay 配置保存成功')
        // Reload config to get masked token
        const reloadRes = await fetch(`${API_PREFIX}/gitea/config`, { credentials: 'include' })
        if (reloadRes.ok) {
          const data = await reloadRes.json()
          setGiteaToken(data.gitea_token || '')
        }
      }
      else {
        alert('保存失败')
      }
    }
    catch {
      alert('保存失败：无法连接后端')
    }
    finally {
      setGiteaSaving(false)
    }
  }

  const handleGiteaTest = async () => {
    setGiteaTesting(true)
    setGiteaTestResult(null)
    try {
      const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      const res = await fetch(`${API_PREFIX}/gitea/config/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify({
          gitea_url: giteaUrl,
          gitea_owner: giteaOwner,
          gitea_repo: giteaRepo,
          gitea_path: giteaPath,
          gitea_token: giteaToken,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setGiteaTestResult(data)
      }
      else {
        // Try to get error message from response
        try {
          const errorData = await res.json()
          setGiteaTestResult({
            success: false,
            message: errorData.message || `测试失败 (HTTP ${res.status})`,
          })
        }
        catch {
          setGiteaTestResult({ success: false, message: `测试失败 (HTTP ${res.status})` })
        }
      }
    }
    catch (err) {
      setGiteaTestResult({
        success: false,
        message: `无法连接后端: ${err instanceof Error ? err.message : '未知错误'}`,
      })
    }
    finally {
      setGiteaTesting(false)
    }
  }

  if (!configLoaded)
    return <div className="flex items-center justify-center py-12"><span className="text-sm text-text-tertiary">加载配置中...</span></div>

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-text-primary">沙箱安全模式</h3>
            <p className="mt-0.5 text-xs text-text-tertiary">开启后，文件上传仅限沙箱目录</p>
          </div>
          <button
            onClick={() => { const n = !securityEnabled; setSecurityEnabled(n); persistSetting('sandbox_security_enabled', String(n)) }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${securityEnabled ? 'bg-components-button-primary-bg' : 'bg-components-input-bg-normal'}`}
          >
            <span className={`inline-block h-4 w-4 rounded-full bg-white transition-transform${securityEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>
        {securityEnabled && !currentPath && (
          <div className="mt-3 rounded-md border border-state-warning-hover-alt bg-state-warning-hover px-3 py-2">
            <p className="text-xs text-text-warning">⚠️ 尚未配置沙箱路径</p>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-text-primary">发送敏感信息提醒</h3>
            <p className="mt-0.5 text-xs text-text-tertiary">发送前弹出确认提示</p>
          </div>
          <button
            onClick={() => { const n = !sensitiveWarning; setSensitiveWarning(n); persistSetting('sensitive_send_warning', String(n)) }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${sensitiveWarning ? 'bg-components-button-primary-bg' : 'bg-components-input-bg-normal'}`}
          >
            <span className={`inline-block h-4 w-4 rounded-full bg-white transition-transform${sensitiveWarning ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-text-primary">映射文件加密</h3>
            <p className="mt-0.5 text-xs text-text-tertiary">导出映射文件时使用32位口令加密保护</p>
          </div>
          <button
            onClick={() => { const n = !encryptionEnabled; setEncryptionEnabled(n); persistSetting('mapping_encryption_enabled', String(n)) }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${encryptionEnabled ? 'bg-components-button-primary-bg' : 'bg-components-input-bg-normal'}`}
          >
            <span className={`inline-block h-4 w-4 rounded-full bg-white transition-transform${encryptionEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>
        {encryptionEnabled && (
          <>
            <div className="mb-4 rounded-md border border-state-accent-hover-alt bg-state-accent-hover px-3 py-2">
              <p className="text-xs text-text-accent">✓ 映射文件将使用AES-256-GCM加密，需要口令才能解密还原</p>
            </div>
            <div className="space-y-3 border-t border-divider-subtle pt-3">
              <div>
                <label className="mb-2 block text-sm font-medium text-text-secondary">全局加密口令（32位）</label>
                <div className="mb-2 flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showPassphrase ? 'text' : 'password'}
                      value={globalPassphrase}
                      onChange={e => setGlobalPassphrase(e.target.value)}
                      placeholder="输入或生成32位加密口令"
                      className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 pr-10 font-mono text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassphrase(!showPassphrase)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
                    >
                      {showPassphrase ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={() => setGlobalPassphrase(generatePassphrase(32))}
                    className="inline-flex items-center gap-1 rounded-md bg-components-button-secondary-bg px-3 py-2 text-sm font-medium text-components-button-secondary-text hover:bg-components-button-secondary-bg-hover"
                    title="生成随机口令"
                  >
                    <ArrowPathIcon className="h-4 w-4" />
                    生成
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (globalPassphrase) {
                        navigator.clipboard.writeText(globalPassphrase)
                        alert('口令已复制到剪贴板')
                      }
                    }}
                    disabled={!globalPassphrase}
                    className="inline-flex items-center gap-1 rounded-md bg-components-button-secondary-bg px-3 py-2 text-sm font-medium text-components-button-secondary-text hover:bg-components-button-secondary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
                    title="复制口令"
                  >
                    <ClipboardDocumentIcon className="h-4 w-4" />
                    复制
                  </button>
                </div>
                {globalPassphrase && globalPassphrase.length < 32 && (
                  <p className="mb-2 text-xs text-text-destructive">⚠️ 口令长度必须至少32位</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => {
                  if (globalPassphrase.length < 32) {
                    alert('口令长度必须至少32位')
                    return
                  }
                  persistSetting('mapping_encryption_passphrase', globalPassphrase)
                  setPassphraseSaved(true)
                  setTimeout(() => setPassphraseSaved(false), 2000)
                }}
                disabled={!globalPassphrase || globalPassphrase.length < 32}
                className="inline-flex items-center rounded-md bg-components-button-primary-bg px-4 py-2 text-sm font-medium text-components-button-primary-text hover:bg-components-button-primary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
              >
                {passphraseSaved ? '已保存 ✓' : '保存口令'}
              </button>
            </div>
          </>
        )}
      </div>

      {currentPath && (
        <div className="rounded-lg border border-divider-regular bg-background-section p-4">
          <div className="flex items-start gap-3">
            <CheckCircleIcon className="mt-0.5 h-5 w-5 text-text-success" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-text-primary">当前沙箱路径</h3>
              <p className="mt-1 break-all font-mono text-sm text-text-secondary">{currentPath}</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="sandbox-path" className="mb-2 block text-sm font-medium text-text-secondary">沙箱目录路径</label>
          <input
            id="sandbox-path"
            type="text"
            value={sandboxPath}
            onChange={handlePathChange}
            onKeyDown={e => e.key === 'Enter' && handleValidate()}
            placeholder="C:\Users\33814\Desktop\report\test"
            className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
          />
        </div>
        {isValid !== null && (
          <div className={`rounded-md p-3 ${isValid ? 'border border-state-success-hover-alt bg-state-success-hover' : 'border border-state-destructive-border bg-state-destructive-hover'}`}>
            <div className="flex items-start gap-2">
              {isValid
                ? (
                    <>
                      <CheckCircleIcon className="mt-0.5 h-5 w-5 text-text-success" />
                      <div className="flex-1"><p className="text-sm font-medium text-text-success">路径有效</p></div>
                    </>
                  )
                : (
                    <>
                      <XCircleIcon className="mt-0.5 h-5 w-5 text-text-destructive" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-text-destructive">路径无效</p>
                        {error && <p className="mt-1 text-xs text-text-destructive">{error}</p>}
                      </div>
                    </>
                  )}
            </div>
          </div>
        )}
        <button
          type="button"
          onClick={handleValidate}
          disabled={isLoading || !sandboxPath.trim()}
          className="inline-flex items-center rounded-md bg-components-button-primary-bg px-4 py-2 text-sm font-medium text-components-button-primary-text hover:bg-components-button-primary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? '验证中...' : '验证并保存'}
        </button>
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <h3 className="mb-1 text-sm font-medium text-text-primary">AI 回复下载路径</h3>
        <p className="mb-3 text-xs text-text-tertiary">留空则使用沙箱路径</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={aiReplyDownloadPath}
            onChange={e => setAiReplyDownloadPath(e.target.value)}
            placeholder={currentPath || '默认使用沙箱路径'}
            className="flex-1 rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
          />
          <button
            type="button"
            onClick={() => { persistSetting('ai_reply_download_path', aiReplyDownloadPath.trim()); setAiReplyDownloadPathSaved(true); setTimeout(() => setAiReplyDownloadPathSaved(false), 2000) }}
            className="inline-flex items-center rounded-md bg-components-button-primary-bg px-3 py-2 text-sm font-medium text-components-button-primary-text hover:bg-components-button-primary-bg-hover"
          >
            {aiReplyDownloadPathSaved ? '已保存 ✓' : '保存'}
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <h3 className="mb-3 text-sm font-medium text-text-primary">FileBay 文件存储配置</h3>
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">FileBay 服务器地址</label>
            <input
              type="text"
              value={giteaUrl}
              onChange={e => setGiteaUrl(e.target.value)}
              placeholder="http://localhost:3000"
              className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">仓库所有者</label>
              <input
                type="text"
                value={giteaOwner}
                onChange={e => setGiteaOwner(e.target.value)}
                placeholder="cheersai"
                className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">仓库名称</label>
              <input
                type="text"
                value={giteaRepo}
                onChange={e => setGiteaRepo(e.target.value)}
                placeholder="file-storage"
                className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">文件路径（可选）</label>
            <input
              type="text"
              value={giteaPath}
              onChange={e => setGiteaPath(e.target.value)}
              placeholder="留空表示根目录，例如: masked 或 documents/reports"
              className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
            />
            <p className="mt-1 text-xs text-text-tertiary">指定从仓库的哪个子目录读取文件</p>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">API Token</label>
            <div className="relative">
              <input
                type={showGiteaToken ? 'text' : 'password'}
                value={giteaToken}
                onChange={e => setGiteaToken(e.target.value)}
                placeholder="输入新的 Token 或留空保持不变"
                className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 pr-10 font-mono text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid"
              />
              <button
                type="button"
                onClick={() => setShowGiteaToken(!showGiteaToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
              >
                {showGiteaToken ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
              </button>
            </div>
          </div>
          {giteaTestResult && (
            <div className={`rounded-md p-3 ${giteaTestResult.success ? 'border border-state-success-hover-alt bg-state-success-hover' : 'border border-state-destructive-border bg-state-destructive-hover'}`}>
              <div className="flex items-start gap-2">
                {giteaTestResult.success ? <CheckCircleIcon className="mt-0.5 h-5 w-5 text-text-success" /> : <XCircleIcon className="mt-0.5 h-5 w-5 text-text-destructive" />}
                <div className="flex-1">
                  <p className={`text-sm font-medium ${giteaTestResult.success ? 'text-text-success' : 'text-text-destructive'}`}>
                    {giteaTestResult.success ? '连接成功' : '连接失败'}
                  </p>
                  <p className={`mt-1 text-xs ${giteaTestResult.success ? 'text-text-success' : 'text-text-destructive'}`}>
                    {giteaTestResult.message}
                  </p>
                </div>
              </div>
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleGiteaSave}
              disabled={giteaSaving}
              className="inline-flex items-center rounded-md bg-components-button-primary-bg px-4 py-2 text-sm font-medium text-components-button-primary-text hover:bg-components-button-primary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {giteaSaving ? '保存中...' : '保存配置'}
            </button>
            <button
              type="button"
              onClick={handleGiteaTest}
              disabled={giteaTesting || !giteaUrl || !giteaOwner || !giteaRepo || !giteaToken}
              className="inline-flex items-center rounded-md bg-components-button-secondary-bg px-4 py-2 text-sm font-medium text-components-button-secondary-text hover:bg-components-button-secondary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {giteaTesting ? '测试中...' : '测试连接'}
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-divider-subtle bg-state-accent-hover p-4">
        <h4 className="mb-2 text-sm font-medium text-text-accent">使用说明</h4>
        <ul className="space-y-1 text-xs text-text-accent">
          <li>• 配置保存到数据库，刷新或换设备不会丢失</li>
          <li>• 目录不存在时会自动创建</li>
          <li>• 映射文件加密默认开启，可在此关闭</li>
          <li>• 全局口令用于所有映射文件的加密和解密</li>
        </ul>
      </div>
    </div>
  )
}
