# 测试 SSO 登录 - 详细步骤

## 当前状态分析

从你的日志来看，你已经到达了 `/apps` 页面，但是：
1. 收到 401 错误 - 说明没有有效的认证 Cookie
2. 收到 400 错误 - 说明某些 API 请求参数有问题

**关键问题**：我没有看到任何 `[SSO]` 开头的日志，这说明：
- 要么 SSO 登录流程没有执行
- 要么日志被清除了（因为没有勾选 "Preserve log"）

## 重新测试（完整步骤）

### 步骤 1: 准备工作

1. **关闭所有浏览器标签页**
2. **打开一个新的浏览器窗口**
3. **按 F12 打开开发者工具**
4. **在 Console 标签中，勾选 "Preserve log"** ⚠️ 非常重要！
5. **在 Network 标签中，勾选 "Preserve log"** ⚠️ 非常重要！

### 步骤 2: 清除 Cookie

1. 在开发者工具中切换到 **Application** 标签
2. 展开 **Cookies**
3. 右键点击 `http://localhost:3000`，选择 "Clear"
4. 右键点击 `http://localhost:5001`，选择 "Clear"

### 步骤 3: 开始测试

1. 在地址栏输入：`http://localhost:3000/signin`
2. 按回车访问
3. 你应该看到登录页面
4. **不要关闭开发者工具**

### 步骤 4: 点击 SSO 登录

1. 点击页面上的 "SSO 登录" 按钮
2. 浏览器会跳转到 SSO 服务器
3. **不要关闭开发者工具**

### 步骤 5: 完成 SSO 认证

1. 在 SSO 页面输入用户名和密码
2. 点击登录
3. 浏览器会自动跳转回 `http://localhost:3000/oauth-callback?code=...&state=...`
4. **不要关闭开发者工具**

### 步骤 6: 观察日志

在 Console 标签中，你应该看到以下日志（按顺序）：

```
[SSO] OAuth callback page loaded
[SSO] Starting token exchange with: {code: "...", state: "...", redirectUri: "..."}
[SSO] Step 1: Exchanging OAuth code for SSO access_token
[SSO] Step 2: Fetching user info from SSO
[SSO] User info received: {email: "...", name: "..."}
[SSO] Step 3: Logging into Dify backend
[SSO] Calling backend /auth/desktop-sso/login with: {email: "...", name: "..."}
[SSO] Backend login response: {result: "success"}
[SSO] Token exchange successful, waiting 1000ms before redirect
[SSO] Redirecting to /apps
```

### 步骤 7: 检查结果

1. 浏览器应该自动跳转到 `http://localhost:3000/apps`
2. 在 Application -> Cookies -> `http://localhost:5001` 中应该看到：
   - `access_token` 或 `__Host-access_token`
   - `refresh_token` 或 `__Host-refresh_token`
   - `csrf_token` 或 `__Host-csrf_token`

## 如果没有看到 [SSO] 日志

### 可能原因 1: 没有勾选 "Preserve log"
日志在页面跳转时被清除了。

**解决方案**：重新测试，确保勾选 "Preserve log"

### 可能原因 2: SSO 登录按钮没有正确配置
`NEXT_PUBLIC_DESKTOP_SSO_ENABLED` 没有设置为 `true`

**解决方案**：检查 `web/.env.local` 文件

### 可能原因 3: 回调 URL 不正确
SSO 服务器没有跳转回 `/oauth-callback`

**解决方案**：检查 SSO 服务器的 OAuth 应用配置

## 如果看到 [SSO] 日志但登录失败

### 情况 1: "authorization code has been used"
OAuth code 被使用了两次

**解决方案**：已修复（使用 useRef 防止重复执行）

### 情况 2: "Token exchange failed"
SSO 服务器返回错误

**解决方案**：查看详细错误信息，检查 SSO 配置

### 情况 3: 后端返回 500
数据库或账户创建失败

**解决方案**：查看后端日志 `api/backend.log`

## 如果登录成功但仍然 401

### 检查 1: Cookie 是否存在
在 Application -> Cookies 中检查是否有 `access_token`

### 检查 2: Cookie 的 Domain
确认 Cookie 的 Domain 是 `localhost` 或为空

### 检查 3: 后端日志
确认后端日志中有 "Desktop SSO Login success"

## 手动测试后端接口

如果 SSO 登录流程有问题，可以手动测试后端接口：

```powershell
# 测试后端登录接口
$body = @{
    email = "test@example.com"
    name = "Test User"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5001/console/api/auth/desktop-sso/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -SessionVariable session

# 查看响应
$response.StatusCode
$response.Headers

# 查看 Cookie
$session.Cookies.GetCookies("http://localhost:5001")
```

如果这个测试成功，说明后端接口没问题，问题在前端。

## 需要提供的信息

如果测试失败，请提供：

1. **Console 标签的完整日志**（特别是 `[SSO]` 开头的）
2. **Network 标签的请求列表**（特别是 `/api/auth/sso/token`、`/api/auth/sso/userinfo`、`/console/api/auth/desktop-sso/login`）
3. **Application -> Cookies 的截图**
4. **当前浏览器地址栏的 URL**
5. **后端日志的最后 100 行**

## 快速诊断

告诉我以下问题的答案：

1. ✅ 或 ❌ 是否看到了 `[SSO] OAuth callback page loaded` 日志？
2. ✅ 或 ❌ 是否看到了 `[SSO] Backend login response: {result: "success"}` 日志？
3. ✅ 或 ❌ 在 Cookies 中是否看到了 `access_token`？
4. ✅ 或 ❌ 浏览器是否自动跳转到了 `/apps` 页面？
5. 当前浏览器地址栏显示的 URL 是什么？
