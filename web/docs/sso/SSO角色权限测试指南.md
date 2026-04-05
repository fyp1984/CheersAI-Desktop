# SSO 角色权限测试指南

## 测试准备

### 1. 配置 SSO 用户角色

在 SSO 系统（Casdoor）中，为测试用户配置不同的角色：

- **管理员测试账号**: 角色设置为 `admin` 或 `owner`
- **技术员测试账号**: 角色设置为 `technician` 或 `editor`
- **普通用户测试账号**: 角色设置为 `user` 或 `normal`

### 2. SSO 用户信息字段

确保 SSO 返回的用户信息包含角色字段，可能的字段名：
- `role`
- `type`
- `userType`

## 测试场景

### 场景 1: 管理员登录

**测试步骤**:
1. 使用管理员账号通过 SSO 登录
2. 检查浏览器控制台日志，确认角色信息
3. 验证侧边栏菜单

**预期结果**:
```
✅ 我的 Agent
✅ 对话
✅ 知识库
✅ 智能体管理
✅ 工作流
✅ 应用中心
✅ 探索
✅ 审计日志
```

**后端日志**:
```
Mapped SSO role 'admin' to system role 'admin'
Desktop SSO Login success for: admin@example.com with role: admin
```

---

### 场景 2: 技术员登录

**测试步骤**:
1. 使用技术员账号通过 SSO 登录
2. 检查浏览器控制台日志，确认角色信息
3. 验证侧边栏菜单

**预期结果**:
```
✅ 我的 Agent
✅ 对话
✅ 知识库
✅ 智能体管理
✅ 工作流
✅ 应用中心
✅ 探索
❌ 审计日志（不可见）
```

**后端日志**:
```
Mapped SSO role 'technician' to system role 'editor'
Desktop SSO Login success for: tech@example.com with role: editor
```

---

### 场景 3: 普通用户登录

**测试步骤**:
1. 使用普通用户账号通过 SSO 登录
2. 检查浏览器控制台日志，确认角色信息
3. 验证侧边栏菜单

**预期结果**:
```
✅ 我的 Agent
✅ 对话
✅ 探索
❌ 知识库（不可见）
❌ 智能体管理（不可见）
❌ 工作流（不可见）
❌ 应用中心（不可见）
❌ 审计日志（不可见）
```

**后端日志**:
```
Mapped SSO role 'user' to system role 'normal'
Desktop SSO Login success for: user@example.com with role: normal
```

---

### 场景 4: 无角色信息（默认）

**测试步骤**:
1. 使用未配置角色的账号通过 SSO 登录
2. 检查浏览器控制台日志
3. 验证侧边栏菜单

**预期结果**:
- 默认为普通用户权限
- 只能看到 3 个基础菜单

**后端日志**:
```
Mapped SSO role 'None' to system role 'normal'
Desktop SSO Login success for: noRole@example.com with role: normal
```

---

## 调试方法

### 1. 查看前端日志

打开浏览器开发者工具（F12），查看 Console 标签：

```javascript
// 应该看到类似的日志
[SSO] User info received: {
  email: "user@example.com",
  name: "Test User",
  role: "technician"  // 或 type: "technician"
}

[SSO] Calling backend /auth/desktop-sso/login with: {
  email: "user@example.com",
  name: "Test User",
  role: "technician"
}
```

### 2. 查看后端日志

在后端终端查看日志：

```bash
# 应该看到类似的日志
Processing SSO login for: user@example.com, role: technician
Mapped SSO role 'technician' to system role 'editor'
Desktop SSO Login success for: user@example.com with role: editor
```

### 3. 检查数据库

查询 `tenant_account_joins` 表，确认角色已正确存储：

```sql
SELECT 
  a.email,
  taj.role,
  taj.created_at,
  taj.updated_at
FROM tenant_account_joins taj
JOIN accounts a ON taj.account_id = a.id
WHERE a.email = 'user@example.com';
```

### 4. 检查用户上下文

在前端代码中添加调试：

```typescript
// 在 side-nav/index.tsx 中
console.log('Current workspace role:', currentWorkspace.role)
console.log('Is Admin:', isAdmin)
console.log('Is Technician:', isTechnician)
console.log('Is User:', isUser)
```

---

## 常见问题

### 问题 1: SSO 未返回角色信息

**症状**: 所有用户都显示为普通用户权限

**解决方法**:
1. 检查 SSO 配置，确保返回角色字段
2. 检查前端日志，查看 `userInfo` 对象
3. 修改 `web/service/sso.ts` 中的字段映射

### 问题 2: 角色未更新

**症状**: 修改 SSO 角色后，用户权限未变化

**解决方法**:
1. 清除浏览器 Cookie
2. 重新登录
3. 检查后端日志，确认角色已更新

### 问题 3: 管理员看不到审计日志

**症状**: 管理员登录后，审计日志菜单不显示

**解决方法**:
1. 检查 `currentWorkspace.role` 是否为 `admin` 或 `owner`
2. 检查前端控制台是否有错误
3. 确认 `isAdmin` 变量值

---

## 角色映射表

| SSO 角色 | 系统角色 | 权限级别 |
|----------|----------|----------|
| admin | admin | 管理员 |
| owner | owner | 所有者 |
| technician | editor | 技术员 |
| editor | editor | 技术员 |
| user | normal | 普通用户 |
| normal | normal | 普通用户 |
| (空) | normal | 普通用户（默认） |

---

## 测试清单

- [ ] 管理员可以看到所有 8 个菜单
- [ ] 技术员可以看到 7 个菜单（无审计日志）
- [ ] 普通用户只能看到 3 个菜单
- [ ] 角色信息正确传递到后端
- [ ] 数据库中角色正确存储
- [ ] 重新登录后角色可以更新
- [ ] 无角色信息时默认为普通用户
- [ ] 前端日志显示正确的角色信息
- [ ] 后端日志显示正确的角色映射

---

**创建日期**: 2026-04-02  
**版本**: v1.0
