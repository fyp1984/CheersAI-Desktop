# 需求文档：SSO 角色权限控制系统

## 简介

本文档定义了基于 SSO（Single Sign-On）的三级角色权限控制系统的功能需求和验收标准。系统从 Casdoor SSO 获取用户角色信息（admin/technician/user），并在前后端实现完整的权限控制机制，动态控制用户的功能访问权限和界面可见性。

## 术语表

- **SSO_Service**: Casdoor 单点登录服务
- **Backend_System**: Flask 后端应用系统
- **Frontend_System**: Next.js 前端应用系统
- **Account**: 用户账户对象
- **Workspace**: 工作空间（租户）
- **System_Role**: 系统角色，包括 'admin', 'editor', 'normal'
- **Workspace_Role**: 工作空间角色，包括 'owner', 'admin', 'editor', 'normal', 'dataset_operator'
- **SSO_Role**: 从 SSO 获取的原始角色值
- **Authorization_Code**: OAuth2 授权码
- **Access_Token**: OAuth2 访问令牌
- **UserInfo**: SSO 返回的用户信息对象
- **Navigation_Menu**: 侧边栏导航菜单
- **Permission_Decorator**: 后端权限验证装饰器
- **Audit_Log**: 审计日志记录

## 需求

### 需求 1：SSO 角色提取和映射

**用户故事**：作为系统，我需要从 SSO 用户信息中提取角色字段并映射到系统角色，以便为用户分配正确的权限级别。

#### 验收标准

1. WHEN SSO_Service 返回 userinfo 包含 type 字段为 'admin' 或 'owner'，THEN THE Backend_System SHALL 映射为系统角色 'admin'
2. WHEN SSO_Service 返回 userinfo 包含 type 字段为 'technician' 或 'editor'，THEN THE Backend_System SHALL 映射为系统角色 'editor'
3. WHEN SSO_Service 返回 userinfo 包含 type 字段为 'user' 或 'normal' 或为空，THEN THE Backend_System SHALL 映射为系统角色 'normal'
4. WHEN SSO_Service 返回 userinfo 包含 role 字段但不包含 type 字段，THEN THE Backend_System SHALL 使用 role 字段进行角色映射
5. THE Backend_System SHALL 对角色值进行标准化处理（转小写并去除空格）
6. THE Backend_System SHALL 确保映射结果只能是 'admin', 'editor', 'normal' 之一

### 需求 2：OAuth2 Token 交换

**用户故事**：作为用户，我需要使用 OAuth2 授权码交换访问令牌，以便通过 SSO 登录系统。

#### 验收标准

1. WHEN Frontend_System 发送 POST 请求到 /api/auth/sso/token 包含有效的 authorization code，THEN THE Backend_System SHALL 与 SSO_Service 交换 access_token
2. WHEN Backend_System 成功获取 access_token，THEN THE Backend_System SHALL 使用该 token 调用 SSO_Service 的 userinfo 端点
3. WHEN SSO_Service 返回 userinfo，THEN THE Backend_System SHALL 提取 email, name, 和 role/type 字段
4. IF authorization code 无效或已过期，THEN THE Backend_System SHALL 返回 401 错误并包含描述性错误消息
5. IF SSO_Service 不可用，THEN THE Backend_System SHALL 返回 503 错误并记录错误日志
6. THE Backend_System SHALL 在 30 秒内完成整个 token 交换流程

### 需求 3：用户账户同步

**用户故事**：作为系统，我需要在 SSO 登录时创建或更新用户账户，以便保持用户信息和角色的同步。

#### 验收标准

1. WHEN Backend_System 接收到 SSO 登录请求，THEN THE Backend_System SHALL 根据 email 查询现有账户
2. WHEN 账户不存在，THEN THE Backend_System SHALL 创建新账户并设置 sso_role, is_sso_user 为 True, status 为 'active'
3. WHEN 账户已存在且 status 为 'active'，THEN THE Backend_System SHALL 更新 sso_role 字段为新的角色值
4. WHEN 账户已存在且 status 为 'pending'，THEN THE Backend_System SHALL 更新 sso_role 并将 status 改为 'active'
5. IF 账户 status 为 'banned'，THEN THE Backend_System SHALL 拒绝登录并返回 403 错误
6. WHEN 创建新账户，THEN THE Backend_System SHALL 同时创建默认工作空间
7. THE Backend_System SHALL 在数据库事务中完成所有账户操作以确保数据一致性

