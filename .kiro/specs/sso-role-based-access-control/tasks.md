# 实现计划：SSO 角色权限控制系统

## 概述

本实现计划将基于 SSO 的三级角色权限控制系统分解为可执行的开发任务。系统从 Casdoor SSO 获取用户角色信息（admin/technician/user），并在前后端实现完整的权限控制机制。

**技术栈**：
- 后端：Python + Flask
- 前端：TypeScript + Next.js + React
- 数据库：PostgreSQL
- SSO：Casdoor OAuth2

**角色定义**：
- 管理员（admin）：8个菜单 - 完整权限
- 技术员（editor）：7个菜单 - 无审计日志
- 普通用户（normal）：5个菜单 - 基础使用权限（主要只读）

---

## 任务列表

### 阶段 1：数据库和后端基础设施

- [ ] 1. 数据库迁移和模型更新
  - [ ] 1.1 创建数据库迁移脚本添加 sso_role 和 is_sso_user 字段
    - 在 `api/migrations/versions/` 创建新的迁移文件
    - 添加 `sso_role VARCHAR(16)` 字段到 accounts 表
    - 添加 `is_sso_user BOOLEAN DEFAULT FALSE` 字段到 accounts 表
    - 为现有用户设置默认值 `sso_role='normal', is_sso_user=False`
    - 添加索引 `idx_accounts_sso_role` 和 `idx_accounts_is_sso_user`
    - _需求: 1.3, 3.2, 3.3, 11.1_

  - [ ] 1.2 更新 Account 模型定义
    - 在 `api/models/account.py` 的 Account 类中添加 `sso_role` 和 `is_sso_user` 字段
    - 添加字段注释说明角色值范围
    - _需求: 3.2, 3.3_

  - [ ]* 1.3 编写数据库迁移的单元测试
    - 测试迁移脚本可以成功执行
    - 测试字段添加和索引创建
    - 测试现有数据的默认值设置
    - _需求: 3.7_

- [ ] 2. SSO 角色提取和映射功能
  - [ ] 2.1 实现角色提取和映射函数
    - 在 `api/services/account_service.py` 创建 `extract_role_from_userinfo(user_info: dict) -> str` 函数
    - 实现 `map_sso_role_to_system_role(sso_role: str) -> str` 函数
    - 支持从 `type` 或 `role` 字段提取角色
    - 实现角色映射逻辑：admin/owner→admin, technician/editor→editor, 其他→normal
    - 对角色值进行标准化处理（转小写、去空格）
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 2.2 编写角色映射的单元测试
    - 测试所有 Casdoor 角色值的映射
    - 测试空值和未知值的处理
    - 测试大小写和空格的标准化
    - _需求: 1.1, 1.2, 1.3_

  - [ ]* 2.3 编写角色映射的属性测试
    - **属性 1: 角色映射的一致性** - 任意 SSO 角色值总是返回有效的系统角色
    - **验证需求: 1.6**
    - 使用 hypothesis 生成随机字符串测试
    - 验证返回值始终在 {'admin', 'editor', 'normal'} 中
    - _需求: 1.6_

- [ ] 3. SSO Token 交换和用户信息获取
  - [ ] 3.1 更新 SSO Token 交换接口
    - 在 `api/controllers/console/auth/sso_token.py` 更新 `SSOTokenExchangeApi.post()` 方法
    - 调用 SSO userinfo 端点获取用户信息（包括角色）
    - 提取 email, name, role/type 字段
    - 调用角色映射函数获取系统角色
    - 添加错误处理：无效 code、SSO 不可用、超时
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 3.2 编写 Token 交换的集成测试
    - Mock SSO 服务响应
    - 测试成功场景
    - 测试错误场景（无效 code、SSO 不可用）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. 用户账户同步服务
  - [ ] 4.1 实现用户账户同步函数
    - 在 `api/services/account_service.py` 实现 `get_or_create_sso_account(email, name, sso_role)` 函数
    - 根据 email 查询现有账户
    - 创建新账户时设置 sso_role, is_sso_user=True, status='active'
    - 更新现有账户的 sso_role 字段
    - 处理 banned 账户（返回 403）
    - 激活 pending 状态的账户
    - 使用数据库事务确保一致性
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 4.2 编写账户同步的单元测试
    - 测试新用户创建
    - 测试现有用户更新
    - 测试 banned 账户拒绝
    - 测试 pending 账户激活
    - _需求: 3.2, 3.3, 3.4, 3.5_

  - [ ]* 4.3 编写账户同步的属性测试
    - **属性 4: 角色同步的幂等性** - 多次同步相同角色不改变最终状态
    - **验证需求: 3.7**
    - 使用 hypothesis 生成随机 email, name, role
    - 验证两次同步后状态一致
    - _需求: 3.7_

