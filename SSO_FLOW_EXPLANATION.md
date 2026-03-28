# SSO 登录流程说明

## OAuth2 授权码流程

### 1. 用户点击 SSO 登录（Desktop 3000端口）
```
http://localhost:3000/signin
```
用户点击 "SSO 登录" 按钮

### 2. 跳转到 SSO 授权页面（SSO 18000端口）
```
http://localhost:18000/login/oauth2/authorize?
  client_id=c98f7150fe9c044bf217&
  redirect_uri=http://localhost:3000/signin/built-in&
  state=xxx&
  response_type=code
```
**这一步在 SSO 服务（18000端口）显示登录页面**

### 3. 用户在 SSO 登录（18000端口）
- 输入用户名: `admin`
- 输入密码: `123456`
- 点击登录

### 4. SSO 授权后回调到 Desktop（3000端口）
```
http://localhost:3000/signin/built-in?code=xxx&state=xxx
```
**Redirect URI 是 Desktop 的地址（3000端口），用于接收授权码**

### 5. Desktop 用授权码换取 Token
Desktop 后端调用 SSO API：
```
POST http://localhost:18000/api/login/oauth2/access_token
```

### 6. 完成登录
Desktop 获取用户信息并跳转到 `/apps`

## 当前配置

### SSO 服务（18000端口）
- **登录页面**: http://localhost:18000/login
- **授权端点**: http://localhost:18000/login/oauth2/authorize
- **Token 端点**: http://localhost:18000/api/login/oauth2/access_token
- **管理员账号**: admin / 123456

### Desktop 应用（3000端口）
- **登录页面**: http://localhost:3000/signin
- **SSO 回调地址**: http://localhost:3000/signin/built-in
- **SSO 登录 URL**: http://localhost:18000
- **Client ID**: c98f7150fe9c044bf217

### Redirect URIs（在 SSO 中配置）
```json
[
  "http://localhost:3000/signin/built-in",
  "http://localhost:3000/oauth-callback",
  "http://localhost:9000/callback"
]
```

**这些是 Desktop 的地址（3000端口），不是 SSO 的地址（18000端口）**

## 为什么 Redirect URI 是 3000 端口？

在 OAuth2 流程中：
- **授权服务器（SSO）**: 18000端口 - 负责用户认证和授权
- **客户端应用（Desktop）**: 3000端口 - 需要接收授权码

**Redirect URI 必须是客户端应用的地址**，因为：
1. 用户在 SSO（18000）登录后
2. SSO 需要把授权码发送回 Desktop（3000）
3. Desktop 用授权码换取 Token
4. 完成登录流程

## 配置正确性验证

✅ **SSO 登录 URL**: http://localhost:18000（正确）
✅ **Redirect URI**: http://localhost:3000/signin/built-in（正确）
✅ **Client ID**: c98f7150fe9c044bf217（正确）
✅ **Enable Password**: 已启用（正确）

所有配置都是正确的！
