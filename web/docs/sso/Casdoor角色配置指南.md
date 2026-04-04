# Casdoor SSO 角色配置指南

## 访问 Casdoor 管理后台

### 1. 登录地址
```
https://uat-sso.cheersai.cloud
```

### 2. 管理员登录
- 使用管理员账号登录
- 通常是 `admin` 账号或具有管理权限的账号

---

## 配置用户角色

### 方法 1: 使用用户类型（Type）字段

Casdoor 默认支持用户类型字段，这是最简单的方法。

#### 步骤：

1. **进入用户管理**
   - 登录后，点击左侧菜单 "Users"（用户）
   - 或访问：`https://uat-sso.cheersai.cloud/users`

2. **编辑用户**
   - 找到要配置的用户
   - 点击用户名或 "Edit" 按钮

3. **设置用户类型**
   - 找到 "Type" 字段
   - 设置为以下值之一：
     - `admin` - 管理员权限
     - `technician` - 技术员权限
     - `user` - 普通用户权限

4. **保存**
   - 点击 "Save" 保存更改

---

### 方法 2: 使用自定义属性（Properties）

如果需要更灵活的配置，可以使用自定义属性。

#### 步骤：

1. **编辑用户**
   - 进入用户编辑页面

2. **添加自定义属性**
   - 找到 "Properties" 或 "Custom Properties" 部分
   - 添加新属性：
     ```json
     {
       "role": "admin"
     }
     ```
   - 或者：
     ```json
     {
       "role": "technician"
     }
     ```

3. **保存**
   - 点击 "Save" 保存更改

---

### 方法 3: 使用用户标签（Tags）

#### 步骤：

1. **编辑用户**
   - 进入用户编辑页面

2. **添加标签**
   - 找到 "Tags" 字段
   - 添加标签：`role:admin` 或 `role:technician` 或 `role:user`

3. **保存**
   - 点击 "Save" 保存更改

---

## 配置应用（Application）返回角色信息

为了确保 SSO 登录时返回角色信息，需要配置应用。

### 步骤：

1. **进入应用管理**
   - 点击左侧菜单 "Applications"（应用）
   - 找到你的应用（Client ID: `c98f7150fe9c044bf217`）

2. **编辑应用**
   - 点击应用名称或 "Edit" 按钮

3. **配置返回字段**
   - 找到 "User info fields" 或 "Claims" 部分
   - 确保包含以下字段：
     - `email` ✅
     - `name` ✅
     - `type` ✅ （用户类型）
     - `properties` ✅ （自定义属性）

4. **保存**
   - 点击 "Save" 保存更改

---

## 角色值对照表

| Casdoor 字段值 | 系统角色 | 权限级别 | 可见菜单数 |
|---------------|---------|---------|-----------|
| admin | admin | 管理员 | 8 个（全部） |
| owner | owner | 所有者 | 8 个（全部） |
| technician | editor | 技术员 | 7 个（无审计日志） |
| editor | editor | 技术员 | 7 个（无审计日志） |
| user | normal | 普通用户 | 3 个（基础功能） |
| normal | normal | 普通用户 | 3 个（基础功能） |
| (空值) | normal | 普通用户 | 3 个（默认） |

---

## 快速配置示例

### 创建管理员用户

1. 进入用户管理
2. 点击 "Add User" 创建新用户
3. 填写基本信息：
   - Name: `Admin User`
   - Email: `admin@example.com`
   - Type: `admin` ⭐
4. 保存

### 创建技术员用户

1. 进入用户管理
2. 点击 "Add User" 创建新用户
3. 填写基本信息：
   - Name: `Tech User`
   - Email: `tech@example.com`
   - Type: `technician` ⭐
4. 保存

### 创建普通用户

1. 进入用户管理
2. 点击 "Add User" 创建新用户
3. 填写基本信息：
   - Name: `Normal User`
   - Email: `user@example.com`
   - Type: `user` ⭐
4. 保存

---

## 验证配置

### 1. 测试 API 返回

使用 Postman 或 curl 测试用户信息接口：

```bash
# 1. 获取 access_token（需要先完成 OAuth 流程）
# 2. 获取用户信息
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://uat-sso.cheersai.cloud/api/userinfo
```

**预期返回**：
```json
{
  "sub": "user-id",
  "name": "Admin User",
  "email": "admin@example.com",
  "type": "admin",  // ⭐ 角色信息
  "properties": {
    "role": "admin"  // ⭐ 或者在这里
  }
}
```

### 2. 测试登录

1. 访问 http://localhost:3000
2. 点击 "Desktop SSO Login"
3. 使用配置好的用户登录
4. 查看浏览器控制台日志：
   ```javascript
   [SSO] User info received: {
     email: "admin@example.com",
     name: "Admin User",
     type: "admin"  // ⭐ 角色信息
   }
   ```
5. 验证菜单显示是否正确

---

## 常见问题

### Q1: 找不到 Type 字段？

**解决方法**：
- 检查 Casdoor 版本，确保是较新版本
- 使用自定义属性（Properties）代替
- 联系 Casdoor 管理员

### Q2: 角色信息没有返回？

**解决方法**：
1. 检查应用配置，确保 "User info fields" 包含 `type` 或 `properties`
2. 检查用户是否正确设置了角色
3. 查看浏览器控制台，检查返回的用户信息

### Q3: 修改角色后没有生效？

**解决方法**：
1. 清除浏览器 Cookie
2. 重新登录
3. 检查后端日志，确认角色已更新

### Q4: 所有用户都显示为普通用户？

**解决方法**：
1. 检查 SSO 是否返回角色信息
2. 检查前端代码是否正确读取 `role` 或 `type` 字段
3. 查看后端日志，确认角色映射

---

## Casdoor 管理界面截图说明

### 用户列表页面
```
Users
├── Add User (按钮)
├── 用户列表
│   ├── Name
│   ├── Email
│   ├── Type ⭐ (角色字段)
│   └── Actions (Edit/Delete)
```

### 用户编辑页面
```
Edit User
├── Basic Info
│   ├── Name
│   ├── Email
│   ├── Type ⭐ (下拉选择: admin/technician/user)
│   └── ...
├── Properties (自定义属性)
│   └── { "role": "admin" } ⭐
└── Save (按钮)
```

### 应用配置页面
```
Edit Application
├── Basic Info
│   ├── Name
│   ├── Client ID
│   └── ...
├── User Info Fields ⭐
│   ├── ☑ email
│   ├── ☑ name
│   ├── ☑ type ⭐
│   └── ☑ properties ⭐
└── Save (按钮)
```

---

## 批量配置脚本

如果需要批量配置用户角色，可以使用 Casdoor API：

```bash
# 更新用户角色
curl -X PUT \
  https://uat-sso.cheersai.cloud/api/update-user \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "your-org",
    "name": "user-name",
    "type": "admin"
  }'
```

---

## 联系支持

如果遇到问题，可以：
1. 查看 Casdoor 官方文档：https://casdoor.org/docs/overview
2. 联系 SSO 管理员
3. 查看项目文档：`web/docs/sso/`

---

**创建日期**: 2026-04-02  
**SSO 地址**: https://uat-sso.cheersai.cloud  
**Client ID**: c98f7150fe9c044bf217
