# SSO 测试就绪

## 问题已解决

**原因**: Desktop 配置的 Client ID (`35f82ac3f099085a6fd0`) 在 SSO 中不存在

**解决**: 已更新为 SSO 默认应用的 Client ID: `c98f7150fe9c044bf217`

## 当前配置

### SSO 服务
- **地址**: http://localhost:18000
- **状态**: ✅ 运行中
- **应用名**: app-built-in
- **Client ID**: c98f7150fe9c044bf217

### Desktop 服务
- **前端**: http://localhost:3000 ✅ 运行中
- **后端**: http://localhost:5001 ✅ 运行中
- **SSO Client ID**: c98f7150fe9c044bf217 ✅ 已更新

## 立即测试

### 1. 访问登录页面
```
http://localhost:3000/signin
```

### 2. 点击 SSO 登录按钮
应该能看到 "SSO 登录" 按钮在邮箱密码表单下方

### 3. 验证跳转
点击后会跳转到：
```
http://localhost:18000/login/oauth2/authorize?client_id=c98f7150fe9c044bf217&redirect_uri=http://localhost:3000/signin?sso=desktop&state=...&response_type=code
```

### 4. SSO 登录
- SSO 页面应该正常加载（不再卡住）
- 输入用户名密码登录
- 授权后回调到 Desktop
- 自动完成登录

## 修改的文件

1. `e:\CheersAI-Desktop\web\.env`
   - Client ID: `35f82ac3f099085a6fd0` → `c98f7150fe9c044bf217`

2. `e:\CheersAI-Desktop\web\.env.tauri`
   - Client ID: `35f82ac3f099085a6fd0` → `c98f7150fe9c044bf217`

## 测试申请内测

申请内测功能会调用 SSO API：
```
POST http://localhost:18000/api/apply-beta
```

数据会保存到 SSO 的 MySQL 数据库中的 `beta_application` 表。

## 注意事项

1. **SSO 默认用户**: 需要先在 SSO 中创建用户才能登录
2. **回调地址**: SSO 应用需要配置回调白名单（当前为空，可能需要手动添加）
3. **Client Secret**: 如果需要验证，需要在 Desktop 后端配置

现在可以测试了！
