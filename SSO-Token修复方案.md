# SSO Token 传递问题修复方案

## 问题分析

桌面应用中 SSO 登录后，token 无法正确传递到系统中。原因可能是：

1. Cookie Domain 配置不匹配
2. SameSite 属性导致跨域 Cookie 被阻止
3. 前端请求配置问题

## 当前配置

### 前端 (.env.local)
```
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

### 后端 Cookie 设置
- Domain: 从 `COOKIE_DOMAIN` 环境变量读取
- SameSite: Lax
- Secure: 根据 HTTPS 自动判断
- HttpOnly: true (access/refresh token)
- Path: /

## 修复方案

### 方案一：配置 Cookie Domain（推荐）

在 `api/.env` 中添加：

```bash
# Cookie Domain 配置
COOKIE_DOMAIN=localhost
# 或者留空让浏览器自动处理
# COOKIE_DOMAIN=
```

### 方案二：修改 SameSite 属性

修改 `api/controllers/console/auth/desktop_sso.py`：

```python
# 在设置 Cookie 时使用 None 而不是 Lax
set_access_token_to_cookie(request, response, token_pair.access_token, samesite="None")
```

注意：SameSite=None 需要 Secure=true（HTTPS）

### 方案三：前端添加 credentials

确保前端请求带上 credentials（已经配置）：

```typescript
// web/service/fetch.ts
credentials: 'include'  // ✅ 已配置
```

## 调试步骤

### 1. 检查 Cookie 是否设置成功

在浏览器开发者工具中：
1. 打开 Application/Storage -> Cookies
2. 查看 localhost:3000 下是否有以下 Cookie：
   - `access_token` 或 `__Host-access_token`
   - `refresh_token` 或 `__Host-refresh_token`
   - `csrf_token` 或 `__Host-csrf_token`

### 2. 检查 Cookie 属性

确认 Cookie 的属性：
- Domain: localhost 或为空
- Path: /
- SameSite: Lax 或 None
- Secure: 根据协议
- HttpOnly: true

### 3. 检查后端日志

查看后端日志确认登录成功：
```
Desktop SSO Login success for: user@example.com
```

### 4. 检查前端请求

在 Network 标签中查看：
1. `/auth/desktop-sso/login` 请求是否成功（200）
2. Response Headers 中是否有 `Set-Cookie`
3. 后续请求的 Request Headers 中是否带上 Cookie

## 快速测试

### 测试 1: 检查环境变量

```bash
cd api
cat .env | grep COOKIE
```

### 测试 2: 手动测试登录接口

```bash
curl -X POST http://localhost:5001/console/api/auth/desktop-sso/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}' \
  -v
```

查看响应中的 `Set-Cookie` header。

### 测试 3: 检查前端 SSO 流程

1. 打开浏览器开发者工具
2. 访问 http://localhost:3000/signin
3. 点击 SSO 登录
4. 完成 SSO 认证
5. 查看 Network 标签中的请求

## 推荐配置

### api/.env
```bash
# Cookie 配置
COOKIE_DOMAIN=
CONSOLE_WEB_URL=http://localhost:3000
CONSOLE_API_URL=http://localhost:5001
```

### web/.env.local
```bash
# SSO 配置
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true

# API 配置
NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:5001/api
```

## 常见问题

### Q1: Cookie 设置了但前端读不到？
A: 检查 Domain 配置，确保前后端在同一域名下。

### Q2: 跨域 Cookie 被阻止？
A: 使用 SameSite=None 并启用 HTTPS，或确保前后端同域。

### Q3: 登录成功但立即退出？
A: 检查 Cookie 的 Path 和 Domain 配置，确保后续请求能带上 Cookie。

## 下一步

1. 检查 `api/.env` 中的 COOKIE_DOMAIN 配置
2. 重启后端服务
3. 清除浏览器 Cookie
4. 重新测试 SSO 登录流程
