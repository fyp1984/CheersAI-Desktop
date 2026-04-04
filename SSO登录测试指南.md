# SSO 登录测试指南

## 当前状态

✅ 所有代码修改已完成
✅ 配置文件已更新
✅ 服务正在运行
⚠️ 需要真实的 `DESKTOP_SSO_CLIENT_SECRET`

## 立即需要做的事情

### 1. 获取真实的 Client Secret

当前 `api/.env` 中的 `DESKTOP_SSO_CLIENT_SECRET=your_client_secret_here` 是占位符。

你需要：
1. 联系 SSO 管理员或查看 SSO 应用配置
2. 获取 client_id `c98f7150fe9c044bf217` 对应的 client_secret
3. 更新 `api/.env` 文件

### 2. 更新配置并重启

```bash
# 1. 编辑 api/.env 文件
# 将 DESKTOP_SSO_CLIENT_SECRET=your_client_secret_here
# 改为 DESKTOP_SSO_CLIENT_SECRET=真实的密钥

# 2. 重启后端服务
# 在 Kiro 中停止并重新启动后端进程
```

## 测试步骤

### 步骤 1：验证配置

运行配置检查脚本：

```bash
python test_sso_config.py
```

应该看到：
```
✓ SSO_API_URL: https://uat-sso.cheersai.cloud/api
✓ DESKTOP_SSO_CLIENT_ID: c98f7150fe9c044bf217
✓ DESKTOP_SSO_CLIENT_SECRET: xxxxxxxx...
✓ 所有 SSO 配置项已正确设置
```

### 步骤 2：测试 SSO 登录

1. 打开浏览器，访问 `http://localhost:3000/signin`

2. 点击 "SSO 登录" 按钮

3. 观察浏览器地址栏，应该跳转到：
   ```
   https://uat-sso.cheersai.cloud/login/oauth2/authorize?
     client_id=c98f7150fe9c044bf217&
     redirect_uri=http://localhost:3000/oauth-callback&
     state=随机字符串&
     response_type=code
   ```

4. 在 SSO 页面完成登录

5. 登录成功后，应该自动跳转回：
   ```
   http://localhost:3000/oauth-callback?code=xxx&state=xxx
   ```

6. 观察页面显示 "Processing SSO login..." 加载动画

7. 几秒后应该自动跳转到 `http://localhost:3000/apps`

### 步骤 3：检查日志

#### 前端控制台（浏览器 F12）

应该看到：
```javascript
Desktop SSO callback params: {code: "...", state: "...", redirectUri: "..."}
Token exchange successful: {result: "success", ...}
```

#### 后端日志

应该看到：
```
SSO token exchange request received
Exchanging code with SSO server, state: xxx
Calling SSO token endpoint: https://uat-sso.cheersai.cloud/api/oauth2/token
Fetching user info from: https://uat-sso.cheersai.cloud/api/oauth2/userinfo
SSO user authenticated: user@example.com
Creating new account for SSO user: user@example.com  (首次登录)
或
Found existing account: user@example.com  (已有账户)
Generating Dify tokens for: user@example.com
Setting authentication cookies for: user@example.com
SSO login successful for: user@example.com
```

### 步骤 4：验证登录状态

1. 在 `/apps` 页面，打开浏览器开发者工具

2. 查看 Application → Cookies → `http://localhost:3000`

3. 应该看到以下 Cookie：
   - `access_token`
   - `refresh_token`
   - `csrf_token`

4. 刷新页面，应该保持登录状态

## 常见问题排查

### 问题 1：点击 SSO 登录后没有跳转

**可能原因**：
- 前端配置错误
- `NEXT_PUBLIC_DESKTOP_SSO_ENABLED` 不是 `true`

**解决方法**：
检查 `web/.env.local` 文件，确保：
```env
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
```

### 问题 2：SSO 登录后显示 "SSO login failed"

**可能原因**：
- Client secret 不正确
- SSO API 返回错误

**解决方法**：
1. 查看后端日志，找到具体错误信息
2. 如果是 "Failed to exchange token with SSO"，检查 client_secret
3. 如果是 "Failed to get user info from SSO"，检查 SSO API 是否正常

### 问题 3：Token 交换成功但没有跳转到 /apps

**可能原因**：
- Cookie 没有被正确设置
- 前端等待时间不够

**解决方法**：
1. 检查后端日志是否显示 "Setting authentication cookies"
2. 检查浏览器 Cookie 是否存在
3. 增加前端等待时间（在 `oauth-callback/page.tsx` 中）

### 问题 4：跳转到 /apps 后又回到登录页

**可能原因**：
- Cookie 没有被浏览器接受
- Cookie 的 domain 或 path 设置不正确

**解决方法**：
1. 检查浏览器 Cookie 设置
2. 确保没有浏览器扩展阻止 Cookie
3. 检查后端 Cookie 设置（在 `sso_token.py` 中）

## 调试技巧

### 1. 启用详细日志

后端已经有详细的日志输出，每个步骤都会记录。

### 2. 使用浏览器网络面板

在浏览器开发者工具的 Network 面板中：
1. 筛选 XHR/Fetch 请求
2. 查找 `/auth/sso/token` 请求
3. 检查请求参数和响应
4. 查看 Response Headers 中的 Set-Cookie

### 3. 手动测试 SSO API

可以使用 curl 测试 SSO API：

```bash
# 1. 获取 authorization code（需要在浏览器中完成）
# 访问：https://uat-sso.cheersai.cloud/login/oauth2/authorize?client_id=c98f7150fe9c044bf217&redirect_uri=http://localhost:3000/oauth-callback&state=test&response_type=code

# 2. 使用 code 交换 token
curl -X POST https://uat-sso.cheersai.cloud/api/oauth2/token \
  -d "grant_type=authorization_code" \
  -d "code=你的code" \
  -d "redirect_uri=http://localhost:3000/oauth-callback" \
  -d "client_id=c98f7150fe9c044bf217" \
  -d "client_secret=你的secret"

# 3. 使用 access_token 获取用户信息
curl -H "Authorization: Bearer 你的access_token" \
  https://uat-sso.cheersai.cloud/api/oauth2/userinfo
```

## 成功标志

当你看到以下所有内容时，SSO 登录就成功了：

✅ 点击 SSO 登录按钮后跳转到 SSO 页面
✅ SSO 登录后跳转回 `/oauth-callback`
✅ 显示 "Processing SSO login..." 加载动画
✅ 前端控制台显示 "Token exchange successful"
✅ 后端日志显示 "SSO login successful"
✅ 浏览器 Cookie 中有 access_token, refresh_token, csrf_token
✅ 自动跳转到 `/apps` 页面
✅ 页面显示用户信息，不再显示登录按钮
✅ 刷新页面后仍然保持登录状态

## 下一步

SSO 登录成功后，你可以：

1. 测试其他功能（创建应用、对话等）
2. 测试登出功能
3. 测试 token 刷新（等待 24 小时后）
4. 在生产环境中部署（需要修改 URL 和 CORS 配置）

## 需要帮助？

如果遇到问题：

1. 查看 `SSO登录修复说明.md` 了解技术细节
2. 检查后端日志和前端控制台
3. 使用上述调试技巧定位问题
4. 确保 client_secret 是正确的

---

**重要提醒**：目前 `DESKTOP_SSO_CLIENT_SECRET` 使用的是占位符 `your_client_secret_here`，你需要将其替换为真实的密钥才能成功登录！
