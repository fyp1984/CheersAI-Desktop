# SSO 修复 - V1.3 对比分析

## 问题分析

根据 V1.3 分支的代码对比，发现了以下关键差异：

### 1. SSO 授权 URL 路径错误

**问题**：
- 当前代码使用：`/login/${protocol}/authorize`（动态路径）
- V1.3 使用：`/login/oauth/authorize`（固定路径）

**影响**：
- 当 `protocol` 设置为 `oauth2` 时，会生成错误的 URL：`/login/oauth2/authorize`
- SSO 服务器实际的端点是：`/login/oauth/authorize`

### 2. 默认协议配置错误

**问题**：
- 当前代码默认：`protocol = 'oauth2'`
- V1.3 默认：`protocol = 'oauth'`

**影响**：
- 即使不使用动态路径，默认值也是错误的

## 已修复的内容

### 1. 修复 `web/service/sso.ts`

```typescript
// 修复前
const authUrl = new URL(`/login/${protocol}/authorize`, ssoBaseUrl)

// 修复后
const authUrl = new URL(`/login/oauth/authorize`, ssoBaseUrl)
```

**说明**：移除了动态路径，直接使用固定的 `/login/oauth/authorize`

### 2. 修复 `web/service/sso-desktop-auth.ts`

```typescript
// 修复前
const protocol = process.env.NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL || 'oauth2'

// 修复后
const protocol = process.env.NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL || 'oauth'
```

**说明**：修改默认协议从 `oauth2` 改为 `oauth`

## 正确的 SSO 登录流程

### 1. 授权请求

```
URL: https://uat-sso.cheersai.cloud/login/oauth/authorize
参数:
  - client_id: c98f7150fe9c044bf217
  - redirect_uri: http://localhost:3000/oauth-callback
  - state: <随机字符串>
  - response_type: code
  - scope: openid profile email
```

### 2. Token 交换

```
URL: https://uat-sso.cheersai.cloud/api/login/oauth/access_token
方法: POST
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <base64(client_id:client_secret)>
Body:
  - grant_type: authorization_code
  - code: <授权码>
  - redirect_uri: http://localhost:3000/oauth-callback
  - client_id: c98f7150fe9c044bf217
  - client_secret: 13b46d1128c1c0c0d93616a04c76a77570f12f4
```

### 3. 获取用户信息

```
URL: https://uat-sso.cheersai.cloud/api/userinfo
方法: GET
Authorization: Bearer <access_token>
```

### 4. Dify 后端登录

```
URL: http://localhost:5001/console/api/auth/desktop-sso/login
方法: POST
Content-Type: application/json
Body:
  {
    "email": "<用户邮箱>",
    "name": "<用户名称>"
  }
```

## 测试步骤

### 1. 清除浏览器数据

在浏览器开发者工具中：
1. 打开 Application/Storage -> Cookies
2. 删除 `localhost:3000` 下的所有 Cookie
3. 删除 `localhost:5001` 下的所有 Cookie
4. 清除 Session Storage

### 2. 打开浏览器控制台

按 F12 打开开发者工具，切换到 Console 标签

### 3. 开始 SSO 登录

1. 访问：http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 观察浏览器地址栏的 URL

**预期 URL**：
```
https://uat-sso.cheersai.cloud/login/oauth/authorize?client_id=c98f7150fe9c044bf217&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Foauth-callback&state=...&response_type=code&scope=openid+profile+email
```

**注意**：URL 路径应该是 `/login/oauth/authorize`，不是 `/login/oauth2/authorize`

### 4. 完成 SSO 认证

在 SSO 登录页面输入凭据并登录

### 5. 观察控制台日志

应该看到以下日志序列：

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

### 6. 检查 Network 请求

在 Network 标签中检查以下请求：

1. **POST /api/auth/sso/token**
   - 状态码：200
   - 响应：`{success: true, access_token: "...", refresh_token: "..."}`

2. **POST /api/auth/sso/userinfo**
   - 状态码：200
   - 响应：`{email: "...", name: "...", id: "..."}`

3. **POST /console/api/auth/desktop-sso/login**
   - 状态码：200
   - 响应：`{result: "success"}`
   - Response Headers 应包含 Set-Cookie

### 7. 检查 Cookie

登录成功后，在 Application -> Cookies -> `http://localhost:5001` 中应该看到：
- `access_token`
- `refresh_token`
- `csrf_token`

### 8. 验证登录状态

页面应该自动跳转到 `/apps`，并且能够正常访问 API

## 如果仍然失败

### 检查授权 URL

如果授权 URL 仍然是 `/login/oauth2/authorize`：
1. 确认前端服务已重启
2. 清除浏览器缓存
3. 检查 `web/service/sso.ts` 的修改是否生效

### 检查 Token 交换错误

如果看到 "invalid_client" 错误：
1. 检查 Client Secret 是否正确
2. 检查 redirect_uri 是否完全匹配
3. 查看后端日志获取详细错误信息

### 检查后端日志

```bash
cd api
Get-Content backend.log -Tail 50
```

查找以下日志：
- Desktop SSO login request received
- Request data: ...
- Processing SSO login for: ...
- Desktop SSO Login success for: ...

## 环境配置

### 前端 (web/.env.local)

```bash
NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:5001/api

NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
DESKTOP_SSO_CLIENT_SECRET=13b46d1128c1c0c0d93616a04c76a77570f12f4
```

### 后端 (api/.env)

```bash
SSO_API_URL=https://uat-sso.cheersai.cloud/api
DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
DESKTOP_SSO_CLIENT_SECRET=your_client_secret_here

CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,*
```

## 服务状态

- 后端：Terminal 7 (Flask API on port 5001) ✅ 运行中
- 前端：Terminal 11 (Next.js on port 3000) ✅ 已重启
- Docker 服务：✅ 全部运行中

## 总结

通过对比 V1.3 分支的代码，我们发现并修复了两个关键问题：

1. SSO 授权 URL 路径从动态的 `/login/${protocol}/authorize` 改为固定的 `/login/oauth/authorize`
2. 默认协议从 `oauth2` 改为 `oauth`

这些修复应该能解决 SSO 登录时的 URL 错误问题。现在可以进行测试了。
