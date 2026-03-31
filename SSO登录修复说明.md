# SSO 登录修复说明

## 问题分析

之前的 SSO 登录流程存在以下问题：

1. **前端调用的端点不存在**：前端调用 `/auth/sso/token`，但后端只有 `/auth/desktop-sso/login`
2. **Token 交换逻辑缺失**：前端无法直接调用 SSO API（会暴露 client_secret）
3. **Cookie 没有被设置**：因为端点不匹配，Cookie 设置逻辑从未执行

## 解决方案

### 1. 创建新的后端端点 `/auth/sso/token`

文件：`api/controllers/console/auth/sso_token.py`

这个端点的功能：
- 接收前端传来的 `code`, `state`, `redirectUri`
- 调用 SSO API 交换 access_token（使用 client_secret）
- 使用 access_token 获取用户信息
- 创建或获取 Dify 账户
- 生成 Dify 的 access_token 和 refresh_token
- 设置 Cookie 并返回

### 2. 添加 SSO 配置

文件：`api/configs/deploy/__init__.py`

添加了三个配置项：
- `SSO_API_URL`: SSO API 基础 URL
- `DESKTOP_SSO_CLIENT_ID`: OAuth2 客户端 ID
- `DESKTOP_SSO_CLIENT_SECRET`: OAuth2 客户端密钥

### 3. 修复前端回调处理

文件：`web/app/oauth-callback/page.tsx`

- 移除了旧的 `useOAuthCallback` hook（用于其他 OAuth 场景）
- 实现了完整的 Desktop SSO 回调处理逻辑
- 调用 `exchangeSSOToken` 与后端交换 token
- 等待 Cookie 设置后重定向到 `/apps`

### 4. 简化 SSO 认证组件

文件：`web/app/signin/components/sso-auth.tsx`

- 移除了重复的回调处理逻辑
- 回调处理统一由 `/oauth-callback` 页面负责

### 5. 修复回调检测逻辑

文件：`web/service/sso-desktop-auth.ts`

- 修改 `isDesktopSSOCallback()` 函数
- 通过检查 `code`, `state` 参数和 sessionStorage 中的 state 来识别回调
- 不再依赖 `sso=desktop` 参数

## 配置要求

### 后端配置（`api/.env`）

```env
SSO_API_URL=https://uat-sso.cheersai.cloud/api
DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
DESKTOP_SSO_CLIENT_SECRET=你的客户端密钥
```

⚠️ **重要**：你需要从 SSO 管理员那里获取 `DESKTOP_SSO_CLIENT_SECRET`

### 前端配置（`web/.env.local`）

```env
NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

## SSO 登录流程

1. 用户访问 `http://localhost:3000/signin`
2. 点击 "SSO 登录" 按钮
3. 前端生成随机 state，保存到 sessionStorage
4. 跳转到 SSO 服务器：
   ```
   https://uat-sso.cheersai.cloud/login/oauth2/authorize?
     client_id=c98f7150fe9c044bf217&
     redirect_uri=http://localhost:3000/oauth-callback&
     state=随机字符串&
     response_type=code
   ```
5. 用户在 SSO 服务器完成认证
6. SSO 服务器重定向回：
   ```
   http://localhost:3000/oauth-callback?code=xxx&state=xxx
   ```
7. 前端 `/oauth-callback` 页面：
   - 验证 state 参数
   - 调用后端 `/console/api/auth/sso/token`，传递 code, state, redirectUri
8. 后端 `/auth/sso/token` 端点：
   - 使用 code + client_secret 向 SSO API 交换 access_token
   - 使用 access_token 获取用户信息（email, name）
   - 创建或获取 Dify 账户
   - 生成 Dify tokens
   - 设置 Cookie（access_token, refresh_token, csrf_token）
   - 返回成功响应
9. 前端等待 1 秒让浏览器处理 Cookie
10. 重定向到 `/apps` 页面

## 测试步骤

1. 确保所有服务正在运行：
   ```bash
   # Docker 服务
   docker-compose -f docker-compose.dev.yaml up -d
   
   # 后端
   cd api
   .venv\Scripts\python.exe -m flask run --host 0.0.0.0 --port=5001 --debug
   
   # 前端
   cd web
   pnpm dev
   ```

2. 访问 `http://localhost:3000/signin`

3. 点击 "SSO 登录" 按钮

4. 在 SSO 页面完成登录

5. 观察：
   - 是否正确跳转到 `/oauth-callback`
   - 浏览器控制台是否有错误
   - 后端日志是否显示 token 交换成功
   - 是否成功跳转到 `/apps` 页面

## 调试技巧

### 查看后端日志

后端会输出详细的日志：
```
SSO token exchange request received
Exchanging code with SSO server, state: xxx
Calling SSO token endpoint: https://uat-sso.cheersai.cloud/api/oauth2/token
Fetching user info from: https://uat-sso.cheersai.cloud/api/oauth2/userinfo
SSO user authenticated: user@example.com
Setting authentication cookies for: user@example.com
SSO login successful for: user@example.com
```

### 查看前端控制台

前端会输出：
```
Desktop SSO callback params: {code: "xxx", state: "xxx", redirectUri: "..."}
Token exchange successful: {result: "success", ...}
```

### 检查 Cookie

在浏览器开发者工具 → Application → Cookies → `http://localhost:3000`

应该看到：
- `access_token`
- `refresh_token`
- `csrf_token`

## 常见问题

### 1. "SSO not configured" 错误

检查 `api/.env` 文件是否包含所有 SSO 配置项。

### 2. "Failed to exchange token with SSO" 错误

可能的原因：
- `DESKTOP_SSO_CLIENT_SECRET` 不正确
- SSO API URL 不正确
- code 已过期（code 只能使用一次）

### 3. Cookie 没有被设置

检查：
- 后端日志是否显示 "Setting authentication cookies"
- 前端是否等待了足够的时间（1秒）
- 浏览器是否阻止了第三方 Cookie（应该不会，因为是同源）

### 4. 无限重定向

检查：
- sessionStorage 中的 state 是否正确
- `/oauth-callback` 页面的 `hasProcessed.current` 是否正常工作

## 下一步

1. **获取 client_secret**：联系 SSO 管理员获取正确的 `DESKTOP_SSO_CLIENT_SECRET`
2. **更新配置**：将 client_secret 添加到 `api/.env`
3. **重启后端**：让配置生效
4. **测试登录**：按照上述测试步骤验证

## 文件清单

修改的文件：
- ✅ `api/controllers/console/auth/sso_token.py` - 新建
- ✅ `api/controllers/console/__init__.py` - 导入新模块
- ✅ `api/configs/deploy/__init__.py` - 添加 SSO 配置
- ✅ `api/.env` - 添加 SSO 配置项
- ✅ `web/app/oauth-callback/page.tsx` - 重写回调处理
- ✅ `web/app/signin/components/sso-auth.tsx` - 简化逻辑
- ✅ `web/service/sso-desktop-auth.ts` - 修复回调检测

配置文件：
- ✅ `api/.env` - 后端环境变量
- ✅ `web/.env.local` - 前端环境变量
