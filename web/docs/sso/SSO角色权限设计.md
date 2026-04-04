# SSO 角色权限设计

## 角色定义

### 1. 管理员 (Admin)
- **SSO 角色标识**: `admin`, `owner`
- **权限**: 完全访问权限
- **可见菜单**:
  - 我的 Agent
  - 对话
  - 知识库
  - 智能体管理
  - 工作流
  - 应用中心
  - 探索
  - 审计日志

### 2. 技术员 (Technician)
- **SSO 角色标识**: `technician`, `editor`
- **权限**: 配置和开发权限
- **可见菜单**:
  - 我的 Agent
  - 对话
  - 知识库
  - 智能体管理
  - 工作流
  - 应用中心
  - 探索

### 3. 用户 (User)
- **SSO 角色标识**: `user`, `normal`
- **权限**: 基础使用权限
- **可见菜单**:
  - 我的 Agent
  - 对话
  - 探索

## 实现方案

### 后端修改

1. **SSO 登录接口** (`api/controllers/console/auth/desktop_sso.py`)
   - 从 SSO 获取用户角色信息
   - 将角色映射到系统角色
   - 存储到 `TenantAccountJoin.role`

2. **角色映射规则**:
   ```python
   SSO_ROLE_MAPPING = {
       'admin': 'admin',
       'owner': 'owner',
       'technician': 'editor',
       'editor': 'editor',
       'user': 'normal',
       'normal': 'normal',
   }
   ```

### 前端修改

1. **权限 Hook** (`web/hooks/use-role-permissions.ts`)
   - 创建自定义 Hook 判断用户权限
   - 基于 `currentWorkspace.role` 判断

2. **侧边栏菜单** (`web/app/components/header/side-nav/index.tsx`)
   - 根据角色显示不同菜单项
   - 使用权限 Hook 控制可见性

## 角色权限对照表

| 功能 | 管理员 | 技术员 | 用户 |
|------|--------|--------|------|
| 我的 Agent | ✅ | ✅ | ✅ |
| 对话 | ✅ | ✅ | ✅ |
| 知识库 | ✅ | ✅ | ❌ |
| 智能体管理 | ✅ | ✅ | ❌ |
| 工作流 | ✅ | ✅ | ❌ |
| 应用中心 | ✅ | ✅ | ❌ |
| 探索 | ✅ | ✅ | ✅ |
| 审计日志 | ✅ | ❌ | ❌ |

## 测试场景

### 管理员登录
- 应该看到所有 8 个菜单项
- 可以访问审计日志

### 技术员登录
- 应该看到 7 个菜单项（无审计日志）
- 可以配置 AI 和工作流

### 用户登录
- 应该看到 3 个菜单项
- 只能使用基础功能

## 注意事项

1. **默认角色**: 如果 SSO 未返回角色，默认为 `normal` (用户)
2. **角色更新**: 每次 SSO 登录时更新角色
3. **前端验证**: 前端仅用于 UI 显示，后端需要做权限验证
4. **路由保护**: 需要在后端 API 层面做权限检查

---

**创建日期**: 2026-04-02  
**版本**: v1.0