### 需求 4：工作空间角色同步

**用户故事**：作为系统，我需要将 SSO 角色同步到用户的工作空间成员角色，以便用户在工作空间中拥有相应的权限。

#### 验收标准

1. WHEN Backend_System 更新用户的 sso_role，THEN THE Backend_System SHALL 同步更新用户所有工作空间的成员角色
2. WHEN 系统角色为 'admin'，THEN THE Backend_System SHALL 将工作空间角色设置为 'owner'
3. WHEN 系统角色为 'editor'，THEN THE Backend_System SHALL 将工作空间角色设置为 'editor'
4. WHEN 系统角色为 'normal'，THEN THE Backend_System SHALL 将工作空间角色设置为 'normal'
5. WHEN 用户是工作空间的唯一 owner，THEN THE Backend_System SHALL 保持其 owner 角色不变
6. THE Backend_System SHALL 确保每个工作空间至少有一个 owner
7. THE Backend_System SHALL 在数据库事务中完成角色同步以确保数据一致性

### 需求 5：后端 API 权限验证

**用户故事**：作为系统，我需要在 API 端点验证用户权限，以便阻止未授权的操作。

#### 验收标准

1. WHEN Backend_System 接收到 API 请求，THEN THE Backend_System SHALL 从请求上下文获取当前用户和工作空间信息
2. WHEN API 端点使用 @require_role 装饰器，THEN THE Backend_System SHALL 验证用户的工作空间角色是否在允许列表中
3. IF 用户角色不在允许列表中，THEN THE Backend_System SHALL 返回 403 错误并包含 "Insufficient permissions" 消息
4. IF 用户角色在允许列表中，THEN THE Backend_System SHALL 允许请求继续执行
5. WHEN 权限验证失败，THEN THE Backend_System SHALL 记录审计日志包含用户ID、工作空间ID、请求端点、时间戳
6. THE Backend_System SHALL 提供 @require_admin 装饰器用于仅管理员可访问的端点
7. THE Backend_System SHALL 提供 @require_editor_or_above 装饰器用于技术员及以上可访问的端点

### 需求 6：前端角色信息管理

**用户故事**：作为前端应用，我需要获取和管理用户的角色信息，以便动态渲染界面和控制功能可见性。

#### 验收标准

1. WHEN Frontend_System 完成 SSO 登录，THEN THE Frontend_System SHALL 从后端 API 获取当前工作空间信息包含 role 字段
2. WHEN Frontend_System 获取到工作空间信息，THEN THE Frontend_System SHALL 将 role 存储在 AppContext 中
3. THE Frontend_System SHALL 提供 useAppContext hook 用于访问当前用户角色
4. THE Frontend_System SHALL 提供 isCurrentWorkspaceManager 判断用户是否为管理员
5. THE Frontend_System SHALL 提供 isCurrentWorkspaceEditor 判断用户是否为技术员或以上
6. WHEN 工作空间信息更新，THEN THE Frontend_System SHALL 自动刷新 AppContext 中的角色信息
7. THE Frontend_System SHALL 在角色信息缺失时默认为 'normal' 角色

### 需求 7：侧边栏导航菜单控制

**用户故事**：作为用户，我希望侧边栏只显示我有权限访问的菜单项，以便清晰地了解可用功能。

#### 验收标准

1. WHEN 用户角色为 'owner' 或 'admin'，THEN THE Frontend_System SHALL 显示 8 个菜单项：我的Agent、对话、知识库、智能体管理、工作流、应用中心、探索、审计日志
2. WHEN 用户角色为 'editor'，THEN THE Frontend_System SHALL 显示 7 个菜单项：我的Agent、对话、知识库、智能体管理、工作流、应用中心、探索
3. WHEN 用户角色为 'normal'，THEN THE Frontend_System SHALL 显示 5 个菜单项：我的Agent、对话、知识库、应用中心、探索
4. WHEN 用户角色为 'dataset_operator'，THEN THE Frontend_System SHALL 只显示知识库相关菜单
5. THE Frontend_System SHALL 根据角色变化动态更新菜单项列表
6. THE Frontend_System SHALL 使用 useMemo 缓存菜单项列表以优化性能
7. THE Frontend_System SHALL 保持菜单项的顺序一致

### 需求 8：页面级权限控制

