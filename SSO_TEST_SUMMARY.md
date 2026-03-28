# SSO 集成测试总结

## 服务状态

### ✅ SSO 服务 (Casdoor)
- **状态**: 运行中 (Docker)
- **地址**: http://localhost:18000
- **容器**: casbin/casdoor:latest
- **数据库**: MySQL (localhost:3306/casdoor)

### ✅ Desktop 后端 API
- **状态**: 运行中
- **地址**: http://localhost:5001
- **数据库**: PostgreSQL (localhost:5432/dify)

### ✅ Desktop 前端
- **状态**: 运行中
- **地址**: http://localhost:3000

## 配置完成

### SSO 服务端配置
1. ✅ 创建 BetaApplication 数据模型 (`F:\CheersAI-SSO\object\beta_application.go`)
2. ✅ 创建 API 控制器 (`F:\CheersAI-SSO\controllers\beta_application.go`)
3. ✅ 添加数据库表同步 (`F:\CheersAI-SSO\object\ormer.go`)

### Desktop 客户端配置
1. ✅ 修改申请内测功能调用 SSO API (`e:\CheersAI-Desktop\api\controllers\console\auth\apply_beta.py`)
2. ✅ 配置 SSO 登录地址: `http://localhost:18000`
3. ✅ 配置 SSO API 地址: `http://localhost:18000/api`

## 测试步骤

### 测试 SSO 登录

1. **访问登录页面**
   ```
   http://localhost:3000/signin
   ```

2. **点击 "SSO 登录" 按钮**
   - 应该能看到登录表单下方有 "或" 分隔线
   - 下方有 "SSO 登录" 按钮

3. **验证跳转**
   - 点击后应跳转到: `http://localhost:18000/login/oauth2/authorize?client_id=35f82ac3f099085a6fd0&redirect_uri=http://localhost:3000/signin?sso=desktop&state=...&response_type=code`

4. **完成 SSO 登录**
   - 在 SSO 页面输入用户名密码
   - 授权后应回调到 Desktop
   - 自动完成 Token 交换
   - 跳转到 `/apps` 页面

### 测试申请内测功能

1. **访问申请页面**
   ```
   http://localhost:3000/signup
   ```

2. **填写申请表单**
   - 邮箱: test@example.com
   - 姓名: Test User
   - 公司: Test Company
   - 用途: Testing SSO integration

3. **提交申请**
   - Desktop 会调用 SSO API: `POST http://localhost:18000/api/apply-beta`
   - 数据保存到 SSO MySQL 数据库
   - 同时备份到 Desktop SQLite

4. **验证数据**
   - 检查 SSO MySQL: `SELECT * FROM beta_application WHERE email='test@example.com'`
   - 检查 Desktop SQLite 备份

## API 接口

### SSO 提供的接口

```bash
# 提交申请内测（公开接口）
POST http://localhost:18000/api/apply-beta
Content-Type: application/x-www-form-urlencoded

email=test@example.com&name=Test User&company=Test Company&useCase=Testing

# 获取申请列表（需要认证）
GET http://localhost:18000/api/get-beta-applications?owner=built-in

# 更新申请状态（需要认证）
POST http://localhost:18000/api/update-beta-application?id=built-in/beta_xxx
Content-Type: application/json

{
  "owner": "built-in",
  "name": "beta_xxx",
  "status": "approved"
}
```

### Desktop 调用流程

```
用户提交申请
    ↓
Desktop API (/api/console/apply-beta)
    ↓
调用 SSO API (http://localhost:18000/api/apply-beta)
    ↓
SSO 保存到 MySQL
    ↓
Desktop 备份到 SQLite
    ↓
返回成功
```

## 故障排查

### SSO 登录按钮不显示
- 检查环境变量: `NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true`
- 刷新浏览器: Ctrl+Shift+R
- 检查浏览器控制台是否有错误

### SSO 页面无法访问
- 确认 SSO 服务运行: `docker ps | grep casdoor`
- 访问测试: `curl http://localhost:18000`
- 检查端口映射: 18000:8000

### 申请内测失败
- 检查 SSO API 可访问性: `curl http://localhost:18000/api/apply-beta`
- 查看 Desktop 后端日志
- 验证邮箱格式
- 检查是否重复提交

### Token 交换失败
- 检查 state 参数是否匹配
- 验证 redirect_uri 配置
- 查看浏览器网络请求

## 下一步优化

1. **在 SSO 中配置 OAuth2 应用**
   - Client ID: `35f82ac3f099085a6fd0`
   - Client Secret: 需要配置
   - 回调地址白名单: `http://localhost:3000/signin?sso=desktop`

2. **添加管理界面**
   - 在 SSO 中查看和审批申请
   - 批量处理申请
   - 导出申请数据

3. **增强安全性**
   - 添加 CSRF 保护
   - 实现 Client Secret 验证
   - 添加请求频率限制

4. **数据同步**
   - 实现 SSO 和 Desktop 数据库的双向同步
   - 添加数据一致性检查
   - 定期同步任务

## 测试结果

- ✅ SSO 服务正常运行
- ✅ Desktop 服务正常运行
- ✅ 环境变量配置正确
- ⏳ 等待用户手动测试 SSO 登录流程
- ⏳ 等待用户手动测试申请内测功能

## 相关文档

- 详细集成指南: `SSO_INTEGRATION_GUIDE.md`
- SSO 实现说明: `SSO_IMPLEMENTATION.md`
- SSO 文档: `sso.md`
