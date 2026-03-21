# Gitea 配置页面使用指南

## 概述

Gitea 配置页面允许用户在 Web 界面中配置 Gitea 服务器连接信息，无需手动编辑配置文件。

## 访问方式

访问 URL: `http://localhost:3000/gitea-settings`

## 功能特性

- ✅ 可视化配置 Gitea 连接信息
- ✅ 实时测试连接
- ✅ 密码字段安全显示/隐藏
- ✅ 配置验证和错误提示
- ✅ 一键保存配置

## 配置项说明

### 1. Gitea 服务器地址

**字段**: `gitea_url`

**说明**: Gitea 服务器的完整 URL

**示例**:
- `http://localhost:3000`
- `https://git.example.com`
- `http://192.168.1.100:3000`

**注意**: 必须包含协议（http:// 或 https://）和端口号

### 2. 仓库所有者

**字段**: `gitea_owner`

**说明**: Gitea 用户名或组织名

**示例**:
- `cheersai` (用户名)
- `my-organization` (组织名)

### 3. 仓库名称

**字段**: `gitea_repo`

**说明**: 用于存储文件的仓库名称

**示例**:
- `file-storage`
- `documents`
- `cheersai-files`

**注意**: 仓库必须已在 Gitea 中创建

### 4. API Token

**字段**: `gitea_token`

**说明**: Gitea API 访问令牌

**如何获取**:
1. 登录 Gitea
2. 进入 **设置** → **应用** → **管理访问令牌**
3. 点击 **生成新令牌**
4. 令牌名称: `CheersAI`
5. 选择权限: `repo` (仓库读写权限)
6. 点击 **生成令牌**
7. 复制生成的令牌

**安全提示**:
- Token 显示时会被遮罩（****）
- 点击眼睛图标可以显示/隐藏
- 留空表示不修改现有 Token

## 使用步骤

### 步骤 1: 准备 Gitea 仓库

在 Gitea 中创建一个用于文件存储的仓库：

```bash
# 仓库信息
所有者: cheersai
仓库名: file-storage
可见性: 私有（推荐）或公开
```

### 步骤 2: 生成 API Token

1. 登录 Gitea
2. 设置 → 应用 → 生成新令牌
3. 选择 `repo` 权限
4. 复制生成的 Token

### 步骤 3: 填写配置

访问 `http://localhost:3000/gitea-settings`，填写：

```
Gitea 服务器地址: http://localhost:3000
仓库所有者: cheersai
仓库名称: file-storage
API Token: [粘贴你的 Token]
```

### 步骤 4: 测试连接

点击 **测试连接** 按钮，验证配置是否正确。

**成功提示**:
```
✓ 连接成功
Successfully connected to Gitea! Found X items in repository.
```

**失败提示**:
```
✗ 连接失败
Failed to connect to Gitea: [错误信息]
```

### 步骤 5: 保存配置

测试成功后，点击 **保存配置** 按钮。

## 界面预览

```
┌─────────────────────────────────────────┐
│ Gitea 配置                              │
│ 配置 Gitea 服务器连接信息，用于文件存储 │
├─────────────────────────────────────────┤
│                                         │
│ Gitea 服务器地址                        │
│ [http://localhost:3000              ]  │
│ Gitea 服务器的完整 URL（包括端口）      │
│                                         │
│ 仓库所有者                              │
│ [cheersai                           ]  │
│ Gitea 用户名或组织名                    │
│                                         │
│ 仓库名称                                │
│ [file-storage                       ]  │
│ 用于存储文件的仓库名称                  │
│                                         │
│ API Token                               │
│ [****************************      ] 👁 │
│ 在 Gitea 设置中生成的 API Token         │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ ✓ 连接成功                       │   │
│ │ Successfully connected to Gitea! │   │
│ └─────────────────────────────────┘   │
│                                         │
│ [💾 保存配置] [🔄 测试连接] [重置]     │
├─────────────────────────────────────────┤
│ 📝 配置说明                             │
│ • 在 Gitea 中创建一个用于文件存储的仓库 │
│ • 在 Gitea 设置中生成 API Token         │
│ • 填写配置信息并测试连接                │
│ • 配置成功后，文件选择器将从 Gitea 获取 │
└─────────────────────────────────────────┘
```

## API 接口

### 获取配置

```
GET /console/api/gitea/config
```