- [ ] 5. Checkpoint - 验证后端基础功能
  - 确保所有测试通过，数据库迁移成功，询问用户是否有问题


### 阶段 2：工作空间角色同步

- [ ] 6. 工作空间角色同步服务
  - [ ] 6.1 实现工作空间角色同步函数
    - 在 `api/services/workspace_service.py` 创建 `sync_workspace_role_from_sso(account, sso_role)` 函数
    - 实现 `map_sso_role_to_workspace_role(sso_role)` 函数（admin→owner, editor→editor, normal→normal）
    - 查询用户的所有工作空间成员关系
    - 更新每个工作空间的角色字段
    - 保护唯一 owner 不被降级
    - 使用数据库事务确保一致性
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 6.2 编写工作空间角色同步的单元测试
    - 测试角色映射逻辑
    - 测试多个工作空间的角色更新
    - 测试唯一 owner 保护
    - _需求: 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 6.3 编写工作空间角色同步的属性测试
    - **属性 3: 工作空间 Owner 的保护** - 同步角色时不会导致工作空间没有 owner
    - **验证需求: 4.6**
    - 验证每个工作空间始终至少有一个 owner
    - _需求: 4.6_

- [ ] 7. 集成账户同步和工作空间同步
  - [ ] 7.1 在 SSO 登录流程中调用同步函数
    - 在 `api/controllers/console/auth/sso_token.py` 的登录逻辑中调用 `get_or_create_sso_account()`
    - 调用 `sync_workspace_role_from_sso()` 同步工作空间角色
    - 确保事务一致性
    - _需求: 3.1, 4.1_

  - [ ]* 7.2 编写完整 SSO 登录流程的集成测试
    - 测试新用户首次登录（创建账户+工作空间+角色）
    - 测试现有用户登录（更新角色）
    - 测试角色变更场景
    - _需求: 3.1, 3.2, 3.3, 4.1, 4.2_

- [ ] 8. Checkpoint - 验证角色同步功能
  - 确保所有测试通过，角色同步正常工作，询问用户是否有问题

### 阶段 3：后端权限验证

- [ ] 9. 权限验证装饰器
  - [ ] 9.1 实现权限验证装饰器
    - 创建 `api/libs/permission_decorators.py` 文件
    - 实现 `require_role(*allowed_roles)` 装饰器
    - 实现 `require_admin` 装饰器（仅 owner/admin）
    - 实现 `require_editor_or_above` 装饰器（owner/admin/editor）
    - 从请求上下文获取当前用户和工作空间
    - 验证用户角色是否在允许列表中
    - 返回 403 错误给无权限请求
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.6, 5.7_

  - [ ] 9.2 实现权限验证失败的审计日志
    - 在权限验证失败时记录审计日志
    - 包含用户ID、工作空间ID、请求端点、时间戳、IP地址
    - _需求: 5.5, 12.1_

  - [ ]* 9.3 编写权限装饰器的单元测试
    - 测试不同角色的访问控制
    - 测试 403 错误返回
    - 测试审计日志记录
    - _需求: 5.2, 5.3, 5.4, 5.5_

  - [ ]* 9.4 编写权限验证的属性测试
    - **属性 2: 权限的单调性** - 更高级别角色拥有更低级别角色的所有权限
    - **验证需求: 5.2, 5.3, 5.4**
    - 验证 admin 可以访问 editor 的所有端点
    - 验证 editor 可以访问 normal 的所有端点
    - _需求: 5.2, 5.3, 5.4_

