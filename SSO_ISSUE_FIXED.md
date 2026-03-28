# SSO 登录卡住问题已解决

## 问题原因

SSO 应用的 `enablePassword` 配置为 `false`，导致登录页面无法显示密码登录表单，页面一直在加载。

## 解决方案

已将 `enable_password` 设置为 `1`（启用）。

## 当前配置

- **SSO 服务**: http://localhost:18000 ✅
- **管理员账号**: admin / 123456
- **Client ID**: c98f7150fe9c044bf217
- **Redirect URI**: http://localhost:3000/signin/built-in
- **Enable Password**: ✅ 已启用
- **Enable Sign Up**: ✅ 已启用

## 测试步骤

1. **刷新浏览器**
   - 清除缓存或使用无痕模式
   - 访问 http://localhost:3000/signin

2. **点击 SSO 登录**
   - 应该能正常跳转到 SSO 登录页面
   - **不再卡住，能看到登录表单**

3. **输入登录信息**
   - 用户名: `admin`
   - 密码: `123456`

4. **完成登录**
   - 点击登录按钮
   - 授权后回调到 Desktop
   - 自动跳转到 /apps

## 所有服务状态

| 服务 | 地址 | 状态 |
|------|------|------|
| SSO 服务 | http://localhost:18000 | ✅ 运行中 |
| Desktop 前端 | http://localhost:3000 | ✅ 运行中 |
| Desktop 后端 | http://localhost:5001 | ✅ 运行中 |

现在可以正常使用 SSO 登录了！
