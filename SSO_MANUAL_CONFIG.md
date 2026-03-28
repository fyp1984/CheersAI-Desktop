# SSO 回调地址手动配置指南

## 问题原因

SSO 页面一直卡住是因为 **SSO 应用的回调地址（redirectUris）为空**。

OAuth2 授权流程需要验证 redirect_uri 是否在白名单中，但当前配置为空数组，导致授权无法完成。

## 解决方案：通过 SSO 管理界面配置

### 步骤 1: 访问 SSO 管理界面

打开浏览器访问：
```
http://localhost:18000
```

### 步骤 2: 登录 SSO

如果还没有管理员账号，需要先注册一个账号。

### 步骤 3: 进入应用管理

1. 登录后，点击左侧菜单 **Applications** (应用)
2. 找到 **app-built-in** 应用
3. 点击编辑

### 步骤 4: 添加回调地址

在 **Redirect URIs** 字段中添加以下地址（每行一个）：

```
http://localhost:3000/signin?sso=desktop
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

### 步骤 5: 保存配置

点击 **Save** 保存配置。

### 步骤 6: 测试 SSO 登录

1. 访问 Desktop 登录页: http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 应该能正常跳转到 SSO 登录页面
4. 登录后自动回调到 Desktop

## 当前配置信息

### SSO 服务
- **地址**: http://localhost:18000
- **应用名**: app-built-in
- **Client ID**: c98f7150fe9c044bf217

### Desktop 配置
- **前端**: http://localhost:3000
- **后端**: http://localhost:5001
- **SSO Client ID**: c98f7150fe9c044bf217

### 需要添加的回调地址
```json
[
  "http://localhost:3000/signin?sso=desktop",
  "http://localhost:3000/oauth-callback",
  "http://localhost:9000/callback"
]
```

## 验证配置是否生效

配置保存后，可以通过以下 API 验证：

```bash
curl "http://localhost:18000/api/get-application?id=admin/app-built-in"
```

查看返回的 `redirectUris` 字段是否包含上述地址。

## 如果无法访问 SSO 管理界面

### 方案 1: 创建管理员账号

1. 访问 http://localhost:18000
2. 点击 Sign up 注册
3. 注册后登录即可访问管理界面

### 方案 2: 使用默认管理员（如果已配置）

检查 SSO 配置文件中是否有默认管理员账号。

## 测试流程

配置完成后：

1. **刷新 Desktop 登录页**
   ```
   http://localhost:3000/signin
   ```

2. **点击 SSO 登录按钮**
   - 应该跳转到 SSO 授权页面
   - 不再卡住

3. **在 SSO 登录**
   - 输入用户名密码
   - 点击登录

4. **自动回调**
   - 回调到 Desktop
   - 完成 Token 交换
   - 跳转到 /apps

## 故障排查

### 如果还是卡住

1. 检查浏览器控制台是否有错误
2. 检查 SSO 日志：
   ```bash
   docker logs fbd99f05b2c7 --tail 50
   ```
3. 确认回调地址已正确配置
4. 确认 Client ID 匹配

### 如果无法登录 SSO

1. 先在 SSO 注册一个账号
2. 或者检查是否有默认管理员账号

## 下一步

配置完成后，SSO 登录应该可以正常工作。如果还有问题，请查看：

- Desktop 后端日志
- SSO 服务日志
- 浏览器开发者工具的网络请求

---

**重要提示**: 由于无法通过命令行直接修改 MySQL 数据库，必须通过 SSO Web 管理界面手动配置回调地址。
