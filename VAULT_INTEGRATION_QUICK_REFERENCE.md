# Vault 集成快速参考

## 🚀 快速启动

### 1. 启动 Vault
```bash
# Vault 会自动启动 API 服务器在端口 7788
# 查看日志确认: ✅ Vault API Server started successfully on port 7788
```

### 2. 启动 Desktop
```bash
# API
cd api && python app.py

# Web
cd web && npm run dev
```

### 3. 测试集成
```bash
# Python 测试
python api/test_vault_integration.py

# PowerShell 测试
.\scripts\test-vault-integration.ps1
```

## 📡 API 端点

### Vault API (localhost:7788)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/filebay/config` | 保存配置 |
| GET | `/api/v1/filebay/config` | 获取配置 |
| DELETE | `/api/v1/filebay/config` | 删除配置 |

### Desktop API (localhost:5001)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/console/api/vault/health` | 检查 Vault 状态 |
| POST | `/console/api/vault/sync-config` | 同步配置到 Vault |

## 💻 代码示例

### 前端 - 自动同步
```typescript
import { autoSyncToVault } from '@/service/vault'

// 登录成功后
const result = await autoSyncToVault()
if (result.synced) {
  console.log('配置已同步到 Vault')
}
```

### 前端 - 手动同步
```typescript
import { syncFileBayConfigToVault } from '@/service/vault'

const handleSync = async () => {
  const result = await syncFileBayConfigToVault()
  if (result.success) {
    Toast.notify({ type: 'success', message: '同步成功' })
  }
}
```

### 前端 - 使用组件
```tsx
import VaultSyncIndicator from '@/app/components/vault-sync-indicator'

<VaultSyncIndicator 
  autoSync={true}
  userEmail={currentUser.email}
/>
```

### curl - 测试 Vault API
```bash
# 健康检查
curl http://localhost:7788/api/v1/health

# 保存配置
curl -X POST http://localhost:7788/api/v1/filebay/config \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://uat-filebay.cheersai.cloud",
    "username": "test_user",
    "repo_name": "workspace",
    "email": "test@example.com",
    "token": "test_token",
    "downloaded_at": "",
    "version": "1.0"
  }'

# 获取配置
curl http://localhost:7788/api/v1/filebay/config

# 删除配置
curl -X DELETE http://localhost:7788/api/v1/filebay/config
```

### Python - 调用 Desktop API
```python
import requests

# 检查 Vault 健康状态
response = requests.get('http://localhost:5001/console/api/vault/health')
print(response.json())

# 同步配置 (需要登录)
response = requests.post(
    'http://localhost:5001/console/api/vault/sync-config',
    headers={'Cookie': 'session=...'},
    json={}
)
print(response.json())
```

## 🗂️ 文件位置

### Vault 端
```
src-tauri/
├── src/
│   ├── commands/
│   │   ├── vault_api_server.rs  ← API 服务器
│   │   └── mod.rs               ← 模块注册
│   └── lib.rs                   ← 启动逻辑
└── Cargo.toml                   ← 依赖配置
```

### Desktop 端
```
api/
├── controllers/
│   └── console/
│       └── vault_integration.py  ← API 控制器
└── test_vault_integration.py     ← 测试脚本

web/
├── service/
│   └── vault.ts                  ← 服务层
└── app/
    └── components/
        └── vault-sync-indicator.tsx  ← UI 组件
```

### 文档
```
docs/
├── VAULT_INTEGRATION.md          ← 详细方案
├── VAULT_INTEGRATION_USAGE.md    ← 使用指南
└── VAULT_INTEGRATION_DIAGRAM.md  ← 架构图

VAULT_INTEGRATION_SUMMARY.md      ← 总结
VAULT_INTEGRATION_CHECKLIST.md    ← 检查清单
VAULT_INTEGRATION_QUICK_REFERENCE.md  ← 快速参考 (本文件)
```

## 🔧 配置

