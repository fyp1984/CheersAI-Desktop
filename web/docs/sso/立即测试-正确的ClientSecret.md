# SSO 登录测试 - 使用正确的 Client Secret

## 已更新配置

### 正确的 Client Secret
从 SSO 管理后台截图获取的正确配置：

- **Client ID**: `c98f7150fe9c044bf217` ✅
- **Client Secret**: `13b46d1129c1e20cb951616a04c76a7757d01296` ✅ (已更新)

### 之前错误的 Client Secret
- ❌ `13b46d1128c1c0c0d93616a04c76a77570f12f4` (旧的，不正确)

### 差异对比
```
旧的: 13b46d1128c1c0c0d93616a04c76a77570f12f4
新的: 13b46d1129c1e20cb951616a04c76a7757d01296
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 这部分不同
```

## 配置文件已更新

### 前端 (web/.env.local)
```bash
DESKTOP_SSO_CLIENT_SECRET=13b46d1129c1e20cb951616a04c76a7757d01296
```

### 后端 (api/.env)
```bash
DESKTOP_SSO_CLIENT_SECRET=13b46d1129c1e20cb951616a04c76a7757d01296
```

## 服务状态

- ✅ 后端: Terminal 7 (Flask API on port 5001) - 运行中
- ✅ 前端: Terminal 15 (Next.js on port 3000) - 已重启，使用正确的 Client Secret
- ✅ Docker 服务: 全部运行中
- ✅ 代码: 完全使用 V1.3 版本

## 测试步骤

### 1. 清除浏览器数据
在浏览器开发者工具中 (F12)：
1. Application -> Cookies
2. 删除 `localhost:3000` 和 `localhost:5001` 下的所有 Cookie
3. Application -> Session Storage
4. 清除所有 Session Storage

### 2. 开始 SSO 登录
1. 访问：http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 完成 SSO 认证

### 3. 观察控制台日志

**预期成功的日志**：
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

### 4. 检查 Network 请求

在 Network 标签中应该看到：
1. **POST /api/auth/sso/token** - 200 ✅
2. **POST /api/auth/sso/userinfo** - 200 ✅
3. **POST /console/api/auth/desktop-sso/login** - 200 ✅

### 5. 验证登录成功

- ✅ 页面自动跳转到 `/apps`
- ✅ 可以看到应用主界面
- ✅ 后续 API 请求返回 200（不再是 401）
- ✅ Cookie 已正确设置

## Redirect URIs 配置

从截图可以看到，SSO 后台已配置的 Redirect URIs：
- ✅ `http://localhost:3000/callback`
- ✅ `http://localhost:3000/signin/built-in`
- ✅ `http://localhost:3000/oauth-callback`
- ✅ `http://localhost:3000/signin?sso=desktop`

我们使用的是：`http://localhost:3000/oauth-callback` ✅

## 授权 URL

SSO 登录时会跳转到：
```
https://uat-sso.cheersai.cloud/login/oauth/authorize?client_id=c98f7150fe9c044bf217&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Foauth-callback&state=...&response_type=code&scope=openid+profile+email
```

## Token Exchange 请求

```
POST https://uat-sso.cheersai.cloud/api/login/oauth/access_token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <base64(client_id:client_secret)>
Accept: application/json

Body:
  grant_type=authorization_code
  code=<授权码>
  redirect_uri=http://localhost:3000/oauth-callback
  client_id=c98f7150fe9c044bf217
  client_secret=13b46d1129c1e20cb951616a04c76a7757d01296
```

## 如果成功

恭喜！🎉 SSO 登录功能完全正常工作！

你应该能够：
- ✅ 通过 SSO 登录到 Dify
- ✅ 自动创建账户和工作空间
- ✅ 访问所有功能
- ✅ Cookie 正确传递

## 如果仍然失败

如果还是看到错误，请提供：
1. 浏览器控制台的完整错误信息
2. Network 标签中失败请求的详细信息
3. Next.js 服务器日志（Terminal 15）

---

**现在可以测试了！这次应该会成功！** 🚀
