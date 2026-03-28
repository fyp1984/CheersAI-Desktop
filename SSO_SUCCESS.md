# ✅ SSO 服务配置成功指南

## 当前状态

- ✅ **SSO 服务**: http://localhost:18000 - 正常运行
- ✅ **Desktop 前端**: http://localhost:3000 - 正常运行
- ✅ **Desktop 后端**: http://localhost:5001 - 正常运行

## 立即开始配置

### 步骤 1: 访问 SSO 管理界面

打开浏览器访问：
```
http://localhost:18000
```

### 步骤 2: 使用默认管理员账号登录

Casdoor 默认管理员账号：
- **用户名**: `admin`
- **密码**: `123`

### 步骤 3: 修改管理员密码（推荐）

登录后，建议立即修改密码：
1. 点击右上角头像
2. 选择 "My Account"
3. 修改密码为 `123456`（或您喜欢的密码）
4. 保存

### 步骤 4: 配置应用的 Redirect URIs

这是**最关键的一步**：

1. 点击左侧菜单 **Applications**
2. 找到默认应用（通常名为 `app-built-in`）
3. 点击应用名称进入详情页
4. 点击 **Edit** 按钮
5. 找到 **Redirect URIs** 字段
6. 添加以下三个回调地址（每行一个）：
   ```
   http://localhost:3000/signin/built-in
   http://localhost:3000/oauth-callback
   http://localhost:9000/callback
   ```
7. 确保 **Enable password** 已勾选 ✅
8. 确保 **Enable sign up** 已勾选 ✅
9. 点击 **Save** 保存

### 步骤 5: 记录 Client ID

在应用详情页面，找到并复制 **Client ID**（类似 `c98f7150fe9c044bf217`）

### 步骤 6: 更新 Desktop 配置

编辑 `e:\CheersAI-Desktop\web\.env`，确认以下配置：

```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:18000
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=<粘贴从 SSO 复制的 Client ID>
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

如果 Client ID 不同，请更新为正确的值。

### 步骤 7: 重启 Desktop 前端（如果修改了 Client ID）

如果您修改了 `.env` 文件：

```bash
# 停止当前进程
Get-Process -Name node | Stop-Process -Force

# 重新启动
cd e:\CheersAI-Desktop\web
pnpm dev
```

## 测试 SSO 登录

### 完整测试流程

1. **访问 Desktop 登录页**
   ```
   http://localhost:3000/signin
   ```

2. **点击 "SSO 登录" 按钮**
   - 应该跳转到 SSO 授权页面（18000端口）

3. **在 SSO 页面登录**
   - 用户名: `admin`
   - 密码: `123` 或您修改后的密码

4. **授权**
   - 如果是首次授权，可能需要点击"授权"按钮

5. **自动回调**
   - 登录成功后自动跳转回 Desktop
   - 完成 Token 交换
   - 跳转到 `/apps` 页面

## 如果遇到问题

### 问题 1: 授权页面一直加载

**原因**: Redirect URIs 未正确配置

**解决**: 
1. 返回 SSO 管理界面
2. 检查 Applications → app-built-in → Redirect URIs
3. 确保包含 `http://localhost:3000/signin/built-in`

### 问题 2: 回调后显示错误

**原因**: Client ID 不匹配

**解决**:
1. 在 SSO 中查看应用的 Client ID
2. 确保 Desktop `.env` 中的 `NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID` 与之一致
3. 重启 Desktop 前端

### 问题 3: 无法登录 SSO

**原因**: 密码错误

**解决**:
- 默认密码是 `123`
- 如果忘记密码，需要重置数据库

### 查看日志

**SSO 日志**:
```bash
docker logs cheersai-sso-casdoor-1 --tail 50
```

**Desktop 前端日志**:
查看运行 `pnpm dev` 的终端输出

**浏览器控制台**:
按 F12 查看 Network 和 Console 标签

## 配置检查清单

在测试前，请确认：

- [ ] SSO 服务运行正常 (http://localhost:18000)
- [ ] 能用 admin/123 登录 SSO 管理界面
- [ ] app-built-in 应用的 Redirect URIs 已配置
- [ ] app-built-in 应用的 Enable password 已启用
- [ ] Desktop .env 中的 Client ID 与 SSO 一致
- [ ] Desktop 前端正在运行 (http://localhost:3000)

## 下一步

配置完成后，您就可以：

1. ✅ 使用 SSO 登录 Desktop
2. ✅ 测试 "Apply Beta" 功能（将使用 SSO 数据库）
3. ✅ 在 SSO 管理界面管理用户和应用

## 重要提示

- **Redirect URIs** 必须完全匹配，包括协议、域名、端口和路径
- **Client ID** 必须在 SSO 和 Desktop 中保持一致
- 修改 `.env` 后必须重启 Desktop 前端
- SSO 的默认密码是 `123`，建议修改

现在请按照上述步骤配置 SSO，然后测试登录！

详细配置指南: `@e:\CheersAI-Desktop\SSO_MANUAL_SETUP.md:1-154`
