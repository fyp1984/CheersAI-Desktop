# 测试 Desktop SSO 登录和配置同步流程

## 🎯 目标

通过 Desktop SSO 登录，自动获取 FileBay 配置并同步到 Vault 数据库。

## ✅ 前置条件检查

所有服务都已启动：
- ✅ Vault Bridge: http://localhost:8765
- ✅ API 服务: http://localhost:5001
- ✅ Web 服务: http://localhost:3000

## 📋 测试步骤

### 1. 验证 Vault Bridge 运行状态

打开浏览器或命令行：

```bash
curl http://localhost:8765/health
```

预期响应：
```json
{
  "status": "ok",
  "service": "vault-bridge",
  "version": "1.0.0",
  "database": "C:\\Users\\33814\\.cheersai\\vault.db",
  "database_exists": true
}
```

### 2. 打开浏览器开发者工具

1. 打开浏览器（Chrome/Edge）
2. 按 F12 打开开发者工具
3. 切换到 **Console** 标签
4. 清空控制台日志（点击 🚫 图标）

### 3. 访问登录页面

在浏览器中访问：
```
http://localhost:3000/signin
```

### 4. 使用 Desktop SSO 登录

1. 点击 "Desktop SSO Login" 按钮
2. 输入你的 SSO 凭据
3. 完成认证流程

### 5. 观察控制台日志

登录成功后，在浏览器控制台中搜索 `[Vault Bridge]`，你应该看到：

```
[Vault Bridge] Service is running, attempting to sync FileBay config
[Vault Bridge] FileBay config synced successfully
```

如果看到这些日志，说明配置已成功同步！

### 6. 验证配置已保存

**方式 A: 使用 API 查询**

在浏览器控制台执行：

```javascript
// 获取当前用户信息
fetch('/console/api/account/profile', {
  credentials: 'include'
}).then(r => r.json()).then(user => {
  console.log('User ID:', user.id);
  console.log('Email:', user.email);
  
  // 查询 Vault 配置
  return fetch(`http://localhost:8765/vault/config/filebay/${user.id}`);
}).then(r => r.json()).then(config => {
  console.log('Vault Config:', config);
});
```

**方式 B: 使用命令行查询**

```bash
# 通过邮箱查询
curl http://localhost:8765/vault/config/filebay/by-email/your-email@example.com
```

**方式 C: 直接查看数据库**

```bash
sqlite3 %USERPROFILE%\.cheersai\vault.db "SELECT * FROM filebay_configs;"
```

### 7. 查看完整配置

预期响应示例：

```json
{
  "url": "https://filebay.example.com",
  "username": "user_abc123",
  "repoName": "workspace",
  "email": "user@example.com",
  "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "updatedAt": "2026-05-06T21:50:00"
}
```

## 🔍 调试信息

### 查看 Vault Bridge 日志

在 Vault Bridge 终端中，你应该看到：

```
2026-05-06 21:50:00,123 - services.vault_bridge_service - INFO - FileBay config saved for user 123 (username: user_abc123)
2026-05-06 21:50:00,124 - werkzeug - INFO - 127.0.0.1 - - [06/May/2026 21:50:00] "POST /vault/config/filebay HTTP/1.1" 200 -
```

### 查看 Web 服务日志

在 Web 服务终端中，你应该看到：

```
GET /console/api/account/profile 200
GET /console/api/gitea/config/download 200
```

## 🐛 故障排查

### 问题 1: 看不到 [Vault Bridge] 日志

**可能原因**:
- Vault Bridge 服务未运行
- 浏览器控制台被过滤

**解决方案**:
1. 检查 Vault Bridge 健康状态：`curl http://localhost:8765/health`
2. 清除控制台过滤器
3. 重新登录

### 问题 2: 配置同步失败

**可能原因**:
- FileBay 配置不完整
- 网络连接问题

**解决方案**:
1. 查看浏览器控制台的错误信息
2. 检查 Vault Bridge 日志
3. 手动测试配置下载：
   ```javascript
   fetch('/console/api/gitea/config/download', {
     credentials: 'include'
   }).then(r => r.json()).then(console.log);
   ```

### 问题 3: 数据库中没有配置

**可能原因**:
- 配置同步时出错
- 数据库权限问题

**解决方案**:
1. 检查数据库文件是否存在：
   ```bash
   ls %USERPROFILE%\.cheersai\vault.db
   ```
2. 查看 Vault Bridge 日志中的错误信息
3. 手动测试保存配置：
   ```bash
   curl -X POST http://localhost:8765/vault/config/filebay \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test123",
       "config": {
         "url": "https://test.com",
         "username": "testuser",
         "repoName": "testrepo",
         "email": "test@test.com",
         "token": "test_token"
       }
     }'
   ```

## 📊 成功标志

登录流程成功完成后，你应该能够：

1. ✅ 在浏览器控制台看到 `[Vault Bridge] FileBay config synced successfully`
2. ✅ 通过 API 查询到配置
3. ✅ 在数据库中看到配置记录
4. ✅ 在 Vault Bridge 日志中看到保存记录

## 🎉 下一步

配置同步成功后，你可以：

1. 在脱敏系统中实现配置读取功能
2. 测试文件脱敏和上传流程
3. 验证端到端集成

## 📝 注意事项

1. **Token 安全**: Token 当前以明文存储，生产环境需要加密
2. **会话管理**: 登录会话有效期限制，过期需要重新登录
3. **配置更新**: 每次登录都会更新配置，保持最新状态

---

**准备好了吗？** 现在就打开浏览器，访问 http://localhost:3000/signin 开始测试！
