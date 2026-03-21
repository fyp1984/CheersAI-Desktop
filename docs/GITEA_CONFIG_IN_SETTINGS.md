# Gitea 配置集成到数据安全设置

## 概述

Gitea 文件存储配置已集成到"数据安全"设置页面中，用户可以在一个统一的界面中配置所有安全相关的设置。

## 访问方式

1. 登录 CheersAI
2. 进入"数据安全"页面（通常在左侧导航栏）
3. 滚动到"Gitea 文件存储配置"部分

## 配置界面

### Gitea 文件存储配置

在数据安全页面的底部，你会看到 Gitea 配置部分：

```
┌─────────────────────────────────────┐
│ Gitea 文件存储配置                  │
├─────────────────────────────────────┤
│ Gitea 服务器地址                    │
│ [http://localhost:3000          ]  │
│                                     │
│ 仓库所有者        │ 仓库名称        │
│ [cheersai      ] │ [file-storage] │
│                                     │
│ API Token                           │
│ [**********************        ] 👁 │
│                                     │
│ ┌─────────────────────────────┐   │
│ │ ✓ 连接成功                   │   │
│ │ Successfully connected!      │   │
│ └─────────────────────────────┘   │
│                                     │
│ [保存配置] [测试连接]              │
└─────────────────────────────────────┘
```

## 配置步骤

### 1. 填写 Gitea 服务器地址

输入你的 Gitea 服务器完整 URL：

```
http://localhost:3000
```

或

```
https://git.example.com
```

### 2. 填写仓库信息

- **仓库所有者**: Gitea 用户名或组织名（例如：`cheersai`）
- **仓库名称**: 用于存储文件的仓库（例如：`file-storage`）

### 3. 输入 API Token

在 Gitea 中生成 API Token：

1. 登录 Gitea
2. 设置 → 应用 → 管理访问令牌
3. 生成新令牌，选择 `repo` 权限
4. 复制 Token 并粘贴到配置框中

**安全提示**:
- Token 会被自动遮罩显示（****）
- 点击眼睛图标可以显示/隐藏
- 留空表示不修改现有 Token

### 4. 测试连接

点击"测试连接"按钮验证配置：

**成功**:
```
✓ 连接成功
Successfully connected to Gitea! Found X items in repository.
```

**失败**:
```
✗ 连接失败
Failed to connect to Gitea: [错误信息]
```

### 5. 保存配置

测试成功后，点击"保存配置"按钮。

## 功能特性

### 自动加载配置

页面打开时会自动从后端加载当前的 Gitea 配置。

### 实时验证

- 输入框实时更新
- 测试连接提供即时反馈
- 错误信息清晰显示

### 安全保护

- Token 自动遮罩
- 支持显示/隐藏切换
- 只在输入新 Token 时更新

### 配置持久化

- 配置保存到后端环境变量
- 重启后需要在 `.env` 文件中永久配置

## 与其他功能的集成

### 沙箱文件选择器

配置 Gitea 后，沙箱文件选择器会自动从 Gitea 仓库获取文件列表。

### 文件上传

虽然文件上传仍使用本地存储，但可以通过 Gitea 管理和分发文件。

## API 接口

### 获取配置

```http
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

```http
POST /console/api/gitea/config
Content-Type: application/json

{
  "gitea_url": "http://localhost:3000",
  "gitea_owner": "cheersai",
  "gitea_repo": "file-storage",
  "gitea_token": "your_token_here"
}
```

### 测试连接

```http
POST /console/api/gitea/config/test
Content-Type: application/json

{
  "gitea_url": "http://localhost:3000",
  "gitea_owner": "cheersai",
  "gitea_repo": "file-storage",
  "gitea_token": "your_token_here"
}
```

## 常见问题

### Q1: 配置保存后重启失效？

**A**: 当前配置为临时配置（环境变量），重启后会失效。

**永久配置**: 在 `api/.env` 文件中添加：

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
   curl http://localhost:3000
   ```

2. **Token 无效**
   - 重新生成 Token
   - 确保选择了 `repo` 权限

3. **仓库不存在**
   - 检查仓库名称
   - 确认仓库已创建

4. **网络问题**
   - 检查 URL 是否正确
   - 确认端口号

### Q3: Token 显示为 ****？

**A**: 这是安全措施，防止 Token 泄露。

- 点击眼睛图标可以显示/隐藏
- 留空表示不修改现有 Token
- 只有输入新 Token 时才会更新

### Q4: 如何修改配置？

**A**:
1. 修改需要更改的字段
2. 点击"测试连接"验证
3. 点击"保存配置"

### Q5: 配置在哪里使用？

**A**: Gitea 配置用于：
- 沙箱文件选择器（从 Gitea 获取文件列表）
- 文件下载（从 Gitea 下载文件内容）
- 文件管理（浏览 Gitea 仓库）

## 技术实现

### 前端组件

**文件**: `web/app/components/data-masking/sandbox-config.tsx`

**新增状态**:
```typescript
const [giteaUrl, setGiteaUrl] = useState("")
const [giteaOwner, setGiteaOwner] = useState("")
const [giteaRepo, setGiteaRepo] = useState("")
const [giteaToken, setGiteaToken] = useState("")
const [showGiteaToken, setShowGiteaToken] = useState(false)
const [giteaTestResult, setGiteaTestResult] = useState(null)
const [giteaTesting, setGiteaTesting] = useState(false)
const [giteaSaving, setGiteaSaving] = useState(false)
```

**新增函数**:
- `handleGiteaSave()` - 保存配置
- `handleGiteaTest()` - 测试连接

### 后端 API

**文件**: `api/controllers/console/gitea_api/gitea_config.py`

**端点**:
- `GET /console/api/gitea/config` - 获取配置
- `POST /console/api/gitea/config` - 保存配置
- `POST /console/api/gitea/config/test` - 测试连接

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

## 界面布局

在数据安全页面中，Gitea 配置位于：

1. 沙箱安全模式
2. 发送敏感信息提醒
3. 映射文件加密
4. 当前沙箱路径
5. 沙箱目录路径
6. AI 回复下载路径
7. **Gitea 文件存储配置** ← 新增
8. 使用说明

## 相关文件

- `web/app/components/data-masking/sandbox-config.tsx` - 配置组件
- `api/controllers/console/gitea_api/gitea_config.py` - 配置 API
- `api/services/gitea_storage_service.py` - Gitea 存储服务
- `web/app/components/base/sandbox-file-picker/index.tsx` - 文件选择器

## 总结

✅ **Gitea 配置已集成到数据安全设置**

- 统一的配置界面
- 实时测试连接
- 安全的 Token 管理
- 完整的错误处理
- 与文件选择器无缝集成

现在用户可以在"数据安全"页面中一站式配置所有安全相关设置，包括 Gitea 文件存储！
