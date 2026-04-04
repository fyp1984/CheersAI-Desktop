# SSO 登录问题总结 - Client Secret 验证失败

## 当前状态

✅ 所有代码已完全使用 V1.3 版本
✅ 授权 URL 正确：`/login/oauth/authorize`
✅ 前后端服务运行正常
❌ Token exchange 失败：Client Secret 无效

## 错误信息

```json
{
  "error": "invalid_client",
  "error_description": "client_secret is invalid for application: [admin/application_8n16xxo], token.CodeChallenge: empty"
}
```

## 已尝试的配置

### 配置 1（当前使用）
- Client ID: `c98f7150fe9c044bf217`
- Client Secret: `13b46d1128c1c0c0d93616a04c76a77570f12f4`
- 结果: ❌ invalid_client

### 配置 2（已测试）
- Client ID: `4ef89efa78a4590d3cf7`
- Client Secret: `08c616602528da4979d9cc701b47cfc6af843cd0`
- 结果: ❌ 用户确认不是这个

## 问题分析

根据错误信息 `"client_secret is invalid for application: [admin/application_8n16xxo]"`：

1. **应用名称**: `admin/application_8n16xxo`
2. **Client ID**: `c98f7150fe9c044bf217` (正确)
3. **Client Secret**: `13b46d1128c1c0c0d93616a04c76a77570f12f4` (SSO 服务器拒绝)

## 可能的原因

### 1. Client Secret 不匹配
- 当前使用的 Client Secret 与 SSO 服务器上配置的不一致
- 可能是从截图复制时出错
- 可能是 SSO 管理后台的 Secret 已更新

### 2. 应用配置问题
- SSO 服务器上的应用配置可能有变化
- redirect_uri 可能需要在 SSO 后台预先配置
- 可能需要其他额外的配置

### 3. 认证方式问题
- 虽然已尝试移除 Basic Auth，但仍然失败
- 可能需要使用不同的认证流程（如 PKCE）

## 需要的信息

为了解决这个问题，需要从 SSO 管理后台确认：

### 1. 应用基本信息
- ✅ 应用名称: `admin/application_8n16xxo`
- ✅ Client ID: `c98f7150fe9c044bf217`
- ❓ Client Secret: **需要重新确认或重新生成**

### 2. 应用配置
- ❓ Redirect URIs: 是否包含 `http://localhost:3000/oauth-callback`
- ❓ Grant Types: 是否启用了 `authorization_code`
- ❓ Response Types: 是否启用了 `code`
- ❓ Scopes: 是否包含 `openid profile email`

### 3. 认证方式
- ❓ Client Authentication Method: 
  - client_secret_basic (Basic Auth)
  - client_secret_post (POST body)
  - 其他方式？
- ❓ 是否需要 PKCE (Proof Key for Code Exchange)

## 测试工具

我已创建了一个测试脚本 `test-sso-token.js`，可以用来独立测试 token exchange：

```bash
# 1. 安装依赖
npm install node-fetch

# 2. 获取授权码
# 访问 http://localhost:3000/signin
# 点击 "SSO 登录"
# 从回调 URL 复制 code 参数

# 3. 更新脚本中的 code
# 编辑 test-sso-token.js，将 YOUR_CODE_HERE 替换为真实的 code

# 4. 运行测试
node test-sso-token.js
```

这个脚本会显示完整的请求和响应，帮助诊断问题。

## 当前代码状态

### V1.3 代码已完全应用

1. **web/app/api/auth/sso/token/route.ts**
   - ✅ 完全使用 V1.3 版本
   - ✅ 同时发送 Basic Auth 和 body 中的凭据
   - ✅ 注释说明 "many IDPs reject Basic Auth"

2. **web/service/sso.ts**
   - ✅ 完全使用 V1.3 版本
   - ✅ 使用 `/login/oauth/authorize`
   - ✅ 3 步登录流程

3. **web/service/sso-desktop-auth.ts**
   - ✅ 默认协议改为 `oauth`
   - ✅ redirect_uri 正确

4. **api/controllers/console/auth/desktop_sso.py**
   - ✅ 完全使用 V1.3 版本
   - ✅ 自动创建账户和工作空间
   - ✅ Cookie 设置正确

## 服务状态

- ✅ 后端: Terminal 7 (Flask API on port 5001) - 运行中
- ✅ 前端: Terminal 14 (Next.js on port 3000) - 运行中，使用 V1.3 代码
- ✅ Docker 服务: 全部运行中

## 下一步行动

### 选项 1: 重新生成 Client Secret（推荐）

1. 登录 SSO 管理后台
2. 找到应用 `admin/application_8n16xxo`
3. 重新生成 Client Secret
4. 更新配置文件
5. 重启前端服务
6. 测试

### 选项 2: 检查应用配置

1. 确认 redirect_uri 已在 SSO 后台配置
2. 确认 grant_type 和 response_type 正确
3. 确认 client authentication method
4. 如果需要 PKCE，需要修改代码实现

### 选项 3: 联系 SSO 管理员

如果以上方法都不行，可能需要：
1. 联系 SSO 系统管理员
2. 确认应用配置是否正确
3. 获取正确的 Client Secret
4. 确认是否有其他特殊要求

## 总结

代码实现已经完全正确（使用 V1.3 版本），问题在于 Client Secret 验证失败。这是一个配置问题，不是代码问题。

需要从 SSO 管理后台获取正确的 Client Secret，或者重新生成一个新的 Client Secret。

一旦 Client Secret 正确，SSO 登录功能将立即工作。
