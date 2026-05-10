# 🚀 快速同步 FileBay 配置

## 问题

本地 HTML 文件（`file://`）无法访问 Vault 系统的 Cookie，导致无法获取配置。

## ✅ 解决方案

使用 **同域页面** 进行同步！

## 📋 步骤

### 1. 确保已登录

访问并登录：
```
http://localhost:3000/signin
```

### 2. 访问同步页面

在**同一个浏览器**中打开：
```
http://localhost:3000/sync-config
```

### 3. 点击"开始同步"

页面会自动：
1. 获取你的用户信息
2. 获取 FileBay 配置
3. 检查 Vault Bridge
4. 同步配置到数据库
5. 验证配置已保存

### 4. 验证成功

在命令行中运行：
```powershell
sqlite3 $env:USERPROFILE\.cheersai\vault.db "SELECT user_id, email, username, repo_name FROM filebay_configs;"
```

应该能看到你的配置！

## 🎯 优势

- ✅ 同域访问，共享 Cookie
- ✅ 无需重新登录
- ✅ 实时反馈
- ✅ 自动验证

## 📝 下一步

配置同步成功后：

1. **在脱敏应用中读取配置**
   - 使用 Rust 读取 `~/.cheersai/vault.db`
   - 参考 `MULTI_METHOD_CONFIG_LOADER.md`

2. **测试配置加载**
   - 打开 `http://localhost:3000/sync-config`
   - 查看已保存的配置

3. **开始使用**
   - 配置已经在 Vault 数据库中
   - 脱敏应用可以直接读取

## 🔧 故障排查

### 问题：页面显示 404

**原因**: Next.js 需要编译新页面

**解决**: 等待几秒钟，刷新页面

### 问题：仍然显示未登录

**原因**: Cookie 未共享或会话过期

**解决**: 
1. 在同一个浏览器中先访问 `http://localhost:3000/signin`
2. 登录成功后，再访问 `http://localhost:3000/sync-config`
3. 不要关闭浏览器

### 问题：Vault Bridge 未运行

**解决**:
```powershell
.\start_vault_bridge.ps1
```

## 📊 完整流程

```
1. 打开浏览器
   ↓
2. 访问 http://localhost:3000/signin
   ↓
3. 登录（Desktop SSO）
   ↓
4. 访问 http://localhost:3000/sync-config
   ↓
5. 点击"开始同步"
   ↓
6. 等待同步完成
   ↓
7. 查看配置详情
   ↓
8. 在脱敏应用中使用配置
```

## 🎉 成功！

现在你的 FileBay 配置已经在 Vault 数据库中了！

脱敏应用可以通过读取 `~/.cheersai/vault.db` 来获取配置，无需手动输入！
