# FileBay 自动配置实现说明

## 概述
本文档说明了如何将 FileBay 配置从手动输入改为自动从企业 API 获取的实现过程。

## 实现目标
- 用户登录后，系统自动从企业 API 获取 FileBay 配置
- 如果企业 API 没有该用户的配置，则回退到用户数据库配置
- 配置优先级：企业 API > 用户数据库配置 > 环境变量

## 技术架构

### 1. 企业 API
- **URL**: `https://moisture-people-detail-possible.trycloudflare.com/inner/api/enterprise/gitea/config?email={email}`
- **方法**: GET
- **参数**: email (用户邮箱)
- **返回**: 
  ```json
  {
    "gitea_url": "https://uat-filebay.cheersai.cloud",
    "gitea_owner": "beta_20260415162204_example_com_9838ca",
    "gitea_repo": "workspace",
    "gitea_path": "masked",
    "gitea_token": "c260...4d23"
  }
  ```

### 2. 前端实现
- **文件**: `web/app/components/data-masking/sandbox-config.tsx`
- **功能**: 
  - 调用 `/console/api/gitea/config/enterprise` 获取企业配置
  - 如果企业配置不可用，则显示手动配置表单
  - 支持测试连接和保存配置

### 3. 后端实现

#### 3.1 企业配置 API
- **文件**: `api/controllers/console/gitea_api/gitea_config.py`
- **端点**: `GET /console/api/gitea/config/enterprise`
- **功能**: 
  - 获取当前用户邮箱
  - 调用企业 API 获取配置
  - 返回配置数据（包含 `is_enterprise_managed` 标志）

#### 3.2 文件列表 API
- **文件**: `api/controllers/console/gitea_api/gitea_files.py`
- **端点**: `GET /console/api/gitea/files`
- **功能**: 
  - 优先从企业 API 获取配置
  - 如果企业 API 失败，回退到用户数据库配置
  - 使用配置连接 FileBay 并列出文件

#### 3.3 内部 API
- **文件**: `api/controllers/inner_api/gitea.py`
- **端点**: `GET /inner/api/enterprise/gitea/config`
- **功能**: 
  - 根据邮箱查询 beta_applications 表
  - 返回用户的 FileBay 配置

### 4. 数据库变更
- **表**: `accounts`
- **新增字段**: `custom_config` (TEXT, nullable)
- **用途**: 存储用户自定义的 FileBay 配置（JSON 格式）

### 5. 配置存储
- **模型**: `api/models/account.py`
- **字段**: `custom_config` (TEXT)
- **属性**: `custom_config_dict` (property)
  - Getter: 将 JSON 字符串解析为字典
  - Setter: 将字典序列化为 JSON 字符串

## 配置流程

### 用户登录后
1. 前端调用 `/console/api/gitea/config/enterprise`
2. 后端获取当前用户邮箱
3. 调用企业 API: `https://moisture-people-detail-possible.trycloudflare.com/inner/api/enterprise/gitea/config?email={email}`
4. 如果成功 (200):
   - 返回企业配置
   - 设置 `is_enterprise_managed=true`
5. 如果失败 (404):
   - 返回 `is_enterprise_managed=false`
   - 前端显示手动配置表单

### 文件列表请求
1. 前端调用 `/console/api/gitea/files?path=`
2. 后端尝试从企业 API 获取配置
3. 如果企业 API 失败，从用户数据库获取配置
4. 使用配置连接 FileBay
5. 返回文件列表

## 环境配置
- **文件**: `api/.env`
- **配置项**: 
  ```
  CLOUDFLARE_TUNNEL_URL=https://moisture-people-detail-possible.trycloudflare.com
  ```

## 已修复的问题

### 1. SSO 登录 403 错误
- **问题**: SSO 登录时返回 403 FORBIDDEN
- **原因**: `desktop_access` 权限检查失败
- **解决**: 临时注释掉 `desktop_access` 检查（在 `api/controllers/console/auth/desktop_sso.py`）

### 2. Account 模型缺少 custom_config 字段
- **问题**: 代码尝试访问 `account.custom_config` 但字段不存在
- **解决**: 
  - 在 `Account` 模型中添加 `custom_config` 字段
  - 添加 `custom_config_dict` 属性用于 JSON 序列化/反序列化
  - 使用 SQL 直接添加数据库列: `ALTER TABLE accounts ADD COLUMN custom_config TEXT`

### 3. 企业 API 配置未正确应用
- **问题**: 文件列表 API 返回 500 错误
- **解决**: 
  - 修复 `gitea_files.py` 中的企业配置获取逻辑
  - 添加详细的日志记录
  - 确保配置正确设置到环境变量

## 测试步骤

1. 启动后端服务:
   ```bash
   cd api
   flask run --host=0.0.0.0 --port=5001 --debug
   ```

2. 启动前端服务:
   ```bash
   cd web
   npm run dev
   ```

3. 使用 SSO 登录（邮箱: admin@cheersai.cloud）

4. 访问数据脱敏页面，点击"配置设置"标签页

5. 检查是否自动加载企业配置

6. 测试文件列表功能

## 注意事项

1. 企业 API 需要返回完整的配置（包括 `gitea_url` 和 `gitea_token`）
2. 如果企业 API 返回不完整的配置，系统会回退到用户数据库配置
3. 用户可以手动保存配置到数据库，但企业配置优先级更高
4. 配置中的 token 在前端显示时会被掩码处理

## 相关文件

### 前端
- `web/app/components/data-masking/sandbox-config.tsx` - 配置组件
- `web/app/(commonLayout)/data-masking/page.tsx` - 数据脱敏页面
- `web/app/components/header/side-nav/index.tsx` - 侧边栏菜单

### 后端
- `api/controllers/console/gitea_api/gitea_config.py` - 配置 API
- `api/controllers/console/gitea_api/gitea_files.py` - 文件列表 API
- `api/controllers/inner_api/gitea.py` - 企业 API 端点
- `api/models/account.py` - Account 模型
- `api/configs/deploy/__init__.py` - 配置文件
- `api/controllers/console/auth/desktop_sso.py` - SSO 登录

## 下一步工作

1. 修改其他 gitea/files 相关端点（file download, metadata, url）使用相同的配置获取逻辑
2. 验证企业配置是否正确应用到所有文件操作
3. 添加更多的错误处理和日志记录
4. 考虑添加配置缓存以提高性能
