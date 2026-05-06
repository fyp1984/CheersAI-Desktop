# Vault 集成方案

## 概述

本方案实现了 Desktop 与 Vault 的集成，使得用户登录 Desktop 后，可以自动将 FileBay 配置同步到 Vault 本地数据库，避免权限问题。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        用户登录 Desktop                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Desktop API (Python/Flask)                                  │
│  - 从 FileBay 获取用户配置                                     │
│  - 调用 Vault API 推送配置                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST
                              │ http://localhost:7788/api/v1/filebay/config
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Vault API Server (Rust/Warp)                                │
│  - 监听本地端口 7788                                           │
│  - 接收 FileBay 配置                                           │
│  - 写入 SQLite 数据库                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Vault 本地数据库 (SQLite)                                     │
│  - 表: user_settings                                          │
│  - Key: filebay_config                                        │
│  - Value: JSON 配置                                           │
└─────────────────────────────────────────────────────────────┘
```

## 实现细节

### 1. Vault 端 (Rust)

#### 1.1 API 服务器

文件: `src-tauri/src/commands/vault_api_server.rs`

功能:
- 启动 HTTP API 服务器 (端口 7788)
- 提供以下接口:
  - `POST /api/v1/filebay/config` - 接收并保存配置
  - `GET /api/v1/filebay/config` - 查询配置
  - `DELETE /api/v1/filebay/config` - 删除配置
  - `GET /api/v1/health` - 健康检查

#### 1.2 数据存储

配置存储在 SQLite 数据库的 `user_settings` 表中:
- Key: `filebay_config`
- Value: JSON 字符串

```json
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

#### 1.3 Tauri Commands

```rust
// 启动 API 服务器
start_vault_api_server(port: Option<u16>) -> Result<String, String>

// 停止 API 服务器
stop_vault_api_server() -> Result<String, String>

// 检查服务器状态
check_vault_api_server_status() -> Result<bool, String>

// 手动保存配置
save_filebay_config_via_api(config: FileBayConfigPayload) -> Result<String, String>

// 手动获取配置
get_filebay_config_via_api() -> Result<Option<FileBayConfigPayload>, String>

// 手动删除配置
delete_filebay_config_via_api() -> Result<String, String>
```

### 2. Desktop 端 (Python)

#### 2.1 API 控制器

文件: `api/controllers/console/vault_integration.py`

功能:
- `/console/api/vault/sync-config` (POST) - 同步配置到 Vault
- `/console/api/vault/health` (GET) - 检查 Vault 健康状态

#### 2.2 配置解析

使用现有的 `resolve_user_filebay_config` 函数获取用户配置:

```python
from libs.filebay_user_config import resolve_user_filebay_config

config_dict = resolve_user_filebay_config(
    identifier=user_email,
    account=current_user,
    mask_token=False,
    allow_global_fallback=False
)
```

#### 2.3 API 调用

```python
import requests

response = requests.post(
    "http://localhost:7788/api/v1/filebay/config",
    json={
        'url': config_dict['gitea_url'],
        'username': config_dict['gitea_owner'],
        'repo_name': config_dict['gitea_repo'],
        'email': user_email,
        'token': config_dict['gitea_token'],
        'downloaded_at': '',
        'version': '1.0'
    },
    timeout=10
)
```

### 3. 前端 (TypeScript)

#### 3.1 服务层

文件: `web/service/vault.ts`

功能:
- `checkVaultHealth()` - 检查 Vault 是否运行
- `syncFileBayConfigToVault()` - 同步配置到 Vault
- `autoSyncToVault()` - 自动同步 (登录后调用)

#### 3.2 使用示例

```typescript
import { autoSyncToVault } from '@/service/vault'

// 用户登录成功后
const result = await autoSyncToVault()
if (result.synced) {
  console.log('配置已同步到 Vault')
} else {
  console.log('Vault 未运行，跳过同步')
}
```

## 使用流程

### 场景 1: 用户登录 Desktop

1. 用户在 Desktop 登录
2. Desktop 前端调用 `autoSyncToVault()`
3. 检查 Vault 是否运行
4. 如果 Vault 运行，调用 Desktop API `/vault/sync-config`
5. Desktop API 获取用户的 FileBay 配置
6. Desktop API 调用 Vault API 推送配置
7. Vault 接收配置并写入本地数据库