### Vault API 端口
```rust
// src-tauri/src/lib.rs
let server = VaultApiServer::new(app_handle, 7788); // 修改端口
```

### Desktop API URL
```typescript
// web/service/vault.ts
const DEFAULT_VAULT_API_URL = 'http://localhost:7788' // 修改 URL
```

## 🐛 故障排查

### Vault API 无法连接
```bash
# 1. 检查 Vault 是否运行
ps aux | grep vault  # Linux/Mac
Get-Process | Where-Object {$_.ProcessName -like "*vault*"}  # Windows

# 2. 检查端口是否监听
netstat -an | grep 7788  # Linux/Mac
netstat -an | findstr 7788  # Windows

# 3. 测试健康检查
curl http://localhost:7788/api/v1/health
```

### 配置同步失败
```bash
# 1. 查看 Desktop 日志
tail -f api/logs/app.log

# 2. 查看 Vault 日志
# (Vault 日志位置取决于启动方式)

# 3. 手动测试 API
curl -X POST http://localhost:7788/api/v1/filebay/config \
  -H "Content-Type: application/json" \
  -d '{"url":"test","username":"test","repo_name":"test","email":"test","token":"test","downloaded_at":"","version":"1.0"}'
```

### 配置未生效
```bash
# 1. 检查数据库
sqlite3 %TEMP%\cheersai-vault\cheersai-vault.db
> SELECT * FROM user_settings WHERE key = 'filebay_config';

# 2. 在 Vault 中手动查询
# 打开 Vault 开发者工具，执行:
await invoke('get_filebay_config_via_api')
```

## 📊 监控命令

### 查看 API 请求日志
```bash
# Desktop API
tail -f api/logs/app.log | grep "Vault"

# Vault (如果有日志文件)
tail -f vault.log | grep "API"
```

### 查看数据库内容
```bash
# Windows
sqlite3 %TEMP%\cheersai-vault\cheersai-vault.db "SELECT * FROM user_settings WHERE key = 'filebay_config';"

# Linux/Mac
sqlite3 /tmp/cheersai-vault/cheersai-vault.db "SELECT * FROM user_settings WHERE key = 'filebay_config';"
```

## 🔑 关键概念

### 数据流
```
FileBay → Desktop API → Vault API → SQLite
```

### 配置存储
```
表: user_settings
Key: filebay_config
Value: JSON 字符串
```

### 错误处理
```
Vault 未运行 → 跳过同步 (不影响登录)
同步失败 → 显示错误 (不影响登录)
```

## 📞 获取帮助

### 文档
- [详细方案](./docs/VAULT_INTEGRATION.md)
- [使用指南](./docs/VAULT_INTEGRATION_USAGE.md)
- [架构图](./docs/VAULT_INTEGRATION_DIAGRAM.md)

### 测试
```bash
# Python 测试
python api/test_vault_integration.py

# PowerShell 测试
.\scripts\test-vault-integration.ps1
```

### 调试
```bash
# 启用详细日志
export RUST_LOG=debug  # Vault
export FLASK_DEBUG=1   # Desktop API
```

## ⚡ 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| API 响应时间 | < 1s | 健康检查和配置操作 |
| 同步时间 | < 2s | 登录后自动同步 |
| 数据库操作 | < 100ms | 读写配置 |

## 🔒 安全检查

- ✅ API 只监听 127.0.0.1
- ✅ Token 存储在本地数据库
- ✅ 无敏感信息泄露到日志
- ✅ 受操作系统权限保护

## 📝 快速命令

```bash
# 启动所有服务
cd api && python app.py &
cd web && npm run dev &

# 测试集成
python api/test_vault_integration.py

# 查看日志
tail -f api/logs/app.log

# 查看数据库
sqlite3 %TEMP%\cheersai-vault\cheersai-vault.db

# 清理配置
curl -X DELETE http://localhost:7788/api/v1/filebay/config
```

---

**提示**: 将此文件保存为书签，方便快速查阅! 📌
