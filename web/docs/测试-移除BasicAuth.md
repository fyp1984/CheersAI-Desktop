# SSO Token Exchange - 移除 Basic Auth 测试

## 修改内容

根据 V1.3 的实现，我移除了 `Authorization: Basic` header，只在请求 body 中发送 client_id 和 client_secret。

### 修改前
```typescript
const authString = Buffer.from(`${clientId}:${clientSecret}`).toString('base64')

headers: {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Authorization': `Basic ${authString}`,  // ← 移除了这个
  'Accept': 'application/json'
}
```

### 修改后
```typescript
headers: {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Accept': 'application/json'
}

// 凭据只在 body 中发送
body: {
  grant_type: 'authorization_code',
  code: '<code>',
  redirect_uri: 'http://localhost:3000/oauth-callback',
  client_id: 'c98f7150fe9c044bf217',
  client_secret: '13b46d1128c1c0c0d93616a04c76a77570f12f4'
}
```

## 为什么这样修改

1. **V1.3 的实现**：V1.3 版本的代码注释说明 "send in body because many IDPs reject Basic Auth"
2. **OAuth 规范**：OAuth 2.0 规范允许两种方式发送客户端凭据：
   - Authorization header (Basic Auth)
   - Request body (client_id + client_secret)
3. **SSO 服务器可能不支持 Basic Auth**：有些 OAuth 服务器只接受 body 中的凭据

## 测试步骤

### 1. 清除浏览器数据
- 打开开发者工具 (F12)
- Application -> Cookies
- 删除所有 localhost 的 Cookie
- 清除 Session Storage

### 2. 开始 SSO 登录
1. 访问：http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 完成 SSO 认证

### 3. 观察结果

#### 成功的标志
在浏览器控制台应该看到：
```
[SSO] OAuth callback page loaded
[SSO] Starting token exchange with: {code: "...", state: "...", redirectUri: "..."}
[SSO] Step 1: Exchanging OAuth code for SSO access_token
[SSO] Step 2: Fetching user info from SSO
[SSO] User info received: {email: "...", name: "..."}
[SSO] Step 3: Logging into Dify backend
[SSO] Backend login response: {result: "success"}
[SSO] Token exchange successful, waiting 1000ms before redirect
[SSO] Redirecting to /apps
```

#### 如果仍然失败
在 Next.js 服务器日志中会看到：
```
[SSO Token Route] Token exchange request: {
  url: 'https://uat-sso.cheersai.cloud/api/login/oauth/access_token',
  clientId: 'c98f7150fe9c044bf217',
  redirectUri: 'http://localhost:3000/oauth-callback',
  codeLength: 20,
  clientSecretLength: 39
}
SSO token exchange failed: {
  status: 401,
  body: '{"error":"invalid_client",...}'
}
```

## 可能的结果

### 结果 1: 成功 ✅
- Token exchange 返回 200
- 获取到 access_token
- 用户信息获取成功
- Dify 登录成功
- 跳转到 /apps

**这意味着**：问题确实是 Basic Auth，移除后就正常了

### 结果 2: 仍然 401 - invalid_client ❌
- 说明问题不是 Basic Auth
- 而是 Client Secret 本身不正确
- 需要从 SSO 管理后台重新获取正确的 Client Secret

### 结果 3: 其他错误
- 查看具体的错误信息
- 可能是其他配置问题

## 服务状态

- ✅ 后端: Terminal 7 (Flask API on port 5001) - 运行中
- ✅ 前端: Terminal 12 (Next.js on port 3000) - 已重启
- ✅ Docker 服务: 全部运行中

## 当前配置

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
```

## 下一步

根据测试结果：
- 如果成功：SSO 登录功能完成 🎉
- 如果仍然失败：需要正确的 Client Secret

---

**现在可以测试了！**
