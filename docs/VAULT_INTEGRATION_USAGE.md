# Vault 集成使用指南

## 快速开始

### 1. 启动 Vault

确保 Vault 应用正在运行。Vault 启动时会自动启动 API 服务器 (端口 7788)。

```bash
# 查看 Vault 日志，确认 API 服务器已启动
# 应该看到类似以下输出:
# 🚀 Vault API Server starting on http://localhost:7788
# ✅ Vault API Server started successfully on port 7788
```

### 2. 启动 Desktop

启动 Desktop 应用 (API 和 Web)。

```bash
# 启动 API
cd api
python app.py

# 启动 Web (另一个终端)
cd web
npm run dev
```

### 3. 登录 Desktop

用户登录 Desktop 后，系统会自动:
1. 检查 Vault 是否运行
2. 如果 Vault 运行，自动同步 FileBay 配置到 Vault
3. 显示同步状态

## 手动同步

### 方法 1: 使用前端组件

在需要显示 Vault 同步状态的页面中使用 `VaultSyncIndicator` 组件:

```tsx
import VaultSyncIndicator from '@/app/components/vault-sync-indicator'

export default function SettingsPage() {
  return (
    <div>
      {/* 其他内容 */}
      
      {/* Vault 同步指示器 */}
      <VaultSyncIndicator 
        autoSync={true}  // 自动同步
        userEmail={currentUser.email}
      />
    </div>
  )
}
```

### 方法 2: 使用 API

```typescript
import { syncFileBayConfigToVault } from '@/service/vault'

// 手动触发同步
const handleSync = async () => {
  const result = await syncFileBayConfigToVault()
  
  if (result.success) {
    console.log('同步成功')
  } else {
    console.error('同步失败:', result.message)
  }
}
```

### 方法 3: 使用 curl

```bash
# 同步配置 (需要登录 session)
curl -X POST http://localhost:5001/console/api/vault/sync-config \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{}'
```

## 测试集成

运行测试脚本验证集成是否正常工作:

```bash
cd api
python test_vault_integration.py
```

测试脚本会执行以下测试:
1. ✅ Vault 健康检查
2. ✅ 保存 FileBay 配置
3. ✅ 获取 FileBay 配置
4. ✅ 删除 FileBay 配置
5. ✅ Desktop 健康检查接口

## API 参考

### Vault API

#### 1. 健康检查

```http
GET http://localhost:7788/api/v1/health
```

响应:
```json
{
  "success": true,
  "message": "Vault API Server is running",
  "data": null
}
```

#### 2. 保存配置

```http
POST http://localhost:7788/api/v1/filebay/config
Content-Type: application/json

{
  "url": "https://uat-filebay.cheersai.cloud",
  "username": "user123",
  "repo_name": "workspace",
  "email": "user@example.com",
  "token": "abc123...",
  "downloaded_at": "2024-01-01T00:00:00Z",
  "version": "1.0"
}
```

