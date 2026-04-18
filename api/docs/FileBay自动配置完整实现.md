# FileBay 自动配置完整实现

## 概述

本文档描述了 SSO 登录用户自动配置 FileBay 的完整实现方案。

## 实现目标

当用户通过 SSO 登录时，系统自动为其配置 FileBay 资源：
1. 在 FileBay 创建用户账号
2. 创建私有仓库
3. 生成访问 Token
4. 初始化脱敏目录
5. 保存配置到数据库

## 架构设计

```
SSO 登录
    ↓
desktop_sso.py (登录成功后)
    ↓
FileBayAutoProvisionService.auto_provision()
    ↓
保存到 Account.custom_config_dict
    ↓
Desktop 通过 Enterprise API 获取配置
    ↓
文件选择器使用配置读取文件
```

## 核心组件

### 1. FileBayAutoProvisionService

**文件**: `api/services/filebay_auto_provision_service.py`

**主要方法**:

#### `auto_provision(email: str) -> dict`
完整的自动配置流程，返回配置字典：
```python
{
    "gitea_url": "https://uat-filebay.cheersai.cloud",
    "gitea_owner": "user_abc123",
    "gitea_repo": "workspace",
    "gitea_token": "a1b2c3d4e5f6..."
}
```

#### `generate_username_from_email(email: str) -> str`
从 email 生成唯一用户名：
- 移除特殊字符
- 添加 SHA1 哈希后缀
- 最大长度 39 字符

示例：
- `test@example.com` → `test_example_com_a1b2c3`
- `admin@1@qq.com` → `admin_1_qq_com_d4e5f6`

#### `create_filebay_user(username: str, email: str) -> str`
在 FileBay 创建用户账号：
- 使用 Admin 权限创建
- 生成随机密码
- 返回密码（用于后续 Token 生成）

API: `POST /api/v1/admin/users`

#### `create_filebay_repo(username: str, repo_name: str) -> dict`
创建私有仓库：
- 仓库名默认为 `workspace`
- 自动初始化（auto_init=true）
- 私有仓库（private=true）

API: `POST /api/v1/admin/users/{username}/repos`

#### `generate_filebay_token(username: str) -> str`
生成访问 Token：
- 使用 Admin 权限为用户创建 Token
- Token 名称：`desktop_auto_{random}`
- 权限范围：read:repository, write:repository, read:user

API: `POST /api/v1/admin/users/{username}/tokens`

#### `init_masked_directory(username: str, repo_name: str, token: str)`
初始化脱敏目录：
- 创建 `masked/.keep` 文件
- 包含说明文档

API: `POST /api/v1/repos/{username}/{repo_name}/contents/{path}`

### 2. SSO 登录触发器

**文件**: `api/controllers/console/auth/desktop_sso.py`

**触发时机**: SSO 登录成功后

**实现逻辑**:
```python
# 在登录成功后
if not account.custom_config_dict or not account.custom_config_dict.get('gitea_url'):
    # 触发自动配置
    service = FileBayAutoProvisionService()
    config = service.auto_provision(email)
    
    # 保存到数据库
    account.custom_config_dict = config
    db.session.commit()
```

**特点**:
- 不影响登录流程（失败不会导致登录失败）
- 只在首次登录时执行
- 已有配置的用户跳过

### 3. Enterprise API

**文件**: `api/controllers/inner_api/gitea.py`

**端点**: `GET /inner/api/enterprise/gitea/config`

**参数**:
- `email`: 用户邮箱（必需）
- `auto_provision`: 是否自动配置（可选，默认 false）

**实现逻辑**:
```python
# 1. 查询用户配置
account = db.session.query(Account).filter_by(email=email).first()

# 2. 如果有配置，直接返回
if account.custom_config_dict.get('gitea_url'):
    return config

# 3. 如果 auto_provision=true，触发自动配置
if auto_provision:
    service = FileBayAutoProvisionService()
    config = service.auto_provision(email)
    account.custom_config_dict = config
    db.session.commit()
    return config

# 4. 否则返回环境变量配置
return env_config
```

**使用场景**:
- Desktop 文件选择器获取配置
- 后端服务间调用
- 手动触发自动配置

### 4. Console API

**文件**: `api/controllers/console/gitea_api/gitea_config.py`

**端点**: `GET /console/api/gitea/config`

**功能**:
- 调用 Enterprise API 获取配置
- 返回脱敏的 Token（前端显示用）
- 回退到数据库查询和环境变量

## 数据存储

### Account.custom_config_dict

**字段**: `Account.custom_config` (TEXT)

**属性**: `custom_config_dict` (property)

**存储格式**:
```json
{
    "gitea_url": "https://uat-filebay.cheersai.cloud",
    "gitea_owner": "user_abc123",
    "gitea_repo": "workspace",
    "gitea_token": "a1b2c3d4e5f6g7h8i9j0..."
}
```

**特点**:
- 自动 JSON 序列化/反序列化
- 每个用户独立配置
- 支持动态更新

## 环境变量配置

```env
# FileBay Admin 配置（用于自动创建用户和仓库）
FILEBAY_BASE_URL=https://uat-filebay.cheersai.cloud
FILEBAY_ADMIN_USERNAME=admin
FILEBAY_ADMIN_PASSWORD=3DIS9cqlR8@E

# FileBay 默认配置
FILEBAY_DEFAULT_REPO=workspace
FILEBAY_DEFAULT_BRANCH=main
FILEBAY_DEFAULT_MASKED_DIR=masked

# SSL 验证（开发环境可设为 false）
BETA_PROVISION_SSL_VERIFY=false
```

## 测试方案

### 1. 单元测试

**文件**: `api/test_complete_auto_provision.py`

