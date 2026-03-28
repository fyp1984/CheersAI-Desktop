# 云端 SSO 配置指南

## 配置变更

已将 Desktop 应用配置为使用云端 SSO 服务：

**SSO 地址**: https://uat-sso.cheersai.cloud/

## Desktop 配置更新

已修改 `e:\CheersAI-Desktop\web\.env.tauri`:

```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
```

## 需要在云端 SSO 配置的内容

### 1. 登录云端 SSO 管理界面

访问: https://uat-sso.cheersai.cloud/

使用管理员账号登录。

### 2. 配置应用 Redirect URIs

在 Applications → app-built-in 中添加以下 Redirect URIs：

```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

**重要**: 如果 Desktop 部署到生产环境，需要添加生产环境的回调地址。

### 3. 确认 Client ID

查看云端 SSO 中 app-built-in 应用的 Client ID，并更新 Desktop 配置：

编辑 `e:\CheersAI-Desktop\web\.env.tauri`:

```env
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=<云端 SSO 的 Client ID>
```

### 4. 确保启用密码登录

在应用配置中确认：
- ✅ Enable password
- ✅ Enable sign up

## 重启 Desktop 前端

修改配置后需要重启：

```bash
# 停止当前进程
Get-Process -Name node | Stop-Process -Force

# 重新启动
cd e:\CheersAI-Desktop\web
pnpm dev
```

## 测试云端 SSO 登录

1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录"
3. 跳转到 https://uat-sso.cheersai.cloud/ 登录页面
4. 使用云端 SSO 账号登录
5. 授权后回调到 Desktop

## 注意事项

### HTTPS vs HTTP

- **云端 SSO**: 使用 HTTPS (https://uat-sso.cheersai.cloud/)
- **本地 Desktop**: 使用 HTTP (http://localhost:3000)
- 确保云端 SSO 允许 HTTP 回调地址（开发环境）

### CORS 配置

如果遇到 CORS 错误，需要在云端 SSO 配置中添加：
- Origin: http://localhost:3000

### 生产环境部署

当 Desktop 部署到生产环境时：
1. 更新 Redirect URIs 为生产环境地址
2. 使用 HTTPS 回调地址
3. 更新 CORS 配置

## 当前配置

| 配置项 | 值 |
|--------|-----|
| SSO 服务 | https://uat-sso.cheersai.cloud/ |
| Desktop 前端 | http://localhost:3000 |
| Desktop 后端 | http://localhost:5001 |
| 回调地址 | http://localhost:3000/signin/built-in |

## 下一步

1. ✅ 已修改 Desktop 配置使用云端 SSO
2. ⏳ 需要在云端 SSO 配置 Redirect URIs
3. ⏳ 确认 Client ID 并更新 Desktop 配置
4. ⏳ 重启 Desktop 前端
5. ⏳ 测试云端 SSO 登录

请先在云端 SSO 管理界面完成配置，然后测试登录！
