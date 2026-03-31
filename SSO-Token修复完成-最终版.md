# SSO Token 传递问题 - 调试版本

## 最新修改

### 1. 增加等待时间
- 从 500ms 增加到 1000ms，让浏览器有更多时间处理 Cookie

### 2. 添加详细日志
在浏览器控制台中可以看到完整的 SSO 登录流程：
- `[SSO] Detected SSO callback` - 检测到 SSO 回调
- `[SSO] Starting token exchange with params` - 开始 token 交换
- `[SSO] Step 1: Exchanging OAuth code for SSO access_token` - 交换 OAuth code
- `[SSO] Step 2: Fetching user info from SSO` - 获取用户信息
- `[SSO] Step 3: Logging into Dify backend` - 登录 Dify 后端
- `[SSO] Backend login response` - 后端登录响应
- `[SSO] Token exchange successful` - Token 交换成功
- `[SSO] Redirecting to /apps` - 重定向到 /apps

## 调试步骤

### 1. 清除所有 Cookie
在浏览器开发者工具中：
- Application/Storage -> Cookies
- 删除 localhost:3000 和 localhost:5001 下的所有 Cookie

### 2. 打开浏览器控制台
- 按 F12 打开开发者工具
- 切换到 Console 标签

### 3. 测试 SSO 登录
1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 完成 SSO 认证
4. 观察控制台日志

### 4. 检查日志输出
查看控制台中的 `[SSO]` 日志，确认每一步是否成功：

**正常流程**：
```
[SSO] Detected SSO callback
[SSO] Starting token exchange with params: {code: "...", state: "...", redirectUri: "..."}
[SSO] Step 1: Exchanging OAuth code for SSO access_token
[SSO] Step 2: Fetching user info from SSO
[SSO] User info received: {email: "...", name: "..."}
[SSO] Step 3: Logging into Dify backend
[SSO] Calling backend /auth/desktop-sso/login with: {email: "...", name: "..."}
[SSO] Backend login response: {result: "success"}
[SSO] Token exchange successful, waiting 1000ms before redirect
[SSO] Redirecting to /apps
```

**如果在某一步失败**，会看到错误日志：
```
[SSO] Token exchange failed: Error: ...
```

### 5. 检查 Network 标签
在 Network 标签中查看：
1. `/api/auth/sso/token` - 应该返回 200
2. `/api/auth/sso/userinfo` - 应该返回 200
3. `/console/api/auth/desktop-sso/login` - 应该返回 200 并设置 Cookie

### 6. 检查 Cookie
在 `/console/api/auth/desktop-sso/login` 请求的 Response Headers 中，应该看到：
```
Set-Cookie: access_token=...; Path=/; HttpOnly; SameSite=Lax
Set-Cookie: refresh_token=...; Path=/; HttpOnly; SameSite=Lax
Set-Cookie: csrf_token=...; Path=/; SameSite=Lax
```

### 7. 检查后端日志
```bash
cd api
Get-Content backend.log -Tail 50
```

应该看到：
```
Desktop SSO login request received
Request data: {'email': '...', 'name': '...'}
Processing SSO login for: ...
Generating tokens for: ...
Setting cookies for: ...
Desktop SSO Login success for: ...
```

## 可能的问题

### 问题 1: `/auth/desktop-sso/login` 返回 500
- 检查后端日志中的错误信息
- 可能是数据库连接问题或账户创建失败

### 问题 2: Cookie 设置了但前端读不到
- 检查 Cookie 的 Domain 属性
- 确保前后端在同一域名下（localhost）

### 问题 3: 页面重定向后立即 401
- 这是当前的问题
- 可能是 Cookie 还没有被浏览器处理
- 或者 Splash 组件立即检查登录状态，使用了旧的 Cookie

### 问题 4: Token 交换失败
- 检查 SSO 服务器配置
- 确认 client_id 和 redirect_uri 正确

## 下一步

根据控制台日志的输出，我们可以确定问题出在哪一步，然后针对性地修复。

请执行上述调试步骤，并将控制台日志和 Network 标签的截图发给我。