**测试内容**:
- 直接调用 FileBayAutoProvisionService
- 测试 Enterprise API 的 auto_provision 参数
- 验证数据库保存
- 验证 API 返回

**运行方式**:
```bash
cd api
python test_complete_auto_provision.py
```

### 2. 集成测试

**测试流程**:
1. 使用 SSO 登录新用户
2. 检查数据库中的 custom_config
3. 调用 Enterprise API 验证配置
4. 使用文件选择器测试文件读取

### 3. 手动测试

**步骤**:
1. 清空测试账号的 custom_config
2. SSO 登录
3. 查看日志确认自动配置执行
4. 打开文件选择器验证功能

## API 调用示例

### 1. 获取配置（不自动配置）

```bash
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=test@example.com"
```

### 2. 获取配置（自动配置）

```bash
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=test@example.com&auto_provision=true"
```

### 3. 前端获取配置

```bash
curl "http://localhost:5001/console/api/gitea/config" \
  -H "Cookie: access_token=..."
```

## 错误处理

### 1. FileBay API 错误

**场景**: FileBay 服务不可用

**处理**:
- 记录详细错误日志
- SSO 登录不受影响（自动配置失败不影响登录）
- 下次登录时重试

### 2. 用户已存在

**场景**: 用户名冲突

**处理**:
- 检测 409/422 状态码
- 跳过用户创建步骤
- 继续后续流程

### 3. 仓库已存在

**场景**: 仓库名冲突

**处理**:
- 检测 409/422 状态码
- 跳过仓库创建步骤
- 继续后续流程

### 4. Token 生成失败

**场景**: Token API 错误

**处理**:
- 记录错误日志
- 抛出异常
- 整个自动配置流程失败

## 日志记录

### 日志级别

- `INFO`: 正常流程
- `WARNING`: 资源已存在
- `ERROR`: 失败情况

### 日志示例

```
[FileBay Auto Provision] Starting for test@example.com
[FileBay Auto Provision] Generated username: test_example_com_a1b2c3
[FileBay Auto Provision] Created user test_example_com_a1b2c3
[FileBay Auto Provision] Created repo test_example_com_a1b2c3/workspace
[FileBay Auto Provision] Generated token for test_example_com_a1b2c3
[FileBay Auto Provision] Initialized masked directory
[FileBay Auto Provision] Completed for test@example.com
```

## 安全考虑

### 1. Token 安全

- Token 存储在数据库中（custom_config）
- Enterprise API 返回完整 Token（后端使用）
- Console API 返回脱敏 Token（前端显示）

### 2. Admin 凭据

- Admin 用户名和密码存储在环境变量
- 仅用于自动配置流程
- 不暴露给前端

### 3. SSL 验证

- 生产环境必须启用 SSL 验证
- 开发环境可以禁用（BETA_PROVISION_SSL_VERIFY=false）

## 性能优化

### 1. 幂等性

- 检查资源是否已存在
- 避免重复创建
- 支持重试

### 2. 超时设置

- HTTP 请求超时：30 秒
- 避免长时间阻塞

### 3. 异步处理（未来优化）

- 可以将自动配置改为异步任务
- 使用 Celery 队列
- 提高登录响应速度

## 监控和告警

### 1. 成功率监控

- 记录自动配置成功/失败次数
- 计算成功率
- 低于阈值时告警

### 2. 性能监控

- 记录自动配置耗时
- 识别性能瓶颈
- 优化慢速步骤

### 3. 错误告警

- FileBay API 连续失败
- Token 生成失败率高
- 及时通知运维团队

## 未来改进

### 1. 批量配置

- 支持批量为用户配置 FileBay
- 管理员界面触发
- 后台任务执行

### 2. 配置迁移

- 支持从环境变量迁移到用户配置
- 一键迁移工具
- 数据验证

### 3. 配置更新

- 支持用户更新配置
- Token 轮换
- 仓库迁移

### 4. 多仓库支持

- 支持用户拥有多个仓库
- 仓库选择器
- 默认仓库设置

## 故障排查

### 问题 1: 自动配置未触发

**检查**:
- 查看 SSO 登录日志
- 确认用户没有现有配置
- 检查环境变量配置

### 问题 2: Token 无效

**检查**:
- 验证 Token 格式
- 测试 Token 权限
- 重新生成 Token

### 问题 3: 文件选择器无法读取文件

**检查**:
- 验证配置是否保存到数据库
- 测试 Enterprise API 返回
- 检查 FileBay 仓库权限

## 相关文件

### 核心实现
- `api/services/filebay_auto_provision_service.py` - 自动配置服务
- `api/controllers/inner_api/gitea.py` - Enterprise API
- `api/controllers/console/auth/desktop_sso.py` - SSO 登录触发器
- `api/controllers/console/gitea_api/gitea_config.py` - Console API

### 测试文件
- `api/test_complete_auto_provision.py` - 完整测试脚本

### 文档
- `api/docs/SSO到FileBay完整自动化流程.md` - 流程设计文档
- `api/docs/FileBay用户配置流程.md` - 配置流程文档
- `api/docs/FileBay自动配置完整实现.md` - 本文档

### 数据模型
- `api/models/account.py` - Account 模型（custom_config_dict）

## 总结

本实现方案提供了完整的 SSO 到 FileBay 自动配置流程：

1. **自动化**: SSO 登录时自动配置，无需手动操作
2. **可靠性**: 完善的错误处理和重试机制
3. **安全性**: Token 安全存储，Admin 凭据保护
4. **可测试**: 完整的测试方案和工具
5. **可维护**: 清晰的日志和文档

用户只需通过 SSO 登录，系统会自动为其配置 FileBay 资源，实现无缝的文件管理体验。

---

**文档版本**: 1.0  
**更新时间**: 2026-04-17  
**作者**: Kiro AI Assistant
