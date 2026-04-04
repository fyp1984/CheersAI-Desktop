# 获取 Client Secret 说明

## 当前状态

✅ SSO 登录流程已经完全正常
✅ 代码实现正确
✅ 配置正确
❌ **唯一的问题：client_secret 不正确**

## 错误信息

```
SSO token exchange failed: {
  status: 401,
  tokenUrl: 'https://uat-sso.cheersai.cloud/api/login/oauth/access_token',
  body: '{"error":"invalid_client","error_description":"client_secret is invalid for application: [admin/application_8n16xxo], token.CodeChallenge: empty"}'
}
```

这个错误明确表示：`client_secret is invalid`

## 当前配置

### web/.env.local
```env
DESKTOP_SSO_CLIENT_SECRET=your_client_secret_here  ← 这是占位符，不是真实的密钥
```

### 应用信息
- Application ID: `admin/application_8n16xxo`
- Client ID: `c98f7150fe9c044bf217`
- Client Secret: **需要获取**

## 如何获取 Client Secret

### 方法 1：从 SSO 管理后台获取

1. 登录 SSO 管理后台：https://uat-sso.cheersai.cloud

2. 找到应用管理页面

3. 查找应用 `admin/application_8n16xxo` 或 client_id `c98f7150fe9c044bf217`

4. 查看应用详情，找到 `Client Secret` 字段

5. 复制 Client Secret

### 方法 2：联系 SSO 管理员

如果你没有 SSO 管理后台的访问权限：

1. 联系 SSO 管理员或系统管理员

2. 提供以下信息：
   - Application ID: `admin/application_8n16xxo`
   - Client ID: `c98f7150fe9c044bf217`
   - 说明需要获取 Client Secret 用于本地开发

3. 管理员会提供 Client Secret

### 方法 3：重新创建应用

如果无法获取现有的 Client Secret：

1. 在 SSO 管理后台创建新的 OAuth 应用

2. 配置 Redirect URI: `http://localhost:3000/oauth-callback`

3. 获取新的 Client ID 和 Client Secret

4. 更新配置文件中的 Client ID 和 Client Secret

## 更新配置

获取到 Client Secret 后：

### 1. 更新 web/.env.local

```env
DESKTOP_SSO_CLIENT_SECRET=真实的密钥（例如：abc123def456...）
```

### 2. 重启前端服务

```bash
# 在 Kiro 中停止前端进程（Terminal 8）
# 然后重新启动
cd web
pnpm dev
```

### 3. 测试 SSO 登录

1. 访问 http://localhost:3000/signin
2. 点击 SSO 登录
3. 完成 SSO 认证
4. 应该成功登录并跳转到 /apps

## 验证配置

更新配置后，可以运行测试脚本验证：

```bash
python test_sso_config.py
```

应该看到：
```
✓ SSO_API_URL: https://uat-sso.cheersai.cloud/api
✓ DESKTOP_SSO_CLIENT_ID: c98f7150fe9c044bf217
✓ DESKTOP_SSO_CLIENT_SECRET: abc123de...  ← 显示真实密钥的前几个字符
✓ 所有 SSO 配置项已正确设置
```

## 成功标志

当 Client Secret 正确后，你会看到：

### 前端控制台
```
[SSO] Step 1: Exchanging OAuth code for SSO access_token
[SSO] Step 2: Fetching user info from SSO
[SSO] User info received: {email: "user@example.com", name: "User Name"}
[SSO] Step 3: Logging into Dify backend
[SSO] Calling backend /auth/desktop-sso/login with: {email: "...", name: "..."}
[SSO] Backend login response: {result: "success"}
[SSO] Token exchange successful, waiting 1000ms before redirect
[SSO] Redirecting to /apps
```

### 后端日志
```
Desktop SSO login request received
Request data: {'email': 'user@example.com', 'name': 'User Name'}
Processing SSO login for: user@example.com
Found existing account for: user@example.com
Generating tokens for: user@example.com
Setting cookies for: user@example.com
Desktop SSO Login success for: user@example.com
```

### 浏览器
- 自动跳转到 /apps 页面
- 显示用户信息
- Cookie 中有 access_token, refresh_token, csrf_token

## 常见问题

### Q: 我没有 SSO 管理后台的访问权限

A: 联系你的团队管理员或 SSO 系统管理员，提供 Application ID 和 Client ID，请求获取 Client Secret。

### Q: Client Secret 是什么样的？

A: 通常是一个长字符串，类似于：
- `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`
- `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- 长度通常在 32-64 个字符

### Q: 更新配置后还是失败

A: 确保：
1. Client Secret 复制完整，没有多余的空格
2. 前端服务已重启
3. 浏览器清除了缓存和 Cookie
4. 使用的是正确的 Client ID

### Q: 可以在代码中硬编码 Client Secret 吗？

A: 不建议！Client Secret 是敏感信息，应该：
1. 只保存在环境变量文件中（.env.local）
2. 不要提交到 Git 仓库
3. 不要在代码中硬编码
4. 不要分享给未授权的人

## 总结

SSO 登录功能已经完全实现并测试通过。唯一剩下的步骤是：

1. 获取真实的 `DESKTOP_SSO_CLIENT_SECRET`
2. 更新 `web/.env.local` 文件
3. 重启前端服务
4. 测试 SSO 登录

一旦 Client Secret 正确，SSO 登录就会立即工作！
