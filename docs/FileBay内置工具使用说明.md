# FileBay 内置工具使用说明

## 概述

FileBay 已经作为内置工具集成到 Dify 系统中，无需安装插件即可直接使用。

## 功能特性

FileBay 工具提供以下功能：

1. **读取文件** (`read_file`) - 从 FileBay 仓库读取文件内容
2. **写入文件** (`write_file`) - 向 FileBay 仓库写入或更新文件
3. **列出文件** (`list_files`) - 列出 FileBay 仓库中的文件和目录

## 配置步骤

### 1. 进入工具配置

1. 登录 Dify 控制台: http://localhost:3000
2. 进入 **工作室** (Studio)
3. 点击 **工具** (Tools) 菜单
4. 在内置工具列表中找到 **FileBay**

### 2. 添加 FileBay 凭证

点击 FileBay 工具的 **添加凭证** 按钮，填写以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| FileBay URL | FileBay 实例的基础 URL | `https://uat-filebay.cheersai.cloud` |
| Access Token | FileBay 个人访问令牌 | 从 FileBay 个人设置中生成 |
| Repository Owner | 仓库所有者用户名 | `junqianxi` |
| Repository Name | 仓库名称 | `workspace` |
| Branch | 分支名称（可选） | `main` (默认) |

### 3. 在应用中使用

#### 在对话应用中使用

1. 创建或编辑一个 **对话型应用**
2. 在 **工具** 配置中，添加 **FileBay** 工具
3. 选择刚才配置的凭证
4. 保存并发布应用

现在你可以在对话中使用 FileBay 功能：

**示例对话：**
```
用户: 读取 masked/config.json 文件的内容
AI: [调用 read_file 工具] 文件内容是...

用户: 列出 masked 目录下的所有文件
AI: [调用 list_files 工具] 目录中包含以下文件...
```

#### 在工作流中使用

1. 创建或编辑一个 **工作流应用**
2. 添加 **工具** 节点
3. 选择 **FileBay** 工具
4. 选择具体的工具（read_file 或 list_files）
5. 配置工具参数：
   - **read_file**: 需要 `file_path` 参数
   - **list_files**: 可选 `directory_path` 参数（留空表示根目录）

#### 在探索 (Explore) 应用中使用

探索应用本质上是对话型应用，配置方式相同：

1. 进入探索应用的编辑页面
2. 在工具配置中添加 FileBay
3. 用户可以通过自然语言与 FileBay 交互

## 工具详细说明

### read_file - 读取文件

**功能**: 从 FileBay 仓库读取指定文件的内容

**参数**:
- `file_path` (必填): 文件路径，例如 `masked/config.json`

**返回**:
```json
{
  "file_path": "masked/config.json",
  "content": "文件内容...",
  "size": 1024,
  "sha": "abc123...",
  "branch": "main"
}
```

**使用场景**:
- 读取配置文件
- 查看文档内容
- 获取数据文件
- 检查代码文件

### write_file - 写入文件

**功能**: 向 FileBay 仓库写入或更新文件内容

**参数**:
- `file_path` (必填): 文件保存路径，例如 `uploads/document.pdf`
- `content` (必填): 文件内容（文本或二进制数据）
- `commit_message` (可选): 提交信息，默认为 "Update file via Dify"

**返回**:
```json
{
  "file_path": "uploads/document.pdf",
  "action": "created",
  "commit_message": "Upload new document",
  "branch": "main",
  "size": 2048,
  "sha": "def456..."
}
```

**使用场景**:
- 保存用户上传的文件
- 创建新文件
- 更新现有文件
- 备份数据

### list_files - 列出文件

**功能**: 列出 FileBay 仓库中指定目录的文件和子目录

**参数**:
- `directory_path` (可选): 目录路径，留空表示根目录

**返回**:
```json
{
  "directory": "masked",
  "branch": "main",
  "directories": [
    {
      "name": "subdir",
      "path": "masked/subdir",
      "type": "dir",
      "size": 0,
      "sha": "..."
    }
  ],
  "files": [
    {
      "name": "config.json",
      "path": "masked/config.json",
      "type": "file",
      "size": 1024,
      "sha": "..."
    }
  ],
  "total_directories": 1,
  "total_files": 1
}
```

**使用场景**:
- 浏览目录结构
- 查找文件
- 列出可用配置
- 目录导航

## 与用户账户集成

如果用户账户已经配置了 FileBay 信息（通过 SSO 登录或管理员配置），系统可以自动使用用户的 FileBay 凭证，无需手动配置。

### 查看用户的 FileBay 配置

管理员可以通过以下脚本查看用户的 FileBay 配置：

```bash
cd api
uv run python check_accounts_filebay.py check <用户邮箱>
```

### 为用户设置 FileBay 配置

管理员可以通过以下脚本为用户设置 FileBay 配置：

```bash
cd api
uv run python set_user_filebay_config.py <用户邮箱>
```

## 技术实现

### 架构

```
Dify 应用
    ↓
FileBay 内置工具
    ↓
NoSNI HTTPS 客户端
    ↓
FileBay API (Gitea)
```

### 特点

1. **无需插件**: 直接集成到 Dify 核心系统
2. **SSL 兼容**: 使用自定义 HTTPS 客户端，兼容各种 SSL 配置
3. **凭证管理**: 支持多租户凭证隔离
4. **错误处理**: 完善的错误提示和异常处理

## 故障排查

### 工具列表中找不到 FileBay

**解决方案**:
1. 确认 API 服务已重启
2. 检查 `api/core/tools/builtin_tool/providers/filebay/` 目录是否存在
3. 查看 API 日志是否有加载错误

### 凭证验证失败

**可能原因**:
1. FileBay URL 格式错误（必须以 http:// 或 https:// 开头）
2. Access Token 无效或过期
3. 仓库所有者或仓库名称错误
4. 网络连接问题

**解决方案**:
1. 检查 FileBay URL 是否可访问
2. 在 FileBay 中重新生成 Access Token
3. 确认仓库所有者和仓库名称正确
4. 检查防火墙和网络设置

### 读取文件失败

**可能原因**:
1. 文件路径错误
2. 文件不存在
3. 没有读取权限
4. 分支名称错误

**解决方案**:
1. 使用 `list_files` 工具确认文件路径
2. 检查文件是否存在于指定分支
3. 确认 Access Token 有读取权限
4. 检查分支名称是否正确

## 下一步计划

未来可以扩展以下功能：

1. **写入文件** - 创建或更新文件
2. **删除文件** - 删除指定文件
3. **搜索文件** - 按名称或内容搜索
4. **文件历史** - 查看文件的提交历史
5. **批量操作** - 批量读取或写入多个文件

## 支持

如有问题，请联系技术支持或查看：
- Dify 文档: https://docs.dify.ai
- FileBay (Gitea) API 文档: https://docs.gitea.com/api/
