# 映射文件加密功能 - 手动添加指南

由于文件反复出现问题，这里提供手动添加步骤。

## 需要修改的文件

### 1. web/app/components/data-masking/sandbox-config.tsx

在文件中找到"发送敏感信息提醒"的div块（大约在第220-240行），在它后面添加以下代码：

```tsx
      {/* Encryption toggle - 添加在"发送敏感信息提醒"之后 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-gray-900">映射文件加密</h3>
            <p className="text-xs text-gray-500 mt-0.5">导出映射文件时使用32位口令加密保护</p>
          </div>
          <button
            onClick={() => { 
              const n = !encryptionEnabled
              setEncryptionEnabled(n)
              persistSetting('mapping_encryption_enabled', String(n)) 
            }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              encryptionEnabled ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                encryptionEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        {encryptionEnabled && (
          <div className="mt-3 rounded-md bg-blue-50 border border-blue-200 px-3 py-2">
            <p className="text-xs text-blue-700">✓ 映射文件将使用AES-256-GCM加密，需要口令才能解密还原</p>
          </div>
        )}
      </div>
```

### 2. 在useEffect中添加加密配置加载

在useEffect中，找到加载`sensitive_send_warning`的代码后，添加：

```tsx
      // 在sensitive_send_warning之后添加
      const enc = remote.mapping_encryption_enabled
      if (enc !== undefined) { 
        setEncryptionEnabled(enc !== 'false')
        localStorage.setItem('mapping_encryption_enabled', enc) 
      }
      else { 
        const l = localStorage.getItem('mapping_encryption_enabled')
        if (l !== null) setEncryptionEnabled(l !== 'false')
        else setEncryptionEnabled(true) 
      }
```

### 3. 在保存配置时添加加密设置

在useEffect中保存配置的部分，添加：

```tsx
        const le = localStorage.getItem('mapping_encryption_enabled')
        if (le !== null) m.mapping_encryption_enabled = le
```

### 4. 更新使用说明

在最后的"使用说明"部分，添加一条：

```tsx
          <li>• 映射文件加密默认开启，可在此关闭</li>
```

## 功能说明

添加完成后，设置界面会显示三个开关：
1. 沙箱安全模式
2. 发送敏感信息提醒
3. **映射文件加密** ← 新添加

## 测试

1. 刷新页面，应该能看到"映射文件加密"开关
2. 开关默认为开启状态
3. 关闭开关后，导出映射文件时不会加密
4. 开启开关后，导出映射文件时会提示设置加密口令

## 如果还是看不到

1. 清除浏览器缓存：`Ctrl + Shift + R`
2. 清除LocalStorage：
   ```javascript
   localStorage.clear()
   location.reload()
   ```
3. 重启开发服务器

## 完整的加密功能已实现

- ✅ 加密工具 (crypto-utils.ts)
- ✅ 文件脱敏组件加密流程 (file-masking.tsx)
- ✅ 文件还原组件解密流程 (file-restore.tsx)
- ✅ 国际化文本 (zh-Hans/en-US)
- ✅ 测试文件
- ⚠️ 设置界面开关 (需要手动添加到 sandbox-config.tsx)

所有其他功能都已完整实现，只需要在设置界面添加这个开关即可。
