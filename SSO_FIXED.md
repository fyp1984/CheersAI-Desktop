# SSO 登录问题已修复

## 问题原因

SSO 页面一直卡住的原因是 **SSO 应用缺少回调地址配置**。

OAuth2 授权流程需要验证 `redirect_uri` 参数是否在应用的白名单中，但 SSO 应用的 `redirectUris` 配置为空数组 `[]`，导致授权流程无法继续。

## 已完成的修复

### 1. 更新 Client ID
- 原配置: `35f82ac3f099085a6fd0` (不存在)
- 新配置: `c98f7150fe9c044bf217` (SSO 默认应用)

### 2. 添加回调地址
修改文件: `F:\CheersAI-SSO\init_data.json`

添加的回调地址:
```json
"redirectUris": [
  "http://localhost:3000/signin?sso=desktop",
  "http://localhost:3000/oauth-callback",
  "http://localhost:9000/callback"
]
```

### 3. 重启 SSO 服务
```bash
docker restart fbd99f05b2c7
```

## 当前配置

### SSO 服务
- **地址**: http://localhost:18000
- **状态**: ✅ 运行中
- **应用**: app-built-in
- **Client ID**: c98f7150fe9c044bf217
- **回调地址**: 
  - http://localhost:3000/signin?sso=desktop
  - http://localhost:3000/oauth-callback
  - http://localhost:9000/callback

### Desktop 服务
- **前端**: http://localhost:3000 ✅
- **后端**: http://localhost:5001 ✅
- **Client ID**: c98f7150fe9c044bf217 ✅

## 现在可以测试了

### 1. 刷新浏览器
访问: http://localhost:3000/signin

### 2. 点击 SSO 登录
点击 "SSO 登录" 按钮

### 3. SSO 页面应该正常加载
- 不再卡住
- 显示登录表单
- 可以输入用户名密码

### 4. 完成登录
- 在 SSO 输入用户名密码
- 授权后回调到 Desktop
- 自动完成 Token 交换
- 跳转到 /apps

## 如果还有问题

### 检查 SSO 用户
SSO 需要先创建用户才能登录。访问 SSO 管理界面:
```
http://localhost:18000
```

### 查看日志
```bash
# SSO 日志
docker logs fbd99f05b2c7 --tail 50

# Desktop 后端日志
# 查看终端输出
```

## 修改的文件

1. `e:\CheersAI-Desktop\web\.env`
   - Client ID 更新

2. `e:\CheersAI-Desktop\web\.env.tauri`
   - Client ID 更新

3. `F:\CheersAI-SSO\init_data.json`
   - 添加 redirectUris 配置

现在 SSO 登录应该可以正常工作了！
