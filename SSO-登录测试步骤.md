# SSO 登录测试步骤

## 重要说明

SSO 登录流程会跳转到 `/oauth-callback` 页面，而不是停留在 `/signin` 页面。

## 测试前准备

### 1. 清除浏览器 Cookie
在浏览器开发者工具中（F12）：
- 切换到 Application/Storage 标签
- 展开 Cookies
- 删除 `localhost:3000` 和 `localhost:5001` 下的所有 Cookie

### 2. 打开浏览器控制台
- 按 F12 打开开发者工具
- 切换到 Console 标签
- 确保 "Preserve log" 选项已勾选（重要！这样页面跳转后日志不会丢失）

### 3. 打开 Network 标签
- 切换到 Network 标签
- 确保 "Preserve log" 选项已勾选

## 测试步骤

### 步骤 1: 访问登录页面
访问 http://localhost:3000/signin

**预期**：
- 看到登录页面
- 控制台可能显示 401 错误（正常，因为还没有登录）

### 步骤 2: 点击 SSO 登录按钮
点击页面上的 "SSO 登录" 按钮

**预期**：
- 浏览器跳转到 SSO 服务器（https://uat-sso.cheersai.cloud）
- 看到 SSO 登录页面

### 步骤 3: 完成 SSO 认证
在 SSO 页面输入用户名和密码，完成认证

**预期**：
- SSO 认证成功后，浏览器自动跳转回 http://localhost:3000/oauth-callback?code=...&state=...

### 步骤 4: 观察回调页面
浏览器应该显示 "Completing SSO login..." 的加载页面

**预期控制台日志**：
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

### 步骤 5: 自动跳转到应用页面
等待 1 秒后，浏览器应该自动跳转到 http://localhost:3000/apps

**预期**：
- 成功进入应用主页
- 不再看到 401 错误

## 检查点

### 检查 1: Network 标签
在 Network 标签中应该看到以下请求：

1. **POST /api/auth/sso/token**
   - Status: 200
   - 这是交换 OAuth code 的请求

2. **POST /api/auth/sso/userinfo**
   - Status: 200
   - 这是获取用户信息的请求

3. **POST /console/api/auth/desktop-sso/login**
   - Status: 200
   - Response Headers 中应该有 `Set-Cookie`
   - 这是登录 Dify 后端的请求

### 检查 2: Cookie
在 Application/Storage -> Cookies -> localhost:5001 中应该看到：
- `access_token` 或 `__Host-access_token`
- `refresh_token` 或 `__Host-refresh_token`
- `csrf_token` 或 `__Host-csrf_token`

### 检查 3: 后端日志
在后端终端或 `api/backend.log` 中应该看到：
```
Desktop SSO login request received
Request data: {'email': '...', 'name': '...'}
Processing SSO login for: ...
Generating tokens for: ...
Setting cookies for: ...
Desktop SSO Login success for: ...
```

## 常见问题

### Q1: 点击 SSO 登录后没有跳转
**可能原因**：
- `NEXT_PUBLIC_DESKTOP_SSO_ENABLED` 未设置为 `true`
- `NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL` 配置错误

**解决方案**：
检查 `web/.env.local` 配置

### Q2: SSO 认证后没有跳转回来
**可能原因**：
- SSO 服务器的 redirect_uri 配置不正确
- 应该配置为 `http://localhost:3000/oauth-callback`

**解决方案**：
联系 SSO 管理员检查 OAuth 应用配置

### Q3: 回调页面显示 "state mismatch"
**可能原因**：
- sessionStorage 中的 state 丢失
- 浏览器隐私设置阻止了 sessionStorage

**解决方案**：
- 检查浏览器隐私设置
- 尝试使用无痕模式测试

### Q4: 看到 "[SSO] Token exchange failed"
**可能原因**：
- OAuth code 已过期或无效
- SSO 服务器返回错误

**解决方案**：
- 查看控制台的详细错误信息
- 检查 Network 标签中的请求响应

### Q5: 后端返回 500 错误
**可能原因**：
- 数据库连接失败
- 账户创建失败

**解决方案**：
- 查看后端日志 `api/backend.log`
- 检查数据库是否正常运行

### Q6: Cookie 设置了但页面跳转后又 401
**可能原因**：
- Cookie 的 Domain 配置不正确
- 浏览器没有正确处理 Cookie

**解决方案**：
- 确认 `api/.env` 中 `COOKIE_DOMAIN=` 为空
- 增加等待时间（已设置为 1000ms）
- 检查浏览器 Cookie 设置

## 如果测试失败

请提供以下信息：
1. 控制台的完整日志（特别是 `[SSO]` 开头的日志）
2. Network 标签中的请求列表（特别是状态码不是 200 的请求）
3. 后端日志 `api/backend.log` 的最后 50 行
4. 浏览器地址栏的 URL（特别是在哪一步卡住了）

## 配置文件参考

### web/.env.local
```bash
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

### api/.env
```bash
COOKIE_DOMAIN=
CONSOLE_WEB_URL=http://localhost:3000
CONSOLE_API_URL=http://localhost:5001
```
