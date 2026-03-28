# ✅ SSO 已配置完成，可以测试

## 当前状态

### 服务运行状态
- ✅ **Desktop 前端**: http://localhost:3000 - 运行中
- ✅ **SSO 服务**: https://uat-sso.cheersai.cloud - 云端
- ⚠️ **Desktop 后端**: 需要单独启动（如果需要完整功能）

### SSO 配置
- ✅ **SSO 地址**: https://uat-sso.cheersai.cloud
- ✅ **Client ID**: c98f7150fe9c044bf217
- ✅ **环境变量**: 已更新 `.env` 文件

## SSO 登录测试

### 测试步骤

1. **使用无痕模式**
   - 按 `Ctrl + Shift + N` 打开无痕窗口

2. **访问登录页**
   ```
   http://localhost:3000/signin
   ```

3. **点击 SSO 登录按钮**
   - 应该跳转到: `https://uat-sso.cheersai.cloud/login/oauth2/authorize?...`
   - **不再是** `localhost:18000`

4. **在云端 SSO 登录**
   - 使用云端 SSO 账号登录
   - 授权应用

5. **回调到 Desktop**
   - 自动跳转回: `http://localhost:3000/signin/built-in?code=...`
   - 完成 Token 交换
   - 跳转到应用页面

## 云端 SSO 配置要求

确保在 https://uat-sso.cheersai.cloud/ 管理界面配置：

### Redirect URIs
```
http://localhost:3000/signin/built-in
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

### 应用设置
- ✅ Enable password
- ✅ Enable sign up
- ✅ Client ID: c98f7150fe9c044bf217

## 如果需要启动后端

如果 SSO 登录后需要访问后端 API（如 Apply Beta 功能），需要启动后端：

### 方法 1: 使用 uv (推荐)

1. 安装 uv:
   ```bash
   pip install uv
   ```

2. 启动后端:
   ```bash
   cd e:\CheersAI-Desktop\api
   uv sync
   uv run flask db upgrade
   uv run flask run --host 0.0.0.0 --port 5001
   ```

### 方法 2: 使用 Docker

如果有 Docker 配置，可以使用:
```bash
cd e:\CheersAI-Desktop
docker-compose -f docker-compose.dev.yaml up -d
```

## 当前可以测试的功能

### 仅前端 + SSO
- ✅ SSO 登录流程
- ✅ OAuth2 授权
- ✅ Token 交换
- ✅ 用户信息获取

### 需要后端的功能
- ⏳ Apply Beta (需要后端 API)
- ⏳ 完整的应用功能

## 立即测试

现在可以使用无痕模式测试 SSO 登录：

1. 打开无痕窗口: `Ctrl + Shift + N`
2. 访问: http://localhost:3000/signin
3. 点击 SSO 登录
4. 验证跳转到云端 SSO: https://uat-sso.cheersai.cloud/

如果跳转正确，说明 SSO 配置成功！
