---
name: "sso-role-permission-integration"
description: "Designs SSO role/permission integration for third-party systems. Invoke when a product needs SSO-based roles, capabilities, session sync, or phased auth rollout."
---

# SSO Role Permission Integration

本 Skill 用于把第三方系统接入统一 SSO 平台时，围绕“角色、权限、能力集、会话、菜单、页面、接口”的整体设计收敛成一套可落地方案。

## 1. 适用场景
- 当一个现有系统已经有本地角色体系，需要与 SSO 的 `roles[] / permissions[]` 对齐时调用
- 当用户要求输出 SSO 接入方案、角色权限矩阵、能力模型、兼容迁移方案时调用
- 当产品已经接入登录，但菜单、页面、接口权限还未统一时调用
- 当需要设计“旧编码兼容 + 新编码切换 + 灰度回滚”方案时调用

## 2. 核心设计原则
- **事实源优先**：SSO 是身份、角色、权限的唯一事实源；业务系统只消费，不再发明上游事实
- **能力收口**：运行时优先解析 `permissions[]`，再解析 `roles[]`，最后才回落本地兼容 role
- **兼容迁移**：允许旧权限编码与新权限编码并存，但必须通过统一映射层收敛，不允许散落在页面和接口中
- **最小权限**：权限缺失、同步失败、字段异常时只允许降权，不允许误提权
- **四层统一**：菜单、页面、操作、接口必须使用同一能力模型

## 3. 标准输入契约
- 标准身份字段：
  - `sub`
  - `preferred_username`
  - `name`
  - `email`
  - `groups[]`
  - `roles[]`
  - `permissions[]`
  - `iss`
  - `aud`
- 登录准入建议使用独立权限，例如：
  - `desktop_access`
  - `portal_access`
  - `vault_access`
- 明确禁止把 `email`、`name`、`role/type` 猜测逻辑继续作为主事实源

## 4. 通用投影模型
- 建议业务系统在登录成功后形成统一投影：
  - `subjectId`
  - `issuer`
  - `clientId`
  - `username`
  - `displayName`
  - `email`
  - `groups`
  - `roles`
  - `permissions`
  - `mappedRole`
  - `workspaceRole` 或本地兼容 role
  - `capabilities`
  - `tokenExpiresAt`
  - `lastSyncedAt`
  - `syncHash`

## 5. 通用实施步骤
- **步骤1：盘点现状**
  - 盘点目标系统现有本地角色、菜单、页面、按钮、接口守卫
  - 盘点 SSO 当前已存在的角色、权限、用户绑定
- **步骤2：定义标准编码**
  - 定义标准角色编码，如 `xxx_team_admin`、`xxx_team_editor`
  - 定义标准权限编码，如 `xxx_access`、`xxx_plugin_manage`
  - 定义历史编码到标准编码的兼容映射表
- **步骤3：建立能力映射层**
  - 从 `permissions[]` 收敛业务能力
  - 从 `roles[]` 补齐角色包能力
  - 最后回落本地 role 作为兼容兜底
- **步骤4：打通登录与会话**
  - 完整接入 `authorize -> token -> userinfo -> 本地登录桥接`
  - 使用 `expires_in / refresh_token` 驱动会话
  - refresh 后重新拉取 userinfo 并同步能力
- **步骤5：统一鉴权**
  - 菜单显隐基于能力
  - 页面守卫基于能力
  - 按钮/操作基于能力
  - 后端接口守卫基于能力
- **步骤6：灰度迁移**
  - 旧新编码并行识别
  - 先真实账号回归，再纯角色测试
  - 最后下线历史编码

## 6. 输出模板

### 6.1 角色权限设计
- 标准角色表
- 标准权限表
- 历史编码兼容表
- 角色到能力映射表

### 6.2 鉴权矩阵
- 菜单矩阵
- 页面矩阵
- 操作矩阵
- 接口矩阵

### 6.3 会话与同步
- token 生命周期
- refresh 时机
- 强同步/轻同步触发点
- 差异对账与降权补偿规则

## 7. 风险控制
- 发现 `sub` 缺失、`iss/aud` 异常时，禁止进入业务成功态
- 同一用户多角色叠加时，必须按统一优先级和能力合并规则处理
- 菜单可见不代表可操作，后端接口必须始终保留能力守卫
- 不要先改页面文案再改权限模型，避免出现名称和能力不一致

## 8. 验收标准
- 业务系统可以完整消费 `sub + roles[] + permissions[]`
- 本地兼容 role 不再是唯一事实源
- 菜单、页面、操作、接口四层鉴权一致
- refresh 后能力可同步更新
- 旧编码与新编码兼容期行为稳定
- 真实账号与纯角色样本回归都通过

## 9. 推荐交付物
- SSO 对接设计文档
- 角色权限矩阵表
- 能力映射表
- 会话续期设计
- 差异对账清单
- 联调与验收清单
