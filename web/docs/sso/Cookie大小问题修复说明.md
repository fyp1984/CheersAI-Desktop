# SSO Cookie 大小问题修复说明

## 问题描述

在 SSO 登录过程中，当 Casdoor 返回的 access_token 过大（超过 4096 字符）时，浏览器会忽略 Set-Cookie 响应头，导致：

1. Cookie 无法设置
2. 后续的 userinfo 请求因为没有 access_token 而返回 401 Unauthorized
3. 用户无法完成 SSO 登录流程

浏览器控制台错误信息：
```
来自 url: http://localhost:3000/api/auth/sso/token/ 的响应中忽略了 Set-Cookie 标头。
名称和值的组合大小必须小于或等于 4096 个字符。
```

## 解决方案

采用服务端会话存储方案，将大型 token 存储在服务器内存中，只在 cookie 中存储小型会话 ID。

### 实现细节

1. **创建会话管理模块** (`web/lib/sso-session.ts`)
   - 使用 Map 在内存中存储 SSO token
   - 生成唯一的会话 ID
   - 自动清理过期会话（每 5 分钟）
   - 支持 access_token 和 refresh_token

2. **修改 Token 交换路由** (`web/app/api/auth/sso/token/route.ts`)
   - 从 Casdoor 获取 access_token 后，不再直接存储到 cookie
   - 生成会话 ID，将 token 存储到服务端会话
   - 只在 cookie 中存储小型会话 ID（约 30-40 字符）

3. **修改 UserInfo 路由** (`web/app/api/auth/sso/userinfo/route.ts`)
   - 从 cookie 读取会话 ID
   - 使用会话 ID 从服务端会话中获取 access_token
   - 使用 access_token 调用 Casdoor 的 userinfo 接口

4. **添加登出路由** (`web/app/api/auth/sso/logout/route.ts`)
   - 清理服务端会话
   - 删除 cookie 中的会话 ID

## 优势

1. **解决 Cookie 大小限制**：会话 ID 只有约 30-40 字符，远小于 4096 字符限制
2. **更安全**：敏感的 access_token 不会暴露在客户端 cookie 中
3. **易于扩展**：未来可以轻松迁移到 Redis 或数据库存储

## 生产环境建议

当前实现使用内存存储，适合开发和测试。生产环境建议：

1. **使用 Redis**：支持分布式部署和持久化
2. **使用数据库**：与现有用户会话系统集成
3. **设置合理的过期时间**：根据安全需求调整会话有效期
4. **添加会话刷新机制**：使用 refresh_token 自动续期

## 测试步骤

1. 清除浏览器 cookie
2. 访问 SSO 登录页面
3. 使用 admin 账号登录
4. 检查浏览器控制台，确认没有 Cookie 大小警告
5. 验证登录成功，能够正常访问系统

## 相关文件

- `web/lib/sso-session.ts` - 会话管理模块
- `web/app/api/auth/sso/token/route.ts` - Token 交换路由
- `web/app/api/auth/sso/userinfo/route.ts` - UserInfo 路由
- `web/app/api/auth/sso/logout/route.ts` - 登出路由
