# 本地 SSO 配置和测试指南

## ✅ 已完成配置

### 1. 本地 Casdoor 服务
- **地址**: http://localhost:18000
- **状态**: ✅ 运行中
- **容器**: cheersai-sso-casdoor-1

### 2. 环境变量已更新
```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:18000
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_PROTOCOL=oauth
NEXT_PUBLIC_DESKTOP_SSO_ENABLED=true
```

---

## 🚀 快速开始

### 第 1 步：访问本地 Casdoor

打开浏览器访问：**http://localhost:18000**

### 第 2 步：登录管理后台

默认管理员账号：
- **用户名**: `admin`
- **密码**: `123`（或查看 docker-compose 配置）

### 第 3 步：创建测试用户

在 Casdoor 管理后台：

1. 点击 **"Users"** 或 **"User Management"**
2. 点击 **"Add User"** 创建新用户

#### 创建 3 个测试用户：

**管理员测试账号**
- Name: `Admin User`
- Email: `admin@test.com`
- Password: `Test123!`

**技术员测试账号**
- Name: `Tech User`
- Email: `tech@test.com`
- Password: `Test123!`

**普通用户测试账号**
- Name: `Normal User`
- Email: `user@test.com`
- Password: `Test123!`

### 第 4 步：测试登录

1. 访问：**http://localhost:3000**
2. 点击 **"Desktop SSO Login"** 按钮
3. 会跳转到：**http://localhost:18000/login/oauth/authorize**
4. 用上面创建的账号登录
5. 登录成功后自动跳回应用

### 第 5 步：验证角色权限

根据登录的账号，查看左侧菜单：

- **admin@test.com** → 8 个菜单（管理员权限）
- **tech@test.com** → 7 个菜单（技术员权限）
- **user@test.com** → 3 个菜单（普通用户权限）

---

## 🔍 验证方法

### 查看后端日志

在 Terminal 1 中应该看到：

```
Processing SSO login for: admin@test.com, role: None
Test mode: Auto-assigned admin role based on email
Mapped SSO role 'admin' to system role 'admin'
Desktop SSO Login success for: admin@test.com with role: admin
```

### 查看前端日志

打开浏览器开发者工具（F12），Console 标签：

```javascript
[SSO] User info received: {
  email: "admin@test.com",
  name: "Admin User",
  role: "admin"
}
[SSO] Backend login response: { result: "success" }
```

---

## 📊 角色权限对照

| 邮箱 | 自动角色 | 菜单数量 | 可见菜单 |
|------|---------|---------|---------|
| admin@test.com | 管理员 | 8 个 | 全部菜单 + 审计日志 |
| tech@test.com | 技术员 | 7 个 | 全部菜单 - 审计日志 |
| user@test.com | 普通用户 | 3 个 | 我的 Agent + 对话 + 探索 |

---

## 🎯 测试清单

- [ ] 访问 http://localhost:18000 确认 Casdoor 运行
- [ ] 用 admin/123 登录 Casdoor 管理后台
- [ ] 创建 admin@test.com 用户
- [ ] 创建 tech@test.com 用户
- [ ] 创建 user@test.com 用户
- [ ] 访问 http://localhost:3000
- [ ] 点击 Desktop SSO Login
- [ ] 用 admin@test.com 登录，验证 8 个菜单
- [ ] 退出，用 tech@test.com 登录，验证 7 个菜单
- [ ] 退出，用 user@test.com 登录，验证 3 个菜单

---

## 🔧 配置应用（如果需要）

如果 SSO 登录失败，可能需要在 Casdoor 中配置应用：

1. 登录 Casdoor 管理后台
2. 点击 **"Applications"**
3. 找到或创建应用：
   - **Name**: CheersAI Desktop
   - **Client ID**: `c98f7150fe9c044bf217`
   - **Client Secret**: `13b46d1129c1e20cb951616a04c76a7757d01296`
   - **Redirect URIs**: `http://localhost:3000/oauth-callback`
4. 保存

---

## ⚠️ 常见问题

### Q1: 无法访问 http://localhost:18000

**解决方法**：
```bash
# 检查容器状态
docker ps | findstr casdoor

# 如果没有运行，启动容器
docker start cheersai-sso-casdoor-1
```

### Q2: 登录后跳转失败

**解决方法**：
1. 检查 Redirect URI 配置
2. 确保是 `http://localhost:3000/oauth-callback`
3. 清除浏览器 Cookie 重试

### Q3: 所有用户都是普通用户权限

**解决方法**：
1. 检查邮箱是否包含关键词（admin/tech）
2. 查看后端日志确认角色分配
3. 清除 Cookie 重新登录

---

## 🎉 测试模式说明

当前使用测试模式，系统会根据邮箱自动分配角色：

- 邮箱包含 `admin` → 管理员权限
- 邮箱包含 `tech` → 技术员权限
- 其他邮箱 → 普通用户权限

**不需要在 Casdoor 中配置任何角色字段！**

---

## 📝 下一步

测试完成后，如果要使用真实的角色配置：
1. 在 Casdoor 中为用户设置 Type 或 Properties
2. 删除代码中的测试模式
3. 重新部署

---

**配置日期**: 2026-04-02  
**SSO 地址**: http://localhost:18000  
**应用地址**: http://localhost:3000  
**状态**: ✅ 已配置完成，可以测试