**响应**:
```json
{
  "gitea_url": "http://localhost:3000",
  "gitea_owner": "cheersai",
  "gitea_repo": "file-storage",
  "gitea_token": "ghp_****...****"
}
```

### 保存配置

```
POST /console/api/gitea/config
Content-Type: application/json

{
  "gitea_url": "http://localhost:3000",
  "gitea_owner": "cheersai",
  "gitea_repo": "file-storage",
  "gitea_token": "your_token_here"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Gitea configuration updated successfully..."
}
```

### 测试连接

```
POST /console/api/gitea/config/test
Content-Type: application/json

{
  "gitea_url": "http://localhost:3000",
  "gitea_owner": "cheersai",
  "gitea_repo": "file-storage",
  "gitea_token": "your_token_here"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Successfully connected to Gitea! Found 5 items in repository."
}
```

## 常见问题

### Q1: 配置保存后重启失效？

**A**: 当前配置为临时配置（存储在环境变量中），重启后会失效。

**永久配置方法**:

在 `api/.env` 文件中添加：

```bash
GITEA_URL=http://localhost:3000
GITEA_TOKEN=your_token_here
GITEA_OWNER=cheersai
GITEA_REPO=file-storage
```

### Q2: 测试连接失败？

**常见原因**:

1. **Gitea 服务未启动**
   ```bash
   # 检查 Gitea 是否运行
   curl http://localhost:3000
   ```

2. **Token 无效或权限不足**
   - 重新生成 Token
   - 确保选择了 `repo` 权限

3. **仓库不存在**
   - 检查仓库名称是否正确
   - 确认仓库已创建

4. **网络问题**
   - 检查 URL 是否正确
   - 确认端口号是否正确

### Q3: Token 显示为 ****？

**A**: 这是安全措施，防止 Token 泄露。

- 点击眼睛图标可以显示/隐藏
- 留空表示不修改现有 Token
- 只有输入新 Token 时才会更新

### Q4: 如何修改配置？

**A**: 
1. 访问配置页面
2. 修改需要更改的字段
3. 点击"测试连接"验证
4. 点击"保存配置"

### Q5: 配置页面在哪里？

**A**: 访问 `http://localhost:3000/gitea-settings`

或者在应用中添加导航链接。

## 安全建议

### 1. Token 安全

- ✅ 不要在公开场合分享 Token
- ✅ 定期轮换 Token
- ✅ 使用最小权限原则（只授予必要的权限）
- ✅ Token 泄露时立即撤销并重新生成

### 2. 仓库权限

- ✅ 使用私有仓库存储敏感文件
- ✅ 定期审查仓库访问权限
- ✅ 启用 Gitea 的两步验证

### 3. 网络安全

- ✅ 生产环境使用 HTTPS
- ✅ 配置防火墙规则
- ✅ 使用 VPN 或内网访问

## 技术实现

### 后端 API

**文件**: `api/controllers/console/gitea_api/gitea_config.py`

**功能**:
- 读取当前配置（Token 会被遮罩）
- 更新配置（临时存储在环境变量）
- 测试连接（验证配置是否正确）

### 前端页面

**文件**: `web/app/(commonLayout)/gitea-settings/page.tsx`

**功能**:
- 配置表单
- 实时验证
- 测试连接
- 保存配置
- 错误提示

### 配置流程

```
用户填写配置
    ↓
点击"测试连接"
    ↓
POST /console/api/gitea/config/test
    ↓
临时设置环境变量
    ↓
尝试连接 Gitea
    ↓
返回测试结果
    ↓
恢复原环境变量
    ↓
用户确认后点击"保存"
    ↓
POST /console/api/gitea/config
    ↓
更新环境变量
    ↓
配置生效
```

## 相关文件

- `api/controllers/console/gitea_api/gitea_config.py` - 配置 API
- `web/app/(commonLayout)/gitea-settings/page.tsx` - 配置页面
- `api/services/gitea_storage_service.py` - Gitea 存储服务
- `docs/GITEA_SETTINGS_PAGE.md` - 本文档

## 总结

✅ **Gitea 配置页面已完成**

- 可视化配置界面
- 实时测试连接
- 安全的 Token 管理
- 完整的错误处理
- 详细的使用说明

现在用户可以通过 Web 界面轻松配置 Gitea 连接信息！
