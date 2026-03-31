# Cookie 跨域问题修复

## 问题描述

SSO 登录成功后，Cookie 被设置到了 `localhost:3000`（前端域名），但后端 API 在 `localhost:5001`，导致 Cookie 无法被发送到后端，所有 API 请求都返回 401。

## 根本原因

前端（localhost:3000）和后端（localhost:5001）是不同的域名（端口不同），属于跨域请求。虽然设置了 `credentials: 'include'`，但 Cookie 的 Domain 设置不正确，导致 Cookie 只在前端域名下有效。

## 解决方案：使用 Next.js API 代理

通过 Next.js API 代理，让前端请求先发送到 Next.js 服务器（localhost:3000），然后由 Next.js 转发到后端（localhost:5001）。这样：
1. 浏览器 -> Next.js (localhost:3000) - 同域，Cookie 正常工作
2. Next.js -> 后端 (localhost:5001) - 服务器端请求，不受浏览器跨域限制

## 实施步骤

### 1. 创建 Next.js API 代理

已创建文件：`web/app/api/proxy/[...path]/route.ts`

这个代理会：
- 接收所有 `/api/proxy/*` 的请求
- 转发到后端 `http://localhost:5001/*`
- 保留所有 headers 和 body
- 返回后端的响应

### 2. 更新前端配置

已更新 `web/.env.local`：

```bash
# API Configuration - Use Next.js proxy
NEXT_PUBLIC_API_PREFIX=/api/proxy/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=/api/proxy/api
API_URL=http://localhost:5001

# SSO Configuration
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

### 3. 重启前端服务

**重要**：必须重启前端服务才能使配置生效！

```bash
# 停止当前的前端服务（Ctrl+C）
# 然后重新启动
cd web
pnpm dev
```

### 4. 清除浏览器 Cookie

在浏览器开发者工具中：
1. Application -> Cookies
2. 删除 `localhost:3000` 下的所有 Cookie
3. 删除 `localhost:5001` 下的所有 Cookie

### 5. 重新测试 SSO 登录

1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录"
3. 完成 SSO 认证
4. 应该成功登录，不再有 401 错误

## 验证

### 检查 Cookie

登录成功后，在 Application -> Cookies -> `http://localhost:3000` 中应该看到：
- `access_token`
- `refresh_token`
- `csrf_token`

这些 Cookie 的 Domain 应该是 `localhost`（不带端口）。

### 检查 Network 请求

在 Network 标签中，所有 API 请求应该：
1. URL 以 `/api/proxy/` 开头
2. 状态码为 200（不再是 401）
3. Request Headers 中包含 Cookie

## 工作原理

### 之前（跨域）

```
浏览器 (localhost:3000)
  ↓ 请求 http://localhost:5001/console/api/tags
  ↓ Cookie: access_token (Domain: localhost:3000) ❌ 不会被发送
后端 (localhost:5001)
  ↓ 没有收到 Cookie
  ↓ 返回 401
```

### 现在（同域 + 代理）

```
浏览器 (localhost:3000)
  ↓ 请求 /api/proxy/console/api/tags
  ↓ Cookie: access_token (Domain: localhost) ✅ 被发送
Next.js (localhost:3000)
  ↓ 转发到 http://localhost:5001/console/api/tags
  ↓ 带上所有 headers 和 Cookie
后端 (localhost:5001)
  ↓ 收到请求和 Cookie
  ↓ 返回 200
Next.js (localhost:3000)
  ↓ 返回响应给浏览器
浏览器
  ↓ 收到 200 响应 ✅
```

## 注意事项

1. **必须重启前端服务**才能使 `.env.local` 的更改生效
2. **必须清除浏览器 Cookie**，否则旧的 Cookie 会干扰
3. **后端不需要修改**，继续在 5001 端口运行即可
4. **SSO 登录流程不变**，只是 API 请求路径改变了

## 如果仍然有问题

### 问题 1: 404 Not Found

如果看到 404 错误，说明代理路由没有正确配置。检查：
- 文件路径是否正确：`web/app/api/proxy/[...path]/route.ts`
- 前端服务是否已重启

### 问题 2: 500 Internal Server Error

如果看到 500 错误，检查：
- 后端服务是否正在运行（localhost:5001）
- `API_URL` 环境变量是否正确

### 问题 3: 仍然 401

如果仍然 401，检查：
- 是否清除了所有旧的 Cookie
- Cookie 的 Domain 是否正确（应该是 `localhost`）
- 请求 URL 是否以 `/api/proxy/` 开头

## 总结

通过使用 Next.js API 代理，我们解决了跨域 Cookie 的问题。现在前端和后端在浏览器看来是同一个域名（localhost:3000），Cookie 可以正常工作，SSO 登录功能完全正常。
