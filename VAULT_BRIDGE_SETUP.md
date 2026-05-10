# Vault Bridge 快速设置指南

## 概述

Vault Bridge 是一个本地监听服务，用于在 Desktop 登录成功后自动将 FileBay 配置同步到本地数据库，供脱敏系统使用。

## 架构流程

```
Desktop 登录成功
    ↓
获取 FileBay 配置
    ↓
HTTP POST → Vault Bridge (localhost:8765)
    ↓
写入 SQLite (~/.cheersai/vault.db)
    ↓
脱敏系统读取配置
```

## 快速开始

### 1. 启动 Vault Bridge 服务

**Windows (PowerShell):**

```powershell
# 在 CheersAI-Desktop 项目根目录
.\start_vault_bridge.ps1
```

**Linux/Mac:**

```bash
cd api
python start_vault_bridge.py
```

### 2. 验证服务运行

打开浏览器访问：http://localhost:8765/health

或使用 curl：

```bash
curl http://localhost:8765/health
```

预期响应：

```json
{
  "status": "ok",
  "service": "vault-bridge",
  "version": "1.0.0",
  "database": "C:\\Users\\YourName\\.cheersai\\vault.db",
  "database_exists": true
}
```

### 3. 启动 Vault Web 服务

```bash
cd web
pnpm dev
```

### 4. 测试登录和配置同步

1. 打开浏览器访问：http://localhost:3000
2. 使用 Desktop SSO 登录
3. 登录成功后，检查浏览器控制台日志：
   - `[Vault Bridge] Service is running, attempting to sync FileBay config`
   - `[Vault Bridge] FileBay config synced successfully`

### 5. 验证配置已保存

**方式 A: 使用 API**

```bash
# 通过用户 ID 查询
curl http://localhost:8765/vault/config/filebay/<USER_ID>

# 通过邮箱查询
curl http://localhost:8765/vault/config/filebay/by-email/<EMAIL>
```

**方式 B: 直接查看数据库**

```bash
# Windows
sqlite3 %USERPROFILE%\.cheersai\vault.db "SELECT * FROM filebay_configs;"

# Linux/Mac
sqlite3 ~/.cheersai/vault.db "SELECT * FROM filebay_configs;"
```

## API 端点

### 健康检查

```
GET /health
```

响应：

```json
{
  "status": "ok",
  "service": "vault-bridge",
  "version": "1.0.0",
  "database": "~/.cheersai/vault.db",
  "database_exists": true
}
```

### 保存 FileBay 配置

```
POST /vault/config/filebay
Content-Type: application/json

{
  "user_id": "用户ID",
  "config": {
    "url": "https://filebay.example.com",
    "username": "user123",
    "repoName": "workspace",
    "email": "user@example.com",
    "token": "ghp_xxxxxxxxxxxx"
  }
}
```

响应：

```json
{
  "success": true,
  "message": "FileBay config saved to Vault",
  "user_id": "用户ID",
  "username": "user123",
  "repo_name": "workspace"
}
```

### 获取 FileBay 配置（通过用户 ID）

```
GET /vault/config/filebay/<user_id>
```

响应：

```json
{
  "url": "https://filebay.example.com",
  "username": "user123",
  "repoName": "workspace",
  "email": "user@example.com",
  "token": "ghp_xxxxxxxxxxxx",
  "updatedAt": "2026-05-06T10:30:00"
}
```

### 获取 FileBay 配置（通过邮箱）

```
GET /vault/config/filebay/by-email/<email>
```

响应：

```json
{
  "userId": "用户ID",
  "url": "https://filebay.example.com",
  "username": "user123",
  "repoName": "workspace",
  "email": "user@example.com",
  "token": "ghp_xxxxxxxxxxxx",
  "updatedAt": "2026-05-06T10:30:00"
}
```

### 删除 FileBay 配置

```
DELETE /vault/config/filebay/<user_id>
```

响应：

```json
{
  "success": true,
  "message": "FileBay config deleted from Vault"
}
```

## 数据库结构

**表名**: `filebay_configs`

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | TEXT | 用户ID（主键） |
| url | TEXT | FileBay URL |
| username | TEXT | FileBay 用户名 |
| repo_name | TEXT | 仓库名 |
| email | TEXT | 用户邮箱 |
| token | TEXT | 访问 Token |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引**:
- `idx_filebay_configs_email` - 邮箱索引
- `idx_filebay_configs_username` - 用户名索引

## 故障排查

### 问题 1: Vault Bridge 服务无法启动

**症状**: 运行启动脚本后报错

**解决方案**:

1. 检查 Python 版本（需要 3.10+）:
   ```bash
   python --version
   ```

2. 检查依赖是否安装:
   ```bash
   cd api
   pip install flask flask-cors
   ```

3. 检查端口是否被占用:
   ```bash
   # Windows
   netstat -ano | findstr :8765
   
   # Linux/Mac
   lsof -i :8765
   ```

### 问题 2: 登录后配置未同步

**症状**: 登录成功，但 Vault 数据库中没有配置

**解决方案**:

1. 检查 Vault Bridge 是否运行:
   ```bash
   curl http://localhost:8765/health
   ```

2. 检查浏览器控制台日志:
   - 打开开发者工具 (F12)
   - 查看 Console 标签
   - 搜索 `[Vault Bridge]`

3. 检查 FileBay 配置是否完整:
   ```bash
   # 访问配置下载端点
   curl http://localhost:5001/console/api/gitea/config/download \
     -H "Cookie: your-session-cookie"
   ```

### 问题 3: 数据库权限错误

**症状**: `Permission denied` 或 `Unable to open database file`

**解决方案**:

1. 检查目录权限:
   ```bash
   # Windows
   icacls %USERPROFILE%\.cheersai
   
   # Linux/Mac
   ls -la ~/.cheersai
   ```

2. 手动创建目录:
   ```bash
   # Windows
   mkdir %USERPROFILE%\.cheersai
   
   # Linux/Mac
   mkdir -p ~/.cheersai
   chmod 700 ~/.cheersai
   ```

### 问题 4: CORS 错误

**症状**: 浏览器控制台显示 CORS 错误

**解决方案**:

Vault Bridge 已启用 CORS，如果仍有问题：

1. 确认 Vault Bridge 版本是最新的
2. 检查浏览器是否阻止了 localhost 请求
3. 尝试使用 `127.0.0.1` 替代 `localhost`

## 日志

Vault Bridge 日志保存在：

- **控制台输出**: 实时日志
- **文件日志**: `api/vault_bridge.log`

查看日志：

```bash
# Windows
type api\vault_bridge.log

# Linux/Mac
tail -f api/vault_bridge.log
```

## 安全考虑

1. **本地访问**: Vault Bridge 默认只监听 `127.0.0.1`，不接受外部连接
2. **Token 存储**: Token 以明文存储在本地数据库中，确保文件权限正确（600）
3. **数据库位置**: `~/.cheersai/vault.db` 只有当前用户可访问

## 下一步

完成 Vault Bridge 设置后，继续实现脱敏系统的配置读取功能：

1. 在脱敏系统中创建 Rust 命令读取 Vault 数据库
2. 在 UI 中添加自动加载配置功能
3. 测试完整的登录→同步→读取流程

详细步骤请参考 [VAULT_DESKTOP_INTEGRATION.md](./VAULT_DESKTOP_INTEGRATION.md)
