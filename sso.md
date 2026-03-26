
文档版本: V2.0  
更新日期: 2026-03-25  
适用对象: CheersAI Desktop（Tauri + Next.js）研发、测试、运维人员


---

1. 文档目标

本文档用于指导在 Desktop 端接入 CheersAI-SSO，实现统一登录、登录态建立与用户信息获取。

当前方案采用 OAuth2 Authorization Code 流程，Desktop 前端负责发起授权，Desktop 服务端负责交换 Token 与安全落库 Cookie。


---

2. 架构与流程

2.1 认证链路

Desktop 登录页点击“SSO 登录”
  -> 跳转 SSO 授权页 /login/oauth/authorize
  -> 用户在 SSO 完成认证
  -> 回调 Desktop: /signin?sso=desktop&code=...&state=...
  -> Desktop 调用 /api/auth/sso/token 交换 access_token
  -> 服务端写入 HTTP-Only Cookie
  -> 前端轮询登录态成功后跳转 /apps

2.2 关键安全点

- 使用 Authorization Code Flow，避免前端直接持有 client secret。
- state 参数用于防 CSRF。
- Token 由服务端写入 HTTP-Only Cookie，降低 XSS 风险。
- 建议生产环境全链路 HTTPS。

---

3. SSO 端前置配置

请在 SSO 应用配置中为 Desktop 应用准备以下信息：

- clientId
- clientSecret
- redirectUris（必须和 Desktop 实际回调地址完全一致）
推荐至少包含以下回调地址：

http://localhost:3000/signin?sso=desktop
http://localhost:3000/oauth-callback
cheersai://oauth-callback

如果 Desktop 部署在其他域名或端口，请同步更新 SSO 应用中的 redirectUris。


---

4. Desktop 端配置

在 Desktop Web 项目中配置环境变量（例如 .env.tauri）：

# SSO 服务地址
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:8000

# 可选：指定 Desktop 对应 SSO Client ID
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=35f82ac3f099085a6fd0

# 可选：协议类型，默认 oauth2
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2

# 可选：强制开启 Desktop SSO 入口
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true

# Tauri 代理前缀
NEXT_PUBLIC_API_PREFIX=/api/proxy/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=/api/proxy/api


---

5. Desktop 代码接入点

5.1 前端认证能力

- web/service/sso.ts
  - 生成 OAuth2 登录地址
  - 交换 Token
  - 获取用户信息
- web/service/sso-desktop-auth.ts
  - Desktop/Tauri 运行时判断
  - 构造 Desktop 回调地址
  - 发起 Desktop SSO 登录
  - 检测回调参数并等待登录完成
- web/app/signin/components/sso-auth.tsx
  - 处理 sso=desktop&code=... 回调
  - 调用 Token Exchange 接口
  - 轮询登录状态并跳转 /apps
5.2 后端接口

1) Token 交换

- 路径: POST /api/auth/sso/token
- 作用:
  1. 接收 authorization code
  2. 代理调用 SSO /api/login/oauth/access_token
  3. 获取 access_token/refresh_token
  4. 写入 HTTP-Only Cookie
2) 用户信息

- 路径: POST /api/auth/sso/userinfo
- 作用:
  1. 使用 access_token 调用 SSO /api/userinfo
  2. 返回用户基础资料用于前端展示

---

6. 联调与启动

6.1 启动 SSO

cd CheersAI-SSO
go run main.go

默认地址：http://localhost:8000

6.2 启动 Desktop

cd CheersAI-Desktop/web
pnpm install
pnpm tauri dev

默认地址：http://localhost:3000

6.3 登录验收

1. 打开 Desktop 登录页。
2. 点击“SSO 登录”，应跳转到 SSO 登录页。
3. 完成认证后回到 /signin?sso=desktop&code=...。
4. 页面自动完成登录并跳转 /apps。

---

7. 常见问题排查

7.1 redirect_uri mismatch

- 检查 SSO 应用配置中的 redirectUris。
- 检查 Desktop 运行地址是否变化（端口、协议、路径）。
- 确保回调地址与请求中的 redirect_uri 完全一致。
7.2 Token 交换失败（Invalid code）

- 确认 code 未过期（通常几分钟内有效）。
- 检查 clientId/clientSecret/redirectUri 组合是否匹配。
- 查看 SSO 服务日志定位具体报错。
7.3 回调成功但未登录

- 检查 /api/auth/sso/token 是否返回成功。
- 检查 Cookie 是否成功写入（HTTP-Only、SameSite）。
- 检查 /api/console/account/profile 是否可返回 200。
7.4 Tauri 中按钮可见但无法跳转

- 检查 NEXT_PUBLIC_DESKTOP_SSO_ENABLED 是否开启。
- 检查 NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL 是否可访问。
- 检查协议参数 NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL 是否正确。

---

8. 生产环境建议

- 更换默认测试账号与 clientSecret。
- 仅允许生产回调域名进入 redirectUris 白名单。
- 开启 HTTPS 与安全 Cookie（Secure）。
- 补充登录成功率、回调失败率与 Token 交换失败率监控。

---

9. 变更记录

- V2.0（2026-03-25）
  - 升级为 Desktop 专版接入文档。
  - 对齐当前 OAuth2 授权码实现与接口。
  - 补充环境变量、联调步骤、验收清单与排障指南。
- V1.0（2026-03-23）
  - 初始版本。