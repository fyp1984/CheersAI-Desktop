# SSO 集成完成指南

## 完成的工作

### 1. SSO 服务端 (F:\CheersAI-SSO)

✅ **创建了 BetaApplication 数据模型**
- 文件: `F:\CheersAI-SSO\object\beta_application.go`
- 功能: 定义 beta_application 表结构和 CRUD 操作

✅ **创建了 API 控制器**
- 文件: `F:\CheersAI-SSO\controllers\beta_application.go`
- 接口:
  - `POST /api/apply-beta` - 公开接口，接收申请内测请求
  - `GET /api/get-beta-applications` - 获取所有申请列表
  - `GET /api/get-beta-application` - 获取单个申请
  - `POST /api/update-beta-application` - 更新申请状态
  - `POST /api/delete-beta-application` - 删除申请

✅ **添加数据库表同步**
- 文件: `F:\CheersAI-SSO\object\ormer.go`
- 在 `createTable()` 函数中添加了 `BetaApplication` 表的同步

### 2. Desktop 客户端 (E:\CheersAI-Desktop)

✅ **修改申请内测功能**
- 文件: `e:\CheersAI-Desktop\api\controllers\console\auth\apply_beta.py`
- 改动:
  - 优先调用 SSO API (`http://localhost:8000/api/apply-beta`)
  - 如果 SSO API 不可用，降级到本地数据库
  - 保留 SQLite 备份功能

✅ **配置 SSO 登录**
- 文件: `e:\CheersAI-Desktop\web\.env`
- 配置:
  ```env
  NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:8000
  NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=35f82ac3f099085a6fd0
  NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth2
  NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
  ```

✅ **配置 SSO API 地址**
- 文件: `e:\CheersAI-Desktop\api\.env`
- 配置: `SSO_API_URL=http://localhost:8000/api`

## 启动步骤

### 1. 启动 SSO 服务

```bash
cd F:\CheersAI-SSO
go run main.go
```

SSO 服务将在 **http://localhost:8000** 启动

### 2. 启动 Desktop 后端

```bash
cd E:\CheersAI-Desktop\api
python -m uv run flask run --host 0.0.0.0 --port=5001 --debug
```

Desktop API 将在 **http://localhost:5001** 启动

### 3. 启动 Desktop 前端

```bash
cd E:\CheersAI-Desktop\web
pnpm dev
```

Desktop 前端将在 **http://localhost:3000** 启动

## 功能说明

### SSO 登录流程

1. 用户在 Desktop 登录页点击 "SSO 登录"
2. 跳转到 SSO 授权页面 `http://localhost:8000/login/oauth2/authorize`
3. 用户在 SSO 完成登录
4. 回调到 Desktop: `http://localhost:3000/signin?sso=desktop&code=...&state=...`
5. Desktop 调用 `/api/auth/sso/token` 交换 access_token
6. 登录成功，跳转到 `/apps`

### 申请内测流程

1. 用户在 Desktop 填写申请内测表单
2. Desktop 调用 SSO API: `POST http://localhost:8000/api/apply-beta`
3. SSO 将申请保存到 MySQL 数据库 (casdoor)
4. Desktop 同时保存到本地 SQLite 作为备份
5. 如果 SSO API 不可用，降级到本地 PostgreSQL 数据库

## 数据存储

### SSO 数据库 (MySQL)
- 数据库名: `casdoor`
- 表名: `beta_application`
- 字段:
  - owner (varchar 100)
  - name (varchar 100) - 唯一标识
  - created_time (datetime)
  - updated_time (datetime)
  - email (varchar 100, indexed)
  - user_name (varchar 100)
  - company (varchar 200)
  - use_case (varchar 1000)
  - status (varchar 50) - pending/approved/rejected
  - ip_address (varchar 100)
  - user_agent (varchar 500)

### Desktop 备份数据库
- PostgreSQL: `beta_application` 表
- SQLite: 本地备份

## 注意事项

1. **SSO 服务必须先启动**，否则 Desktop 的 SSO 登录和申请内测功能会降级到本地模式

2. **MySQL 数据库配置**
   - SSO 使用 MySQL，配置在 `F:\CheersAI-SSO\conf\app.conf`
   - 默认连接: `root:root@tcp(localhost:3306)/casdoor`

3. **OAuth2 Client 配置**
   - 需要在 SSO 中配置 Desktop 应用
   - Client ID: `35f82ac3f099085a6fd0`
   - 回调地址白名单需包含: `http://localhost:3000/signin?sso=desktop`

4. **环境变量**
   - Desktop Web: `NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true`
   - Desktop API: `SSO_API_URL=http://localhost:8000/api`

## 测试验证

### 测试 SSO 登录
1. 访问 http://localhost:3000/signin
2. 点击 "SSO 登录" 按钮
3. 应跳转到 SSO 登录页面
4. 完成登录后应回调并自动登录

### 测试申请内测
1. 访问 Desktop 申请内测页面
2. 填写邮箱、姓名等信息
3. 提交后检查:
   - SSO MySQL 数据库中是否有记录
   - Desktop SQLite 中是否有备份
   - 如果 SSO 不可用，检查 Desktop PostgreSQL

## 故障排查

### SSO 服务无法启动
- 检查 MySQL 是否运行
- 检查端口 8000 是否被占用
- 查看 `F:\CheersAI-SSO\logs/casdoor.log`

### Desktop 无法连接 SSO
- 确认 SSO 服务已启动
- 检查防火墙设置
- 验证 `SSO_API_URL` 配置正确

### 申请内测失败
- 检查 SSO API 是否可访问
- 查看 Desktop 后端日志
- 验证邮箱格式是否正确
- 检查是否重复提交

## 下一步优化建议

1. 在 SSO 中添加管理界面查看和审批申请
2. 添加邮件通知功能
3. 实现申请状态同步机制
4. 添加更多的数据验证和安全检查