- [ ] 10. 应用权限装饰器到 API 端点
  - [ ] 10.1 为知识库 API 添加权限控制
    - 在 `api/controllers/console/datasets/datasets.py` 的创建、编辑、删除端点添加 `@require_editor_or_above`
    - 保持查询端点对所有角色开放
    - _需求: 5.2, 5.3, 10.3, 10.4_

  - [ ] 10.2 为 Agent API 添加权限控制
    - 在 Agent 创建、编辑、删除端点添加 `@require_editor_or_above`
    - 保持查询端点对所有角色开放
    - _需求: 5.2, 5.3, 10.3, 10.4_

  - [ ] 10.3 为审计日志 API 添加权限控制
    - 在审计日志查询端点添加 `@require_admin`
    - _需求: 5.2, 5.6_

  - [ ] 10.4 为插件和工作流 API 添加权限控制
    - 在插件和工作流相关端点添加 `@require_editor_or_above`
    - _需求: 5.2, 5.3_

  - [ ]* 10.5 编写 API 权限控制的集成测试
    - 测试不同角色访问各个端点
    - 验证 403 错误返回
    - _需求: 5.2, 5.3, 5.4_


- [ ] 11. 实现数据过滤逻辑
  - [ ] 11.1 为普通用户过滤 Agent 列表
    - 在 Agent 查询逻辑中，普通用户只返回已发布的 Agent
    - 技术员和管理员返回所有 Agent
    - _需求: 10.5, 10.6, 10.7_

  - [ ] 11.2 为普通用户提供知识库只读访问
    - 普通用户可以查看知识库列表和详情
    - 普通用户可以搜索知识库内容
    - _需求: 10.1, 10.2_

  - [ ]* 11.3 编写数据过滤的单元测试
    - 测试不同角色看到的数据范围
    - _需求: 10.1, 10.2, 10.5, 10.6_

- [ ] 12. Checkpoint - 验证后端权限控制
  - 确保所有测试通过，权限控制正常工作，询问用户是否有问题

### 阶段 4：前端角色信息管理

- [ ] 13. 前端 SSO 服务更新
  - [ ] 13.1 更新 SSO Token 交换服务
    - 在 `web/service/sso.ts` 更新 `exchangeSSOToken()` 函数
    - 确保从后端获取包含角色信息的响应
    - 添加错误处理
    - _需求: 2.1, 2.2, 6.1, 6.2_

  - [ ]* 13.2 编写 SSO 服务的单元测试
    - Mock API 响应
    - 测试成功和错误场景
    - _需求: 6.1, 6.2_

- [ ] 14. 应用上下文更新
  - [ ] 14.1 确认 AppContext 包含角色信息
    - 检查 `web/context/app-context.tsx` 中的 `ICurrentWorkspace` 接口包含 `role` 字段
    - 确认 `useAppContext` hook 提供角色判断方法
    - 确认 `isCurrentWorkspaceManager`, `isCurrentWorkspaceEditor` 等方法存在
    - _需求: 6.3, 6.4, 6.5, 6.6_

  - [ ] 14.2 实现角色信息刷新机制
    - 在工作空间信息更新时自动刷新角色
    - 处理角色信息缺失的情况（默认为 normal）
    - _需求: 6.6, 6.7_

  - [ ]* 14.3 编写 AppContext 的单元测试
    - 测试角色判断方法
    - 测试角色信息刷新
    - _需求: 6.4, 6.5, 6.6_

- [ ] 15. 权限控制 Hook
  - [ ] 15.1 创建 usePermission Hook
    - 创建 `web/hooks/use-permission.ts` 文件
    - 实现 `usePermission()` hook 返回权限判断结果
    - 提供 `isAdmin`, `isEditor`, `isNormal` 判断
    - 提供 `canCreateAgent`, `canEditAgent`, `canDeleteAgent` 等细粒度权限
    - 提供 `canCreateDataset`, `canEditDataset` 权限
    - 提供 `canViewAuditLogs` 权限（仅管理员）
    - 提供 `hasRole()`, `hasAnyRole()` 通用方法
    - _需求: 9.5, 9.6, 9.7_

  - [ ] 15.2 创建 useRequireRole Hook
    - 在 `web/hooks/use-permission.ts` 实现 `useRequireRole(requiredRole)` hook
    - 在用户角色不满足时重定向到 403 页面
    - _需求: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 15.3 编写权限 Hook 的单元测试
    - 测试不同角色的权限判断结果
    - 测试页面重定向逻辑
    - _需求: 9.5, 9.6, 9.7, 8.4, 8.5_

  - [ ]* 15.4 编写权限 Hook 的属性测试
    - **属性 2: 权限的单调性** - 更高级别角色拥有更低级别角色的所有权限
    - **验证需求: 9.5**
    - 验证 admin 的所有 can* 方法返回值 >= editor
    - 验证 editor 的所有 can* 方法返回值 >= normal
    - _需求: 9.5_

