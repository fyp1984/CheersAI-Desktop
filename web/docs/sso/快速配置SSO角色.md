# 快速配置 SSO 角色 - 5 分钟指南

## 🚀 快速开始

### 第 1 步：登录 Casdoor 管理后台

访问：**https://uat-sso.cheersai.cloud**

使用管理员账号登录。

---

### 第 2 步：进入用户管理

点击左侧菜单 **"Users"** 或直接访问：
```
https://uat-sso.cheersai.cloud/users
```

---

### 第 3 步：编辑用户角色

#### 方法 A：使用 Type 字段（推荐）

1. 找到要配置的用户
2. 点击用户名或 "Edit" 按钮
3. 找到 **"Type"** 字段
4. 从下拉菜单选择：
   - `admin` - 管理员（8 个菜单）
   - `technician` - 技术员（7 个菜单）
   - `user` - 普通用户（3 个菜单）
5. 点击 **"Save"** 保存

#### 方法 B：使用自定义属性

1. 编辑用户
2. 找到 **"Properties"** 部分
3. 添加 JSON：
   ```json
   {
     "role": "admin"
   }
   ```
4. 保存

---

### 第 4 步：配置应用返回字段

1. 点击左侧菜单 **"Applications"**
2. 找到应用（Client ID: `c98f7150fe9c044bf217`）
3. 点击编辑
4. 确保 **"User Info Fields"** 包含：
   - ☑ `email`
   - ☑ `name`
   - ☑ `type` ⭐
5. 保存

---

### 第 5 步：测试

1. 访问 http://localhost:3000
2. 点击 "Desktop SSO Login"
3. 使用配置好的用户登录
4. 验证菜单显示：
   - **管理员**: 8 个菜单（包括审计日志）
   - **技术员**: 7 个菜单（无审计日志）
   - **普通用户**: 3 个菜单（基础功能）

---

## 📋 角色对照表

| Type 值 | 显示菜单 |
|---------|---------|
| admin | 我的 Agent, 对话, 知识库, 智能体管理, 工作流, 应用中心, 探索, 审计日志 |
| technician | 我的 Agent, 对话, 知识库, 智能体管理, 工作流, 应用中心, 探索 |
| user | 我的 Agent, 对话, 探索 |

---

## 🔍 验证方法

### 浏览器控制台（F12）

登录后查看 Console，应该看到：
```javascript
[SSO] User info received: {
  email: "user@example.com",
  name: "User Name",
  type: "admin"  // ⭐ 角色信息
}
```

### 后端日志

查看 Terminal 4，应该看到：
```
Mapped SSO role 'admin' to system role 'admin'
Desktop SSO Login success for: user@example.com with role: admin
```

---

## ⚠️ 注意事项

1. **修改后需要重新登录** - 清除浏览器 Cookie 后重新登录
2. **默认角色** - 如果未设置角色，默认为普通用户（user）
3. **大小写敏感** - 角色值使用小写：`admin`, `technician`, `user`

---

## 🆘 遇到问题？

### 角色没有生效？
1. 清除浏览器 Cookie
2. 重新登录
3. 查看浏览器控制台和后端日志

### 找不到 Type 字段？
使用自定义属性（Properties）代替

### 所有用户都是普通用户？
检查应用配置，确保返回 `type` 字段

---

**完成！** 现在你的 SSO 用户已经配置好角色权限了。

详细文档：`web/docs/sso/Casdoor角色配置指南.md`
