# Vault Bridge 完整演示指南

## ✅ 系统状态

所有服务已启动并正常运行：

- ✅ **Vault Bridge**: http://localhost:8765 (正常运行)
- ✅ **API 服务**: http://localhost:5001 (正常运行)
- ✅ **Web 服务**: http://localhost:3000 (正常运行)
- ✅ **数据库**: `C:\Users\33814\.cheersai\vault.db` (已初始化)

## 🎯 演示目标

展示 Desktop SSO 登录后，FileBay 配置自动同步到 Vault 数据库的完整流程。

## 📋 演示步骤

### 方式 A: 真实登录流程（推荐）

#### 1. 打开浏览器并准备开发者工具

```
1. 打开 Chrome 或 Edge 浏览器
2. 按 F12 打开开发者工具
3. 切换到 Console 标签
4. 清空日志（点击 🚫 图标）
```

#### 2. 访问登录页面

```
http://localhost:3000/signin
```

#### 3. 使用 Desktop SSO 登录

```
1. 点击 "Desktop SSO Login" 按钮
2. 输入你的 SSO 凭据
3. 完成认证
```

#### 4. 观察自动同步过程

登录成功后，在浏览器 Console 中你会看到：

```javascript
[Vault Bridge] Service is running, attempting to sync FileBay config
[Vault Bridge] FileBay config synced successfully
```

#### 5. 验证配置已保存

在浏览器 Console 中执行：

```javascript
// 获取当前用户信息
fetch('/console/api/account/profile', {
  credentials: 'include'
}).then(r => r.json()).then(user => {
  console.log('✓ 用户信息:', user);
  
  // 查询 Vault 配置
  return fetch(`http://localhost:8765/vault/config/filebay/${user.id}`);
}).then(r => r.json()).then(config => {
  console.log('✓ Vault 配置:', config);
  console.log('  - URL:', config.url);
  console.log('  - 用户名:', config.username);
  console.log('  - 仓库:', config.repoName);
  console.log('  - Token:', config.token.substring(0, 20) + '...');
});
```

### 方式 B: 测试脚本演示（已完成）

我们刚才已经运行了测试脚本，结果如下：

```powershell
PS E:\CheersAI-Desktop> .\test_vault_sync.ps1

========================================
  Vault Bridge 配置同步测试
========================================

1. 检查 Vault Bridge 服务...
   ✓ Vault Bridge 运行正常

2. 模拟配置同步...
   ✓ 配置同步成功
   响应: {
     "success": true,
     "user_id": "test_user_123",
     "username": "test_user",
     "repo_name": "workspace"
   }

3. 验证配置已保存...
   ✓ 配置读取成功
   配置内容: {
     "url": "https://filebay.example.com",
     "username": "test_user",
     "repoName": "workspace",
     "email": "test@example.com",
     "token": "ghp_test_token_1234567890",
     "updatedAt": "2026-05-06T21:51:35"
   }

4. 查看数据库内容...
   ✓ 数据库查询成功
   数据库记录:
   test_user_123|test@example.com|test_user|workspace|ghp_test_token_12345...

5. 清理测试数据...
   ✓ 测试数据已清理
