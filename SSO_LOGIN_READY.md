# SSO 管理员账号已创建

## 已完成

✅ 通过 MySQL 直接创建了必要的数据库表和数据：
- `organization` 表 - built-in 组织
- `user` 表 - admin 管理员账号
- `application` 表 - app-built-in 应用（已配置 Redirect URIs）

## 登录信息

### SSO 管理员账号

- **登录地址**: http://localhost:18000/login
- **用户名**: `admin`
- **密码**: `123456`

## 立即登录测试

1. 访问 http://localhost:18000/login
2. 输入用户名: `admin`
3. 输入密码: `123456`
4. 点击登录

## 登录后验证配置

登录成功后，验证 Redirect URIs 是否已配置：

1. 点击左侧菜单 **Applications**
2. 找到 **app-built-in** 应用
3. 检查 **Redirect URIs** 是否包含：
   ```
   http://localhost:3000/signin?sso=desktop
   http://localhost:3000/oauth-callback
   http://localhost:9000/callback
   ```

如果已经配置好，可以直接测试 Desktop SSO 登录。

## 启用 Desktop SSO

如果 Redirect URIs 已配置好，重新启用 Desktop SSO：

1. 编辑 `e:\CheersAI-Desktop\web\.env`
2. 修改: `NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true`
3. 重启 Desktop 前端

## 测试 Desktop SSO 登录

1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 应该跳转到 SSO 登录页面
4. 使用 `admin` / `123456` 登录
5. 授权后自动回调到 Desktop
6. 完成登录

## 当前配置

- **SSO 地址**: http://localhost:18000
- **管理员账号**: admin / 123456
- **Client ID**: c98f7150fe9c044bf217
- **Redirect URIs**: 已配置
- **组织**: built-in

现在可以登录 SSO 了！
