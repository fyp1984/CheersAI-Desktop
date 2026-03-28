# 简化解决方案

## 当前问题

SSO 数据库初始化有问题，无法创建管理员账号。

## 最简单的解决方案

**直接在 SSO 注册页面注册，然后手动跳过邮箱验证**

### 步骤 1: 访问注册页面

打开浏览器，访问：
```
http://localhost:18000/signup
```

### 步骤 2: 填写注册信息

- Username: `admin`
- Display name: `Admin`
- Password: `123456`
- Confirm password: `123456`
- Email: `admin@example.com` (随便填)
- 勾选同意条款

### 步骤 3: 点击注册

即使提示需要邮箱验证码，**不要管它**，直接：

1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 执行以下代码跳过验证：

```javascript
// 方法 1: 直接提交表单（如果有表单）
document.querySelector('form').submit();

// 方法 2: 或者直接调用 API
fetch('/api/signup', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    owner: 'built-in',
    name: 'admin',
    password: '123456',
    displayName: 'Admin',
    email: 'admin@example.com',
    application: 'app-built-in'
  })
}).then(r => r.json()).then(console.log);
```

### 步骤 4: 或者使用密码登录

如果注册不成功，尝试直接登录：

1. 访问 http://localhost:18000/login
2. 选择 "Password" 登录方式
3. 尝试常见的默认账号：
   - Username: `admin` / Password: `admin`
   - Username: `admin` / Password: `123456`
   - Username: `built-in/admin` / Password: `123456`

## 替代方案：直接修改数据库配置

如果上述方法都不行，我们可以：

### 方案 A: 使用 MySQL 客户端工具

1. 下载 MySQL Workbench 或 HeidiSQL
2. 连接到 `localhost:3306`
3. 用户名: `root`，密码: `root`
4. 选择 `casdoor` 数据库
5. 直接在 `application` 表中修改 `redirect_uris` 字段

### 方案 B: 暂时禁用 SSO，使用邮箱密码登录

修改 Desktop 配置，暂时不使用 SSO：

1. 编辑 `e:\CheersAI-Desktop\web\.env`
2. 设置 `NEXT_PUBLIC_DESKTOP_SSO_ENABLED=false`
3. 重启 Desktop 前端
4. 使用邮箱密码登录 Desktop

## 最终目标

无论用什么方法，只要能登录 SSO 管理界面，就可以：

1. 进入 **Applications** → **app-built-in**
2. 添加 **Redirect URIs**:
   ```
   http://localhost:3000/signin?sso=desktop
   http://localhost:3000/oauth-callback
   http://localhost:9000/callback
   ```
3. 保存

然后 Desktop 的 SSO 登录就可以正常工作了。

## 当前配置

- **SSO 地址**: http://localhost:18000
- **Client ID**: c98f7150fe9c044bf217
- **Demo 模式**: 已启用

## 建议

由于 SSO 数据库初始化一直有问题，建议：

1. **先暂时禁用 Desktop SSO**，使用邮箱密码登录
2. **单独配置 SSO 服务**，确保能正常注册和登录
3. **配置好 Redirect URIs** 后，再启用 Desktop SSO

这样可以避免被 SSO 注册问题卡住。