```

## 🔍 Vault Bridge 日志

在 Vault Bridge 服务终端中，你可以看到实时日志：

```
2026-05-06 21:51:35,114 - services.vault_bridge_service - INFO - FileBay config saved for user test_user_123 (username: test_user)
2026-05-06 21:51:35,114 - werkzeug - INFO - 127.0.0.1 - - [06/May/2026 21:51:35] "POST /vault/config/filebay HTTP/1.1" 200 -
```

## 📊 数据流程图

```
┌─────────────────────────────────────────────────────────────┐
│  1. 用户在浏览器中使用 Desktop SSO 登录                       │
│     http://localhost:3000/signin                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. OAuth 回调页面 (oauth-callback/page.tsx)                 │
│     - exchangeSSOToken() 交换 Token                          │
│     - 获取用户信息 (/console/api/account/profile)            │
│     - 获取 FileBay 配置 (/console/api/gitea/config/download) │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 检查 Vault Bridge 健康状态                                │
│     GET http://localhost:8765/health                         │
│     响应: {"status": "ok"}                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 同步配置到 Vault Bridge                                   │
│     POST http://localhost:8765/vault/config/filebay          │
│     Body: {                                                  │
│       "user_id": "123",                                      │
│       "config": {                                            │
│         "url": "https://filebay.example.com",               │
│         "username": "user_abc",                             │
│         "repoName": "workspace",                            │
│         "email": "user@example.com",                        │
│         "token": "ghp_xxxx"                                 │
│       }                                                      │
│     }                                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Vault Bridge 保存到 SQLite 数据库                         │
│     INSERT INTO filebay_configs (...)                        │
│     数据库: C:\Users\33814\.cheersai\vault.db                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  6. 浏览器控制台显示成功消息                                   │
│     [Vault Bridge] FileBay config synced successfully        │
└─────────────────────────────────────────────────────────────┘
```

## 🎬 实时演示命令

### 监控 Vault Bridge 日志

在一个终端中运行：

```powershell
# 实时查看日志
Get-Content api\vault_bridge.log -Wait -Tail 20
```

### 监控数据库变化

在另一个终端中运行：

```powershell
# 每 2 秒查询一次数据库
while ($true) {
    Clear-Host
    Write-Host "=== Vault 数据库内容 ===" -ForegroundColor Cyan
    sqlite3 "$env:USERPROFILE\.cheersai\vault.db" "SELECT user_id, email, username, repo_name, datetime(updated_at) as updated FROM filebay_configs;"
    Start-Sleep -Seconds 2
}
```

### 测试 API 端点

```powershell
# 健康检查
curl http://localhost:8765/health

# 查询所有配置（需要先登录）
# 通过邮箱查询
curl http://localhost:8765/vault/config/filebay/by-email/your-email@example.com

# 通过用户 ID 查询
curl http://localhost:8765/vault/config/filebay/123
```

## 📸 预期结果截图说明

### 1. 浏览器控制台

你应该看到：
```
✓ [Vault Bridge] Service is running, attempting to sync FileBay config
✓ [Vault Bridge] FileBay config synced successfully
```

### 2. Vault Bridge 日志

你应该看到：
```
INFO - FileBay config saved for user xxx (username: xxx)
INFO - 127.0.0.1 - - [06/May/2026 21:51:35] "POST /vault/config/filebay HTTP/1.1" 200 -
```

### 3. 数据库查询结果

```json
{
  "url": "https://filebay.example.com",
  "username": "user_abc123",
  "repoName": "workspace",
  "email": "user@example.com",
  "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "updatedAt": "2026-05-06T21:51:35"
}
```

## 🎯 成功标准

✅ 所有以下条件都满足，说明集成成功：

1. ✅ Vault Bridge 服务正常运行
2. ✅ 登录后浏览器控制台显示同步成功
3. ✅ 可以通过 API 查询到配置
4. ✅ 数据库中有配置记录
5. ✅ Vault Bridge 日志中有保存记录

## 🚀 下一步

配置同步成功后，你可以：

1. **在脱敏系统中实现配置读取**
   - 创建 Rust 命令读取 Vault 数据库
   - 在 UI 中添加自动加载功能

2. **测试完整流程**
   - 登录 → 配置同步 → 脱敏系统读取 → 文件上传

3. **生产环境部署**
   - 配置系统服务自动启动
   - 实现 Token 加密存储
   - 添加监控和告警

## 📞 需要帮助？

参考文档：
- [TEST_LOGIN_FLOW.md](./TEST_LOGIN_FLOW.md) - 详细测试步骤
- [VAULT_BRIDGE_QUICK_REFERENCE.md](./VAULT_BRIDGE_QUICK_REFERENCE.md) - 快速参考
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 实施总结

---

**准备好了吗？** 现在就打开浏览器开始真实的登录测试！🎉
