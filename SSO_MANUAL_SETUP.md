# SSO 手动配置指南

## 问题总结

`init_data.json` 配置过于复杂，导致 SSO 初始化失败。现在使用 Casdoor 默认配置，通过 Web UI 手动配置应用。

## 当前状态

- ✅ SSO 服务已启动（使用默认配置）
- ✅ 数据库已重建
- ⏳ 需要通过 Web UI 手动配置

## 手动配置步骤

### 1. 访问 SSO 管理界面

```
http://localhost:18000
```

### 2. 使用默认管理员账号登录

Casdoor 默认账号：
- **用户名**: `admin`
- **密码**: `123`

### 3. 修改管理员密码（可选）

登录后建议修改密码为 `123456`

### 4. 配置应用

1. 点击左侧菜单 **Applications**
2. 找到默认应用（通常是 `app-built-in`）
3. 点击 **Edit** 编辑

### 5. 配置 Redirect URIs

在应用编辑页面，找到 **Redirect URIs** 字段，添加：

```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

### 6. 启用密码登录

确保以下选项已启用：
- ✅ **Enable password**
- ✅ **Enable sign up**

### 7. 记录 Client ID

在应用详情页面，复制 **Client ID**（应该类似 `c98f7150fe9c044bf217`）

### 8. 保存配置

点击 **Save** 保存所有更改

## Desktop 配置

确认 Desktop 的环境变量配置正确：

```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:18000
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=<从 SSO 复制的 Client ID>
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

## 测试 SSO 登录

1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录"
3. 跳转到 SSO 登录页面
4. 使用 `admin` / `123456` 登录
5. 授权后回调到 Desktop
6. 完成登录

## 如果还是有问题

### 检查 Client ID

确保 Desktop 的 `NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID` 与 SSO 应用的 Client ID 一致。

### 检查 Redirect URIs

确保 SSO 应用的 Redirect URIs 包含 Desktop 的回调地址。

### 查看浏览器控制台

按 F12 查看是否有 JavaScript 错误或网络请求失败。

### 查看 SSO 日志

```bash
docker logs cheersai-sso-casdoor-1 --tail 50
```

## 当前服务

| 服务 | 地址 | 状态 |
|------|------|------|
| SSO 服务 | http://localhost:18000 | ✅ 运行中 |
| Desktop 前端 | http://localhost:3000 | ✅ 运行中 |
| Desktop 后端 | http://localhost:5001 | ✅ 运行中 |

现在请按照上述步骤手动配置 SSO 应用！