响应:
```json
{
  "success": true,
  "message": "FileBay configuration saved successfully",
  "data": {
    "url": "https://uat-filebay.cheersai.cloud",
    "username": "user123",
    "repo_name": "workspace",
    "email": "user@example.com",
    "token": "abc123...",
    "downloaded_at": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

#### 3. 获取配置

```http
GET http://localhost:7788/api/v1/filebay/config
```

响应:
```json
{
  "success": true,
  "message": "Configuration retrieved successfully",
  "data": {
    "url": "https://uat-filebay.cheersai.cloud",
    "username": "user123",
    "repo_name": "workspace",
    "email": "user@example.com",
    "token": "abc123...",
    "downloaded_at": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

#### 4. 删除配置

```http
DELETE http://localhost:7788/api/v1/filebay/config
```

响应:
```json
{
  "success": true,
  "message": "Configuration deleted successfully",
  "data": null
}
```

### Desktop API

#### 1. 检查 Vault 健康状态

```http
GET http://localhost:5001/console/api/vault/health
```

响应:
```json
{
  "available": true,
  "message": "Vault API 可用"
}
```

#### 2. 同步配置到 Vault

```http
POST http://localhost:5001/console/api/vault/sync-config
Content-Type: application/json

{
  "vault_api_url": "http://localhost:7788"  // 可选
}
```

响应:
```json
{
  "success": true,
  "message": "FileBay 配置已成功同步到 Vault"
}
```

## 集成到登录流程

### 1. 修改登录成功回调

在用户登录成功后，调用自动同步:

```typescript
// web/app/signin/page.tsx

import { autoSyncToVault } from '@/service/vault'

const handleLoginSuccess = async (user) => {
  // 原有的登录成功逻辑
  // ...
  
  // 自动同步到 Vault
  try {
    const result = await autoSyncToVault()
    if (result.synced) {
      console.log('[Login] Config synced to Vault')
    }
  } catch (error) {
    // 同步失败不影响登录
    console.error('[Login] Failed to sync to Vault:', error)
  }
}
```

### 2. 在设置页面添加同步按钮

```tsx
// web/app/components/header/account-setting/gitea-settings-page/index.tsx

import { syncFileBayConfigToVault } from '@/service/vault'

const handleSyncToVault = async () => {
  try {
    const result = await syncFileBayConfigToVault()
    
    if (result.success) {
      Toast.notify({
        type: 'success',
        message: '配置已同步到 Vault',
      })
    } else {
      Toast.notify({
        type: 'error',
        message: result.message,
      })
    }
  } catch (error) {
    Toast.notify({
      type: 'error',
      message: '同步失败，请重试',
    })
  }
}

// 在 UI 中添加按钮
<button onClick={handleSyncToVault}>
  同步到 Vault
</button>
```

## 故障排查

### 问题 1: Vault API 无法连接

**症状**: Desktop 提示 "无法连接到 Vault"

**解决方案**:
1. 确认 Vault 应用正在运行
2. 检查 Vault 日志，确认 API 服务器已启动
3. 检查端口 7788 是否被占用
4. 尝试手动访问 `http://localhost:7788/api/v1/health`

### 问题 2: 配置同步失败

**症状**: Desktop 提示 "同步失败"

**解决方案**:
1. 检查 Desktop 日志，查看错误详情
2. 检查 Vault 日志，查看是否有错误
3. 确认用户的 FileBay 配置是否完整
4. 尝试手动调用 API 测试

### 问题 3: 配置未生效

**症状**: Vault 中看不到配置

**解决方案**:
1. 在 Vault 中打开开发者工具，调用 `get_filebay_config_via_api()`
2. 检查数据库文件是否存在
3. 检查数据库中的 `user_settings` 表

### 问题 4: 端口冲突

**症状**: Vault API 服务器启动失败

**解决方案**:
1. 修改 Vault API 端口 (在 `lib.rs` 中修改)
2. 同时修改 Desktop 调用的端口
3. 重新编译 Vault

## 配置选项

### Vault 端

在 `src-tauri/src/lib.rs` 中修改 API 服务器端口:

```rust
let server = VaultApiServer::new(app_handle, 7788); // 修改端口号
```

### Desktop 端

在 `web/service/vault.ts` 中修改默认 Vault API URL:

```typescript
const DEFAULT_VAULT_API_URL = 'http://localhost:7788' // 修改 URL
```

## 安全建议

1. **本地通信**: API 服务器只监听 `127.0.0.1`，不对外暴露
2. **Token 加密**: 考虑对存储的 Token 进行加密
3. **访问控制**: 可以添加简单的认证机制 (如 API Key)
4. **日志记录**: 记录所有 API 调用，便于审计

## 性能优化

1. **连接池**: 使用连接池管理数据库连接
2. **缓存**: 缓存配置，减少数据库查询
3. **异步处理**: 使用异步 I/O 提高性能
4. **超时设置**: 设置合理的超时时间

## 未来计划

- [ ] 支持多用户配置
- [ ] 配置版本管理
- [ ] 配置同步历史记录
- [ ] 配置验证和测试
- [ ] 自动重试机制
- [ ] 配置加密存储
- [ ] WebSocket 实时同步
- [ ] 配置冲突解决

## 相关文档

- [Vault 集成方案](./VAULT_INTEGRATION.md)
- [FileBay 配置说明](./GITEA_CONFIG_IN_SETTINGS.md)
- [API 文档](./API_REFERENCE.md)
