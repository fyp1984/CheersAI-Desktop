# SSO Client Secret 验证失败

## 当前问题

SSO token exchange 失败，错误信息：
```
{
  "error": "invalid_client",
  "error_description": "client_secret is invalid for application: [admin/application_8n16xxo], token.CodeChallenge: empty"
}
```

## 问题分析

1. **Client Secret 不正确**
   - 当前使用的 Client Secret: `13b46d1128c1c0c0d93616a04c76a77570f12f4`
   - SSO 服务器返回 "client_secret is invalid"
   - 应用名称: `admin/application_8n16xxo`

2. **可能的原因**
   - Client Secret 从截图中复制时可能有误
   - SSO 管理后台的 Client Secret 可能已更新
   - 需要重新生成 Client Secret

## 需要的操作

### 1. 从 SSO 管理后台获取正确的 Client Secret

请访问 SSO 管理后台：
- URL: https://uat-sso.cheersai.cloud
- 找到应用: `application_8n16xxo`
- 查看或重新生成 Client Secret

### 2. 更新环境配置

获取正确的 Client Secret 后，需要更新两个文件：

#### 前端配置 (web/.env.local)
```bash
DESKTOP_SSO_CLIENT_SECRET=<正确的_client_secret>
```

#### 后端配置 (api/.env)
```bash
DESKTOP_SSO_CLIENT_SECRET=<正确的_client_secret>
```

### 3. 重启服务

更新配置后，需要重启前端服务：
```bash
# 停止当前的前端服务 (Ctrl+C)
# 然后重新启动
cd web
pnpm dev
```

后端服务不需要重启（Flask 会自动重新加载环境变量）。

## 当前配置信息

### SSO 配置
- SSO URL: `https://uat-sso.cheersai.cloud`
- Client ID: `c98f7150fe9c044bf217`
- Client Secret: `13b46d1128c1c0c0d93616a04c76a77570f12f4` ❌ (无效)
- 应用名称: `admin/application_8n16xxo`

### 授权 URL (已修复)
```
https://uat-sso.cheersai.cloud/login/oauth/authorize
```
✅ 正确 (已从 `/login/oauth2/authorize` 修复为 `/login/oauth/authorize`)

### Token Exchange URL
```
https://uat-sso.cheersai.cloud/api/login/oauth/access_token
```

## 已完成的修复

1. ✅ 修复了授权 URL 路径 (从 `oauth2` 改为 `oauth`)
2. ✅ 修复了默认协议配置 (从 `oauth2` 改为 `oauth`)
3. ✅ 前端服务已重启
4. ❌ Client Secret 验证失败 - 需要正确的 Client Secret

## 测试流程

一旦获得正确的 Client Secret 并更新配置后：

1. 清除浏览器 Cookie 和 Session Storage
2. 访问 http://localhost:3000/signin
3. 点击 "SSO 登录"
4. 完成 SSO 认证
5. 观察控制台日志

**预期结果**：
- Token exchange 成功 (200)
- 用户信息获取成功 (200)
- Dify 后端登录成功 (200)
- 自动跳转到 /apps

## 调试信息

### 当前请求参数
```
POST https://uat-sso.cheersai.cloud/api/login/oauth/access_token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <base64(client_id:client_secret)>

Body:
  grant_type=authorization_code
  code=<授权码>
  redirect_uri=http://localhost:3000/oauth-callback
  client_id=c98f7150fe9c044bf217
  client_secret=13b46d1128c1c0c0d93616a04c76a77570f12f4
```

### 服务状态
- ✅ 后端: Terminal 7 (Flask API on port 5001) - 运行中
- ✅ 前端: Terminal 11 (Next.js on port 3000) - 运行中
- ✅ Docker 服务: 全部运行中

## 下一步

**请提供正确的 Client Secret**，然后我会：
1. 更新 `web/.env.local`
2. 更新 `api/.env`
3. 重启前端服务
4. 重新测试 SSO 登录流程
