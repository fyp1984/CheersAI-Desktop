# SSO 登录测试步骤

## 当前状态

✅ 后端 Flask API 运行中 (Terminal 16, port 5001)
✅ 前端 Next.js 运行中 (Terminal 17, port 3000) - **已重启**
✅ Docker 服务全部运行中
✅ 代码已完全使用 V1.3 版本
✅ SSO 配置正确：
   - SSO URL: `https://uat-sso.cheersai.cloud`
   - Client ID: `c98f7150fe9c044bf217`
   - Client Secret: `13b46d1129c1e20cb951616a04c76a7757d01296`
   - Protocol: `oauth`

## 问题分析

根据日志分析：
1. ✅ SSO 授权成功 - 回调 URL 正确
2. ✅ Token exchange 成功
3. ✅ 获取用户信息成功
4. ❌ 调用后端 `/auth/desktop-sso/login` 时 CORS 失败

**CORS 测试结果**：
- 使用 curl 测试 OPTIONS 请求 → ✅ 返回 200 OK
- 浏览器发送 OPTIONS 请求 → ❌ CORS 错误

**可能原因**：
1. 浏览器缓存了之前失败的 CORS 响应
2. 浏览器的 CORS 策略问题

## 测试步骤

### 1. 清除浏览器缓存（重要！）

**Chrome/Edge**：
1. 按 `F12` 打开开发者工具
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

**或者使用无痕模式**：
1. 按 `Ctrl+Shift+N` 打开无痕窗口
2. 访问 `http://localhost:3000`

### 2. 开始测试

1. 打开浏览器，访问 `http://localhost:3000`
2. 点击"Desktop SSO Login"按钮
3. 在 SSO 页面登录
4. 观察浏览器控制台的日志

### 3. 预期结果

浏览器控制台应该显示：
```
[SSO] OAuth callback page loaded
[SSO] Starting token exchange with: {code: "...", state: "...", redirectUri: "..."}
[SSO] Step 1: Exchanging OAuth code for SSO access_token
[SSO] Step 2: Fetching user info from SSO
[SSO] User info received: {id: "...", email: "...", name: "..."}
[SSO] Step 3: Logging into Dify backend
[SSO] Calling backend /auth/desktop-sso/login with: {email: "...", name: "..."}
[SSO] Backend login response: {result: "success"}
[SSO] Token exchange successful, waiting 1000ms before redirect
[SSO] Redirecting to /apps
```

然后自动跳转到 `/apps` 页面，登录成功！

### 4. 如果仍然失败

**检查浏览器网络请求**：
1. 打开开发者工具 (F12)
2. 切换到 Network 标签
3. 筛选 "desktop-sso"
4. 查看 OPTIONS 和 POST 请求的详细信息
5. 截图发送给我

**检查后端日志**：
```bash
# 查看后端是否收到请求
Get-Content api/backend.log -Tail 50 | Select-String -Pattern "desktop-sso"
```

## 后端 CORS 配置验证

已验证后端 CORS 配置正确：
```bash
curl -X OPTIONS http://localhost:5001/console/api/auth/desktop-sso/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,x-csrf-token" \
  -v
```

返回：
```
< HTTP/1.1 200 OK
< Access-Control-Allow-Origin: http://localhost:3000
< Access-Control-Allow-Credentials: true
< Access-Control-Allow-Headers: content-type, x-csrf-token
< Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
```

## 代码对比 V1.3

已确认以下文件完全使用 V1.3 版本：
- ✅ `web/app/api/auth/sso/token/route.ts` - 同时发送 Basic Auth 和 body 凭据
- ✅ `web/service/sso.ts` - 使用 `/login/oauth/authorize`
- ✅ `web/service/sso-desktop-auth.ts` - 默认协议 `oauth`
- ✅ `web/app/oauth-callback/page.tsx` - V1.3 版本
- ✅ `api/controllers/console/auth/desktop_sso.py` - 自动创建账户和工作空间
- ✅ `api/controllers/console/__init__.py` - 已导入 `desktop_sso`

## 下一步

如果清除缓存后仍然失败，请提供：
1. 浏览器控制台的完整日志（包括错误信息）
2. 浏览器 Network 标签中 OPTIONS 请求的详细信息
3. 后端日志中是否有 desktop-sso 相关的请求

---

**重要提示**：前端服务器已重启，请务必清除浏览器缓存或使用无痕模式测试！
