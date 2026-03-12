"use client"

import { useState, useEffect, useCallback } from "react"
import { CheckCircleIcon, XCircleIcon } from "@heroicons/react/24/outline"
import { useSandboxSecurity } from "@/context/sandbox-security-context"

interface SandboxConfigProps { onConfigured?: (path: string) => void }
const API_PREFIX = "http://localhost:5001/console/api"

async function fetchUserConfig(): Promise<Record<string, string>> {
  try {
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ""
    const res = await fetch(`${API_PREFIX}/user-config`, { credentials: "include", headers: { "X-CSRF-Token": csrfToken } })
    if (!res.ok) return {}
    const data = await res.json()
    return (data.config as Record<string, string>) || {}
  } catch { return {} }
}

async function saveUserConfig(patch: Record<string, string>): Promise<void> {
  try {
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ""
    await fetch(`${API_PREFIX}/user-config`, {
      method: "PUT", credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({ config: patch }),
    })
  } catch { /* best-effort */ }
}

export function SandboxConfig({ onConfigured }: SandboxConfigProps) {
  const { enabled: securityEnabled, setEnabled: setSecurityEnabled, setSandboxPath: setContextSandboxPath } = useSandboxSecurity()
  const [sandboxPath, setSandboxPath] = useState("")
  const [currentPath, setCurrentPath] = useState("")
  const [isValid, setIsValid] = useState<boolean | null>(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [aiReplyDownloadPath, setAiReplyDownloadPath] = useState("")
  const [aiReplyDownloadPathSaved, setAiReplyDownloadPathSaved] = useState(false)
  const [sensitiveWarning, setSensitiveWarning] = useState(true)
  const [encryptionEnabled, setEncryptionEnabled] = useState(true)
  const [configLoaded, setConfigLoaded] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const remote = await fetchUserConfig()
      if (cancelled) return
      const path = remote.sandbox_path || localStorage.getItem("sandbox_path") || ""
      if (path && !path.startsWith("[")) {
        setCurrentPath(path); setSandboxPath(path); setIsValid(true)
        setContextSandboxPath(path); localStorage.setItem("sandbox_path", path)
        onConfigured?.(path)
      }
      const aiPath = remote.ai_reply_download_path || localStorage.getItem("ai_reply_download_path") || ""
      if (aiPath) { setAiReplyDownloadPath(aiPath); localStorage.setItem("ai_reply_download_path", aiPath) }
      const warn = remote.sensitive_send_warning
      if (warn !== undefined) { setSensitiveWarning(warn !== "false"); localStorage.setItem("sensitive_send_warning", warn) }
      else { const l = localStorage.getItem("sensitive_send_warning"); if (l !== null) setSensitiveWarning(l !== "false") }
      const enc = remote.mapping_encryption_enabled
      if (enc !== undefined) { setEncryptionEnabled(enc !== "false"); localStorage.setItem("mapping_encryption_enabled", enc) }
      else { const l = localStorage.getItem("mapping_encryption_enabled"); if (l !== null) setEncryptionEnabled(l !== "false"); else setEncryptionEnabled(true) }
      const sec = remote.sandbox_security_enabled
      if (sec !== undefined) { setSecurityEnabled(sec === "true"); localStorage.setItem("sandbox_security_enabled", sec) }
      if (!remote.sandbox_path && path) {
        const m: Record<string, string> = {}
        if (path) m.sandbox_path = path
        if (aiPath) m.ai_reply_download_path = aiPath
        const lw = localStorage.getItem("sensitive_send_warning"); if (lw !== null) m.sensitive_send_warning = lw
        const le = localStorage.getItem("mapping_encryption_enabled"); if (le !== null) m.mapping_encryption_enabled = le
        const ls = localStorage.getItem("sandbox_security_enabled"); if (ls !== null) m.sandbox_security_enabled = ls
        const lp = localStorage.getItem("sandbox_export_pin"); if (lp) m.sandbox_export_pin = lp
        if (Object.keys(m).length > 0) saveUserConfig(m)
      }
      setConfigLoaded(true)
    })()
    return () => { cancelled = true }
  }, [])

  const persistSetting = useCallback((key: string, value: string) => {
    localStorage.setItem(key, value); saveUserConfig({ [key]: value })
  }, [])

  const handlePathChange = (e: React.ChangeEvent<HTMLInputElement>) => { setSandboxPath(e.target.value); setIsValid(null); setError("") }

  const handleValidate = async () => {
    const trimmed = sandboxPath.trim()
    if (!trimmed) { setError("请输入沙箱路径"); setIsValid(false); return }
    const isAbsolute = /^[A-Za-z]:[\\/]/.test(trimmed) || trimmed.startsWith("/") || trimmed.startsWith("\\\\")
    if (!isAbsolute) { setError("请输入完整的绝对路径"); setIsValid(false); return }
    setIsLoading(true); setError("")
    try {
      const res = await fetch(`http://localhost:5001/console/api/data-masking/sandbox/files/list?sandbox_path=${encodeURIComponent(trimmed)}`)
      if (res.ok) { setIsValid(true); setCurrentPath(trimmed); setContextSandboxPath(trimmed); persistSetting("sandbox_path", trimmed); onConfigured?.(trimmed) }
      else { const d = await res.json().catch(() => ({})); setIsValid(false); setError(d.error || "路径验证失败") }
    } catch { setIsValid(false); setError("无法连接后端服务") }
    finally { setIsLoading(false) }
  }

  if (!configLoaded) return <div className="flex items-center justify-center py-12"><span className="text-sm text-text-tertiary">加载配置中...</span></div>

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-text-primary">沙箱安全模式</h3>
            <p className="text-xs text-text-tertiary mt-0.5">开启后，文件上传仅限沙箱目录</p>
          </div>
          <button onClick={() => { const n = !securityEnabled; setSecurityEnabled(n); persistSetting("sandbox_security_enabled", String(n)) }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${securityEnabled ? "bg-components-button-primary-bg" : "bg-components-input-bg-normal"}`}>
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${securityEnabled ? "translate-x-6" : "translate-x-1"}`} />
          </button>
        </div>
        {securityEnabled && !currentPath && (
          <div className="mt-3 rounded-md bg-state-warning-hover border border-state-warning-hover-alt px-3 py-2">
            <p className="text-xs text-text-warning">⚠️ 尚未配置沙箱路径</p>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-text-primary">发送敏感信息提醒</h3>
            <p className="text-xs text-text-tertiary mt-0.5">发送前弹出确认提示</p>
          </div>
          <button onClick={() => { const n = !sensitiveWarning; setSensitiveWarning(n); persistSetting("sensitive_send_warning", String(n)) }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${sensitiveWarning ? "bg-components-button-primary-bg" : "bg-components-input-bg-normal"}`}>
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${sensitiveWarning ? "translate-x-6" : "translate-x-1"}`} />
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-text-primary">映射文件加密</h3>
            <p className="text-xs text-text-tertiary mt-0.5">导出映射文件时使用32位口令加密保护</p>
          </div>
          <button onClick={() => { const n = !encryptionEnabled; setEncryptionEnabled(n); persistSetting("mapping_encryption_enabled", String(n)) }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${encryptionEnabled ? "bg-components-button-primary-bg" : "bg-components-input-bg-normal"}`}>
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${encryptionEnabled ? "translate-x-6" : "translate-x-1"}`} />
          </button>
        </div>
        {encryptionEnabled && (
          <div className="mt-3 rounded-md bg-state-accent-hover border border-state-accent-hover-alt px-3 py-2">
            <p className="text-xs text-text-accent">✓ 映射文件将使用AES-256-GCM加密，需要口令才能解密还原</p>
          </div>
        )}
      </div>

      {currentPath && (
        <div className="rounded-lg border border-divider-regular bg-background-section p-4">
          <div className="flex items-start gap-3">
            <CheckCircleIcon className="h-5 w-5 text-text-success mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-text-primary">当前沙箱路径</h3>
              <p className="mt-1 text-sm text-text-secondary font-mono break-all">{currentPath}</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="sandbox-path" className="block text-sm font-medium text-text-secondary mb-2">沙箱目录路径</label>
          <input id="sandbox-path" type="text" value={sandboxPath} onChange={handlePathChange}
            onKeyDown={e => e.key === "Enter" && handleValidate()}
            placeholder="C:\Users\33814\Desktop\report\test"
            className="w-full rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid" />
        </div>
        {isValid !== null && (
          <div className={`rounded-md p-3 ${isValid ? "bg-state-success-hover border border-state-success-hover-alt" : "bg-state-destructive-hover border border-state-destructive-border"}`}>
            <div className="flex items-start gap-2">
              {isValid ? (<><CheckCircleIcon className="h-5 w-5 text-text-success mt-0.5" /><div className="flex-1"><p className="text-sm font-medium text-text-success">路径有效</p></div></>) : (<><XCircleIcon className="h-5 w-5 text-text-destructive mt-0.5" /><div className="flex-1"><p className="text-sm font-medium text-text-destructive">路径无效</p>{error && <p className="mt-1 text-xs text-text-destructive">{error}</p>}</div></>)}
            </div>
          </div>
        )}
        <button type="button" onClick={handleValidate} disabled={isLoading || !sandboxPath.trim()}
          className="inline-flex items-center rounded-md bg-components-button-primary-bg px-4 py-2 text-sm font-medium text-components-button-primary-text hover:bg-components-button-primary-bg-hover disabled:opacity-50 disabled:cursor-not-allowed">
          {isLoading ? "验证中..." : "验证并保存"}</button>
      </div>

      <div className="rounded-lg border border-divider-regular bg-components-panel-bg p-4">
        <h3 className="text-sm font-medium text-text-primary mb-1">AI 回复下载路径</h3>
        <p className="text-xs text-text-tertiary mb-3">留空则使用沙箱路径</p>
        <div className="flex gap-2">
          <input type="text" value={aiReplyDownloadPath} onChange={e => setAiReplyDownloadPath(e.target.value)}
            placeholder={currentPath || "默认使用沙箱路径"}
            className="flex-1 rounded-md border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:outline-none focus:ring-1 focus:ring-state-accent-solid" />
          <button type="button" onClick={() => { persistSetting("ai_reply_download_path", aiReplyDownloadPath.trim()); setAiReplyDownloadPathSaved(true); setTimeout(() => setAiReplyDownloadPathSaved(false), 2000) }}
            className="inline-flex items-center rounded-md bg-components-button-primary-bg px-3 py-2 text-sm font-medium text-components-button-primary-text hover:bg-components-button-primary-bg-hover">
            {aiReplyDownloadPathSaved ? "已保存 ✓" : "保存"}</button>
        </div>
      </div>

      <div className="rounded-lg border border-divider-subtle bg-state-accent-hover p-4">
        <h4 className="text-sm font-medium text-text-accent mb-2">使用说明</h4>
        <ul className="space-y-1 text-xs text-text-accent">
          <li>• 配置保存到数据库，刷新或换设备不会丢失</li>
          <li>• 目录不存在时会自动创建</li>
          <li>• 映射文件加密默认开启，可在此关闭</li>
        </ul>
      </div>
    </div>
  )
}
