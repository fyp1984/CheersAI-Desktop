# ✅ 云端 SSO 配置完成

## 配置更新

已将 Desktop 应用配置为使用云端 UAT SSO 服务：

**SSO 地址**: https://uat-sso.cheersai.cloud/

## 当前配置

### Desktop 环境变量 (`e:\CheersAI-Desktop\web\.env.tauri`)

```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

### Desktop 服务

- **前端**: http://localhost:3000 (正在重启)
- **后端**: http://localhost:5001

## 需要在云端 SSO 配置

### 1. 登录云端 SSO

访问: **https://uat-sso.cheersai.cloud/**

### 2. 配置 Redirect URIs

在 Applications → app-built-in 中添加以下回调地址：

```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

### 3. 确认 Client ID

查看云端 SSO 中 app-built-in 的 Client ID：
- 如果与 `c98f7150fe9c044bf217` 不同，需要更新 `.env.tauri` 并重启前端

### 4. 确保启用密码登录

在应用配置中确认：
- ✅ Enable password
- ✅ Enable sign up

## 测试 SSO 登录

Desktop 前端启动完成后：

1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录"
3. 跳转到 https://uat-sso.cheersai.cloud/ 登录页面
4. 使用云端 SSO 账号登录
5. 授权后回调到 Desktop (http://localhost:3000/signin/built-in)
6. 完成登录并跳转到 /apps

## 可能遇到的问题

### 问题 1: Redirect URI 不匹配

**错误**: `redirect_uri_mismatch`

**解决**: 
- 在云端 SSO 中添加 `http://localhost:3000/signin/built-in`
- 确保地址完全匹配（包括协议、端口、路径）

### 问题 2: Client ID 不匹配

**错误**: `invalid_client`

**解决**:
- 查看云端 SSO 的 Client ID
- 更新 `.env.tauri` 中的 `NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID`
- 重启 Desktop 前端

### 问题 3: CORS 错误

**错误**: `Access-Control-Allow-Origin`

**解决**:
- 在云端 SSO 配置中添加 CORS 允许的 Origin
- 添加: `http://localhost:3000`

## 配置检查清单

在测试前确认：

- [ ] 云端 SSO 服务可访问 (https://uat-sso.cheersai.cloud/)
- [ ] 云端 SSO 中已配置 Redirect URIs
- [ ] Desktop Client ID 与云端 SSO 一致
- [ ] Desktop 前端已重启并运行
- [ ] 有云端 SSO 的登录账号

## 下一步

1. ✅ Desktop 配置已更新为云端 SSO
2. ✅ Desktop 前端正在重启
3. ⏳ 在云端 SSO 配置 Redirect URIs
4. ⏳ 测试 SSO 登录

现在请访问云端 SSO 管理界面配置 Redirect URIs，然后测试登录！
