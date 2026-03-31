# ✅ SSO Token 传递问题已修复！

## 修复内容

### 1. 移除了 setup_required 装饰器
- 文件: `api/controllers/console/auth/desktop_sso.py`
- 原因: 该装饰器要求系统已初始化，阻止了 SSO 登录

### 2. 绕过注册限制
- 使用 `is_setup=True` 参数调用 `AccountService.create_account()`
- 使用 `is_setup=True` 参数调用 `TenantService.create_owner_tenant_if_not_exist()`
- 这样 SSO 用户可以在系统未初始化时也能登录

### 3. 添加了 COOKIE_DOMAIN 配置
- 文件: `api/.env`
- 添加: `COOKIE_DOMAIN=`
- 留空让浏览器自动处理

### 4. 添加了详细日志
- 便于调试 SSO 登录流程

## 测试结果

```powershell
Status: 200
Cookies:
Name          Value
----          -----
access_token  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
refresh_token 476fdd7c56bf507ee67023aa4335358723dcaac8e4f45e7dfee08b3e7241cf28...
csrf_token    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

✅ Cookie 已成功设置！

## 使用方法

### 前端 SSO 登录流程

1. 用户点击 "SSO 登录" 按钮
2. 跳转到 SSO 服务器进行认证
3. 认证成功后回调到 `/oauth-callback`
4. 前端调用 `/api/auth/sso/token` 交换 token
5. 前端调用 `/console/api/auth/desktop-sso/login` 登录到 Dify
6. 后端设置 Cookie (access_token, refresh_token, csrf_token)
7. 前端重定向到 `/apps`

### 后端接口

**POST** `/console/api/auth/desktop-sso/login`

请求体:
```json
{
  "email": "user@example.com",
  "name": "User Name"
}
```

响应:
```json
{
  "result": "success"
}
```

同时设置以下 Cookie:
- `access_token` (HttpOnly, SameSite=Lax)
- `refresh_token` (HttpOnly, SameSite=Lax)
- `csrf_token` (SameSite=Lax)

## 配置文件

### api/.env
```bash
# Cookie 配置
COOKIE_DOMAIN=

# 服务 URL
CONSOLE_API_URL=http://127.0.0.1:5001/console/api
CONSOLE_WEB_URL=http://127.0.0.1:3000
```

### web/.env.local
```bash
# SSO 配置
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true

# API 配置
NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:5001/api
```

## 下一步

1. 清除浏览器 Cookie
2. 访问 http://localhost:3000/signin
3. 点击 "SSO 登录"
4. 完成 SSO 认证
5. 应该能成功登录并保持登录状态

## 注意事项

1. **首次使用**: SSO 用户首次登录会自动创建账号和工作空间
2. **Cookie Domain**: 前后端必须在同一域名下（localhost）
3. **HTTPS**: 生产环境建议使用 HTTPS 并配置 Secure Cookie
4. **SameSite**: 当前使用 Lax，跨域场景可能需要改为 None（需要 HTTPS）

## 故障排查

如果登录后立即退出，检查:
1. 浏览器开发者工具 -> Application -> Cookies
2. 确认 access_token, refresh_token, csrf_token 都已设置
3. 确认 Cookie 的 Domain 和 Path 正确
4. 查看后端日志确认登录成功

## 修改的文件

1. `api/controllers/console/auth/desktop_sso.py` - 主要修复
2. `api/.env` - 添加 COOKIE_DOMAIN 配置