### 场景 2: 用户更新 FileBay 配置

1. 用户在 Desktop 设置页面更新 FileBay 配置
2. 保存成功后，调用 `autoSyncToVault()`
3. 同步最新配置到 Vault

### 场景 3: Vault 启动时自动启动 API 服务器

在 Vault 的 `lib.rs` 中添加启动逻辑:

```rust
// 在 Tauri Builder 之后
let app = tauri::Builder::default()
    // ... 其他配置
    .build(tauri::generate_context!())
    .expect("error while running tauri application");

// 启动 API 服务器
app.run(|app_handle, event| {
    if let tauri::RunEvent::Ready = event {
        let app_handle = app_handle.clone();
        tauri::async_runtime::spawn(async move {
            use crate::commands::vault_api_server::VaultApiServer;
            let server = VaultApiServer::new(app_handle, 7788);
            if let Err(e) = server.start().await {
                eprintln!("Failed to start Vault API server: {}", e);
            }
        });
    }
});
```

## 安全考虑

### 1. 本地通信

- API 服务器只监听 `127.0.0.1`，不对外暴露
- 使用 HTTP 协议 (本地通信无需 HTTPS)

### 2. Token 安全

- Token 存储在 SQLite 数据库中
- 数据库文件位于用户目录，受操作系统权限保护
- 可以考虑对 Token 进行加密存储

### 3. CORS 配置

- 允许所有来源 (因为是本地通信)
- 生产环境可以限制为 Desktop 的来源

## 错误处理

### 1. Vault 未运行

Desktop 调用 Vault API 时会先检查健康状态，如果 Vault 未运行，会跳过同步，不影响用户登录。

### 2. 网络超时

设置合理的超时时间 (10 秒)，避免长时间等待。

### 3. 配置不完整

Desktop API 会验证配置完整性，如果配置不完整，返回 404 错误。

## 测试

### 1. 测试 Vault API

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

# 查询配置
curl http://localhost:7788/api/v1/filebay/config

# 删除配置
curl -X DELETE http://localhost:7788/api/v1/filebay/config
```

### 2. 测试 Desktop API

```bash
# 检查 Vault 健康状态
curl http://localhost:5001/console/api/vault/health

# 同步配置 (需要登录)
curl -X POST http://localhost:5001/console/api/vault/sync-config \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{}'
```

## 部署

### 1. Vault 端

- 确保 `warp` 和 `hyper` 依赖已添加到 `Cargo.toml`
- 编译 Vault 应用
- 启动时自动启动 API 服务器

### 2. Desktop 端

- 确保 `requests` 库已安装
- 注册 Vault 集成控制器
- 在登录成功后调用自动同步

### 3. 前端

- 导入 Vault 服务
- 在登录成功回调中调用 `autoSyncToVault()`

## 未来优化

1. **配置加密**: 对存储在数据库中的 Token 进行加密
2. **配置版本管理**: 支持配置版本控制和回滚
3. **多用户支持**: 支持多个用户的配置存储
4. **配置同步状态**: 显示配置同步状态和历史记录
5. **自动重试**: 如果同步失败，自动重试
6. **配置验证**: 在保存前验证配置的有效性

## 常见问题

### Q1: Vault API 服务器启动失败怎么办?

A: 检查端口 7788 是否被占用，可以修改端口号。

### Q2: Desktop 无法连接到 Vault 怎么办?

A: 确保 Vault 应用正在运行，并且 API 服务器已启动。

### Q3: 配置同步失败怎么办?

A: 检查 Desktop 日志和 Vault 日志，确认错误原因。

### Q4: 如何手动触发配置同步?

A: 可以在 Desktop 设置页面添加"同步到 Vault"按钮，调用 `syncFileBayConfigToVault()`。

## 总结

本方案通过在 Vault 启动时开启本地 HTTP API 服务器，使得 Desktop 可以在用户登录后自动推送 FileBay 配置到 Vault 本地数据库，避免了文件权限问题，实现了无缝集成。
