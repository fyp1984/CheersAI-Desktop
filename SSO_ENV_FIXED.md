# ✅ SSO 环境变量已修复

## 问题原因

Desktop 使用的是 `.env` 文件，而不是 `.env.tauri` 文件。

之前只修改了 `.env.tauri`，但 Next.js 默认加载 `.env` 文件，导致还是使用 `localhost:18000`。

## 已修复

已修改 `e:\CheersAI-Desktop\web\.env` 文件：

**修改前**:
```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:18000
```

**修改后**:
```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
```

## 当前配置

### 两个环境变量文件都已更新

1. **`.env`** (Next.js 默认使用)
   ```env
   NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
   NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
   ```

2. **`.env.tauri`** (Tauri 桌面版使用)
   ```env
   NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
   NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
   ```

## 重启状态

- ✅ 已停止旧进程
- ⏳ 正在重启 Desktop 前端
- ⏳ 等待编译完成

## 测试步骤

Desktop 启动完成后（约 20-30 秒）：

### 1. 使用无痕模式

按 `Ctrl + Shift + N` 打开无痕窗口

### 2. 访问登录页

```
http://localhost:3000/signin
```

### 3. 点击 SSO 登录

现在应该跳转到：
```
https://uat-sso.cheersai.cloud/login/oauth2/authorize?client_id=c98f7150fe9c044bf217&redirect_uri=http://localhost:3000/signin/built-in&state=...&response_type=code
```

**确认**: URL 中应该是 `uat-sso.cheersai.cloud`，不再是 `localhost:18000`

### 4. 完成登录

- 使用云端 SSO 账号登录
- 授权后回调到 Desktop

## 云端 SSO 配置要求

确保在 https://uat-sso.cheersai.cloud/ 管理界面配置：

### Redirect URIs
```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

### 应用设置
- ✅ Enable password
- ✅ Enable sign up
- ✅ Client ID: c98f7150fe9c044bf217

## 下一步

1. ✅ 已修改 `.env` 文件
2. ✅ 已停止旧进程
3. ⏳ Desktop 前端正在重启
4. ⏳ 等待启动完成
5. ⏳ 使用无痕模式测试 SSO 登录

等待 Desktop 启动完成后，使用无痕模式测试，现在应该会跳转到云端 SSO 了！
