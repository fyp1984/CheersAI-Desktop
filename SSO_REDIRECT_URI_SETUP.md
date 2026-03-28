# SSO Redirect URI 配置指南

## 问题

SSO 授权页面一直在加载，URL 为：
```
https://uat-sso.cheersai.cloud/login/oauth2/authorize?client_id=c98f7150fe9c044bf217&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fsignin%2Fbuilt-in&state=jk7fxum2ndgvylsmh3q4fn&response_type=code
```

## 原因

云端 SSO 应用中没有配置 Redirect URI: `http://localhost:3000/signin/built-in`

## 解决方案

### 1. 登录云端 SSO 管理界面

访问: **https://uat-sso.cheersai.cloud/**

使用管理员账号登录。

### 2. 找到应用配置

1. 点击左侧菜单 **Applications**
2. 找到应用 `app-built-in` (Client ID: `c98f7150fe9c044bf217`)
3. 点击应用名称进入详情页

### 3. 编辑 Redirect URIs

1. 点击 **Edit** 按钮
2. 找到 **Redirect URIs** 字段
3. 添加以下回调地址（每行一个）：

```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

**重要**: 
- 确保包含 `http://localhost:3000/signin/built-in`
- 协议、域名、端口、路径必须完全匹配
- 不要有多余的空格或换行

### 4. 保存配置

点击 **Save** 按钮保存更改。

### 5. 验证配置

保存后，可以在应用详情页确认 Redirect URIs 已包含：
```
http://localhost:3000/signin/built-in
```

## 重新测试

配置保存后：

1. **关闭当前的授权页面**
2. **返回 Desktop 登录页**: http://localhost:3000/signin
3. **重新点击 SSO 登录**
4. **现在应该能看到登录表单**，不再一直加载

## 其他可能的配置

### 如果使用不同的回调路径

如果您的 Desktop 使用其他回调路径，也需要添加到 Redirect URIs：

- `/oauth-callback`
- `/signin?sso=desktop`
- 其他自定义路径

### 如果部署到生产环境

生产环境需要添加生产域名的 Redirect URIs：
```
https://your-domain.com/signin/built-in
https://your-domain.com/oauth-callback
```

## 当前配置总结

### Desktop 配置
- **SSO 地址**: https://uat-sso.cheersai.cloud
- **Client ID**: c98f7150fe9c044bf217
- **回调地址**: http://localhost:3000/signin/built-in

### 需要在云端 SSO 配置
- **Redirect URIs**: 必须包含 `http://localhost:3000/signin/built-in`
- **Enable password**: 必须启用
- **Enable sign up**: 必须启用

## 配置完成后

所有服务已就绪：
- ✅ Desktop 前端: http://localhost:3000
- ✅ Desktop 后端: http://localhost:5001
- ✅ SSO 服务: https://uat-sso.cheersai.cloud
- ⏳ Redirect URIs: 需要在云端 SSO 配置

配置完成后即可正常使用 SSO 登录！