- [ ] 16. Checkpoint - 验证前端基础功能
  - 确保所有测试通过，Hook 正常工作，询问用户是否有问题

### 阶段 5：前端界面权限控制

- [ ] 17. 侧边栏导航菜单控制
  - [ ] 17.1 更新侧边栏导航组件
    - 在 `web/app/components/header/side-nav/index.tsx` 实现菜单过滤逻辑
    - 使用 `useAppContext` 获取当前用户角色
    - 根据角色动态生成菜单项列表
    - 管理员：8个菜单（我的Agent、对话、知识库、智能体管理、工作流、应用中心、探索、审计日志）
    - 技术员：7个菜单（无审计日志）
    - 普通用户：5个菜单（我的Agent、对话、知识库、应用中心、探索）
    - 使用 useMemo 缓存菜单列表优化性能
    - _需求: 7.1, 7.2, 7.3, 7.5, 7.6, 7.7_

  - [ ]* 17.2 编写侧边栏的单元测试
    - 测试不同角色显示的菜单数量
    - 测试菜单项的正确性
    - _需求: 7.1, 7.2, 7.3_


- [ ] 18. 页面级权限保护
  - [ ] 18.1 保护审计日志页面
    - 在审计日志页面组件中使用 `useRequireRole(['owner', 'admin'])`
    - 无权限用户自动重定向到 403 页面
    - _需求: 8.1, 8.4, 8.5_

  - [ ] 18.2 保护智能体管理页面
    - 在智能体管理页面使用 `useRequireRole(['owner', 'admin', 'editor'])`
    - _需求: 8.2, 8.4, 8.5_

  - [ ] 18.3 保护工作流页面
    - 在工作流页面使用 `useRequireRole(['owner', 'admin', 'editor'])`
    - _需求: 8.3, 8.4, 8.5_

  - [ ] 18.4 创建 403 权限拒绝页面
    - 创建 `web/app/403/page.tsx` 组件
    - 显示友好的错误提示
    - 提供返回首页的链接
    - _需求: 8.7_

  - [ ]* 18.5 编写页面权限保护的集成测试
    - 测试不同角色访问受保护页面
    - 验证重定向行为
    - _需求: 8.1, 8.2, 8.3, 8.4_

- [ ] 19. 功能级权限控制 - 我的Agent页面
  - [ ] 19.1 控制我的Agent页面的操作按钮
    - 在我的Agent页面使用 `usePermission` hook
    - 根据 `canCreateAgent` 控制创建按钮可见性
    - 根据 `canEditAgent` 控制编辑按钮可见性
    - 根据 `canDeleteAgent` 控制删除按钮可见性
    - 普通用户只显示使用和查看按钮
    - _需求: 9.1, 9.2_

  - [ ]* 19.2 编写我的Agent页面的单元测试
    - 测试不同角色看到的按钮
    - _需求: 9.1, 9.2_

- [ ] 20. 功能级权限控制 - 知识库页面
  - [ ] 20.1 控制知识库页面的操作按钮
    - 在知识库页面使用 `usePermission` hook
    - 根据 `canCreateDataset` 控制创建按钮可见性
    - 根据 `canEditDataset` 控制编辑、删除、上传按钮可见性
    - 普通用户只显示查看和搜索功能
    - _需求: 9.2, 9.6_

  - [ ]* 20.2 编写知识库页面的单元测试
    - 测试不同角色看到的按钮
    - _需求: 9.2_

- [ ] 21. 功能级权限控制 - 应用中心页面
  - [ ] 21.1 控制应用中心页面的操作按钮
    - 在应用中心页面使用 `usePermission` hook
    - 技术员及以上显示安装、配置、卸载按钮
    - 普通用户只显示浏览和使用按钮
    - _需求: 9.3_

  - [ ]* 21.2 编写应用中心页面的单元测试
    - 测试不同角色看到的按钮
    - _需求: 9.3_

- [ ] 22. Checkpoint - 验证前端权限控制
  - 确保所有测试通过，UI 权限控制正常，询问用户是否有问题