**用户故事**：作为系统，我需要在页面级别验证用户权限，以便阻止用户访问无权限的页面。

#### 验收标准

1. WHEN 用户尝试访问审计日志页面且角色不是 'owner' 或 'admin'，THEN THE Frontend_System SHALL 重定向到 403 页面
2. WHEN 用户尝试访问智能体管理页面且角色为 'normal'，THEN THE Frontend_System SHALL 重定向到 403 页面
3. WHEN 用户尝试访问工作流页面且角色为 'normal'，THEN THE Frontend_System SHALL 重定向到 403 页面
4. THE Frontend_System SHALL 提供 useRequireRole hook 用于页面级权限保护
5. WHEN 用户角色满足要求，THEN THE Frontend_System SHALL 正常渲染页面内容
6. THE Frontend_System SHALL 在权限检查时显示加载状态避免闪烁
7. THE Frontend_System SHALL 在 403 页面提供返回首页的链接

### 需求 9：功能级权限控制

**用户故事**：作为用户，我希望只看到我有权限执行的操作按钮，以便避免执行无权限的操作。

#### 验收标准

1. WHEN 用户角色为 'normal' 且在我的Agent页面，THEN THE Frontend_System SHALL 隐藏创建、编辑、删除、配置、发布按钮
2. WHEN 用户角色为 'normal' 且在知识库页面，THEN THE Frontend_System SHALL 隐藏创建、编辑、删除、上传、管理文档按钮
3. WHEN 用户角色为 'normal' 且在应用中心页面，THEN THE Frontend_System SHALL 隐藏安装、配置、卸载按钮
4. WHEN 用户角色为 'editor' 或以上，THEN THE Frontend_System SHALL 显示所有创建和编辑相关按钮
5. THE Frontend_System SHALL 提供 usePermission hook 返回细粒度的权限判断结果
6. THE Frontend_System SHALL 提供 canCreateAgent, canEditAgent, canDeleteAgent 等权限判断方法
7. THE Frontend_System SHALL 提供 canViewAuditLogs 权限判断方法仅对管理员返回 true

### 需求 10：只读模式支持

**用户故事**：作为普通用户，我希望能够查看知识库和应用中心的内容，但不能进行修改操作。

#### 验收标准

1. WHEN 用户角色为 'normal' 且访问知识库列表，THEN THE Backend_System SHALL 返回所有可见的知识库
2. WHEN 用户角色为 'normal' 且访问知识库详情，THEN THE Backend_System SHALL 返回知识库的完整信息
3. WHEN 用户角色为 'normal' 且尝试创建知识库，THEN THE Backend_System SHALL 返回 403 错误
4. WHEN 用户角色为 'normal' 且尝试编辑知识库，THEN THE Backend_System SHALL 返回 403 错误
5. WHEN 用户角色为 'normal' 且访问我的Agent列表，THEN THE Backend_System SHALL 只返回已发布的Agent
6. WHEN 用户角色为 'editor' 或以上且访问我的Agent列表，THEN THE Backend_System SHALL 返回所有Agent包括草稿
7. THE Backend_System SHALL 在返回数据前根据用户角色进行过滤

### 需求 11：角色信息安全存储

**用户故事**：作为系统，我需要安全地存储和传输角色信息，以便防止角色信息被篡改。

#### 验收标准

1. THE Backend_System SHALL 将角色信息编码到 JWT token 的 payload 中
2. THE Backend_System SHALL 使用 HttpOnly cookie 存储 JWT token
3. THE Backend_System SHALL 对 JWT token 进行签名以防止篡改
4. THE Backend_System SHALL 设置 JWT token 的过期时间不超过 24 小时
5. THE Backend_System SHALL 在验证权限时从 JWT token 或数据库获取角色信息
6. THE Backend_System SHALL 不信任前端传递的角色信息
7. THE Backend_System SHALL 使用 HTTPS 传输所有包含角色信息的请求

### 需求 12：审计日志记录

**用户故事**：作为管理员，我需要查看系统的审计日志，以便追踪权限相关的操作和异常。

#### 验收标准

