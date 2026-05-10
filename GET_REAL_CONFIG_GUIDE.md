# 获取真实 FileBay 配置 - 完整指南

## 🎯 问题分析

当前状态：
- ✅ Vault Bridge 服务正常运行
- ✅ 数据库文件存在
- ❌ **数据库中没有配置数据**（这是问题所在）

## 📋 解决步骤

### 步骤 1: 在 Vault Web 中登录

1. **打开浏览器**，访问：
   ```
   http://localhost:3000/signin
   ```

2. **使用 Desktop SSO 登录**
   - 点击 "Desktop SSO Login" 按钮
   - 输入你的 SSO 凭据
   - 完成认证

3. **等待登录成功**
   - 页面会重定向到 `/apps`
   - 这时配置应该已经自动同步到 Vault 数据库

### 步骤 2: 验证配置已同步

打开浏览器开发者工具（F12），在 Console 中执行：

```javascript
// 1. 获取用户信息
fetch('/console/api/account/profile', {
  credentials: 'include'
}).then(r => r.json()).then(user => {
  console.log('✓ 用户信息:', user);
  window.currentUser = user;
});

// 2. 获取 FileBay 配置
fetch('/console/api/gitea/config/download', {
  credentials: 'include'
}).then(r => r.json()).then(config => {
  console.log('✓ FileBay 配置:', config);
  window.currentConfig = config;
});

// 3. 检查 Vault Bridge
fetch('http://localhost:8765/health')
  .then(r => r.json())
  .then(health => console.log('✓ Vault Bridge:', health));

// 4. 手动同步配置到 Vault
fetch('http://localhost:8765/vault/config/filebay', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: window.currentUser.id,
    config: {
      url: window.currentConfig.gitea_url,
      username: window.currentConfig.gitea_owner,
      repoName: window.currentConfig.gitea_repo,
      email: window.currentUser.email,
      token: window.currentConfig.gitea_token
    }
  })
}).then(r => r.json()).then(result => {
  console.log('✓ 同步结果:', result);
});
```

### 步骤 3: 验证数据库中有数据

在命令行中执行：

```powershell
sqlite3 $env:USERPROFILE\.cheersai\vault.db "SELECT user_id, email, username, repo_name FROM filebay_configs;"
```

应该能看到类似这样的输出：
```
user123|user@example.com|user_abc|workspace
```

### 步骤 4: 重新测试配置加载

现在重新打开测试页面：
```
file:///E:/CheersAI-Desktop/test_all_methods.html
```

点击"测试所有方法"，应该能看到至少方法 1 和方法 2 成功。

## 🚨 如果还是失败

### 问题 A: 登录后配置没有自动同步

**原因**: OAuth 回调页面可能没有触发同步

**解决方案**: 手动同步

在浏览器 Console 中执行上面步骤 2 的代码。

### 问题 B: 获取配置时返回 403

**原因**: 会话过期或未登录

**解决方案**: 
1. 清除浏览器缓存和 Cookie
2. 重新登录
3. 确保在同一个浏览器标签页中操作

### 问题 C: Vault Bridge 无法连接

**原因**: 服务未运行或端口被占用

**解决方案**:
```powershell
# 检查服务状态
curl http://localhost:8765/health

# 如果失败，重启服务
.\start_vault_bridge.ps1
```

## 📝 完整的手动同步脚本

如果自动同步不工作，使用这个脚本手动同步：

```javascript
// 在浏览器 Console 中执行
(async function syncConfig() {
  try {
    // 1. 获取用户信息
    const userResponse = await fetch('/console/api/account/profile', {
      credentials: 'include'
    });
    
    if (!userResponse.ok) {
      console.error('❌ 未登录或会话过期');
      console.log('请先登录: http://localhost:3000/signin');
      return;
    }
    
    const user = await userResponse.json();
    console.log('✓ 用户信息:', user);
    
    // 2. 获取 FileBay 配置
    const configResponse = await fetch('/console/api/gitea/config/download', {
      credentials: 'include'
    });
    
    if (!configResponse.ok) {
      console.error('❌ 获取配置失败');
      return;
    }
    
    const config = await configResponse.json();
    console.log('✓ FileBay 配置:', config);
    
    // 3. 检查 Vault Bridge
    const healthResponse = await fetch('http://localhost:8765/health');
    
    if (!healthResponse.ok) {
      console.error('❌ Vault Bridge 未运行');
      console.log('请启动 Vault Bridge: .\\start_vault_bridge.ps1');
      return;
    }
    
    console.log('✓ Vault Bridge 运行正常');
    
    // 4. 同步配置
    const syncResponse = await fetch('http://localhost:8765/vault/config/filebay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        config: {
          url: config.gitea_url,
          username: config.gitea_owner,
          repoName: config.gitea_repo,
          email: user.email,
          token: config.gitea_token
        }
      })
    });
    
    if (!syncResponse.ok) {
      console.error('❌ 同步失败');
      return;
    }
    
    const result = await syncResponse.json();
    console.log('✅ 同步成功!', result);
    
    // 5. 验证
    const verifyResponse = await fetch(`http://localhost:8765/vault/config/filebay/${user.id}`);
    
    if (verifyResponse.ok) {
      const savedConfig = await verifyResponse.json();
      console.log('✅ 验证成功! 配置已保存:', savedConfig);
    }
    
  } catch (error) {
    console.error('❌ 错误:', error);
  }
})();
```

## ✅ 成功标志

完成后，你应该能看到：

1. **浏览器 Console**:
   ```
   ✓ 用户信息: {id: "123", email: "user@example.com", ...}
   ✓ FileBay 配置: {gitea_url: "...", gitea_owner: "...", ...}
   ✓ Vault Bridge 运行正常
   ✅ 同步成功!
   ✅ 验证成功! 配置已保存
   ```

2. **命令行查询**:
   ```powershell
   PS> sqlite3 $env:USERPROFILE\.cheersai\vault.db "SELECT * FROM filebay_configs;"
   # 应该能看到你的配置数据
   ```

3. **测试页面**:
   - 方法 1: ✓ 成功
   - 方法 2: ✓ 成功
   - 至少这两个方法应该成功

## 🎯 下一步

配置同步成功后：
1. 在脱敏应用中实现读取 Vault 数据库的代码
2. 测试自动加载配置
3. 开始使用文件脱敏功能

---

**需要帮助？** 如果还有问题，请提供：
- 浏览器 Console 的错误信息
- Vault Bridge 日志
- 数据库查询结果
