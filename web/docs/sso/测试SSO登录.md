# 测试 SSO 登录

## 当前状态

✅ 后端正在运行 (http://localhost:5001)
✅ 前端正在运行 (http://localhost:3000)
✅ redirect_uri 已修复（移除了 ?sso=desktop 参数）
⚠️ 需要真实的 DESKTOP_SSO_CLIENT_SECRET

## 快速测试步骤

### 1. 打开浏览器测试

访问：http://localhost:3000/signin

### 2. 点击 SSO 登录按钮

应该跳转到：
```
https://uat-sso.cheersai.cloud/login/oauth2/authorize?
  client_id=c98f7150fe9c044bf217&
  redirect_uri=http://localhost:3000/oauth-callback&  ← 注意：没有 ?sso=desktop
  state=随机字符串&
  response_type=code
```

### 3. 完成 SSO 登录

在 SSO 页面输入用户名和密码

### 4. 观察回调

登录成功后会跳转到：
```
http://localhost:3000/oauth-callback?code=xxx&state=xxx
```

### 5. 查看日志

#### 前端控制台（F12）

应该看到：
```javascript
Desktop SSO callback params: {code: "...", state: "...", redirectUri: "http://localhost:3000/oauth-callback"}
```

然后调用后端 API...

#### 后端日志

应该看到：
```
SSO token exchange request received
Request data: {'code': '...', 'state': '...', 'redirectUri': 'http://localhost:3000/oauth-callback'}
Exchanging code with SSO server, state: xxx
Calling SSO token endpoint: https://uat-sso.cheersai.cloud/api/oauth2/token
```

### 6. 可能的结果

#### 情况 A：Client Secret 正确

```
Fetching user info from: https://uat-sso.cheersai.cloud/api/oauth2/userinfo
SSO user authenticated: user@example.com
Creating new account for SSO user: user@example.com
Generating Dify tokens for: user@example.com
Setting authentication cookies for: user@example.com
SSO login successful for: user@example.com
```

前端会显示 "SSO login successful" 并跳转到 /apps

#### 情况 B：Client Secret 不正确

```
SSO token exchange failed: 400 - {"error": "invalid_client"}
```

前端会显示 "SSO login failed" 错误提示

## 当前配置

### api/.env
```env
SSO_API_URL=https://uat-sso.cheersai.cloud/api
DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
DESKTOP_SSO_CLIENT_SECRET=your_client_secret_here  ← 需要真实密钥
```

### web/.env.local
```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

## 修复内容

刚刚修复的问题：

1. ❌ 之前：`redirect_uri=http://localhost:3000/oauth-callback?sso=desktop`
2. ✅ 现在：`redirect_uri=http://localhost:3000/oauth-callback`

这个修复很重要，因为：
- SSO 服务器需要 redirect_uri 完全匹配
- 额外的查询参数会导致匹配失败
- 我们通过 sessionStorage 中的 state 来识别回调，不需要额外参数

## 下一步

1. **如果你有真实的 client_secret**：
   - 更新 `api/.env` 文件
   - 重启后端服务
   - 测试 SSO 登录

2. **如果没有 client_secret**：
   - 联系 SSO 管理员获取
   - 或者查看 SSO 应用配置页面
   - client_id 是 `c98f7150fe9c044bf217`

## 验证配置

运行配置检查：
```bash
python test_sso_config.py
```

应该看到所有配置项都已设置。

## 现在可以测试了！

访问 http://localhost:3000/signin 开始测试 SSO 登录。
