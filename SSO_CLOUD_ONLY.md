# 完全切换到云端 SSO

## 问题分析

您看到的 URL 还是 `localhost:18000`，说明 Desktop 前端使用了缓存的配置或环境变量未正确加载。

## 已执行的修复

### 1. 确认环境变量配置

`e:\CheersAI-Desktop\web\.env.tauri`:
```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
```

### 2. 清除 Next.js 缓存

已删除 `.next` 目录，强制重新构建。

### 3. 重启 Desktop 前端

已停止旧进程并重新启动，确保加载新的环境变量。

## 验证步骤

Desktop 前端启动完成后（约 30-40 秒）：

### 1. 清除浏览器缓存

**重要**: 在浏览器中按 `Ctrl + Shift + Delete`，清除缓存和 Cookie。

或者使用无痕模式：`Ctrl + Shift + N`

### 2. 访问登录页

```
http://localhost:3000/signin
```

### 3. 点击 SSO 登录

现在应该跳转到：
```
https://uat-sso.cheersai.cloud/login/oauth2/authorize?client_id=...
```

**不再是** `localhost:18000`

### 4. 完成登录

- 使用云端 SSO 账号登录
- 授权后回调到 Desktop

## 如果还是显示 localhost:18000

### 检查 1: 环境变量是否生效

在浏览器控制台（F12）执行：
```javascript
console.log(process.env.NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL)
```

应该显示: `https://uat-sso.cheersai.cloud`

### 检查 2: 是否使用了正确的 .env 文件

Desktop 应该使用 `.env.tauri` 文件。

确认 `e:\CheersAI-Desktop\web\.env.tauri` 中的配置：
```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
```

### 检查 3: 是否有其他 .env 文件覆盖

检查是否存在 `.env.local` 或 `.env` 文件覆盖了配置：

```bash
ls e:\CheersAI-Desktop\web\.env*
```

如果有其他 `.env` 文件，确保它们不包含 `NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL`。

## 当前配置

| 配置项 | 值 |
|--------|-----|
| SSO 服务 | https://uat-sso.cheersai.cloud |
| Desktop 前端 | http://localhost:3000 |
| Client ID | c98f7150fe9c044bf217 |
| Redirect URI | http://localhost:3000/signin/built-in |

## 云端 SSO 配置要求

确保在 https://uat-sso.cheersai.cloud/ 中配置：

### Redirect URIs
```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

### Client ID
```
c98f7150fe9c044bf217
```

### 应用设置
- ✅ Enable password
- ✅ Enable sign up

## 下一步

1. ✅ 已清除 Next.js 缓存
2. ✅ 已重启 Desktop 前端
3. ⏳ 等待前端启动完成（约 30-40 秒）
4. ⏳ 清除浏览器缓存
5. ⏳ 测试 SSO 登录，验证跳转到云端 SSO

请等待 Desktop 前端启动完成，然后清除浏览器缓存并重新测试！
