# SSO Demo 模式已启用

## 已完成的修改

修改了 `F:\CheersAI-SSO\docker-compose.yml`，添加了 `isDemoMode: "true"` 环境变量。

Demo 模式会禁用邮箱和手机验证要求，允许直接注册账号。

## SSO 服务已重启

服务地址: http://localhost:18000

## 现在可以注册

### 方式 1: 直接注册（推荐）

1. 访问 http://localhost:18000
2. 点击 "Sign up" 或 "注册"
3. 填写：
   - Username: admin
   - Display name: Admin
   - Password: 设置密码
   - Confirm password: 重复密码
   - Email: 可以随便填或留空
   - 勾选同意条款
4. 点击 "Sign Up"

在 Demo 模式下，应该可以直接注册成功，不需要邮箱验证码。

### 方式 2: 使用密码登录

如果注册页面还是要求验证码，可以尝试：
1. 在登录页面选择 "Password" 登录方式
2. 如果已经有账号，直接登录
3. 如果没有账号，尝试注册

## 登录后配置

注册并登录后，立即配置：

### 1. 添加 Redirect URIs

Applications → app-built-in → Edit

在 Redirect URIs 添加：
```
http://localhost:3000/signin?sso=desktop
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

保存。

### 2. 测试 Desktop SSO 登录

1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录"
3. 使用刚注册的账号登录
4. 应该能正常回调到 Desktop

## 如果还是不行

如果 Demo 模式下还是要求验证码，说明数据库中的应用配置覆盖了环境变量。

此时需要：
1. 删除 MySQL 数据库重新初始化
2. 或者使用 Casdoor 的默认管理员账号（如果有）
3. 或者直接通过 MySQL 修改数据库

## 当前配置

- **SSO 地址**: http://localhost:18000
- **Demo 模式**: 已启用
- **Client ID**: c98f7150fe9c044bf217
- **邮箱验证**: 应该已禁用

现在请刷新 http://localhost:18000 并尝试注册！