1. WHEN 用户权限验证失败，THEN THE Backend_System SHALL 记录审计日志包含用户ID、工作空间ID、请求端点、时间戳、IP地址
2. WHEN 用户角色发生变更，THEN THE Backend_System SHALL 记录审计日志包含账户ID、旧角色、新角色、变更时间、操作者
3. WHEN 用户首次通过 SSO 登录，THEN THE Backend_System SHALL 记录审计日志包含账户创建信息
4. THE Backend_System SHALL 提供审计日志查询 API 仅允许管理员访问
5. THE Backend_System SHALL 支持按用户、时间范围、操作类型筛选审计日志
6. THE Backend_System SHALL 支持导出审计日志为 CSV 格式
7. THE Backend_System SHALL 保留审计日志至少 90 天

### 需求 13：错误处理和恢复

**用户故事**：作为系统，我需要优雅地处理各种错误情况，以便提供良好的用户体验和系统稳定性。

#### 验收标准

1. WHEN SSO_Service 未返回角色信息，THEN THE Backend_System SHALL 将用户角色设置为默认值 'normal' 并记录警告日志
2. WHEN 用户账户 status 为 'banned'，THEN THE Backend_System SHALL 返回 403 错误并包含 "Account is banned" 消息
3. WHEN 数据库事务失败，THEN THE Backend_System SHALL 回滚所有更改并返回 500 错误
4. WHEN SSO_Service 不可用，THEN THE Backend_System SHALL 返回 503 错误并提示用户稍后重试
5. WHEN Frontend_System 无法获取工作空间信息，THEN THE Frontend_System SHALL 默认为 'normal' 角色并尝试自动重新获取
6. WHEN API 请求超时，THEN THE Backend_System SHALL 返回 504 错误并记录错误日志
7. THE Backend_System SHALL 为所有错误响应提供描述性的错误消息

## 非功能需求

### 性能需求

1. THE Backend_System SHALL 在 200 毫秒内完成权限验证
2. THE Backend_System SHALL 在 30 秒内完成 SSO token 交换流程
3. THE Frontend_System SHALL 在 100 毫秒内完成菜单项过滤和渲染
4. THE Backend_System SHALL 支持至少 1000 个并发用户同时登录
5. THE Backend_System SHALL 使用数据库索引优化角色查询性能

### 可用性需求

1. THE System SHALL 提供清晰的错误消息帮助用户理解问题
2. THE Frontend_System SHALL 在权限不足时显示友好的提示信息
3. THE Frontend_System SHALL 在加载状态时显示加载指示器
4. THE System SHALL 在用户角色变更后 5 分钟内生效（token 刷新后）
5. THE Frontend_System SHALL 提供 403 页面包含返回首页的链接

### 安全需求

1. THE Backend_System SHALL 对所有 API 端点进行权限验证
2. THE Backend_System SHALL 使用 HTTPS 传输所有敏感数据
3. THE Backend_System SHALL 使用 HttpOnly cookie 存储认证 token
4. THE Backend_System SHALL 实施 CSRF 保护机制
5. THE Backend_System SHALL 对 JWT token 进行签名验证
6. THE Backend_System SHALL 记录所有权限验证失败的尝试
7. THE Backend_System SHALL 采用默认拒绝策略（白名单机制）

### 可维护性需求

1. THE Backend_System SHALL 使用装饰器模式实现权限验证以提高代码复用性
2. THE Frontend_System SHALL 使用 Hook 模式封装权限判断逻辑
3. THE System SHALL 提供清晰的角色映射配置便于修改
4. THE System SHALL 使用数据库迁移脚本管理 schema 变更
5. THE System SHALL 提供详细的日志记录便于问题排查

### 兼容性需求

1. THE System SHALL 支持现有用户平滑迁移到 SSO 角色系统
2. THE System SHALL 为现有用户设置默认角色 'normal'
3. THE System SHALL 保持向后兼容不影响非 SSO 用户的登录
4. THE System SHALL 支持 Casdoor 的 type 和 role 两种角色字段格式

### 可扩展性需求

1. THE System SHALL 设计支持未来添加新角色
2. THE System SHALL 设计支持未来实现细粒度权限控制
3. THE System SHALL 设计支持未来实现多租户权限隔离
4. THE System SHALL 使用配置化的权限矩阵便于扩展

### 可测试性需求

1. THE System SHALL 提供独立的角色映射函数便于单元测试
2. THE System SHALL 提供权限验证装饰器便于集成测试
3. THE System SHALL 提供测试用户配置指南
4. THE System SHALL 支持在测试环境模拟不同角色的用户

---

**文档版本**: v1.0  
**创建日期**: 2024-01-XX  
**状态**: 待审核
