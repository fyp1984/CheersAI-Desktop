# SSO 数据库已重置

## 已完成的操作

1. **停止 SSO 服务**
2. **删除 casdoor 数据库**
3. **重新创建空数据库**
4. **重启 SSO 服务**

SSO 现在会使用 `init_data.json` 的配置重新初始化数据库。

## 配置已生效

`init_data.json` 中的配置：
- Email 验证规则: `None` (不需要验证)
- Email provider: `provider_email_default`
- Redirect URIs: 已配置
- Demo 模式: 已启用

## 现在可以注册

### 访问 SSO
```
http://localhost:18000
```

### 注册账号

1. 点击 "Sign up" 或 "注册"
2. 填写：
   - **Username**: admin
   - **Display name**: Admin
   - **Password**: 设置密码
   - **Confirm password**: 重复密码
   - **Email**: 可以随便填或留空（不需要验证码）
   - **Phone**: 留空
   - 勾选同意条款
3. 点击 "Sign Up"

**应该可以直接注册成功，不需要邮箱验证码！**

## 注册成功后配置

登录后立即配置 Redirect URIs：

1. 进入 **Applications** → **app-built-in** → 编辑
2. 在 **Redirect URIs** 添加：
   ```
   http://localhost:3000/signin?sso=desktop
   http://localhost:3000/oauth-callback
   http://localhost:9000/callback
   ```
3. 保存

## 测试 Desktop SSO 登录

配置完成后：
1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录"
3. 使用刚注册的账号登录
4. 应该能正常回调到 Desktop

## 当前状态

- **SSO 地址**: http://localhost:18000
- **数据库**: 已重置并重新初始化
- **Demo 模式**: 已启用
- **Email 验证**: 已禁用
- **Client ID**: c98f7150fe9c044bf217

现在访问 http://localhost:18000 应该可以直接注册账号了！
