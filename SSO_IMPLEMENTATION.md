# Desktop SSO 登录实现说明

## 实现概述

已根据 `sso.md` 文档为 CheersAI-Desktop 项目添加了 SSO 登录功能，SSO 服务地址为 `https://uat-sso.cheersai.cloud`。

## 实现的文件

### 1. 环境配置
- **文件**: `web/.env.tauri`
- **新增配置**:
  ```env
  NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
  NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=35f82ac3f099085a6fd0
  NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
  NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
  ```

### 2. SSO 服务层
- **文件**: `web/service/sso.ts`
  - 新增 `getDesktopSSOLoginUrl()` - 生成 OAuth2 登录地址
  - 新增 `exchangeSSOToken()` - 交换 Token
  - 新增 `getSSOUserInfo()` - 获取用户信息

- **文件**: `web/service/sso-desktop-auth.ts` (新建)
  - `isTauriRuntime()` - 检测是否在 Tauri 环境
  - `isDesktopRuntime()` - 检测是否在 Desktop 环境
  - `generateRandomState()` - 生成随机 state 参数
  - `getDesktopCallbackUrl()` - 构造回调地址
  - `startDesktopSSOLogin()` - 发起 Desktop SSO 登录
  - `isDesktopSSOCallback()` - 检测是否为 SSO 回调
  - `getDesktopSSOCallbackParams()` - 获取回调参数并验证 state
  - `isDesktopSSOEnabled()` - 检查 SSO 是否启用

### 3. 前端组件
- **文件**: `web/app/signin/components/sso-auth.tsx`
  - 更新支持 Desktop SSO 登录流程
  - 处理 `sso=desktop&code=...` 回调
  - 调用 Token Exchange 接口
  - 轮询登录状态并跳转 `/apps`

- **文件**: `web/app/signin/normal-form.tsx`
  - 在登录页面添加 SSO 登录按钮
  - 仅在 Desktop 环境且 SSO 启用时显示

### 4. 后端 API 接口
- **文件**: `web/app/api/auth/sso/token/route.ts` (新建)
  - 路径: `POST /api/auth/sso/token`
  - 功能:
    1. 接收 authorization code
    2. 调用 SSO `/api/login/oauth/access_token`
    3. 获取 access_token/refresh_token
    4. 写入 HTTP-Only Cookie

- **文件**: `web/app/api/auth/sso/userinfo/route.ts` (新建)
  - 路径: `POST /api/auth/sso/userinfo`
  - 功能:
    1. 使用 access_token 调用 SSO `/api/userinfo`
    2. 返回用户基础资料

## 认证流程

1. Desktop 登录页点击 "SSO 登录" 按钮
2. 跳转到 SSO 授权页 `https://uat-sso.cheersai.cloud/login/oauth2/authorize`
3. 用户在 SSO 完成认证
4. 回调到 Desktop: `/signin?sso=desktop&code=...&state=...`
5. Desktop 调用 `/api/auth/sso/token` 交换 access_token
6. 服务端写入 HTTP-Only Cookie
7. 前端轮询登录态成功后跳转 `/apps`

## 安全特性

- ✅ 使用 Authorization Code Flow
- ✅ state 参数防 CSRF 攻击
- ✅ Token 存储在 HTTP-Only Cookie
- ✅ client_secret 仅在服务端使用

## 启动和测试

### 启动 Desktop
```bash
cd web
pnpm install
pnpm tauri dev
```

### 登录验收
1. 打开 Desktop 登录页
2. 点击 "SSO 登录" 按钮
3. 应跳转到 SSO 登录页
4. 完成认证后回到 `/signin?sso=desktop&code=...`
5. 页面自动完成登录并跳转 `/apps`

## 环境变量说明

需要在服务端环境变量中配置（不在 .env.tauri 中）:
- `DESKTOP_SSO_CLIENT_SECRET` - SSO Client Secret（保密）

## 注意事项

1. SSO 应用需要配置回调地址白名单，包括:
   - `http://localhost:3000/signin?sso=desktop`
   - `http://localhost:3000/oauth-callback`
   - `cheersai://oauth-callback`

2. 生产环境建议:
   - 使用 HTTPS
   - 配置正确的 client_secret
   - 仅允许生产回调域名

3. 如遇问题，检查:
   - SSO 服务是否可访问
   - 环境变量是否正确配置
   - 回调地址是否在 SSO 白名单中
   - 浏览器控制台是否有错误信息
