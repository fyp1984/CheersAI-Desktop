# SSO 配置最终修复

## 问题根源

1. **init_data.json 未挂载到容器**
   - SSO 容器无法读取主机上的 `init_data.json`
   - 导致数据库初始化失败

2. **应用配置不完整**
   - `init_data.json` 中应用的 `owner` 和 `name` 为空
   - 导致 SSO 无法正确加载应用配置

## 已完成的修复

### 1. 修改 init_data.json

设置正确的应用配置：
```json
{
  "owner": "admin",
  "name": "app-built-in",
  "displayName": "Built-in Application",
  "clientId": "c98f7150fe9c044bf217",
  "enablePassword": true,
  "enableSignUp": true,
  "redirectUris": [
    "http://localhost:3000/signin/built-in",
    "http://localhost:3000/oauth-callback",
    "http://localhost:9000/callback"
  ]
}
```

### 2. 修改 docker-compose.yml

挂载 `init_data.json` 到容器：
```yaml
volumes:
  - ./conf:/conf/
  - ./init_data.json:/init_data.json
```

### 3. 重建数据库

- 删除旧数据库
- 重新启动 SSO 服务
- 从 `init_data.json` 初始化数据库

## 当前配置

### SSO 服务
- **地址**: http://localhost:18000
- **Client ID**: c98f7150fe9c044bf217
- **Redirect URIs**: 
  - http://localhost:3000/signin/built-in
  - http://localhost:3000/oauth-callback
  - http://localhost:9000/callback
- **Enable Password**: true
- **Enable Sign Up**: true

### 管理员账号
- **用户名**: admin
- **密码**: 123456

### Desktop 配置
- **SSO Login URL**: http://localhost:18000
- **Client ID**: c98f7150fe9c044bf217
- **Callback URL**: http://localhost:3000/signin/built-in

## 测试步骤

1. **等待 SSO 服务完全启动**（约20秒）

2. **访问 Desktop 登录页**
   ```
   http://localhost:3000/signin
   ```

3. **点击 SSO 登录**
   - 跳转到 SSO 授权页面（18000端口）
   - **应该能看到登录表单，不再卡住**

4. **输入登录信息**
   - 用户名: admin
   - 密码: 123456

5. **完成登录**
   - 授权后回调到 Desktop
   - 自动跳转到 /apps

## 验证配置

检查 SSO 应用配置是否正确加载：
```bash
curl "http://localhost:18000/api/get-application?id=admin/app-built-in"
```

应该返回：
```json
{
  "name": "app-built-in",
  "clientId": "c98f7150fe9c044bf217",
  "redirectUris": ["http://localhost:3000/signin/built-in", ...],
  "enablePassword": true
}
```

现在 SSO 登录应该可以正常工作了！
