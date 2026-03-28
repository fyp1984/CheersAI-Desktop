# SSO 注册问题已解决

## 问题

注册 SSO 账号时需要邮箱验证码，但是：
- Email provider 需要登录后才能配置
- 没有 Email provider 就收不到验证码
- 收不到验证码就无法注册账号

这是一个循环依赖问题。

## 解决方案

已修改 SSO 应用配置，将邮箱验证规则从 `Normal` 改为 `None`，这样注册时不需要邮箱验证码。

## 修改内容

文件: `F:\CheersAI-SSO\init_data.json`

```json
{
  "name": "Email",
  "visible": true,
  "required": false,
  "prompted": false,
  "rule": "None"  // 从 "Normal" 改为 "None"
}
```

## 现在可以注册了

### 步骤 1: 访问 SSO 注册页面

打开浏览器访问:
```
http://localhost:18000
```

点击 "注册" 或 "Sign up"

### 步骤 2: 填写注册信息

填写以下信息（不需要填邮箱）:
- **用户名**: admin (或任意用户名)
- **显示名称**: Admin
- **密码**: 设置一个密码
- **确认密码**: 重复密码
- **邮箱**: 可以留空或填写任意邮箱（不需要验证）
- **手机**: 可以留空
- **同意条款**: 勾选

### 步骤 3: 完成注册

点击 "注册" 按钮，应该可以直接注册成功，不需要邮箱验证码。

### 步骤 4: 登录 SSO

使用刚注册的用户名和密码登录。

### 步骤 5: 配置应用

登录后进行以下配置:

#### 5.1 添加 Redirect URIs

1. 点击左侧菜单 **Applications**
2. 找到 **app-built-in** 应用
3. 点击编辑
4. 在 **Redirect URIs** 字段添加:
   ```
   http://localhost:3000/signin?sso=desktop
   http://localhost:3000/oauth-callback
   http://localhost:9000/callback
   ```
5. 点击 **Save**

#### 5.2 配置 Email Provider (可选)

如果需要邮箱验证功能:

1. 点击左侧菜单 **Providers**
2. 点击 **Add** 创建新 provider
3. 填写:
   - Name: provider_email_default
   - Category: Email
   - Type: Default
   - Host: smtp.example.com
   - Port: 587
4. 保存后，回到 Applications → app-built-in
5. 在 Providers 部分添加 provider_email_default

## 测试 SSO 登录

配置完 Redirect URIs 后:

1. 访问 Desktop 登录页: http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 应该能正常跳转到 SSO 登录页面
4. 输入用户名密码登录
5. 授权后自动回调到 Desktop
6. 完成登录并跳转到 /apps

## 当前配置

- **SSO 地址**: http://localhost:18000
- **应用**: app-built-in
- **Client ID**: c98f7150fe9c044bf217
- **邮箱验证**: 已禁用（可以不填邮箱注册）

## 重要提示

1. **立即注册账号**: SSO 服务已重启，现在可以直接注册，不需要邮箱验证码
2. **配置 Redirect URIs**: 注册登录后，必须配置 Redirect URIs 才能使用 SSO 登录
3. **Email Provider**: 可选配置，如果不需要邮箱验证功能可以暂时不配置

现在可以访问 http://localhost:18000 注册账号了！
